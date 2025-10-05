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
# 🔷 BRANDING BAR COMPACTA
# ======================================================
logo_path = "logo_synapse.png"

if os.path.exists(logo_path):
    logo_base64 = get_base64_image(logo_path)
    st.markdown(
        f"""
        <div style='background-color:#0E1117; padding:10px 25px; display:flex; align-items:center; justify-content:flex-start; gap:10px; border-bottom:1px solid #222;'>
            <img src="data:image/png;base64,{logo_base64}" width="42" style="border-radius:6px;">
            <div style='display:flex; flex-direction:column; align-items:flex-start;'>
                <h2 style='color:#FFFFFF; margin:0; font-weight:600;'>Synapse.IA</h2>
                <h5 style='color:#AAAAAA; margin:0; font-weight:normal;'>Tribunal de Justiça de São Paulo</h5>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.title("🧠 Synapse.IA")
    st.caption("Tribunal de Justiça de São Paulo")

# ======================================================
# 🎨 ESTILO GERAL
# ======================================================
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #0E1117;
    }
    [data-testid="stSidebar"] {
        background-color: #161A23;
    }
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
# 🔐 CONFIGURAÇÃO OPENAI
# ======================================================
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("❌ Chave da OpenAI não encontrada. Configure em Settings > Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# ======================================================
# ⚙️ FUNÇÕES AUXILIARES
# ======================================================
from knowledge.validators.validator_engine import validate_document, SUPPORTED_ARTEFACTS

def load_prompt(agent_name):
    try:
        with open(f"prompts/{agent_name}.json", "r", encoding="utf-8") as f:
            return json.load(f)["prompt"]
    except FileNotFoundError:
        return f"⚠️ Prompt do agente {agent_name} não encontrado."

def run_agent(agent_name, insumos):
    prompt_base = load_prompt(agent_name)
    user_message = f"Insumos fornecidos:\n{insumos}\n\nElabore o documento conforme instruções do agente {agent_name}."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt_base},
            {"role": "user", "content": user_message}
        ],
        temperature=0.4,
        max_tokens=1800
    )
    return response.choices[0].message.content

# Extração de texto
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        return f"⚠️ Erro ao processar PDF: {e}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except Exception as e:
        return f"⚠️ Erro ao processar DOCX: {e}"

def extract_text_from_excel(file):
    try:
        df = pd.read_excel(file)
        return f"Conteúdo da planilha (amostra):\n{df.head(20).to_string(index=False)}"
    except Exception as e:
        return f"⚠️ Erro ao processar Excel: {e}"

def extract_text_from_csv(file):
    try:
        df = pd.read_csv(file)
        return f"Conteúdo do CSV (amostra):\n{df.head(20).to_string(index=False)}"
    except Exception as e:
        return f"⚠️ Erro ao processar CSV: {e}"

# ======================================================
# 🧩 INTERFACE PRINCIPAL
# ======================================================
st.divider()
st.subheader("📥 Insumos manuais")
insumos = st.text_area(
    "Descreva o objeto, justificativa, requisitos, prazos, critérios etc.",
    height=200
)

st.subheader("📂 Upload de Documento (opcional)")
uploaded_file = st.file_uploader(
    "Envie PDF, DOCX, XLSX ou CSV (ex.: ETP, TR, Contrato, Obras etc.)",
    type=["pdf", "docx", "xlsx", "csv"]
)

conteudo_documento = ""
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        conteudo_documento = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        conteudo_documento = extract_text_from_docx(uploaded_file)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        conteudo_documento = extract_text_from_excel(uploaded_file)
    elif uploaded_file.type == "text/csv":
        conteudo_documento = extract_text_from_csv(uploaded_file)

    if conteudo_documento and not conteudo_documento.startswith("⚠️"):
        st.success("📄 Arquivo processado com sucesso! Conteúdo incorporado aos insumos.")
    else:
        st.error(conteudo_documento)

insumos_finais = insumos + "\n\n" + conteudo_documento

st.subheader("🤖 Selecionar Agente")
agent_name = st.selectbox("Escolha o agente:", SUPPORTED_ARTEFACTS)
use_semantic = st.checkbox("🔍 Executar validação semântica")

if st.button("▶️ Executar Agente"):
    if not insumos_finais.strip():
        st.warning("⚠️ Por favor, insira insumos ou envie um documento antes de executar.")
    else:
        with st.spinner("Gerando documento..."):
            result = run_agent(agent_name, insumos_finais)
            validation = validate_document(agent_name, result, use_semantic=use_semantic, client=client)

        st.subheader("📊 Avaliação de Conformidade — Checklist RÍGIDO")
        st.write(f"**Score Rígido:** {validation.get('rigid_score', 0.0):.1f}%")
        rigid_rows = validation.get("rigid_result", [])
        if rigid_rows:
            df_rigido = pd.DataFrame(rigid_rows)
            df_rigido["obrigatório"] = df_rigido["obrigatorio"].apply(lambda x: "✅" if x else "⬜")
            df_rigido["presente"] = df_rigido["presente"].apply(lambda x: "✅" if x else "❌")
            st.dataframe(df_rigido[["id", "descricao", "obrigatório", "presente"]], use_container_width=True)
        else:
            st.info("Nenhum item identificado no checklist rígido.")

        if use_semantic:
            st.subheader("🧠 Avaliação de Conformidade — Semântica (IA)")
            st.write(f"**Score Semântico:** {validation.get('semantic_score', 0.0):.1f}%")
            sem_rows = validation.get("semantic_result", [])
            if sem_rows:
                df_sem = pd.DataFrame(sem_rows)
                if "adequacao_nota" in df_sem.columns:
                    df_sem["status"] = df_sem["adequacao_nota"].apply(
                        lambda n: "✅ Adequado" if n == 100 else ("⚠️ Parcial" if n > 0 else "❌ Ausente")
                    )
                cols = [c for c in ["id", "descricao", "adequacao_nota", "status", "justificativa"] if c in df_sem.columns]
                st.dataframe(df_sem[cols], use_container_width=True)
            else:
                st.info("Nenhum item identificado na validação semântica.")

        st.subheader("📄 Documento Gerado")
        st.text_area("Documento Gerado:", value=result, height=600)
