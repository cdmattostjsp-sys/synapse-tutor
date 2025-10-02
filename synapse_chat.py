import os
import json
import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import pandas as pd

# Importa engine unificado
from knowledge.validators.validator_engine import validate_document, SUPPORTED_ARTEFACTS

# Inicializa o cliente OpenAI
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("❌ Chave da OpenAI não encontrada. Configure em Settings > Secrets.")
    st.stop()

client = OpenAI(api_key=api_key)

# Função para carregar os prompts de cada agente
def load_prompt(agent_name):
    try:
        with open(f"prompts/{agent_name}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["prompt"]
    except FileNotFoundError:
        return f"⚠️ Prompt do agente {agent_name} não encontrado."

# Função que envia mensagem ao modelo
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

# Funções auxiliares para leitura de arquivos
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

# Configuração da página
st.set_page_config(page_title="Synapse.IA - Orquestrador", layout="wide")
st.title("🧠 Synapse.IA – Prova de Conceito (POC)")

# Entrada manual
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

# Insumos finais
insumos_finais = insumos + "\n\n" + conteudo_documento

# Seleção do agente
st.subheader("🤖 Selecionar Agente")
agent_name = st.selectbox("Escolha o agente:", SUPPORTED_ARTEFACTS)

# Checkbox para validação semântica
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
            df_rigido["status"] = df_rigido.apply(
                lambda r: "✅ Presente" if r["presente"] else "❌ Ausente", axis=1
            )
            df_rigido["obrigatorio"] = df_rigido["obrigatorio"].apply(lambda x: "✅" if x else "⬜")
            st.dataframe(df_rigido[["id", "descricao", "obrigatorio", "status"]], use_container_width=True)
        else:
            st.info("Nenhum item identificado no checklist rígido.")

        # --- Avaliação SEMÂNTICA ---
        if use_semantic:
            st.subheader("🧠 Avaliação de Conformidade — Semântica (IA)")
            st.write(f"**Score Semântico:** {validation.get('semantic_score', 0.0):.1f}%")

            sem_rows = validation.get("semantic_result", [])
            if sem_rows:
                df_sem = pd.DataFrame(sem_rows)
                df_sem["status"] = df_sem.apply(
                    lambda r: "✅ Adequado" if r["adequacao_nota"] == 100 else (
                        "⚠️ Parcial" if r["adequacao_nota"] > 0 else "❌ Ausente"
                    ),
                    axis=1
                )
                if "presente" in df_sem.columns:
                    df_sem["presente"] = df_sem["presente"].apply(lambda x: "✅" if x else "❌")

                st.dataframe(
                    df_sem[["id", "descricao", "presente", "adequacao_nota", "status", "justificativa"]],
                    use_container_width=True
                )

                # Exibir faltantes
                faltantes_all = []
                for r in sem_rows:
                    if r.get("faltantes"):
                        for f in r["faltantes"]:
                            faltantes_all.append(f"• **{r['id']}**: {f}")
                if faltantes_all:
                    st.markdown("### Pontos que ainda faltam detalhar (semântico):")
                    st.markdown("\n".join(faltantes_all))
            else:
                st.info("Nenhum item identificado na validação semântica.")

        # --- Documento (sempre por último) ---
        st.subheader("📄 Documento Gerado")
        st.text_area("Documento Gerado:", value=result, height=600)
