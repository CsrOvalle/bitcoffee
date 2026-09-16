import base64
import hashlib
import os
import re
import secrets
import smtplib
import sqlite3
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Bitcoffee | PIT-II",
    page_icon="☕",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp, [data-testid="stHeader"] {
        background-color: #8B2613 !important;
    }

    h1, h2, h3, h4, h5, h6, p, label {
        color: #FFFFFF !important;
    }

    div.stButton > button {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        border: 1px solid #DDDDDD !important;
        font-weight: bold !important;
        border-radius: 6px !important;
    }

    div.stButton > button p,
    div.stButton > button span,
    div.stButton > button div,
    button[kind] p,
    button[kind] span {
        color: #000000 !important;
    }

    div.stButton > button:hover {
        background-color: #D3D3D3 !important;
        border-color: #FFFFFF !important;
        color: #000000 !important;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
        color: #1A1A1A !important;
        background-color: #FFFFFF !important;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        min-height: 2rem !important;
        height: 2rem !important;
    }

    div[data-testid="stTextInput"] input {
        padding: 0.25rem 0.65rem !important;
        font-size: 0.9rem !important;
    }

    div[data-testid="stTextInput"] label {
        margin-bottom: 0.15rem !important;
        font-size: 0.82rem !important;
    }

    div[data-baseweb="select"] > div {
        color: #1A1A1A !important;
        background-color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PRODUTOS = [
    {
        "id": 1,
        "nome": "Bourbon Amarelo 250g",
        "preco": 38.90,
        "desc": "Café 100% Arábica de alta qualidade com notas de chocolate e caramelo.",
    },
    {
        "id": 2,
        "nome": "Chapada Diamantina 250g",
        "preco": 42.50,
        "desc": "Grãos selecionados com acidez equilibrada e aroma marcante.",
    },
    {
        "id": 3,
        "nome": "Blend Especial 250g",
        "preco": 35.00,
        "desc": "Combinação exclusiva de grãos para um café encorpado.",
    },
]

TELA_INICIAL = "TELA201 - PRINCIPAL"

DB_PATH = Path(__file__).with_name("bitcoffee.db")


def conectar_banco():
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco():
    with conectar_banco() as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                senha_hash TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
            """
        )
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens_recuperacao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expira_em TEXT NOT NULL,
                utilizado INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def gerar_hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def email_cadastrado(email: str) -> bool:
    with conectar_banco() as conexao:
        registro = conexao.execute(
            "SELECT 1 FROM usuarios WHERE email = ? COLLATE NOCASE", (email.strip(),)
        ).fetchone()
    return registro is not None


def cadastrar_usuario(email: str, senha: str) -> bool:
    try:
        with conectar_banco() as conexao:
            conexao.execute(
                "INSERT INTO usuarios (email, senha_hash, criado_em) VALUES (?, ?, ?)",
                (email.strip().lower(), gerar_hash_senha(senha), datetime.now(timezone.utc).isoformat()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def autenticar_usuario(email: str, senha: str) -> bool:
    with conectar_banco() as conexao:
        registro = conexao.execute(
            "SELECT senha_hash FROM usuarios WHERE email = ? COLLATE NOCASE", (email.strip(),)
        ).fetchone()
    return registro is not None and registro["senha_hash"] == gerar_hash_senha(senha)


def registrar_token_recuperacao(email: str, token: str) -> None:
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=5)
    with conectar_banco() as conexao:
        conexao.execute(
            "UPDATE tokens_recuperacao SET utilizado = 1 WHERE email = ? AND utilizado = 0",
            (email.strip().lower(),),
        )
        conexao.execute(
            "INSERT INTO tokens_recuperacao (email, token_hash, expira_em) VALUES (?, ?, ?)",
            (email.strip().lower(), gerar_hash_senha(token), expira_em.isoformat()),
        )


def enviar_email_recuperacao(email: str, token: str) -> tuple[bool, str]:
    """Envia o e-mail quando as variáveis SMTP estiverem configuradas."""
    smtp_host = os.getenv("BITCOFFEE_SMTP_HOST")
    smtp_port = int(os.getenv("BITCOFFEE_SMTP_PORT", "587"))
    smtp_user = os.getenv("BITCOFFEE_SMTP_USER")
    smtp_password = os.getenv("BITCOFFEE_SMTP_PASSWORD")
    remetente = os.getenv("BITCOFFEE_SMTP_FROM", smtp_user or "")

    registrar_token_recuperacao(email, token)

    if not all((smtp_host, smtp_user, smtp_password, remetente)):
        return False, "SMTP não configurado. O token foi registrado apenas para demonstração local."

    mensagem = EmailMessage()
    mensagem["Subject"] = "Bitcoffee — recuperação de senha"
    mensagem["From"] = remetente
    mensagem["To"] = email
    mensagem.set_content(
        f"Olá!\n\nUse o token {token} para redefinir sua senha da Bitcoffee. "
        "Este token expira em 5 minutos.\n\nSe você não solicitou isso, ignore esta mensagem."
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as servidor:
            servidor.starttls()
            servidor.login(smtp_user, smtp_password)
            servidor.send_message(mensagem)
        return True, "E-mail de recuperação enviado. O token é válido por 5 minutos."
    except (OSError, smtplib.SMTPException) as erro:
        return False, f"Não foi possível enviar o e-mail pelo SMTP: {erro}"


inicializar_banco()

if "tela_atual" not in st.session_state:
    st.session_state.tela_atual = TELA_INICIAL
if "carrinho" not in st.session_state:
    st.session_state.carrinho = []
if "produto_selecionado" not in st.session_state:
    st.session_state.produto_selecionado = None
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
if "subtotal_compra" not in st.session_state:
    st.session_state.subtotal_compra = 0.0
if "cupom_aplicado" not in st.session_state:
    st.session_state.cupom_aplicado = ""
if "desconto" not in st.session_state:
    st.session_state.desconto = 0.0


def navegar_para(nome_tela: str) -> None:
    """Altera a tela atual e reinicia a execução do Streamlit."""
    st.session_state.tela_atual = nome_tela
    st.rerun()


def formatar_moeda(valor: float) -> str:
    """Formata valores no padrão visual brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def imagem_generica(texto: str = "Bitcoffee", largura: int = 260) -> None:
    """Exibe uma imagem local simples, sem depender de URL externa."""
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="170" viewBox="0 0 520 340">
      <defs>
        <linearGradient id="fundo" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#b63b19"/>
          <stop offset="100%" stop-color="#4a180e"/>
        </linearGradient>
      </defs>
      <rect width="520" height="340" rx="24" fill="url(#fundo)"/>
      <circle cx="260" cy="150" r="72" fill="none" stroke="#f5d7a5" stroke-width="5" opacity=".8"/>
      <path d="M215 130h85v45c0 25-18 42-42 42s-43-17-43-42z" fill="none" stroke="#fff8ec" stroke-width="7"/>
      <path d="M300 142h22c19 0 31 11 31 27s-12 27-31 27h-18" fill="none" stroke="#fff8ec" stroke-width="7"/>
      <text x="260" y="265" text-anchor="middle" fill="#fff8ec" font-family="Arial" font-size="20" letter-spacing="4">{texto}</text>
    </svg>
    """
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    st.image(f"data:image/svg+xml;base64,{encoded}", width=largura)


def render_header() -> None:
    col_logo, col_usuario, col_carrinho = st.columns([6, 2, 2])
    with col_logo:
        st.title("☕ Bitcoffee")
    with col_usuario:
        if st.session_state.usuario_logado:
            st.write(f"👤 {st.session_state.usuario_logado}")
            if st.button("Sair", key="sair_header"):
                st.session_state.usuario_logado = None
                navegar_para(TELA_INICIAL)
        elif st.button("Entrar", key="entrar_header"):
            navegar_para("TELA101 - LOGIN")
    with col_carrinho:
        quantidade = sum(item["quantidade"] for item in st.session_state.carrinho)
        if st.button(f"🛒 Carrinho ({quantidade})", key="carrinho_header"):
            navegar_para("TELA203 - PEDIDO")
    st.divider()


def buscar_produto(produto_id: int):
    return next((produto for produto in PRODUTOS if produto["id"] == produto_id), None)


def adicionar_ao_carrinho(produto: dict) -> None:
    for item in st.session_state.carrinho:
        if item["produto"]["id"] == produto["id"]:
            item["quantidade"] += 1
            break
    else:
        st.session_state.carrinho.append({"produto": produto, "quantidade": 1})
    st.success("Produto adicionado ao carrinho!")


def calcular_subtotal() -> float:
    return sum(
        item["produto"]["preco"] * item["quantidade"]
        for item in st.session_state.carrinho
    )
    
if st.session_state.tela_atual == TELA_INICIAL:
    render_header()
    termo = st.text_input(
        "Pesquisar",
        placeholder="Pesquise por produto...",
        label_visibility="collapsed",
        key="busca_produto",
    ).strip().lower()

    st.subheader("Catálogo de Cafés Especiais")
    produtos_filtrados = [
        produto
        for produto in PRODUTOS
        if termo in produto["nome"].lower() or termo in produto["desc"].lower()
    ]

    if not produtos_filtrados:
        st.info("Nenhum produto encontrado para essa busca.")
    else:
        colunas = st.columns(3)
        for indice, produto in enumerate(produtos_filtrados):
            with colunas[indice % 3]:
                imagem_generica("BITCOFFEE", 220)
                st.write(f"**{produto['nome']}**")
                st.write(formatar_moeda(produto["preco"]))
                st.caption(produto["desc"])
                if st.button("Ver detalhes", key=f"detalhe_{produto['id']}"):
                    st.session_state.produto_selecionado = produto
                    navegar_para("TELA206 - DESCRIÇÃO")
                    
elif st.session_state.tela_atual == "TELA206 - DESCRIÇÃO":
    if st.button("← Menu principal", key="menu_principal_descricao"):
        navegar_para(TELA_INICIAL)
    if st.button("⬅️ Voltar", key="voltar_descricao"):
        navegar_para(TELA_INICIAL)

    produto = st.session_state.produto_selecionado or PRODUTOS[0]
    st.title("☕ Bitcoffee")
    coluna_imagem, coluna_dados = st.columns([1, 1])
    with coluna_imagem:
        imagem_generica("BITCOFFEE", 320)
    with coluna_dados:
        st.subheader(produto["nome"])
        st.write("⭐⭐⭐⭐☆  Avalie aqui")
        st.write("**Descrição:**")
        st.write(produto["desc"])
        st.write(f"### {formatar_moeda(produto['preco'])}")
        if st.button("Adicionar ao carrinho", key="adicionar_detalhes"):
            adicionar_ao_carrinho(produto)
            
elif st.session_state.tela_atual == "TELA203 - PEDIDO":
    if st.button("← Menu principal", key="menu_principal_pedido"):
        navegar_para(TELA_INICIAL)
    render_header()
    st.subheader("TELA203 - PEDIDO")

    if not st.session_state.carrinho:
        st.info("Seu carrinho está vazio.")
        if st.button("Voltar às compras", key="voltar_compras_vazio"):
            navegar_para(TELA_INICIAL)
    else:
        for indice, item in enumerate(st.session_state.carrinho):
            produto = item["produto"]
            coluna_imagem, coluna_dados, coluna_qtd, coluna_remover = st.columns([1, 3, 2, 1])
            with coluna_imagem:
                imagem_generica("CAFÉ", 90)
            with coluna_dados:
                st.write(f"**{produto['nome']}**")
                st.write(formatar_moeda(produto["preco"]))
            with coluna_qtd:
                item["quantidade"] = st.number_input(
                    "Quantidade",
                    min_value=1,
                    max_value=99,
                    value=item["quantidade"],
                    key=f"quantidade_{produto['id']}",
                )
            with coluna_remover:
                if st.button("Remover", key=f"remover_{produto['id']}"):
                    st.session_state.carrinho.pop(indice)
                    st.rerun()
            st.divider()

        subtotal = calcular_subtotal()
        st.write(f"### Subtotal: {formatar_moeda(subtotal)}")
        st.text_input("CEP para calcular frete", placeholder="Digite seu CEP", key="cep_frete")

        if st.button("Finalizar pedido", key="finalizar_pedido"):
            st.session_state.subtotal_compra = subtotal
            navegar_para("TELA202 - PAGAMENTO")
            
elif st.session_state.tela_atual == "TELA202 - PAGAMENTO":
    if st.button("← Menu principal", key="menu_principal_pagamento"):
        navegar_para(TELA_INICIAL)
    if st.button("⬅️ Voltar ao pedido", key="voltar_pagamento"):
        navegar_para("TELA203 - PEDIDO")

    st.title("☕ Bitcoffee")
    st.subheader("TELA202 - PAGAMENTO")
    subtotal = st.session_state.subtotal_compra
    st.write(f"Subtotal: **{formatar_moeda(subtotal)}**")

    opcao_pagamento = st.radio(
        "Selecione a opção de pagamento",
        ["Pix", "Cartão"],
        horizontal=True,
        key="opcao_pagamento",
    )
    codigo_cupom = st.text_input("Insira aqui o cupom de desconto", key="codigo_cupom")

    if st.button("Aplicar cupom", key="aplicar_cupom"):
        if codigo_cupom.strip().upper() == "BIT10":
            st.session_state.cupom_aplicado = "BIT10"
            st.session_state.desconto = subtotal * 0.10
            st.success("Cupom aplicado: 10% de desconto.")
        elif codigo_cupom.strip():
            st.session_state.cupom_aplicado = ""
            st.session_state.desconto = 0.0
            st.warning("Cupom não encontrado.")

    if opcao_pagamento == "Pix":
        email_recibo = st.text_input("E-mail para receber o comprovante", key="email_recibo")
        confirma_pix = st.checkbox("Confirmo que os dados do pedido estão corretos", key="confirma_pix")
    else:
        numero_cartao_pagamento = st.text_input("Número do cartão", key="numero_cartao_pagamento")
        nome_cartao_pagamento = st.text_input("Nome impresso no cartão", key="nome_cartao_pagamento")
        validade_cartao_pagamento = st.text_input("Validade (MM/AA)", key="validade_cartao_pagamento")
        cvv_cartao_pagamento = st.text_input("CVV", type="password", key="cvv_cartao_pagamento")
        confirma_cartao = st.checkbox("Confirmo que os dados do cartão estão corretos", key="confirma_cartao")

    total = subtotal - st.session_state.desconto
    st.write(f"Desconto: **{formatar_moeda(st.session_state.desconto)}**")
    st.write(f"### Total: {formatar_moeda(total)}")

    if st.button("Confirmar", key="confirmar_pagamento"):
        erros_pagamento = []
        if opcao_pagamento == "Pix":
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_recibo.strip()):
                erros_pagamento.append("Informe um e-mail válido para o comprovante.")
            if not confirma_pix:
                erros_pagamento.append("Confirme os dados do pedido antes de continuar.")
        else:
            numero_limpo = re.sub(r"\D", "", numero_cartao_pagamento)
            if not nome_cartao_pagamento.strip():
                erros_pagamento.append("Informe o nome impresso no cartão.")
            if not 13 <= len(numero_limpo) <= 19:
                erros_pagamento.append("O número do cartão deve ter entre 13 e 19 dígitos.")
            if not re.fullmatch(r"(0[1-9]|1[0-2])/\d{2}", validade_cartao_pagamento.strip()):
                erros_pagamento.append("Informe a validade no formato MM/AA.")
            if not re.fullmatch(r"\d{3,4}", cvv_cartao_pagamento.strip()):
                erros_pagamento.append("O CVV deve ter 3 ou 4 dígitos.")
            if not confirma_cartao:
                erros_pagamento.append("Confirme os dados do cartão antes de continuar.")

        if erros_pagamento:
            for erro in erros_pagamento:
                st.error(erro)
        elif opcao_pagamento == "Pix":
            navegar_para("TELA205 - PIX")
        else:
            navegar_para("TELA207 - CARTÃO")

elif st.session_state.tela_atual == "TELA205 - PIX":
    if st.button("← Menu principal", key="menu_principal_pix"):
        navegar_para(TELA_INICIAL)
    st.subheader("TELA205 - PIX")
    st.write(f"### Total a pagar: {formatar_moeda(st.session_state.subtotal_compra - st.session_state.desconto)}")
    st.info("Demonstração acadêmica: o QR Code abaixo é ilustrativo e não realiza cobrança real.")
    imagem_generica("PIX DEMO", 260)

    if st.button("Copiar código", key="copiar_pix"):
        st.toast("Código PIX demonstrativo copiado.")
    if st.button("Cancelar", key="cancelar_pix"):
        navegar_para(TELA_INICIAL)
        
elif st.session_state.tela_atual == "TELA207 - CARTÃO":
    if st.button("← Menu principal", key="menu_principal_cartao"):
        navegar_para(TELA_INICIAL)
    st.subheader("TELA207 - CARTÃO")
    coluna_formulario, coluna_info = st.columns([2, 1])
    with coluna_formulario:
        st.text_input("Nome do cartão", key="nome_cartao")
        st.text_input("Número do cartão", key="numero_cartao")
        st.text_input("Data de expiração", key="validade_cartao")
        st.text_input("CVV", type="password", key="cvv_cartao")
        if st.button("Confirmar pagamento", key="confirmar_cartao"):
            st.success("Pagamento demonstrativo validado com sucesso!")
            st.session_state.carrinho = []
            st.session_state.subtotal_compra = 0.0
            st.session_state.desconto = 0.0
            if st.button("Ir para tela inicial", key="ir_inicial_cartao"):
                navegar_para(TELA_INICIAL)
    with coluna_info:
        st.info("Bandeiras aceitas:\n\n- Visa\n- Mastercard\n- Elo")
        
elif st.session_state.tela_atual == "TELA101 - LOGIN":
    if st.button("← Menu principal", key="menu_principal_login"):
        navegar_para(TELA_INICIAL)
    st.title("☕ Bitcoffee")
    st.subheader("TELA101 - LOGIN")
    email = st.text_input("E-mail", key="login_email")
    senha = st.text_input("Senha", type="password", key="login_senha")

    coluna_entrar, coluna_cadastro = st.columns(2)
    with coluna_entrar:
        if st.button("ENTRAR", key="entrar_login"):
            email_normalizado = email.strip().lower()
            if not email_normalizado or not senha:
                st.warning("Informe o e-mail e a senha.")
            elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_normalizado):
                st.warning("Digite um e-mail válido.")
            elif email_normalizado == "admin@cafe.com" and senha == "admin":
                st.session_state.usuario_logado = "Perfil Admin"
                navegar_para("TELA301 - ADMINISTRAÇÃO")
            elif email_cadastrado(email_normalizado) and not autenticar_usuario(email_normalizado, senha):
                st.error("Este e-mail já está cadastrado, mas a senha informada está incorreta.")
            elif autenticar_usuario(email_normalizado, senha):
                st.session_state.usuario_logado = email_normalizado
                navegar_para(TELA_INICIAL)
            else:
                st.error("E-mail não encontrado. Crie uma conta antes de entrar.")
    with coluna_cadastro:
        if st.button("CRIAR CONTA", key="criar_conta_login"):
            navegar_para("TELA102 - CADASTRO")

    if st.button("Esqueceu a senha?", key="esqueceu_senha"):
        navegar_para("TELA103 - RECUPERAÇÃO DE CONTA")

elif st.session_state.tela_atual == "TELA102 - CADASTRO":
    if st.button("← Menu principal", key="menu_principal_cadastro"):
        navegar_para(TELA_INICIAL)
    st.title("☕ Bitcoffee")
    st.subheader("TELA102 - CADASTRO")
    nome = st.text_input("Nome", key="cadastro_nome")
    sobrenome = st.text_input("Sobrenome", key="cadastro_sobrenome")
    email_cadastro = st.text_input("E-mail", key="cadastro_email")
    st.text_input("CPF", key="cadastro_cpf")
    senha_cadastro = st.text_input("Senha (entre 8 e 16 caracteres)", type="password", key="cadastro_senha")
    confirmar_senha = st.text_input("Confirmar senha", type="password", key="confirmar_senha")
    st.text_input("CEP", key="cadastro_cep")
    st.text_input("UF", key="cadastro_uf")
    st.text_input("Cidade", key="cadastro_cidade")
    st.text_input("Bairro", key="cadastro_bairro")
    st.text_input("Rua", key="cadastro_rua")
    st.text_input("Número", key="cadastro_numero")
    st.text_input("Complemento", key="cadastro_complemento")

    aceite = st.checkbox("Aceito os termos de uso", key="aceite_termos")
    if st.button("Ver termos de uso e LGPD", key="ver_termos"):
        navegar_para("TELA104 - TERMOS DE USO E LGPD")
    st.text_input("Código de confirmação", key="codigo_confirmacao")

    if st.button("Cadastrar", key="cadastrar_usuario"):
        email_normalizado = email_cadastro.strip().lower()
        erros = []
        if not nome.strip() or not sobrenome.strip():
            erros.append("Informe nome e sobrenome.")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_normalizado):
            erros.append("Digite um e-mail válido.")
        if email_cadastrado(email_normalizado):
            erros.append("Este e-mail já está em uso.")
        if not 8 <= len(senha_cadastro) <= 16:
            erros.append("A senha deve ter entre 8 e 16 caracteres.")
        if senha_cadastro != confirmar_senha:
            erros.append("As senhas não coincidem.")
        if not aceite:
            erros.append("Você precisa aceitar os termos de uso.")

        if erros:
            for erro in erros:
                st.error(erro)
        elif cadastrar_usuario(email_normalizado, senha_cadastro):
            st.success("Cadastro realizado com sucesso! Você já pode fazer login.")
            navegar_para("TELA101 - LOGIN")
        else:
            st.error("Este e-mail já está em uso.")

elif st.session_state.tela_atual == "TELA103 - RECUPERAÇÃO DE CONTA":
    if st.button("← Menu principal", key="menu_principal_recuperacao"):
        navegar_para(TELA_INICIAL)
    st.title("☕ Bitcoffee")
    st.subheader("TELA103 - RECUPERAÇÃO DE CONTA")
    st.write("Informe o e-mail cadastrado para receber as instruções de alteração da senha.")
    email_recuperacao = st.text_input("E-mail da conta", key="email_recuperacao")

    if st.button("Enviar e-mail de recuperação", key="enviar_recuperacao"):
        email_normalizado = email_recuperacao.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email_normalizado):
            st.warning("Digite um e-mail válido.")
        elif not email_cadastrado(email_normalizado):
            st.error("Não encontramos uma conta com esse e-mail.")
        else:
            token = f"{secrets.randbelow(100000):05d}"
            enviado, mensagem = enviar_email_recuperacao(email_normalizado, token)
            if enviado:
                st.success(mensagem)
            else:
                st.warning(mensagem)
                st.info("Para envio real, configure BITCOFFEE_SMTP_HOST, BITCOFFEE_SMTP_PORT, BITCOFFEE_SMTP_USER, BITCOFFEE_SMTP_PASSWORD e BITCOFFEE_SMTP_FROM.")

    if st.button("Voltar para login", key="voltar_login_recuperacao"):
        navegar_para("TELA101 - LOGIN")

elif st.session_state.tela_atual == "TELA104 - TERMOS DE USO E LGPD":
    if st.button("← Menu principal", key="menu_principal_termos"):
        navegar_para(TELA_INICIAL)
    st.title("☕ Bitcoffee")
    st.subheader("TELA104 - TERMOS DE USO E LGPD")
    st.text_area(
        "Termos de Uso",
        value="Este texto é um espaço demonstrativo para os termos de uso e a política de privacidade.",
        height=200,
        key="termos_uso",
    )
    if st.button("Voltar ao cadastro", key="voltar_cadastro_termos"):
        navegar_para("TELA102 - CADASTRO")
        
elif st.session_state.tela_atual == "TELA301 - ADMINISTRAÇÃO":
    if st.button("← Menu principal", key="menu_principal_admin"):
        navegar_para(TELA_INICIAL)
    st.title("☕ Bitcoffee")
    st.write("Perfil administrador")
    st.subheader("Painel Administrativo")

    coluna_1, coluna_2 = st.columns(2)
    with coluna_1:
        if st.button("Gerenciar estoque", use_container_width=True, key="gerenciar_estoque"):
            navegar_para("TELA302 - ESTOQUE")
        st.button("Logs do sistema", use_container_width=True, key="logs_sistema")
    with coluna_2:
        st.button("Gerar relatório", use_container_width=True, key="gerar_relatorio")
        st.button("Gestão de cafés", use_container_width=True, key="gestao_cafes")

    st.button("Alertas do sistema", use_container_width=True, key="alertas_sistema")
    if st.button("Sair da administração", key="sair_administracao"):
        st.session_state.usuario_logado = None
        navegar_para(TELA_INICIAL)

elif st.session_state.tela_atual == "TELA302 - ESTOQUE":
    if st.button("← Menu principal", key="menu_principal_estoque"):
        navegar_para(TELA_INICIAL)
    st.title("☕ Bitcoffee")
    st.write("Perfil administrador")
    st.subheader("Controle de Estoque")

    for produto in PRODUTOS:
        coluna_imagem, coluna_dados, coluna_preco = st.columns([1, 3, 2])
        with coluna_imagem:
            imagem_generica("CAFÉ", 90)
        with coluna_dados:
            st.write(f"**Nome:** {produto['nome']}")
            st.write(f"**ID:** {produto['id']}")
            st.write("Quantidade em estoque: 15")
        with coluna_preco:
            st.number_input(
                "Preço unitário",
                value=float(produto["preco"]),
                min_value=0.0,
                step=0.50,
                key=f"preco_estoque_{produto['id']}",
            )
        st.divider()

    coluna_desfazer, coluna_registrar = st.columns(2)
    with coluna_desfazer:
        if st.button("Desfazer", key="desfazer_estoque"):
            st.toast("Alterações desfeitas.")
    with coluna_registrar:
        if st.button("Registrar alterações", key="registrar_estoque"):
            st.success("Estoque atualizado com sucesso!")

    if st.button("Voltar ao painel administrativo", key="voltar_admin_estoque"):
        navegar_para("TELA301 - ADMINISTRAÇÃO")
