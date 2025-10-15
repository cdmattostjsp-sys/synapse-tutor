# =========================================
# Synapse Tutor v2.6 – Página DFD (UX de Jornada + só score semântico)
# =========================================

import sys
import os
from datetime import datetime
import streamlit as st
import yaml
from openai import OpenAI

# Ajuste do PATH
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Imports locais
from validator_engine_vNext import validate_document
from utils.formatter_docx import markdown_to_docx
from utils.recommender_engine import enhance_markdown

# -------------------------------
# Config
# -------------------------------
st.set_page_config(page_title="Synapse Tutor — Jornada Guiada", layout="wide")

st.title("🧭 Synapse Tutor — Jornada Guiada")
st.markdown("""
O **Synapse Tutor** conduz você pela **jornada de contratação**.  
**Primeiro passo:** elaborar o **Documento de Formalização da Demanda (DFD)**.  
Em seguida, evoluímos para **ETP → TR → Contrato → Fiscalização**, sempre validando conteúdo e sugerindo aprimoramentos com base na **Lei nº 14.133/2021** e **IN SAAB nº 12/2025**.
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
# Etapa 1 – Coleta de respostas (DFD)
# -------------------------------
st.header("1) DFD — Preencha as respostas do primeiro passo")
question_bank = _load_question_bank()
dfd_questions = question_bank.get("dfd", {})

answered = 0
for key, pergunta in dfd_questions.items():
    campo = f"resp_{key}"
    resposta = st.text_area(pergunta, value=st.session_state["respostas"].get(campo, ""), height=80)
    if resposta.strip():
        st.session_state["respostas"][campo] = resposta
        answered += 1

st.progress(answered / max(len(dfd_questions), 1), text=f"{answered}/{len(dfd_questions)} respostas")

# -------------------------------
# Etapa 2 – Geração do Documento Base
# -------------------------------
st.header("2) Gerar rascunho do DFD")
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

_Gerado automaticamente pelo Synapse Tutor — SAAB/TJSP_
"""
        st.session_state["dfd_text"] = dfd_text
        st.session_state["validation_result"] = None
        st.session_state["enhanced_markdown"] = ""
        st.success("✅ Documento base criado.")
        with st.expander("👁️ Visualizar rascunho gerado"):
            st.markdown(st.session_state["dfd_text"])
        st.info("ℹ️ Agora execute a **validação** para análise semântica e recomendações automáticas.")

# -------------------------------
# Etapa 3 – Validação e Recomendações
# -------------------------------
st.header("3) Validação semântica e recomendações")
include_suggestions = st.checkbox("💡 Incluir sugestões construtivas no resultado", value=True)

if st.button("Executar validação"):
    if not st.session_state["dfd_text"]:
        st.warning("⚠️ Gere o documento DFD antes.")
    else:
        client = _load_api_client()
        if client:
            with st.spinner("🔍 Executando validação semântica..."):
                vr = validate_document(st.session_state["dfd_text"], "DFD", client)
                st.session_state["validation_result"] = vr
                enhanced = enhance_markdown(vr.get("guided_markdown", ""), vr, include_suggestions)
                st.session_state["enhanced_markdown"] = enhanced
                st.success("✅ Validação concluída!")

# -------------------------------
# Resultados e Exportação
# -------------------------------
vr = st.session_state.get("validation_result")
if vr:
    st.subheader("📊 Resultado da análise")
    # ⚠️ Removemos o score rígido da UI (mantém-se disponível em logs se necessário)
    sem_score = vr.get("semantic_score", 0.0)
    st.metric("Score Semântico", f"{sem_score:.1f}%")

    st.markdown("### 📝 Rascunho orientado (pronto para exportação)")
    md_final = st.session_state["enhanced_markdown"] or vr.get("guided_markdown", "")
    st.markdown(md_final)

    # Exportação (DOCX sempre; PDF se disponível no ambiente)
    buffer, pdf_path = markdown_to_docx(
        md_final,
        "DFD (Rascunho Orientado)",
        vr.get("summary", ""),
    )

    docx_name = "DFD_orientado.docx"
    st.download_button(
        "⬇️ Baixar (.docx)",
        data=buffer,
        file_name=docx_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    if pdf_path and os.path.exists(pdf_path):
        pdf_name = os.path.basename(pdf_path)
        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇️ Baixar (.pdf)",
                data=f,
                file_name=pdf_name,
                mime="application/pdf",
            )
    else:
        st.info("📄 O arquivo PDF pode não estar disponível neste ambiente (dependência opcional).")

st.divider()
st.caption("Jornada: DFD → ETP → TR → Contrato → Fiscalização • Synapse.IA | SAAB | TJSP")
