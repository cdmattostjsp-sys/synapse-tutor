import streamlit as st
import base64
import os
from openai import OpenAI

# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================
st.set_page_config(page_title="Synapse.IA", layout="wide")

# ============================================================
# ESTILOS GERAIS - NOVA PALETA TJSP
# ============================================================
st.markdown("""
    <style>
    body {
        background-color: #F4F4F4;
    }
    .branding-bar {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        background-color: #F4F4F4;
        padding: 12px 25px;
        border-bottom: 2px solid #C6A75E;
        margin-bottom: 10px;
    }
    .branding-logo {
        height: 75px;
        margin-right: 20px;
    }
    .branding-text {
        line-height: 1.2;
    }
    .branding-title {
        font-size: 38px;
        font-weight: 700;
        color: #8B0000; /* vermelho TJSP */
        font-family: 'Segoe UI', sans-serif;
    }
    .branding-subtitle {
        font-size: 18px;
        font-weight: 500;
        color: #C6A75E; /* dourado TJSP */
        font-family: 'Segoe UI', sans-serif;
    }
    .section-title {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #8B0000 !important;
        font-family: 'Segoe UI', sans-serif;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brain-icon {
        height: 26px;
        vertical-align: middle;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
LOGO_PATH = "logo_synapse.png"

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        st.warning(f"⚠️ O arquivo '{bin_file}' não foi encontrado. "
                   f"Verifique se o logo está na raiz do projeto.")
        return None

def branding_bar():
    """Exibe o cabeçalho institucional do aplicativo."""
    logo_base64 = get_base64_of_bin_file(LOGO_PATH)
    if logo_base64:
        st.markdown(f"""
        <div class="branding-bar">
            <img src="data:image/png;base64,{logo_base64}" class="branding-logo">
            <div class="branding-text">
                <div class="branding-title">Synapse.IA</div>
                <div class="branding-subtitle">Tribunal de Justiça de São Paulo</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="branding-bar">
            <div class="branding-text">
                <div class="branding-title">Synapse.IA</div>
                <div class="branding-subtitle">Tribunal de Justiça de São Paulo</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# INTERFACE PRINCIPAL
# ============================================================
branding_bar()
st.markdown("")

# SEÇÃO 1 - INSUMOS MANUAIS
st.markdown("""
<div class="section-title">
    <img src="https://cdn-icons-png.flaticon.com/512/709/709496.png" class="brain-icon">
    Insumos Manuais
</div>
""", unsafe_allow_html=True)
with st.expander("Clique para inserir informações manuais"):
    st.text_area("Descreva aqui o objeto, justificativa ou requisitos do artefato:")

# SEÇÃO 2 - UPLOAD DE DOCUMENTO
st.markdown("""
<div class="section-title">
    <img src="https://cdn-icons-png.flaticon.com/512/3022/3022255.png" class="brain-icon">
    Upload de Documento (opcional)
</div>
""", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Selecione um arquivo", type=["pdf", "docx", "txt"])

# SEÇÃO 3 - SELEÇÃO DE AGENTE
st.markdown("""
<div class="section-title">
    <img src="https://cdn-icons-png.flaticon.com/512/1161/1161388.png" class="brain-icon">
    Selecionar Agente
</div>
""", unsafe_allow_html=True)
agent = st.selectbox(
    "Escolha o agente responsável pela validação:",
    ["ETP", "TR", "DFD", "PCA", "PESQUISA_PRECOS", "OBRAS", "EDITAL", "CONTRATO", "MAPA_RISCOS", "FISCALIZACAO"]
)

# SEÇÃO 4 - BOTÃO DE EXECUÇÃO
if st.button("Executar Validação"):
    st.success(f"✅ Validação do artefato **{agent}** concluída com sucesso!")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("""
<hr style="border-top: 1px solid #C6A75E;">
<div style="text-align:center; font-size:13px; color:gray;">
    © 2025 - Projeto Synapse.IA | Desenvolvido no âmbito do Tribunal de Justiça de São Paulo
</div>
""", unsafe_allow_html=True)
