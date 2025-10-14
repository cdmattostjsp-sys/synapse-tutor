import sys
import os
from datetime import datetime
import streamlit as st
import yaml
from openai import OpenAI
import json

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from validator_engine_vNext import validate_document
from utils.formatter_docx import markdown_to_docx
from utils.recommender_engine import enhance_markdown, generate_summary

EXPORTS_DIR = os.path.join(root_dir, "exports")
LOGS_DIR = os.path.join(EXPORTS_DIR, "logs")
RASCDIR = os.path.join(EXPORTS_DIR, "rascunhos")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(RASCDIR, exist_ok=True)

st.set_page_config(page_title="Synapse Tutor v2 – DFD", layout="wide")
st.title("🧭 Synapse Tutor — Jornada Guiada Interativa (DFD)")

# -------------------------------------
# FUNÇÕES AUXILIARES
# -------------------------------------
def _load_api_client():
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        st.warning("⚠️ Para validação semântica, configure OPENAI_API_KEY.")
        return None
    return OpenAI(api_key=api_key)

def _load_question_bank():
    try:
        with open(os.path.join("journey", "question_bank.yaml"), "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.error("❌ Arquivo 'journey/question_bank.yaml' não encontrado.")
        st.stop()

# -------------------------------------
# INTERFACE E ESTADO
# -------------------------------------
question_bank = _load_question_bank()
dfd_questions = question_bank.get("dfd", {})

st.markdown("O Tutor agora gera rascunhos numerados, com registro de autor e exportação DOCX + PDF.")

if st.button("🧹 Limpar sessão atual"):
    st.session_state.clear()
    st.success("Sessão limpa. Preencha novamente os campos.")

if "respostas" not in st.session_state:
    st.session_state["respostas"] = {}

# -------------------------------------
# COLETA DE RESPOSTAS
# -------------------------------------
st.subheader("🧾 Preencha as respostas abaixo")
answered = 0
for key, pergunta in dfd_questions.items():
    campo = f"resp_{key}"
    resposta = st.text_area(pergunta, value=st.session_state["respostas"].get(campo, ""), height=80)
    if resposta.strip():
        st.session_state["respostas"][campo] = resposta
        answered += 1
st.progress(answered / len(dfd_questions or [1]), text=f"{answered}/{len(dfd_questions)} respostas")

# -------------------------------------
# MODO E RESPONSÁVEL
# -------------------------------------
st.divider()
modo_tutor = st.radio("🎚️ Selecione o modo de operação:", ["Tutor Orientador", "Avaliador Institucional"])
tutor_mode = True if modo_tutor == "Tutor Orientador" else False
responsavel = st.text_input("👤 Informe o responsável pela elaboração (nome e cargo):")

# -------------------------------------
# GERAÇÃO + VALIDAÇÃO
# -------------------------------------
if st.button("🚀 Gerar e Validar Documento"):
    r = st.session_state["respostas"]
    if not r:
        st.warning("⚠️ Preencha as respostas primeiro.")
    else:
        client = _load_api_client()
        if not client:
            st.stop()

        with st.spinner("Gerando DFD e executando validação..."):
            dfd_text = f"""
# Documento de Formalização da Demanda (DFD)
**Data:** {datetime.now():%d/%m/%Y}
**Unidade Solicitante:** {r.get('resp_unidade_demandante', 'Não informado')}
**Responsável:** {responsavel or r.get('resp_responsavel', 'Não informado')}

## Descrição do Objeto
{r.get('resp_objeto', 'Não informado')}

## Justificativa da Necessidade
{r.get('resp_justificativa', 'Não informado')}

## Quantidade, Urgência e Riscos
- Quantidade: {r.get('resp_quantidade_ou_escopo', 'Não informado')}
- Urgência: {r.get('resp_condicao_urgencia', 'Não informado')}
- Riscos: {r.get('resp_riscos', 'Não informado')}

## Alinhamento Institucional
{r.get('resp_alinhamento_planejamento', 'Não informado')}

## Documentos de Suporte
{r.get('resp_documentos_suporte', 'Não informado')}

_Gerado automaticamente pelo Synapse Tutor — SAAB/TJSP, versão 2025_
"""
            vr = validate_document(dfd_text, "DFD", client)
            enhanced = enhance_markdown(vr.get("guided_markdown", ""), vr, True, tutor_mode)
            summary = generate_summary(vr, tutor_mode, responsavel)

            buffer, pdf_path = markdown_to_docx(enhanced, f"DFD ({modo_tutor})", summary, RASCDIR, responsavel)

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "mode": modo_tutor,
                "responsavel": responsavel,
                "scores": {"rigid": vr.get("rigid_score", 0), "semantic": vr.get("semantic_score", 0)},
                "files": {"docx": pdf_path.replace(".pdf", ".docx"), "pdf": pdf_path},
            }
            with open(os.path.join(LOGS_DIR, "tutor_logs.jsonl"), "a", encoding="utf-8") as log:
                log.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        st.success("✅ Documento validado e exportado com sucesso.")
        st.download_button("⬇️ Baixar .DOCX", data=buffer, file_name="DFD_orientado.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ Baixar .PDF", data=f, file_name="DFD_orientado.pdf", mime="application/pdf")
