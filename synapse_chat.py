import os
import json
import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import pandas as pd
from PIL import Image

# Importa engine unificado
from knowledge.validators.validator_engine import validate_document, SUPPORTED_ARTEFACTS

# ======================================================
# 🧠 CONFIGURAÇÃO VISUAL DO APP
# ======================================================
st.set_page_config(page_title="Synapse.IA – Prova de Conceito (POC)", layout="wide")

# --- Cabeçalho Institucional com Logotipo ---
try:
    logo = Image.open("ChatGPT Image 4 de out. de 2025, 17_46_48.png")
    st.image(logo, width=320)
except Exception:
    st.warning("⚠️ Logotipo não encontrado. Verifique o nome do arquivo ou caminho.")

st.markdown(
    """
    <div style='text-align: center; margin-top: -30px;'>
        <h1 style='color: #FFFFFF;'>Prova de Conceito – Synapse.IA</h1>
        <h4 style='color: #AAAAAA;'>Tribunal de Justiça de São Paulo (TJSP)</h4>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Estilo de fundo e layout ---
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #0E1117;
    }
    [data-testid="stSidebar"] {
        background-color: #161A23;
    }
    h1, h2, h3, h4, h5, h6, p {
        color: #FFFFFF;
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

# Carrega prompt do agente
def load_prompt(agent_name):
    try:
        with open(f"prompts/{agent_name}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["prompt"]
    except FileNotFoundError:
        return f"⚠️ Prompt do agente {agent_name} não encontrado."

# Executa agente
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

# Leitura de arquivos
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        return f"⚠️ Erro ao processar PDF: {e}"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        return f"⚠️ Erro ao processar DOCX: {e}"

def extract_text_from_excel(file):
    try:
        df = pd.read_excel(file)
        preview = df.head(20).to_string(index=False)
        return f"Conteúdo da planilha (amostra):\n{preview}"
    except Exception as e:
        return f"⚠️ Erro ao processar Excel: {e}"

def extract_text_from_csv(file):
    try:
        df = pd.read_csv(file)
        preview = df.head(20).to_string(index=False)
        return f"Conteúdo do CSV (amostra):\n{preview}"
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

# Upload de arquivo
st.subheader("📂 Upload de Documento (opcional)")
uploaded_file = st.file_uploader(
    "Envie PDF, DOCX, XLSX ou CSV (ex.: ETP, TR, Contrato, Obras etc.)",
    type=["pdf", "docx", "xlsx", "csv"]
)

conteudo_documento = ""
if uploaded_file is not None:
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

# Junta insumos
insumos_finais = insumos + "\n\n" + conteudo_documento

# Seleção de agente
st.subheader("🤖 Selecionar Agente")
agent_name = st.selectbox("Escolha o agente:", SUPPORTED_ARTEFACTS)

# Opção de validação semântica
use_semantic = st.checkbox("🔍 Executar validação semântica")

# Botão executar
if st.button("▶️ Executar Agente"):
    if not insumos_finais.strip():
        st.warning("⚠️ Por favor, insira insumos ou envie um documento antes de executar.")
    else:
        with st.spinner("Gerando documento..."):
            result = run_agent(agent_name, insumos_finais)
            validation = validate_document(agent_name, result, use_semantic=use_semantic, client=client)

        # --- Avaliação RÍGIDA ---
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

        # --- Avaliação SEMÂNTICA ---
        if use_semantic:
            st.subheader("🧠 Avaliação de Conformidade — Semântica (IA)")
            st.write(f"**Score Semântico:** {validation.get('semantic_score', 0.0):.1f}%")

            sem_rows = validation.get("semantic_result", [])
            if sem_rows:
                df_sem = pd.DataFrame(sem_rows)
                if "presente" in df_sem.columns:
                    df_sem["presente"] = df_sem["presente"].apply(lambda x: "✅" if x else "❌")
                if "adequacao_nota" in df_sem.columns:
                    df_sem["status"] = df_sem["adequacao_nota"].apply(
                        lambda n: "✅ Adequado" if n == 100 else ("⚠️ Parcial" if n > 0 else "❌ Ausente")
                    )
                cols = [c for c in ["id", "descricao", "presente", "adequacao_nota", "status", "justificativa"] if c in df_sem.columns]
                st.dataframe(df_sem[cols], use_container_width=True)
            else:
                st.info("Nenhum item identificado na validação semântica.")

        # --- Documento Final ---
        st.subheader("📄 Documento Gerado")
        st.text_area("Documento Gerado:", value=result, height=600)
