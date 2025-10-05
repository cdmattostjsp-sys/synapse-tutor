import os
import json
import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import pandas as pd
import base64

# ======================================================
# 🧠 CONFIGURAÇÃO VISUAL DO APP
# ======================================================
st.set_page_config(page_title="Synapse.IA", layout="wide")

def get_base64_image(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ======================================================
# 🔷 BRANDING BAR (versão institucional compacta)
# ======================================================
logo_path = "logo_synapse.png"

if os.path.exists(logo_path):
    logo_base64 = get_base64_image(logo_path)
    st.markdown(
        f"""
        <div style='
            background-color:#0E1117;
            padding:12px 30px 6px 25px;
            display:flex;
            align-items:center;
            justify-content:flex-start;
            gap:16px;
            border-bottom:1px solid #303030;
            margin-bottom:10px;
        '>
            <img src="data:image/png;base64,{logo_base64}" width="62" style="border-radius:6px;">
            <div style='display:flex; flex-direction:column; align-items:flex-start; line-height:1.1;'>
                <h2 style='color:#FFFFFF; margin:0; font-weight:600; font-size:1.7rem;'>Synapse.IA</h2>
                <h5 style='color:#AAAAAA; margin:2px 0 0 0; font-weight:normal; font-size:1rem;'>Tribunal de Justiça de São Paulo</h5>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.title("🧠 Synapse.IA")
    st.caption("Tribunal de Justiça de São Paulo")

# ======================================================
# 🎨 ESTILO GERAL DO APP
# ======================================================
st.markdown(
    """
    <style>
        .stTextArea textarea {
            background-color: #1E1E1E;
            color: white;
            border-radius: 8px;
        }
        .stFileUploader {
            background-color: #1E1E1E;
            border-radius: 8px;
        }
        .stSelectbox {
            background-color: #1E1E1E;
        }
        .stButton button {
            border-radius: 6px;
            height: 2.8em;
        }
        /* Títulos padronizados */
        .section-title {
            display:flex;
            align-items:center;
            gap:10px;
            font-size:1.7rem;
            color:#FFFFFF;
            font-weight:600;
            margin-top:35px;
            margin-bottom:6px;
        }
        .section-subtext {
            color:#AAAAAA;
            font-size:0.9rem;
            margin-top:-5px;
            margin-bottom:10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
# ⚙️ CONFIGURAÇÃO DO CLIENTE OPENAI
# ======================================================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ======================================================
# 📂 FUNÇÕES DE LEITURA DE DOCUMENTOS
# ======================================================
def read_file(file):
    if file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
        return df.to_string()
    elif file.name.endswith(".csv"):
        df = pd.read_csv(file)
        return df.to_string()
    else:
        return file.read().decode("utf-8", errors="ignore")

# ======================================================
# 🧩 INTERFACE DO APP
# ======================================================
# Título 1: Insumos Manuais
st.markdown(
    f"""
    <div class="section-title">
        <img src="data:image/png;base64,{get_base64_image(logo_path)}" width="36">
        Insumos Manuais
    </div>
    <div class="section-subtext">Descreva o objeto, justificativa, requisitos, prazos, critérios etc.</div>
    """,
    unsafe_allow_html=True
)
texto_usuario = st.text_area("", height=200)

# Título 2: Upload de Documento
st.markdown(
    f"""
    <div class="section-title">
        <img src="data:image/png;base64,{get_base64_image(logo_path)}" width="36">
        Upload de Documento (opcional)
    </div>
    <div class="section-subtext">Envie PDF, DOCX, XLSX ou CSV (ex.: ETP, TR, Contrato, Obras etc.)</div>
    """,
    unsafe_allow_html=True
)
uploaded_file = st.file_uploader("Drag and drop file here", type=["pdf", "docx", "xlsx", "csv"])

# Título 3: Selecionar Agente
st.markdown(
    f"""
    <div class="section-title">
        <img src="data:image/png;base64,{get_base64_image(logo_path)}" width="36">
        Selecionar Agente
    </div>
    """,
    unsafe_allow_html=True
)
agente = st.selectbox("Escolha o agente:", ["ETP", "TR", "EDITAL", "CONTRATO", "PESQUISA_PRECOS", "DFD", "PCA", "FISCALIZACAO", "OBRAS", "MAPA_RISCOS"])
executar_semantico = st.checkbox("Executar validação semântica")

# ======================================================
# 🚀 EXECUÇÃO DO AGENTE
# ======================================================
if st.button("▶️ Executar Agente"):
    with st.spinner("Executando análise..."):
        document_text = texto_usuario
        if uploaded_file:
            document_text += "\n\n" + read_file(uploaded_file)

        prompt = f"""
        Você é um validador técnico. Analise o seguinte documento do tipo {agente}
        e aponte se contém os elementos obrigatórios, conforme as normas do TJSP
        e a Lei 14.133/2021. Apresente uma nota (0 a 100) e uma justificativa breve
        para cada item avaliado.
        Documento:
        {document_text}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um avaliador técnico de documentos administrativos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800
            )
            result_text = response.choices[0].message.content
            st.success("✅ Validação concluída com sucesso!")
            st.text_area("Resultado da Validação", value=result_text, height=400)

        except Exception as e:
            st.error(f"Erro ao processar: {e}")
