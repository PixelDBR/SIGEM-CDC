import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta, time

# Configuração Inicial da Página
st.set_page_config(
    page_title="SIGEM - Gestão Escolar & Mecanografia", 
    page_icon="🏫", 
    layout="wide"
)

# -----------------------------------------------------------------------------
# 1. BANCO DE DADOS (SQLITE) - PERSISTÊNCIA REAL DE DADOS
# -----------------------------------------------------------------------------

def conectar_bd():
    conn = sqlite3.connect("escola.db", check_same_thread=False)
    return conn

def inicializar_bd():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Tabela de Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            login TEXT PRIMARY KEY,
            senha TEXT,
            nivel TEXT,
            nome TEXT,
            email TEXT
        )
    """)
    
    # Tabela de Reservas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solicitante TEXT,
            nivel TEXT,
            tipo TEXT,
            recurso TEXT,
            quantidade INTEGER,
            data_reserva TEXT,
            horario TEXT,
            observacao TEXT,
            status TEXT
        )
    """)
    
    # Tabela de Impressões
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS impressoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solicitante TEXT,
            email TEXT,
            tipo_documento TEXT,
            data_necessidade TEXT,
            copias INTEGER,
            cor TEXT,
            observacao TEXT,
            status TEXT
        )
    """)

    # Tabela de Estoque de Insumos da Mecanografia
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumos (
            codigo INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT UNIQUE,
            qtd_estoque INTEGER,
            qtd_minima INTEGER,
            unidade TEXT
        )
    """)
    
    # Inserir usuários padrão caso não existam
    usuarios_padrao = [
        ("Nicolas A", "1234", "Administrador", "Nicolau", "nicolau@gmail.com"),
        ("J Pedro", "1234", "Administrador", "Joao Pedro", "jpedro@gmail.com"),
        ("J Wender", "1234", "Administrador", "+Novo", "jwender@gmail.com"),
        ("Ryan", "1234", "Administrador", "Ryan", "ryan@gmail.com"),
        ("Gabriel", "1234", "Administrador", "Gabriel", "gabriel@gmail.com"),
        ("Professor", "1234", "Professor", "Professor(a) Genérico(a)", "professor@gmail.com"),
        ("Coordenação", "1234", "Coordenação", "Coordenador(a) Genérico(a)", "coordenacao@gmail.com")
    ]
    cursor.executemany("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?,?)", usuarios_padrao)

    # Inserir insumos padrão de mecanografia caso não existam
    insumos_padrao = [
        ("Papel A4 (Folhas)", 5000, 1000, "Unidades"),
        ("Toner HP Preto", 10, 2, "Unidades"),
        ("Toner HP Colorido", 5, 1, "Unidades")
    ]
    cursor.executemany("INSERT OR IGNORE INTO insumos (descricao, qtd_estoque, qtd_minima, unidade) VALUES (?,?,?,?)", insumos_padrao)

    conn.commit()
    conn.close()

# Inicializa o banco de dados ao abrir a aplicação
inicializar_bd()

ESTOQUE_EQUIPAMENTOS = {
    "Datashow": 5,
    "Controle da TV": 4,
    "Caixa de Som": 3,
    "Microfone": 4,
    "Bolas de Futebol": 10,
    "Bolas de Vôlei": 8,
    "Kits de Coletes": 5,
    "Cones de Treinamento": 15
}

# Inicialização do Estado de Login na Sessão do Navegador
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_atual = None
    st.session_state.nivel_acesso = None
    st.session_state.nome_usuario = None
    st.session_state.email_usuario = None

# -----------------------------------------------------------------------------
# 2. TELA DE LOGIN
# -----------------------------------------------------------------------------

def tela_login():
    st.title("🏫 Sistema Integrado de Gestão e Mecanografia (SIGEM)")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔑 Acesso ao Sistema")
        usuario_input = st.text_input("Usuário:")
        senha_input = st.text_input("Senha:", type="password")
        
        if st.button("Entrar", use_container_width=True):
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("SELECT senha, nivel, nome, email FROM usuarios WHERE login = ?", (usuario_input,))
            user = cursor.fetchone()
            conn.close()
            
            if user and user[0] == senha_input:
                st.session_state.logado = True
                st.session_state.usuario_atual = usuario_input
                st.session_state.nivel_acesso = user[1]
                st.session_state.nome_usuario = user[2]
                st.session_state.email_usuario = user[3]
                st.success(f"Bem-vindo(a), {st.session_state.nome_usuario}!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

# -----------------------------------------------------------------------------
# 3. SISTEMA PRINCIPAL
# -----------------------------------------------------------------------------

def sistema_principal():
    st.sidebar.title("👤 Perfil do Usuário")
    st.sidebar.write(f"**Nome:** {st.session_state.nome_usuario}")
    st.sidebar.write(f"**E-mail:** {st.session_state.email_usuario}")
    st.sidebar.write(f"**Nível:** `{st.session_state.nivel_acesso}`")
    
    if st.sidebar.button("Sair (Logout)"):
        st.session_state.logado = False
        st.rerun()

    st.title("📌 Painel de Gestão e Pedidos")

    abas = ["🖨️ Solicitar Impressão", "📅 Reservar Recursos", "📋 Painel de Solicitações"]
    if st.session_state.nivel_acesso in ["Administrador", "Coordenação"]:
        abas.append("📊 Gestão da Coordenação")
        
    guias = st.tabs(abas)

    # -------------------------------------------------------------------------
    # ABA 1: SOLICITAR IMPRESSÃO
    # -------------------------------------------------------------------------
    with guias[0]:
        st.header("🖨️ Solicitação de Impressão (Mecanografia)")
        
        # RN01: Validação de Antecedência Mínima de 48 Horas
        data_minima = date.today() + timedelta(days=2)
        st.info("ℹ **Antes de fazer sua solicitação, envie o arquivo no e-mail. Essas informações serão necessárias apenas para confirmar sua identidade.**")
        
        with st.form("form_impressao", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                nome_prof = st.text_input("Nome do Solicitante:")
                email_prof = st.text_input("E-mail de Contato:")
                tipo_documento = st.selectbox(
                    "Tipo de Documento:", 
                    [".pdf", ".png", ".jpg", ".txt(Texto)", ".docx(Word)", ".pptx(PowerPoint)", ".xlsx(Excel)", "Outro"],
                    index=None,
                    placeholder="Selecione um formato..."
                )
                
            with col2:
                data_necessidade = st.date_input("Para quando precisa do material pronto?", min_value=data_minima, value=data_minima)
                qtd_copias = st.number_input("Quantidade de Cópias:", min_value=1, value=30)
                formato_cor = st.radio("Impressão:", ["Preto e Branco", "Colorida"])

            obs_impressao = st.text_area("Observações para a Mecanografia:", placeholder="Ex: Grampear em duplas, imprimir frente e verso.")
            
            btn_enviar_impressao = st.form_submit_button("Enviar Solicitação de Impressão")

            if btn_enviar_impressao:
                if not tipo_documento:
                    st.error("❌ Por favor, selecione o tipo de documento antes de enviar.")
                else:
                    solicitante_final = nome_prof if nome_prof else st.session_state.nome_usuario
                    email_final = email_prof if email_prof else st.session_state.email_usuario

                    conn = conectar_bd()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO impressoes (solicitante, email, tipo_documento, data_necessidade, copias, cor, observacao, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        solicitante_final, email_final, tipo_documento, 
                        data_necessidade.strftime("%d/%m/%Y"), qtd_copias, formato_cor, 
                        obs_impressao if obs_impressao else "Sem observações", "Pendente"
                    ))
                    conn.commit()
                    conn.close()

                    st.success("✅ Solicitação gravada no banco de dados com sucesso!")
                    
                    st.markdown("### 📄 Confirmação do Envio")
                    with st.container(border=True):
                        st.write(f"👤 **Nome do Professor:** {solicitante_final}")
                        st.write(f"📧 **E-mail de Confirmação:** {email_final}")
                        st.write(f"📑 **Tipo do Documento:** {tipo_documento}")
                        st.write(f"📅 **Data Limite de Entrega:** {data_necessidade.strftime('%d/%m/%Y')}")
                        st.write(f"🔢 **Quantidade de Cópias:** {qtd_copias} ({formato_cor})")
                        if obs_impressao:
                            st.write(f"📝 **Observação:** {obs_impressao}")

    # -------------------------------------------------------------------------
    # ABA 2: RESERVAR RECURSOS
    # -------------------------------------------------------------------------
    with guias[1]:
        st.header("Realizar Reserva de Recursos")
        
        tipo_reserva = st.selectbox(
            "O que você deseja reservar?",
            ["Laboratório", "Equipamento Tecnológico", "Equipamento de Educação Física"]
        )

        with st.form("form_reserva", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                data_reserva = st.date_input("Data da Reserva:", min_value=date.today())
                hora_inicio = st.time_input("Horário de Início:", value=time(7, 30))
                hora_fim = st.time_input("Horário de Término:", value=time(8, 20))

            with col2:
                recurso_selecionado = ""
                qtd_reservada = 1

                if tipo_reserva == "Laboratório":
                    recurso_selecionado = st.selectbox("Escolha o Laboratório:", [
                        "Laboratório de Informática 1",
                        "Laboratório de Informática 2",
                        "Laboratório de Ciências / Biologia",
                        "Laboratório de Química / Física"
                    ])
                    qtd_reservada = 1
                    
                elif tipo_reserva == "Equipamento Tecnológico":
                    recurso_selecionado = st.selectbox("Escolha o Equipamento:", [
                        "Datashow", "Controle da TV", "Caixa de Som", "Microfone"
                    ])
                    max_disp = ESTOQUE_EQUIPAMENTOS[recurso_selecionado]
                    qtd_reservada = st.number_input(f"Quantidade (Max: {max_disp}):", min_value=1, max_value=max_disp, value=1)

                elif tipo_reserva == "Equipamento de Educação Física":
                    recurso_selecionado = st.selectbox("Escolha o Material:", [
                        "Bolas de Futebol", "Bolas de Vôlei", "Kits de Coletes", "Cones de Treinamento"
                    ])
                    max_disp = ESTOQUE_EQUIPAMENTOS[recurso_selecionado]
                    qtd_reservada = st.number_input(f"Quantidade (Max: {max_disp}):", min_value=1, max_value=max_disp, value=1)

            observacao = st.text_area("Observações / Finalidade Pedagógica:")
            btn_submeter = st.form_submit_button("Confirmar Reserva")

            if btn_submeter:
                status_inicial = "Pendente"
                
                conn = conectar_bd()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO reservas (solicitante, nivel, tipo, recurso, quantidade, data_reserva, horario, observacao, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    st.session_state.nome_usuario, st.session_state.nivel_acesso,
                    tipo_reserva, recurso_selecionado, qtd_reservada,
                    data_reserva.strftime("%d/%m/%Y"), f"{hora_inicio.strftime('%H:%M')} às {hora_fim.strftime('%H:%M')}",
                    observacao if observacao else "Nenhuma", status_inicial
                ))
                conn.commit()
                conn.close()

                st.success("Reserva enviada para análise e gravada com sucesso!")

    # -------------------------------------------------------------------------
    # ABA 3: PAINEL DE SOLICITAÇÕES
    # -------------------------------------------------------------------------
    with guias[2]:
        st.header("📋 Histórico de Pedidos e Reservas")
        
        conn = conectar_bd()
        
        st.subheader("🖨️ Solicitações de Impressão Enviadas")
        if st.session_state.nivel_acesso == "Professor":
            # Busca todas as impressões associadas ao e-mail ou ao nome do usuário logado
            query_imp = "SELECT * FROM impressoes WHERE LOWER(email) = LOWER(?) OR LOWER(solicitante) = LOWER(?)"
            df_imp = pd.read_sql_query(query_imp, conn, params=(st.session_state.email_usuario, st.session_state.nome_usuario))
        else:
            df_imp = pd.read_sql_query("SELECT * FROM impressoes", conn)
            
        if not df_imp.empty:
            st.dataframe(df_imp, use_container_width=True)
        else:
            st.info("Nenhuma solicitação de impressão encontrada.")

        st.divider()

        st.subheader("📅 Reservas de Recursos (Laboratórios/Materiais)")
        if st.session_state.nivel_acesso == "Professor":
            query_res = "SELECT * FROM reservas WHERE LOWER(solicitante) = LOWER(?)"
            df_res = pd.read_sql_query(query_res, conn, params=(st.session_state.nome_usuario,))
        else:
            df_res = pd.read_sql_query("SELECT * FROM reservas", conn)

        if not df_res.empty:
            st.dataframe(df_res, use_container_width=True)
        else:
            st.info("Nenhuma reserva encontrada.")
            
        conn.close()

    # -------------------------------------------------------------------------
    # ABA 4: PAINEL DA COORDENAÇÃO / MECANOGRAFIA
    # -------------------------------------------------------------------------
    if st.session_state.nivel_acesso in ["Administrador", "Coordenação"]:
        with guias[3]:
            st.header("⚙️ Controle de Mecanografia e Gestão de Pedidos")
            
            conn = conectar_bd()
            cursor = conn.cursor()
            
            # --- SEÇÃO DE ALERTAS DE ESTOQUE DE INSUMOS ---
            cursor.execute("SELECT descricao, qtd_estoque, qtd_minima, unidade FROM insumos WHERE qtd_estoque <= qtd_minima")
            alertas = cursor.fetchall()
            if alertas:
                for item in alertas:
                    st.warning(f"⚠️ **Alerta de Insumo Crítico:** O item **{item[0]}** está em nível crítico! Estoque Atual: {item[1]} {item[3]} (Mínimo: {item[2]} {item[3]}).")

            # --- SEÇÃO 1: SOLICITAÇÕES DE IMPRESSÃO ---
            st.subheader("🖨️ Fila de Impressão Pendente")
            cursor.execute("SELECT * FROM impressoes WHERE status = 'Pendente'")
            impressoes_pendentes = cursor.fetchall()
            
            if impressoes_pendentes:
                for item in impressoes_pendentes:
                    imp_id, solicitante, email, tipo_doc, dt_necessidade, copias, cor, obs, status = item
                    
                    with st.expander(f"Impressão #{imp_id} - {solicitante} ({tipo_doc})"):
                        st.write(f"**E-mail:** {email}")
                        st.write(f"**Para a Data:** {dt_necessidade}")
                        st.write(f"**Cópias requeridas:** {copias} ({cor})")
                        st.write(f"**Observação:** {obs}")
                        
                        col1, col2 = st.columns(2)
                        if col1.button("✅ Concluir/Aprovar e Dar Baixa de Papel", key=f"ap_imp_{imp_id}"):
                            # RN04: Baixa Automática de Insumos (Deduz o papel do estoque)
                            cursor.execute("UPDATE insumos SET qtd_estoque = qtd_estoque - ? WHERE descricao LIKE '%Papel A4%'", (copias,))
                            cursor.execute("UPDATE impressoes SET status = 'Aprovada / Concluída' WHERE id = ?", (imp_id,))
                            conn.commit()
                            st.success(f"Solicitação #{imp_id} aprovada! Abatidas {copias} folhas de papel A4 do estoque.")
                            st.rerun()
                            
                        if col2.button("❌ Recusar", key=f"rec_imp_{imp_id}"):
                            cursor.execute("UPDATE impressoes SET status = 'Recusada' WHERE id = ?", (imp_id,))
                            conn.commit()
                            st.rerun()
            else:
                st.info("Nenhuma solicitação de impressão pendente.")

            st.divider()

            # --- SEÇÃO 2: FILA DE RESERVAS DE EQUIPAMENTOS E SALAS ---
            st.subheader("📅 Fila de Reservas de Recursos e Espaços Pendentes")
            cursor.execute("SELECT * FROM reservas WHERE status = 'Pendente'")
            reservas_pendentes = cursor.fetchall()
            
            if reservas_pendentes:
                for item in reservas_pendentes:
                    res_id, solicitante, nivel, tipo_reserva_item, recurso, qtd, dt, hr, obs, status = item
                    
                    with st.expander(f"Reserva #{res_id} - {solicitante} ({recurso})"):
                        st.write(f"**Tipo de Recurso:** {tipo_reserva_item}")
                        st.write(f"**Solicitante (Cargo):** {solicitante} ({nivel})")
                        st.write(f"**Data Agendada:** {dt}")
                        st.write(f"**Horário:** {hr}")
                        st.write(f"**Quantidade Solicitada:** {qtd}")
                        st.write(f"**Observação/Finalidade Pedagógica:** {obs}")
                        
                        col_ap, col_rec = st.columns(2)
                        if col_ap.button("✅ Aprovar Reserva", key=f"ap_res_{res_id}"):
                            cursor.execute("UPDATE reservas SET status = 'Aprovada' WHERE id = ?", (res_id,))
                            conn.commit()
                            st.success(f"Reserva #{res_id} aprovada com sucesso!")
                            st.rerun()
                            
                        if col_rec.button("❌ Recusar Reserva", key=f"rec_res_{res_id}"):
                            cursor.execute("UPDATE reservas SET status = 'Recusada' WHERE id = ?", (res_id,))
                            conn.commit()
                            st.rerun()
            else:
                st.info("Nenhuma reserva de recurso pendente no momento.")

            st.divider()
            
            # --- SEÇÃO 3: GESTÃO DO ESTOQUE DE INSUMOS DE IMPRESSÃO ---
            st.subheader("📦 Estoque de Insumos de Reprografia e Impressão (Mecanografia)")
            df_insumos = pd.read_sql_query("SELECT codigo AS 'Código', descricao AS 'Item/Insumo', qtd_estoque AS 'Qtd Atual', qtd_minima AS 'Qtd Mínima', unidade AS 'Unidade' FROM insumos", conn)
            st.dataframe(df_insumos, use_container_width=True)

            st.divider()
            st.subheader("⚽ Equipamentos Tecnológicos e de Educação Física")
            st.json(ESTOQUE_EQUIPAMENTOS)

            conn.close()

# -----------------------------------------------------------------------------
# 4. EXECUÇÃO DO FLUXO
# -----------------------------------------------------------------------------
if not st.session_state.logado:
    tela_login()
else:
    sistema_principal()