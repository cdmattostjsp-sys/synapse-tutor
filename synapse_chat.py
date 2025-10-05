import streamlit as st
from PIL import Image
import base64
import os
import io

# === NOVO: OpenAI e Validator Engine ===
from openai import OpenAI
from knowledge.validators.validator_engine import validate_document

# ===============================
# CONFIGURAÇÕES GERAIS DA PÁGINA
# ===============================
st.set_page_config(
    page_title="Synapse.IA",
    page_icon="🧠",
    layout="wide",
)

# ===============================
# UTIL – carregar imagem em base64
# ===============================
def img_to_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# Carrega o logo (cérebro azul) — mantém exatamente como estava
LOGO_PATH = "logo_synapse.png"
logo_b64 = ""
try:
    logo_b64 = img_to_b64(LOGO_PATH)
except Exception:
    logo_b64 = ""  # não quebra o app se o logo não existir

# ===============================
# ESTILOS CSS (ajustes de layout)
# ===============================
st.markdown(
    f"""
    <style>
    /* Container principal – evita corte do título no topo  */
    .block-container {{
        padding-top: 0.9rem;   /* ↑ aumentei para evitar clipping do h1 */
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }}

    /* Branding bar com degradê sutil */
    .branding-bar {{
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 14px 0 12px 0; /* ↑ top padding maior para não cortar */
        background: linear-gradient(180deg, #10151e 0%, #0E1117 100%);
        border-bottom: 1px solid #303030;
        margin-bottom: 10px;
    }}

    .branding-title {{
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        line-height: 1.1;
    }}

    .branding-subtitle {{
        font-size: 1rem;
        color: #bdbdbd;
        margin: 0;
        line-height: 1.2;
    }}

    /* Títulos de seção – mesmo peso e hierarquia visual */
    .section-title {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.7rem;      /* proporcional ao título do app */
        font-weight: 700;
        color: #ffffff;
        margin-top: 1.6rem;
        margin-bottom: 0.35rem;
        text-shadow: 0 0 8px rgba(0, 150, 255, 0.22);
    }}

    .section-subtext {{
        color: #AAAAAA;
        font-size: 0.95rem;
        margin-top: -4px;
        margin-bottom: 10px;
    }}

    /* Linha divisória azul entre blocos (estilo institucional) */
    .section-divider {{
        height: 1px;
        width: 100%;
        background: #1d4ed8; /* azul institucional */
        opacity: 0.35;
        margin: 12px 0 12px 0;
    }}

    /* Inputs */
    textarea, .stTextArea textarea {{
        background-color: #1E1E1E;
        color: #ffffff;
        border-radius: 8px;
        border: 1px solid #444;
        min-height: 150px;
    }}

    .stFileUploader {{
        background-color: #2C2C2C;
        border-radius: 10px;
        padding: 12px;
    }}

    .stButton>button {{
        background-color: #007BFF;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
    }}

    .stButton>button:hover {{
        background-color: #3399FF;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===============================
# CABEÇALHO / BRANDING BAR
# ===============================
st.markdown(
    f"""
    <div class="branding-bar">
        {'<img src="data:image/png;base64,' + logo_b64 + '" alt="Logo Synapse.IA" width="66" style="border-radius:6px;">' if logo_b64 else ''}
        <div style="display:flex; flex-direction:column;">
            <h1 class="branding-title">Synapse.IA</h1>
            <p class="branding-subtitle">Tribunal de Justiça de São Paulo</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ===============================
# SEÇÃO 1 – INSUMOS MANUAIS
# ===============================
st.markdown(
    """
    <div class="section-title">
        <div style="font-size:1.6rem;">📥</div>
        Insumos Manuais
    </div>
    <div class="section-subtext">Descreva o objeto, justificativa, requisitos, prazos, critérios etc.</div>
    """,
    unsafe_allow_html=True,
)
insumos = st.text_area("", height=180)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ===============================
# SEÇÃO 2 – UPLOAD DE DOCUMENTO
# ===============================
st.markdown(
    """
    <div class="section-title">
        <div style="font-size:1.6rem;">📂</div>
        Upload de Documento (opcional)
    </div>
    <div class="section-subtext">Envie PDF, DOCX, XLSX ou CSV (ex.: ETP, TR, Contrato, Obras etc.)</div>
    """,
    unsafe_allow_html=True,
)
uploaded_files = st.file_uploader(
    "Drag and drop file here",
    type=["pdf", "docx", "xlsx", "csv", "txt"],
    accept_multiple_files=True,
)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ===============================
# SEÇÃO 3 – SELECIONAR AGENTE
# (com o cérebro azul, igual ao do cabeçalho)
# ===============================
st.markdown(
    f"""
    <div class="section-title">
        {'<img src="data:image/png;base64,' + logo_b64 + '" width="32" style="transform: translateY(2px);">' if logo_b64 else '<div style="font-size:1.6rem;">🧠</div>'}
        Selecionar Agente
    </div>
    """,
    unsafe_allow_html=True,
)
agente = st.selectbox(
    "Escolha o agente:",
    ["ETP", "DFD", "TR", "CONTRATO", "EDITAL", "PESQUISA_PRECOS", "FISCALIZACAO", "OBRAS", "MAPA_RISCOS", "PCA"],
)
validar_semantica = st.checkbox("Executar validação semântica", value=True)

# ===============================
# EXTRAÇÃO DE TEXTO DE UPLOADS
# ===============================
def extract_text_from_uploads(files) -> str:
    if not files:
        return ""
    chunks = []
    for f in files:
        name = (f.name or "").lower()
        data = f.read()
        # TXT direto
        if name.endswith(".txt"):
            try:
                chunks.append(data.decode("utf-8", errors="ignore"))
                continue
            except Exception as e:
                st.warning(f"Falha ao ler TXT {f.name}: {e}")
        # PDF opcional
        if name.endswith(".pdf"):
            try:
                from PyPDF2 import PdfReader  # opcional; só funciona se estiver no requirements
                reader = PdfReader(io.BytesIO(data))
                text = "\n".join([page.extract_text() or "" for page in reader.pages])
                chunks.append(text)
                continue
            except Exception as e:
                st.warning(f"Falha ao extrair texto do PDF {f.name}: {e}")
        # DOCX opcional
        if name.endswith(".docx"):
            try:
                import docx  # opcional; só funciona se estiver no requirements
                doc = docx.Document(io.BytesIO(data))
                text = "\n".join([p.text for p in doc.paragraphs])
                chunks.append(text)
                continue
            except Exception as e:
                st.warning(f"Falha ao extrair texto do DOCX {f.name}: {e}")
        # Fallback: tentativa de decodificação bruta
        try:
            chunks.append(data.decode("utf-8", errors="ignore"))
        except Exception:
            pass
    return "\n\n".join(chunks).strip()

# ===============================
# CHAVE OPENAI E CLIENT
# ===============================
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("🔴 OPENAI_API_KEY não encontrada em Secrets/ambiente. Configure em Settings → Secrets e reinicie o app.")
        return None
    try:
        # OBS: Por padrão, os validadores usam o cliente passado aqui.
        # Para máxima qualidade, usaremos gpt-4o no backend sem alterar o layout.
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        st.error(f"Erro ao inicializar cliente OpenAI: {e}")
        return None

# ===============================
# BOTÃO DE AÇÃO – EXECUTAR AGENTE
# ===============================
if st.button("Executar Agente"):
    if not insumos and not uploaded_files:
        st.warning("⚠️ Insira algum texto em 'Insumos Manuais' ou envie um arquivo para análise.")
    else:
        # Concatena insumos + textos extraídos dos uploads
        texto = (insumos or "").strip()
        texto_uploads = extract_text_from_uploads(uploaded_files)
        if texto_uploads:
            texto = (texto + "\n\n" + texto_uploads).strip()

        client = get_openai_client()
        if client is None:
            st.stop()

        with st.spinner(f"Executando validação do artefato {agente}..."):
            try:
                # Chama o motor de validação central — mantém a lógica já validada
                # (internamente os validadores semânticos usarão gpt-4o; se preferir gpt-4o-mini me avise)
                resultado = validate_document(texto, agente, client)

                if not resultado:
                    st.error("O validador não retornou resultado. Verifique logs do engine ou tente um insumo menor.")
                else:
                    st.success(f"✅ Agente **{agente}** executado com sucesso!")
                    # Exibe exatamente o texto retornado pelo motor (pontuações, itens, justificativas)
                    st.markdown("### 🧾 Resultado da Análise")
                    st.markdown(resultado)
            except Exception as e:
                st.error(f"❌ Erro ao processar o agente {agente}: {e}")
