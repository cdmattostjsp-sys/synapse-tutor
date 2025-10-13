import sys
import os

# =========================================
# Ajuste de PATH
# =========================================
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from datetime import datetime
import streamlit as st
import yaml
from openai import OpenAI

from validator_engine_vNext import validate_document
from utils.formatter_docx import markdown_to_docx
from utils.recommender_engine import enhance_markdown

# -------------------------------
# Config
# -------------------------------
st.set_page_config(page_title="Synapse Tutor – Jornada Guiada v2", layout="wide")

st.title("🧭 Synapse Tutor — Jornada Guiada Interativa (DFD)")
st.markdown("""
O **Synapse Tutor v2** agora permite **inserir ou ocultar sugestões construtivas** no rascunho final (.docx),
mantendo a aderência à **Lei nº 14.133/2021** e à **IN SAAB nº 12/2025**.
""")

# -------------------------------
# Funções auxiliares
# -------------------------------
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

# -------------------------------
# Estado
# -------------------------------
if "respostas" not in st.session_state:
    st.session_state["respostas"] = {}
if "dfd_text" not in st.session_state:
    st.session_state["dfd_text"] = ""
if "validation_result" not in st.session_state:
    st.session_state["validation_result"] = None
if "enhanced_markdown" not in st.session_state:
    st.session_state["enhanced_markdown"] = ""

# -------------------------------
# Perguntas
# -------------------------------
question_bank = _load_question_bank()
dfd_questions = question_bank.get("dfd", {})
st.divider()
st.subheader("🧾 Preencha as respostas abaixo")

answered = 0
for key, pergunta in dfd_questions.items():
    campo = f"resp_{key}"
    resposta = st.text_area(pergunta, value=st.session_state["respostas"].get(campo, ""), height=80)
    if resposta.strip():
        st.session_state["respostas"][campo] = resposta
        answered += 1

st.progress(answered / len(dfd_questions or [1]), text=f"{answered}/{len(dfd_questions)} respostas")

# -------------------------------
# Geração do DFD
# -------------------------------
st.divider()
st.subheader("📄 Geração do Documento")

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

## 1️⃣ Descrição do Objeto
{r.get('resp_objeto', 'Não informado')}

## 2️⃣ Justificativa da Necessidade
{r.get('resp_justificativa', 'Não informado')}

## 3️⃣ Quantidade, Urgência e Riscos
- **Quantidade:** {r.get('resp_quantidade_ou_escopo', 'Não informado')}
- **Urgência:** {r.get('resp_condicao_urgencia', 'Não informado')}
- **Riscos:** {r.get('resp_riscos', 'Não informado')}

## 4️⃣ Alinhamento Institucional
{r.get('resp_alinhamento_planejamento', 'Não informado')}

## 5️⃣ Documentos de Suporte
{r.get('resp_documentos_suporte', 'Não informado')}

_Gerado automaticamente pelo Synapse Tutor — SAAB/TJSP, versão POC 2025_
"""
        st.session_state["dfd_text"] = dfd_text
        st.session_state["validation_result"] = None
        st.session_state["enhanced_markdown"] = ""
        st.success("✅ Documento base criado.")

# -------------------------------
# Validação + Recomendações
# -------------------------------
st.divider()
st.subheader("✅ Validação e Recomendações")

include_suggestions = st.checkbox("🔘 Incluir sugestões construtivas no resultado", value=True)

if st.button("Executar validação"):
    if not st.session_state["dfd_text"]:
        st.warning("⚠️ Gere o documento DFD antes.")
    else:
        client = _load_api_client()
        if client:
            with st.spinner("Executando validação..."):
                vr = validate_document(st.session_state["dfd_text"], "DFD", client)
                st.session_state["validation_result"] = vr
                enhanced = enhance_markdown(vr.get("guided_markdown", ""), vr, include_suggestions)
                st.session_state["enhanced_markdown"] = enhanced
                st.success("Validação e recomendações concluídas!")

vr = st.session_state.get("validation_result")
if vr:
    c1, c2 = st.columns(2)
    c1.metric("Score Rígido", f"{vr.get('rigid_score', 0):.1f}%")
    c2.metric("Score Semântico", f"{vr.get('semantic_score', 0):.1f}%")

    st.markdown("### 📝 Rascunho Orientado Final")
    md_final = st.session_state["enhanced_markdown"] or vr.get("guided_markdown", "")
    st.markdown(md_final)

    # Downloads
    st.download_button("⬇️ Baixar (.md)", data=md_final.encode(), file_name="DFD_orientado.md", mime="text/markdown")

    buffer = markdown_to_docx(md_final, "DFD (Rascunho com Sugestões)" if include_suggestions else "DFD (Rascunho Limpo)")
    st.download_button("⬇️ Baixar (.docx)", data=buffer, file_name="DFD_orientado.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
