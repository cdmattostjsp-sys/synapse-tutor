import streamlit as st
from PIL import Image
import base64
import os

# ==============================
# CONFIGURAÇÃO GERAL DO APLICATIVO
# ==============================

st.set_page_config(
    page_title="Synapse.IA",
    page_icon="🧠",
    layout="wide"
)

# Define as cores institucionais do TJSP
BACKGROUND_COLOR = "#F4F4F4"     # cinza-claro
RED_TJSP = "#8B0000"             # vermelho institucional
GOLD_TJSP = "#C6A75E"            # dourado fosco

# Define o caminho das imagens (ajuste o nome conforme o arquivo no repositório)
LOGO_PATH = "logo_synapse_tjsp.png"
ICON_PATH = "icon_synapse_tjsp.png"

# ==============================
# FUNÇÃO PARA CONVERTER IMAGEM EM BASE64 (para embutir no HTML)
# ==============================
def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# ==============================
# BRANDING BAR
# ==============================
def branding_bar():
    logo_base64 = get_base64_of_bin_file(LOGO_PATH)
    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: center;
            background-color: {BACKGROUND_COLOR};
            padding: 0.8rem 1.2rem;
            border-bottom: 1px solid #ccc;
        ">
            <img src="data:image/png;base64,{logo_base64}" style="height: 60px; margin-right: 12px;">
            <div style="line-height: 1;">
                <h1 style="margin: 0; font-size: 2.2rem; color: {RED_TJSP}; font-weight: 700;">Synapse.<span style="color: {GOLD_TJSP};">IA</span></h1>
                <h3 style="margin: 0; font-size: 1.1rem; color: {GOLD_TJSP}; font-weight: 500;">Tribunal de Justiça de São Paulo</h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

branding_bar()

# ==============================
# ESTILO GLOBAL DO APP
# ==============================
st.markdown(
    f"""
    <style>
        .main {{
            background-color: {BACKGROUND_COLOR};
        }}
        h2 {{
            font-size: 1.8rem !important;
            color: {RED_TJSP};
            font-weight: 700 !important;
            display: flex;
            align-items: center;
        }}
        h3 {{
            font-size: 1.1rem !important;
            color: #444;
        }}
        .icon {{
            height: 26px;
            margin-right: 8px;
        }}
        .section-title {{
            margin-top: 2.2rem;
            margin-bottom: 1.2rem;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================
# SEÇÃO: INSUMOS MANUAIS
# ==============================
st.markdown(
    f"""
    <h2 class="section-title">
        <img src="https://cdn-icons-png.flaticon.com/512/1828/1828640.png" class="icon">
        Insumos Manuais
    </h2>
    """,
    unsafe_allow_html=True
)

insumo_text = st.text_area(
    "Descreva o contexto, objetivo e informações adicionais:",
    height=160,
    placeholder="Digite aqui os detalhes do seu artefato..."
)

# ==============================
# SEÇÃO: UPLOAD DE DOCUMENTO
# ==============================
st.markdown(
    f"""
    <h2 class="section-title">
        <img src="https://cdn-icons-png.flaticon.com/512/151/151773.png" class="icon">
        Upload de Documento (opcional)
    </h2>
    """,
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader("Selecione um arquivo (PDF, DOCX, TXT, etc.)", type=["pdf", "docx", "txt"])

# ==============================
# SEÇÃO: SELECIONAR AGENTE
# ==============================
if os.path.exists(ICON_PATH):
    agent_icon_base64 = get_base64_of_bin_file(ICON_PATH)
else:
    agent_icon_base64 = ""

st.markdown(
    f"""
    <h2 class="section-title">
        <img src="data:image/png;base64,{agent_icon_base64}" class="icon">
        Selecionar Agente
    </h2>
    """,
    unsafe_allow_html=True
)

agent_options = [
    "DFD - Documento de Formalização da Demanda",
    "ETP - Estudo Técnico Preliminar",
    "TR - Termo de Referência",
    "PCA - Planejamento Anual de Contratações",
    "Matriz de Riscos",
    "Pesquisa de Preços",
    "Fiscalização",
    "Contrato",
    "Edital"
]

agent_choice = st.selectbox("Selecione o agente responsável pela elaboração:", agent_options)

# ==============================
# BOTÃO DE EXECUÇÃO
# ==============================
if st.button("Executar Análise"):
    st.success(f"✅ Análise iniciada para o agente **{agent_choice}** com insumo fornecido.")
