import streamlit as st
import sqlite3
import hashlib # biblioteca que salva a senha criptografada


arquivo_bd = "usuarios.db" #define o nome do arquivo do banco de dados

# função que inicia e cria a tabela de usuarios no banco de dados
def init_db():
    with sqlite3.connect(arquivo_bd) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
            nome_usuario TEXT PRIMARY KEY,
            senha TEXT NOT NULL
            )
        """    
        )
    conn.commit()

# função que criptografa as senhas, para salva-las com segurança no banco de dados
def hashar_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

#função para criar usuario
def criar_usuario(nome_usuario, senha):
    
    try:
        with sqlite3.connect(arquivo_bd) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios(nome_usuario, senha) VALUES(?,?)", (nome_usuario, hashar_senha(senha)),
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

#função que autentica o usuario, usando os dados do arquivo do banco de dados
def autenticar_usuario(nome_usuario, senha):
    with sqlite3.connect(arquivo_bd) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT senha FROM usuarios WHERE nome_usuario = ?", (nome_usuario,)
        )
        resultado = cursor.fetchone()
        if resultado and resultado[0] == hashar_senha(senha):
            return True
        return False
#inicia o banco de dados
init_db()
if "logged_in" not in st.session_state: #checa se o usuario ja está logado 
    st.session_state.logged_in = False
if "username" not in st.session_state: #checa qual o nome do usuario
    st.session_state.username = ""

if st.session_state.logged_in:
    st.sidebar.image(
        "/home/Jaopedro/Documentos/SIGEM-CDC/SIGEM(1)(1).png",
        width=500
    )
    st.set_page_config(initial_sidebar_state="expanded")
    st.title(f"Bem-Vindo, {st.session_state.username}!")

    #cria um botão para sair do login
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
else:
    st.sidebar.image(
        "/home/Jaopedro/Documentos/SIGEM-CDC/SIGEM(1)(1).png",
        width=500
    )
    st.set_page_config(initial_sidebar_state="expanded")
    st.title("AUTENTICAÇÃO DO SIGEM")

    tab1, tab2 = st.tabs(["Fazer login", "Cadastrar"])

    with tab1:
        st.subheader("Faça login na sua conta")
        with st.form("campo_login"):
            login_usuario = st.text_input("Usuário").strip()
            login_senha = st.text_input("Senha", type="password")
            enviar_login = st.form_submit_button("Logar")

            if enviar_login:
                if login_usuario and login_senha:
                    if autenticar_usuario(login_usuario, login_senha):
                        st.session_state.logged_in = True
                        st.session_state.username = login_usuario
                        st.success("Login Bem-sucedido!")
                        st.rerun()
                    else:
                        st.error("Nome de usuário ou senha inválidos.")
                else:
                    st.warning("preencha todos os campos.")
    with tab2:
        st.subheader("Cadastre-se.")
        with st.form("Faça seu cadastro"):
            novo_usuario = st.text_input("Usuário").strip()
            nova_senha = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirmar Senha", type="password")
            enviar_cadastro = st.form_submit_button("Cadastrar")

            if enviar_cadastro:
                if not novo_usuario or not nova_senha:
                    st.warning("Preencha todos os campos.")
                elif nova_senha != confirmar_senha:
                    st.error("As senhas não coincidem")
                else:
                    if criar_usuario(novo_usuario, nova_senha):
                        st.success("Cadastro bem-sucedido! Vá para a aba de Login.")
                    else:
                        st.error("Já existe um usuario com este nome. Escolha outro.")
                    