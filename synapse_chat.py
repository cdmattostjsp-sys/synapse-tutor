import os
import json
import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import pandas as pd

# importa o validador unificado
from knowledge.validators.validator_engine import (
    engine_rigid_validate,
    engine_missing_rigid,
    engine_semantic_validate,
)

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
    "Envie PDF, DOCX, XLSX ou CSV (ex.: ETP, pesquisa de preços, minuta etc.)",
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
agent_list = [
    "PCA", "DFD", "ETP", "TR", "PESQUISA_PRECOS", "CONTRATO",
    "FISCALIZACAO", "CHECKLIST", "PARECER_JURIDICO", "MAPA_RISCOS", "EDITAL"
]
agent_name = st.selectbox("Escolha o agente:", agent_list)

# Opção: rodar validação semântica
run_semantic = st.checkbox("Rodar validação semântica (IA)", value=False)

# Botão executar
if st.button("▶️ Executar Agente"):
    if not insumos_finais.strip():
        st.warning("⚠️ Por favor, insira insumos ou envie um documento antes de executar.")
    else:
        with st.spinner("Gerando documento..."):
            result = run_agent(agent_name, insumos_finais)

        st.subheader("📄 Saída do Agente")

        if agent_name in ["ETP", "TR"]:
            score, results = engine_rigid_validate(result, agent_name)
            faltando = engine_missing_rigid(results)

            st.subheader(f"🔎 Conformidade – {agent_name} (Checklist RÍGIDO / Engine)")
            st.metric("Selo de Conformidade (rígido)", f"{score}%")
            if faltando:
                st.warning("Itens ausentes ou incompletos (rígido):")
                for it in faltando:
                    st.write(f"• {it}")
            else:
                st.success("Checklist integralmente atendido ✅")

            df = pd.DataFrame(results)
            df["ok"] = df["ok"].map({True: "✅", False: "❌"})
            st.dataframe(df[["id", "descricao", "ok"]], use_container_width=True)

            if run_semantic:
                with st.spinner("Executando validação semântica (IA)..."):
                    sem_score, sem_results = engine_semantic_validate(result, agent_name, client)

                st.subheader(f"🧠 Conformidade Semântica — {agent_name} (IA / Engine)")
                st.metric("Selo Semântico", f"{sem_score}%")

                df2 = pd.DataFrame(sem_results)
                df2["presente"] = df2["presente"].map({True: "✅", False: "❌"})
                st.dataframe(df2[["id", "descricao", "presente", "adequacao_nota", "justificativa"]], use_container_width=True)

                pend = [r for r in sem_results if r.get("faltantes")]
                if pend:
                    st.info("Pontos que ainda faltam detalhar (semântico):")
                    for r in pend:
                        falt = "; ".join(r["faltantes"][:5])
                        st.write(f"• **{r['id']}**: {falt}")

        st.divider()
        st.text_area("Documento Gerado:", value=result, height=600)
