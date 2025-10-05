import streamlit as st
from PIL import Image
import base64
import io

# ===============================
# CONFIGURAÇÕES GERAIS DA PÁGINA
# ===============================
st.set_page_config(
    page_title="Synapse.IA",
    page_icon="🧠",
    layout="wide",
)

# ===============================
# ESTILOS CSS PERSONALIZADOS
# ===============================
st.markdown(
    """
    <style>
    /* Fundo geral e remoção de margens */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Branding bar */
    .branding-bar {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px 0 15px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1rem;
    }

    .branding-text {
        display: flex;
        flex-direction: column;
    }

    .branding-title {
        font-size: 2rem;
        font-weight: 800;
        color: white;
        margin: 0;
        padding: 0;
    }

    .branding-subtitle {
        font-size: 1rem;
        color: #bbb;
        margin: 0;
        padding: 0;
    }

    /* Seções */
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 1.5rem;
        margin-bottom: 0.3rem;
        text-shadow: 0px 0px 8px rgba(0, 150, 255, 0.25);
    }

    /* Ícones das seções */
    .section-icon {
        font-size: 1.6rem;
        display: flex;
        align-items: center;
    }

    textarea, .stTextArea textarea {
        background-color: #1E1E1E;
        color: white;
        border-radius: 8px;
        border: 1px solid #444;
        min-height: 150px;
    }

    .stFileUploader {
        background-color: #2C2C2C;
        border-radius: 10px;
        padding: 15px;
    }

    .stButton>button {
        background-color: #007BFF;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
    }

    .stButton>button:hover {
        background-color: #3399FF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===============================
# CABEÇALHO / BRANDING BAR
# ===============================
logo = Image.open("logo_synapse.png")

col1, col2 = st.columns([0.1, 0.9])
with col1:
    st.image(logo, width=70)
with col2:
    st.markdown(
        """
        <div class="branding-text">
            <h1 class="branding-title">Synapse.IA</h1>
            <p class="branding-subtitle">Tribunal de Justiça de São Paulo</p>
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
        <div class="section-icon">📥</div>
        Insumos Manuais
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("Descreva o objeto, justificativa, requisitos, prazos, critérios etc.")
insumos = st.text_area("", height=180)

# ===============================
# SEÇÃO 2 – UPLOAD DE DOCUMENTO
# ===============================
st.markdown(
    """
    <div class="section-title">
        <div class="section-icon">📂</div>
        Upload de Documento (opcional)
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("Envie PDF, DOCX, XLSX ou CSV (ex.: ETP, TR, Contrato, Obras etc.)")
uploaded_files = st.file_uploader(
    "Drag and drop file here", type=["pdf", "docx", "xlsx", "csv"], accept_multiple_files=True
)

# ===============================
# SEÇÃO 3 – SELECIONAR AGENTE
# ===============================
st.markdown(
    """
    <div class="section-title">
        <div class="section-icon">🧠</div>
        Selecionar Agente
    </div>
    """,
    unsafe_allow_html=True,
)

agente = st.selectbox("Escolha o agente:", ["ETP", "DFD", "TR", "Contrato", "Checklist", "Fiscalização"])
validar = st.checkbox("Executar validação semântica")

if st.button("Executar Agente"):
    st.success(f"Agente **{agente}** executado com sucesso!")
