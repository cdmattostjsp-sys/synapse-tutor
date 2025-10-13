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

# -------------------------------------
# CONFIG
# -------------------------------------
st.set_page_config(page_title="Synapse Tutor v2 – DFD", layout="wide")
st.title("🧭 Synapse Tutor — Jornada Guiada Interativa (DFD)")

st.markdown("""
O Synapse Tutor v2 agora registra automaticamente **logs de execução**, pontuação e modo de operação.
""")

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
# ESTADO
# -------------------------------------
if "respostas" not in st.session_state:
    st.session_state["respostas"] = {}
if "validation_result" not in st.session_state:
    st.session_state["validation_result"] = None

# -------------------------------------
# PERGUNTAS
# -------------------------------------
question_bank = _load_question_bank()
dfd_questions = question_bank.get("dfd", {})
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
# MODO DE OPERAÇÃO
# -------------------------------------
st.divider()
modo_tutor = st.radio("🎚️ Selecione o modo de operação:", ["Tutor Orientador", "Avaliador Institucional"])
tutor_mode = True if modo_tutor == "Tutor Orientador" else False

# -------------------------------------
# GERAÇÃO DO DOCUMENTO
# -------------------------------------
st.divider()
if st.button("Gerar DFD", type="primary"):
    r = st.session_state["respostas"]
    if not r:
        st.warning("⚠️ Preencha as respostas primeiro.")
    else:
        dfd_text = f"""
# Documento de Formalização da Demanda (DFD)
**Data:** {datetime.now():%d/%m/%Y}
**Unidade Solicitante:** {r.get('resp_unidade_demandante', 'Não informado')}
**Responsável:** {r.get('resp_responsavel', 'Não informado')}

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
        st.session_state["dfd_text"] = dfd_text
        with st.expander("👁️ Prévia do Documento Base"):
            st.markdown(dfd_text)
        st.success("✅ Documento base criado.")

# -------------------------------------
# VALIDAÇÃO
# -------------------------------------
st.divider()
include_suggestions = st.checkbox("💡 Incluir sugestões construtivas", value=True)

if st.button("Executar Validação e Gerar Relatório"):
    if "dfd_text" not in st.session_state:
        st.warning("⚠️ Gere o documento primeiro.")
    else:
        client = _load_api_client()
        if client:
            with st.spinner("Executando validação semântica..."):
                vr = validate_document(st.session_state["dfd_text"], "DFD", client)
                enhanced = enhance_markdown(vr.get("guided_markdown", ""), vr, include_suggestions, tutor_mode)
                summary = generate_summary(vr, tutor_mode)

                # Exportação DOCX + LOG
                buffer = markdown_to_docx(enhanced, f"DFD ({modo_tutor})", summary)
                filename_docx = f"DFD_{datetime.now():%Y%m%d_%H%M%S}.docx"
                filepath_docx = os.path.join(RASCDIR, filename_docx)
                with open(filepath_docx, "wb") as f:
                    f.write(buffer.getvalue())

                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "mode": modo_tutor,
                    "scores": {"rigid": vr.get("rigid_score", 0), "semantic": vr.get("semantic_score", 0)},
                    "file": filename_docx,
                }
                log_file = os.path.join(LOGS_DIR, "tutor_logs.jsonl")
                with open(log_file, "a", encoding="utf-8") as log:
                    log.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

                # Exibição e download
                st.success("✅ Validação e registro concluídos.")
                st.markdown(summary)
                st.download_button("⬇️ Baixar DOCX", data=buffer,
                                   file_name=filename_docx,
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
