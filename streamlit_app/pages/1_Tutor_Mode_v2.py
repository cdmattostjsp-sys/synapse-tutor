# =========================================
# Synapse Tutor v2.8 – Jornada + Exemplos Pedagógicos + Revisor Leve
# =========================================

import sys
import os
import re
from datetime import datetime
import streamlit as st
import yaml
from openai import OpenAI

# Ajuste do PATH raiz
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Imports locais
from validator_engine_vNext import validate_document
from utils.formatter_docx import markdown_to_docx
from utils.recommender_engine import enhance_markdown
from utils.recommender_examples import build_example_snippets

# -------------------------------
# Configuração inicial
# -------------------------------
st.set_page_config(page_title="Synapse Tutor — Jornada Guiada", layout="wide")

st.title("🧭 Synapse Tutor — Jornada Guiada")
st.markdown("""
O **Synapse Tutor** conduz você pela **jornada completa da contratação pública**.  
**Primeiro passo:** Documento de Formalização da Demanda (DFD).  
Depois, avançamos para **ETP → TR → Contrato → Fiscalização**, sempre com validação baseada na **Lei nº 14.133/2021** e **IN SAAB nº 12/2025**.
""")

# Painel de progresso visual
st.progress(0.2, "1️⃣ DFD (atual) → 2️⃣ ETP → 3️⃣ TR → 4️⃣ Contrato → 5️⃣ Fiscalização")
st.caption("Etapa atual: Formalização da Demanda • Etapas futuras: ETP → TR → Contrato → Fiscalização")

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

# Revisor leve de escrita (heurístico, não bloqueante)
COMMON_FIXES = [
    (r"\bAdmininstra", "Administra"),
    (r"\bJustila\b", "Justiça"),
    (r"\bprovar materiais\b", "prover materiais"),
    (r"\bPresiência\b", "Presidência"),
    (r"\b19º\b", "19ª"),
    (r"\bForum\b", "Fórum"),
]
def soft_spellcheck(text: str) -> list[str]:
    hints = []
    for pat, sug in COMMON_FIXES:
        if re.search(pat, text, flags=re.IGNORECASE):
            hints.append(f"Possível ajuste: **{sug}** (encontrado padrão `{pat}`)")
    return hints

def collect_all_answers(resps: dict) -> str:
    """Concatena respostas para rodar revisor leve e dar feedback rápido."""
    parts = []
    for k, v in resps.items():
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
    return "\n".join(parts)

# -------------------------------
# Estado da sessão
# -------------------------------
if "respostas" not in st.session_state:
    st.session_state["respostas"] = {}
if "dfd_text" not in st.session_state:
    st.session_state["dfd_text"] = ""
if "validation_result" not in st.session_state:
    st.session_state["validation_result"] = None
if "enhanced_markdown" not in st.session_state:
    st.session_state["enhanced_markdown"] = ""
if "example_inserts" not in st.session_state:
    st.session_state["example_inserts"] = []  # trechos inseridos no rascunho

# -------------------------------
# Etapa 1 – Coleta de respostas
# -------------------------------
st.header("1️⃣ DFD — Preencha as respostas iniciais")
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

# Revisor leve de escrita (apenas dicas)
if answered:
    joined = collect_all_answers(st.session_state["respostas"])
    issues = soft_spellcheck(joined)
    if issues:
        with st.expander("🔎 Dicas de escrita detectadas (opcional)"):
            for i in issues:
                st.markdown(f"- {i}")
            st.caption("Essas correções são apenas sugestões visuais; não bloqueiam o fluxo.")

# -------------------------------
# Etapa 2 – Geração do Documento Base
# -------------------------------
st.header("2️⃣ Gerar Rascunho do DFD")
if st.button("Gerar DFD", type="primary"):
    r = st.session_state["respostas"]
    if not r:
        st.warning("⚠️ Preencha as respostas antes de gerar o documento.")
    else:
        base = f"""
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
        # Também colamos eventuais exemplos já inseridos (se existirem de execuções anteriores)
        if st.session_state["example_inserts"]:
            base += "\n\n---\n### 🧩 Exemplos inseridos nesta sessão\n" + "\n\n".join(st.session_state["example_inserts"])

        st.session_state["dfd_text"] = base
        st.session_state["validation_result"] = None
        st.session_state["enhanced_markdown"] = ""
        st.success("✅ Documento base criado com sucesso!")
        with st.expander("👁️ Visualizar rascunho gerado"):
            st.markdown(st.session_state["dfd_text"])

# -------------------------------
# Etapa 3 – Validação Semântica
# -------------------------------
st.header("3️⃣ Validação Semântica e Recomendações")
include_suggestions = st.checkbox("💡 Incluir sugestões construtivas no resultado", value=True)

if st.button("Executar validação"):
    if not st.session_state["dfd_text"]:
        st.warning("⚠️ Gere o documento DFD antes.")
    else:
        client = _load_api_client()
        if client:
            with st.spinner("🔍 Executando análise semântica..."):
                vr = validate_document(st.session_state["dfd_text"], "DFD", client)
                st.session_state["validation_result"] = vr
                enhanced = enhance_markdown(vr.get("guided_markdown", ""), vr, include_suggestions)
                st.session_state["enhanced_markdown"] = enhanced
                st.success("✅ Validação concluída com sucesso!")

# -------------------------------
# Resultados e Exportação (+ EXEMPLOS)
# -------------------------------
vr = st.session_state.get("validation_result")
if vr:
    st.subheader("📊 Resultado da Análise")
    sem_score = vr.get("semantic_score", 0.0)
    st.metric("Score Semântico", f"{sem_score:.1f}%")

    st.markdown("### 📝 Rascunho Orientado")
    md_final = st.session_state["enhanced_markdown"] or vr.get("guided_markdown", "")
    st.markdown(md_final)

    # --- EXEMPLOS PEDAGÓGICOS (NOVO) ---
    st.markdown("### 🧩 Exemplos ilustrativos (não vinculantes)")
    # Mapeia lacunas com base no texto das sugestões que costumam aparecer
    raw_md = md_final.lower()
    lacunas_detectadas = []
    if "lei nº 14.133/2021" not in raw_md:
        lacunas_detectadas.append("Lei 14.133")
    if "especificaç" in raw_md and "incluir" in raw_md or "especificações" in raw_md:
        lacunas_detectadas.append("especificações técnicas")
    if "estimativa de custos" in raw_md or "adicionar estimativa" in raw_md or "custos" in raw_md:
        lacunas_detectadas.append("estimativa de custos")
    if "sustentabilidade" not in raw_md:
        lacunas_detectadas.append("sustentabilidade")

    exemplos = build_example_snippets(lacunas_detectadas) if lacunas_detectadas else {}

    if exemplos:
        for tema, texto in exemplos.items():
            with st.expander(f"Exemplo para: {tema}"):
                st.markdown(texto)
                if st.button(f"Inserir este exemplo no rascunho ({tema})"):
                    # guarda exemplo e recarrega bloco final com exemplo incluido
                    st.session_state["example_inserts"].append(texto + "\n\n[EXEMPLO ILUSTRATIVO – revisar antes de manter no documento]")
                    st.success("Exemplo inserido para reuso. Clique novamente em **Gerar DFD** se quiser ver no rascunho base.")
    else:
        st.caption("Nenhum exemplo sugerido nesta análise.")

    # Exportação (DOCX sempre; PDF se disponível no ambiente)
    buffer, pdf_path = markdown_to_docx(
        md_final,
        "DFD (Rascunho Orientado)",
        vr.get("summary", ""),
    )

    st.download_button(
        "⬇️ Baixar Documento (.docx)",
        data=buffer,
        file_name="DFD_orientado.docx",
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
st.caption("Etapa atual: DFD • Próximas: ETP → TR → Contrato → Fiscalização • Synapse.IA | SAAB | TJSP")
