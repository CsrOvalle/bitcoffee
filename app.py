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


# ============================================================
# CONFIGURAÇÃO E ESTILO
# ============================================================
st.set_page_config(
    page_title="Bitcoffee | PIT-II",
    page_icon="☕",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --espresso: #26170f;
        --coffee: #5d3322;
        --caramel: #c8783c;
        --terracotta: #a64326;
        --cream: #f7f1e7;
        --paper: #fffaf2;
        --sand: #eadfce;
        --muted: #746256;
        --line: #decfbc;
    }

    html { scroll-behavior: smooth; }

    .stApp {
        background:
            radial-gradient(circle at 8% 2%, rgba(200, 120, 60, 0.10), transparent 24rem),
            linear-gradient(180deg, #fbf7f0 0%, var(--cream) 100%) !important;
        color: var(--espresso) !important;
    }

    [data-testid="stHeader"] {
        background: rgba(251, 247, 240, 0.88) !important;
        backdrop-filter: blur(12px);
    }

    [data-testid="stToolbar"] { color: var(--espresso) !important; }

    .block-container {
        max-width: 1180px !important;
        /* A barra nativa do Streamlit é fixa e ocupa a parte superior. */
        padding-top: 5.5rem !important;
        padding-bottom: 4rem !important;
    }

    h1, h2, h3, h4, h5, h6, p, label,
    [data-testid="stMarkdownContainer"] {
        color: var(--espresso) !important;
    }

    h1, h2, h3 {
        font-family: Georgia, "Times New Roman", serif !important;
        letter-spacing: -0.025em !important;
    }

    h1 { font-size: clamp(2rem, 4vw, 3.6rem) !important; }
    h2 { font-size: clamp(1.65rem, 3vw, 2.4rem) !important; }

    [data-testid="stCaptionContainer"] p,
    .stCaptionContainer p {
        color: var(--muted) !important;
        line-height: 1.65 !important;
    }

    hr {
        border-color: rgba(93, 51, 34, 0.15) !important;
        margin: 1.25rem 0 !important;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        color: #17120f !important;
        background-color: #ffffff !important;
        border: 1px solid var(--line) !important;
        min-height: 2.65rem !important;
        padding: 0.55rem 1.15rem !important;
        font-weight: 700 !important;
        border-radius: 999px !important;
        box-shadow: 0 5px 14px rgba(46, 26, 16, 0.07) !important;
        transition: transform 160ms cubic-bezier(0.23, 1, 0.32, 1),
                    background-color 160ms cubic-bezier(0.23, 1, 0.32, 1),
                    box-shadow 160ms cubic-bezier(0.23, 1, 0.32, 1) !important;
    }

    div.stButton > button p,
    div.stButton > button span,
    div.stButton > button div,
    div.stDownloadButton > button p,
    button[kind] p,
    button[kind] span {
        color: #17120f !important;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background-color: #e5ddd2 !important;
        border-color: #c8b49d !important;
        color: #17120f !important;
        transform: translateY(-1px);
        box-shadow: 0 9px 22px rgba(46, 26, 16, 0.12) !important;
    }

    div.stButton > button:active { transform: scale(0.98); }
    div.stButton > button:focus-visible { outline: 3px solid rgba(200, 120, 60, 0.35) !important; }

    div[data-baseweb="input"],
    div[data-baseweb="textarea"],
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border-color: var(--line) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 14px rgba(46, 26, 16, 0.04) !important;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] > div {
        color: #1a1512 !important;
        background-color: transparent !important;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        min-height: 2.45rem !important;
        height: 2.45rem !important;
    }

    div[data-testid="stTextInput"] input {
        padding: 0.4rem 0.8rem !important;
        font-size: 0.92rem !important;
    }

    div[data-testid="stTextInput"] label {
        margin-bottom: 0.2rem !important;
        font-size: 0.84rem !important;
        font-weight: 650 !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 250, 242, 0.92) !important;
        border: 1px solid rgba(93, 51, 34, 0.13) !important;
        border-radius: 20px !important;
        box-shadow: 0 14px 38px rgba(60, 34, 20, 0.08) !important;
        overflow: hidden;
    }

    [data-testid="stAlert"] {
        border-radius: 14px !important;
        border-width: 1px !important;
    }

    .site-brand {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        min-height: 2.7rem;
    }

    .brand-mark {
        width: 2.45rem;
        height: 2.45rem;
        display: grid;
        place-items: center;
        border-radius: 50%;
        color: #fffaf2;
        background: var(--espresso);
        font-size: 1.25rem;
        box-shadow: 0 7px 18px rgba(38, 23, 15, 0.18);
    }

    .brand-copy strong {
        display: block;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 1.55rem;
        line-height: 1;
        letter-spacing: -0.03em;
        color: var(--espresso);
    }

    .brand-copy small {
        color: var(--muted);
        font-size: 0.67rem;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }

    .user-chip {
        background: #efe5d7;
        border: 1px solid var(--line);
        color: var(--coffee);
        padding: 0.45rem 0.75rem;
        border-radius: 999px;
        text-align: center;
        font-size: 0.8rem;
        margin-bottom: 0.45rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .hero {
        display: grid;
        grid-template-columns: minmax(0, 1.3fr) minmax(260px, .7fr);
        gap: 2rem;
        align-items: center;
        min-height: 420px;
        padding: clamp(2rem, 6vw, 5rem);
        margin: 1.1rem 0 2.8rem;
        overflow: hidden;
        position: relative;
        border-radius: 30px;
        background:
            radial-gradient(circle at 82% 20%, rgba(222, 159, 93, .34), transparent 17rem),
            linear-gradient(125deg, #21130d 0%, #4d2a1d 55%, #763b24 100%);
        box-shadow: 0 25px 60px rgba(48, 27, 17, 0.20);
    }

    .hero::after {
        content: "";
        position: absolute;
        width: 320px;
        height: 320px;
        right: -110px;
        bottom: -175px;
        border: 1px solid rgba(255,255,255,.16);
        border-radius: 50%;
        box-shadow: 0 0 0 42px rgba(255,255,255,.025), 0 0 0 84px rgba(255,255,255,.02);
    }

    .hero-copy { position: relative; z-index: 2; }

    .hero-kicker {
        display: inline-block;
        color: #f2c894;
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .17em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .hero h1 {
        color: #fffaf2 !important;
        font-size: clamp(2.8rem, 5.8vw, 5.3rem) !important;
        line-height: .98 !important;
        max-width: 760px;
        margin: 0 0 1.2rem;
    }

    .hero p {
        color: #eadfd2 !important;
        max-width: 620px;
        font-size: 1.06rem;
        line-height: 1.7;
        margin-bottom: 1.7rem;
    }

    .hero-cta {
        display: inline-block;
        background: #fffaf2;
        color: var(--espresso) !important;
        text-decoration: none !important;
        border-radius: 999px;
        padding: .8rem 1.25rem;
        font-weight: 800;
        box-shadow: 0 10px 25px rgba(0,0,0,.18);
    }

    .hero-visual {
        position: relative;
        z-index: 2;
        display: grid;
        place-items: center;
        min-height: 280px;
    }

    .hero-seal {
        width: 250px;
        aspect-ratio: 1;
        display: grid;
        place-items: center;
        text-align: center;
        border-radius: 50%;
        color: #fff7ea;
        border: 1px solid rgba(255,255,255,.38);
        background: rgba(255,255,255,.08);
        box-shadow: inset 0 0 0 14px rgba(255,255,255,.035), 0 24px 55px rgba(0,0,0,.28);
        transform: rotate(-4deg);
    }

    .hero-seal .cup { font-size: 4.4rem; line-height: 1; }
    .hero-seal strong { display: block; font-family: Georgia, serif; font-size: 1.45rem; margin-top: .5rem; }
    .hero-seal small { display: block; color: #e5c7a5; letter-spacing: .16em; margin-top: .35rem; }

    .trust-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: -1.5rem auto 3.2rem;
    }

    .trust-item {
        background: rgba(255,250,242,.9);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 10px 30px rgba(56, 31, 18, .06);
    }

    .trust-item strong { display: block; color: var(--coffee); font-size: .96rem; }
    .trust-item span { color: var(--muted); font-size: .8rem; }

    .section-heading { margin: 0 0 1.35rem; }
    .section-heading .eyebrow {
        color: var(--terracotta);
        text-transform: uppercase;
        letter-spacing: .16em;
        font-size: .72rem;
        font-weight: 800;
    }
    .section-heading h2 { margin: .25rem 0 .4rem; }
    .section-heading p { color: var(--muted) !important; max-width: 680px; }

    .product-meta {
        display: flex;
        flex-wrap: wrap;
        gap: .4rem;
        margin: .75rem 0 .15rem;
    }

    .product-meta span {
        background: #efe3d4;
        color: #68432e;
        border-radius: 999px;
        padding: .28rem .55rem;
        font-size: .7rem;
        font-weight: 750;
    }

    .product-price {
        color: var(--terracotta);
        font-family: Georgia, serif;
        font-size: 1.35rem;
        font-weight: 800;
        margin: .55rem 0;
    }

    .product-description {
        color: var(--muted);
        line-height: 1.55;
        min-height: 3.1rem;
        font-size: .88rem;
    }

    .product-art {
        width: 100%;
        overflow: hidden;
        border-radius: 15px;
        margin-bottom: .85rem;
        background: #eadfce;
    }

    .product-art svg { width: 100%; height: auto; display: block; }

    .page-intro {
        padding: 1.6rem 1.8rem;
        margin: .4rem 0 1.4rem;
        border-left: 5px solid var(--caramel);
        border-radius: 0 18px 18px 0;
        background: #fffaf2;
        box-shadow: 0 10px 30px rgba(56,31,18,.06);
    }
    .page-intro h1 { margin: 0 0 .25rem; font-size: 2.2rem !important; }
    .page-intro p { margin: 0; color: var(--muted) !important; }

    .admin-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 1.2rem 0 1.8rem;
    }
    .admin-stat {
        padding: 1.15rem;
        border-radius: 16px;
        background: #fffaf2;
        border: 1px solid var(--line);
    }
    .admin-stat strong { display: block; font: 700 1.6rem Georgia, serif; color: var(--coffee); }
    .admin-stat span { color: var(--muted); font-size: .8rem; }

    @media (max-width: 780px) {
        .block-container { padding-top: 4.75rem !important; }
        .hero { grid-template-columns: 1fr; min-height: auto; padding: 2rem; border-radius: 22px; }
        .hero-visual { min-height: 190px; }
        .hero-seal { width: 180px; }
        .trust-row, .admin-stats { grid-template-columns: 1fr; }
        .product-description { min-height: auto; }
    }

    @media (prefers-reduced-motion: reduce) {
        * { scroll-behavior: auto !important; transition: none !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DADOS E ESTADO DA APLICAÇÃO
# ============================================================
PRODUTOS = [
    {
        "id": 1,
        "nome": "Bourbon Amarelo 250g",
        "preco": 38.90,
        "desc": "Café 100% Arábica de alta qualidade com notas de chocolate e caramelo.",
        "origem": "Sul de Minas",
        "torra": "Média clara",
        "notas": "Chocolate e caramelo",
        "cor": "#a94f2c",
    },
    {
        "id": 2,
        "nome": "Chapada Diamantina 250g",
        "preco": 42.50,
        "desc": "Grãos selecionados com acidez equilibrada e aroma marcante.",
        "origem": "Chapada Diamantina",
        "torra": "Média",
        "notas": "Mel e frutas amarelas",
        "cor": "#c37a3d",
    },
    {
        "id": 3,
        "nome": "Blend Especial 250g",
        "preco": 35.00,
        "desc": "Combinação exclusiva de grãos para um café encorpado.",
        "origem": "Blend da casa",
        "torra": "Média escura",
        "notas": "Cacau e castanhas",
        "cor": "#71402c",
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
if "perfil_usuario" not in st.session_state:
    st.session_state.perfil_usuario = None
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


def imagem_generica(texto: str = "Bitcoffee", largura: int = 260, cor: str = "#9f472a") -> None:
    """Exibe uma ilustração vetorial própria, sem depender de imagens externas."""
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 340" role="img" aria-label="Embalagem ilustrativa {texto}">
      <defs>
        <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#f2e6d6"/>
          <stop offset="100%" stop-color="#d9c0a4"/>
        </linearGradient>
        <linearGradient id="bag" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="{cor}"/>
          <stop offset="100%" stop-color="#3c2118"/>
        </linearGradient>
        <filter id="shadow"><feDropShadow dx="0" dy="16" stdDeviation="12" flood-opacity=".22"/></filter>
      </defs>
      <rect width="520" height="340" rx="26" fill="url(#bg)"/>
      <circle cx="82" cy="70" r="46" fill="#ffffff" opacity=".22"/>
      <circle cx="438" cy="274" r="82" fill="#ffffff" opacity=".16"/>
      <g filter="url(#shadow)">
        <path d="M171 63h178l20 218c2 22-13 39-35 39H186c-22 0-37-17-35-39z" fill="url(#bag)"/>
        <path d="M171 63h178l-15 31H186z" fill="#2c1a13" opacity=".78"/>
        <rect x="194" y="120" width="132" height="122" rx="10" fill="#fff8ed"/>
        <circle cx="260" cy="162" r="31" fill="none" stroke="{cor}" stroke-width="4"/>
        <path d="M239 154h36v21c0 12-8 20-18 20s-18-8-18-20z" fill="none" stroke="{cor}" stroke-width="4"/>
        <path d="M275 159h10c8 0 13 5 13 12s-5 12-13 12h-8" fill="none" stroke="{cor}" stroke-width="4"/>
        <text x="260" y="218" text-anchor="middle" fill="#3b2419" font-family="Georgia" font-size="15" font-weight="700">BITCOFFEE</text>
      </g>
      <path d="M52 286c20-30 42-30 62 0M407 67c18-27 38-27 56 0" fill="none" stroke="#6d422d" stroke-width="3" stroke-linecap="round" opacity=".22"/>
    </svg>
    """
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    st.markdown(
        f'<div class="product-art"><img src="data:image/svg+xml;base64,{encoded}" alt="{texto}" style="width:100%;display:block"></div>',
        unsafe_allow_html=True,
    )


def render_header() -> None:
    col_logo, col_espaco, col_usuario, col_carrinho = st.columns([4.7, 1.8, 1.7, 1.8], vertical_alignment="center")
    with col_logo:
        st.markdown(
            """
            <div class="site-brand">
              <div class="brand-mark">☕</div>
              <div class="brand-copy"><strong>Bitcoffee</strong><small>Cafés especiais</small></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_espaco:
        st.markdown("<span></span>", unsafe_allow_html=True)
    with col_usuario:
        if st.session_state.usuario_logado:
            st.markdown(f'<div class="user-chip">{st.session_state.usuario_logado}</div>', unsafe_allow_html=True)
            if st.button("Sair", key="sair_header", use_container_width=True):
                sair_da_conta()
        elif st.button("Entrar", key="entrar_header", use_container_width=True):
            navegar_para("TELA101 - LOGIN")
    with col_carrinho:
        quantidade = sum(item["quantidade"] for item in st.session_state.carrinho)
        if st.button(f"Carrinho · {quantidade}", key="carrinho_header", use_container_width=True):
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


def usuario_e_administrador() -> bool:
    return st.session_state.get("perfil_usuario") == "administrador"


def sair_da_conta() -> None:
    st.session_state.usuario_logado = None
    st.session_state.perfil_usuario = None
    navegar_para(TELA_INICIAL)



def render_hero() -> None:
    st.markdown(
        """
        <section class="hero">
          <div class="hero-copy">
            <span class="hero-kicker">Torra fresca · origem selecionada</span>
            <h1>Seu café favorito começa na origem.</h1>
            <p>Grãos especiais escolhidos para transformar a rotina em um momento de pausa, aroma e sabor.</p>
            <a class="hero-cta" href="#catalogo">Conhecer os cafés</a>
          </div>
          <div class="hero-visual" aria-hidden="true">
            <div class="hero-seal">
              <div><span class="cup">☕</span><strong>Bitcoffee</strong><small>CAFÉ DE VERDADE</small></div>
            </div>
          </div>
        </section>
        <div class="trust-row">
          <div class="trust-item"><strong>100% Arábica</strong><span>Grãos selecionados por qualidade</span></div>
          <div class="trust-item"><strong>Torra em pequenos lotes</strong><span>Mais frescor em cada pacote</span></div>
          <div class="trust-item"><strong>Compra segura</strong><span>Protótipo acadêmico transparente</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_intro(titulo: str, subtitulo: str) -> None:
    st.markdown(
        f'<section class="page-intro"><h1>{titulo}</h1><p>{subtitulo}</p></section>',
        unsafe_allow_html=True,
    )


# ============================================================
# TELA 201 — PRINCIPAL
# ============================================================
if st.session_state.tela_atual == TELA_INICIAL:
    render_header()
    render_hero()

    st.markdown('<div id="catalogo"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="section-heading">
          <span class="eyebrow">Nossa seleção</span>
          <h2>Cafés para descobrir com calma</h2>
          <p>Escolha pelo perfil de torra, pela origem ou pelas notas sensoriais que mais combinam com você.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    termo = st.text_input(
        "Pesquisar",
        placeholder="Busque por café, origem ou nota sensorial...",
        label_visibility="collapsed",
        key="busca_produto",
    ).strip().lower()

    produtos_filtrados = [
        produto
        for produto in PRODUTOS
        if termo in produto["nome"].lower()
        or termo in produto["desc"].lower()
        or termo in produto["origem"].lower()
        or termo in produto["notas"].lower()
    ]

    if not produtos_filtrados:
        st.info("Nenhum café encontrado. Tente pesquisar por origem, torra ou nota sensorial.")
    else:
        colunas = st.columns(3, gap="large")
        for indice, produto in enumerate(produtos_filtrados):
            with colunas[indice % 3]:
                with st.container(border=True):
                    imagem_generica(produto["nome"].replace(" 250g", ""), 260, produto["cor"])
                    st.markdown(f"### {produto['nome']}")
                    st.markdown(
                        f'<div class="product-meta"><span>{produto["origem"]}</span><span>Torra {produto["torra"]}</span></div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f'<div class="product-price">{formatar_moeda(produto["preco"])}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="product-description">{produto["desc"]}</div>', unsafe_allow_html=True)
                    st.caption(f"Notas: {produto['notas']}")
                    if st.button("Ver café", key=f"detalhe_{produto['id']}", use_container_width=True):
                        st.session_state.produto_selecionado = produto
                        navegar_para("TELA206 - DESCRIÇÃO")

    st.markdown(
        """
        <div style="margin-top:3.5rem;padding:2rem;border-radius:22px;background:#2b1a12;color:#fff8ee;text-align:center">
          <div style="font-family:Georgia,serif;font-size:1.7rem;font-weight:700;color:#fff8ee">Da origem para a sua xícara.</div>
          <div style="margin-top:.5rem;color:#d9c9bc">Bitcoffee — uma experiência acadêmica de cafeteria gourmet.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# TELA 206 — DESCRIÇÃO
# ============================================================
elif st.session_state.tela_atual == "TELA206 - DESCRIÇÃO":
    if st.button("← Menu principal", key="menu_principal_descricao"):
        navegar_para(TELA_INICIAL)
    produto = st.session_state.produto_selecionado or PRODUTOS[0]
    render_page_intro("Detalhes do café", "Conheça a origem e o perfil sensorial antes de escolher.")
    coluna_imagem, coluna_dados = st.columns([1, 1])
    with coluna_imagem:
        imagem_generica(produto["nome"].replace(" 250g", ""), 360, produto.get("cor", "#9f472a"))
    with coluna_dados:
        st.subheader(produto["nome"])
        st.markdown(
            f'<div class="product-meta"><span>{produto.get("origem", "Origem selecionada")}</span><span>Torra {produto.get("torra", "Média")}</span></div>',
            unsafe_allow_html=True,
        )
        st.write("★★★★☆  Avaliação demonstrativa")
        st.write("**Perfil sensorial**")
        st.write(produto.get("notas", produto["desc"]))
        st.write(produto["desc"])
        st.markdown(f'<div class="product-price">{formatar_moeda(produto["preco"])}</div>', unsafe_allow_html=True)
        if st.button("Adicionar ao carrinho", key="adicionar_detalhes"):
            adicionar_ao_carrinho(produto)


# ============================================================
# TELA 203 — PEDIDO
# ============================================================
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


# ============================================================
# TELA 202 — PAGAMENTO
# ============================================================
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

# ============================================================
# TELA 205 — PIX
# ============================================================
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


# ============================================================
# TELA 207 — CARTÃO
# ============================================================
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


# ============================================================
# TELA 300 — LOGIN DO ADMINISTRADOR
# ============================================================
elif st.session_state.tela_atual == "TELA300 - LOGIN ADMINISTRADOR":
    if st.button("← Menu principal", key="menu_principal_login_admin"):
        navegar_para(TELA_INICIAL)
    st.title("☕ Bitcoffee")
    st.subheader("TELA300 - LOGIN DO ADMINISTRADOR")
    st.info("Acesso restrito à administração da loja.")
    email_admin = st.text_input("E-mail do administrador", key="email_admin")
    senha_admin = st.text_input("Senha do administrador", type="password", key="senha_admin")

    if st.button("ENTRAR COMO ADMINISTRADOR", key="entrar_admin"):
        if email_admin.strip().lower() == "admin@cafe.com" and senha_admin == "admin":
            st.session_state.usuario_logado = "Administrador da Bitcoffee"
            st.session_state.perfil_usuario = "administrador"
            navegar_para("TELA301 - ADMINISTRAÇÃO")
        else:
            st.error("E-mail ou senha de administrador incorretos.")

    st.caption("Acesso demonstrativo do protótipo: admin@cafe.com / admin")


# ============================================================
# TELA 101 — LOGIN
# ============================================================
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
            elif email_cadastrado(email_normalizado) and not autenticar_usuario(email_normalizado, senha):
                st.error("Este e-mail já está cadastrado, mas a senha informada está incorreta.")
            elif autenticar_usuario(email_normalizado, senha):
                st.session_state.usuario_logado = email_normalizado
                st.session_state.perfil_usuario = "cliente"
                navegar_para(TELA_INICIAL)
            else:
                st.error("E-mail não encontrado. Crie uma conta antes de entrar.")
    with coluna_cadastro:
        if st.button("CRIAR CONTA", key="criar_conta_login"):
            navegar_para("TELA102 - CADASTRO")

    if st.button("Esqueceu a senha?", key="esqueceu_senha"):
        navegar_para("TELA103 - RECUPERAÇÃO DE CONTA")

    if st.button("Acesso administrativo", key="acesso_administrativo"):
        navegar_para("TELA300 - LOGIN ADMINISTRADOR")

# ============================================================
# TELA 102 — CADASTRO
# ============================================================
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

# ============================================================
# TELA 103 — RECUPERAÇÃO DE CONTA
# ============================================================
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

# ============================================================
# TELA 104 — TERMOS DE USO E LGPD
# ============================================================
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


# ============================================================
# TELA 301 — ADMINISTRAÇÃO
# ============================================================
elif st.session_state.tela_atual == "TELA301 - ADMINISTRAÇÃO":
    if st.button("← Menu principal", key="menu_principal_admin"):
        navegar_para(TELA_INICIAL)
    if not usuario_e_administrador():
        st.error("Acesso restrito. Entre como administrador para abrir esta área.")
        if st.button("Ir para login administrativo", key="ir_login_admin_bloqueado"):
            navegar_para("TELA300 - LOGIN ADMINISTRADOR")
        st.stop()
    render_page_intro("Painel administrativo", "Visão geral e atalhos para a gestão da loja.")
    st.write(f"Perfil conectado: **{st.session_state.usuario_logado}**")
    st.markdown(
        """
        <div class="admin-stats">
          <div class="admin-stat"><strong>3</strong><span>cafés cadastrados</span></div>
          <div class="admin-stat"><strong>45</strong><span>unidades em estoque</span></div>
          <div class="admin-stat"><strong>1</strong><span>cupom demonstrativo ativo</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("Gestão da loja")

    coluna_1, coluna_2 = st.columns(2, gap="large")
    with coluna_1:
        if st.button("Gerenciar estoque", use_container_width=True, key="gerenciar_estoque"):
            navegar_para("TELA302 - ESTOQUE")
        st.button("Logs do sistema", use_container_width=True, key="logs_sistema")
    with coluna_2:
        st.button("Gerar relatório", use_container_width=True, key="gerar_relatorio")
        st.button("Gestão de cafés", use_container_width=True, key="gestao_cafes")

    st.button("Alertas do sistema", use_container_width=True, key="alertas_sistema")
    if st.button("Sair da administração", key="sair_administracao"):
        sair_da_conta()


# ============================================================
# TELA 302 — ESTOQUE
# ============================================================
elif st.session_state.tela_atual == "TELA302 - ESTOQUE":
    if st.button("← Menu principal", key="menu_principal_estoque"):
        navegar_para(TELA_INICIAL)
    if not usuario_e_administrador():
        st.error("Acesso restrito. Entre como administrador para abrir o estoque.")
        if st.button("Ir para login administrativo", key="ir_login_admin_estoque_bloqueado"):
            navegar_para("TELA300 - LOGIN ADMINISTRADOR")
        st.stop()
    st.title("☕ Bitcoffee")
    st.write(f"Perfil: **{st.session_state.usuario_logado}**")
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
