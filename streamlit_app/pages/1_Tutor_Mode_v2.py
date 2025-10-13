import os
from datetime import datetime

import streamlit as st
import yaml

# ================================
# Synapse Tutor v2 — DFD (POC TJSP)
# Agora com VALIDAÇÃO SEMÂNTICA e
# RASCUNHO ORIENTADO (markdown).
# ================================

# Reuso do engine de validação já existente no repo
# (mantém consistência com a página sinapse_chat_vNext.py)
from validator_engine_vNext import validate_document  # API pública validate_document(...)
from openai import OpenAI  # cliente OpenAI para o engine

# -------------------------------
# Config da página
# -------------------------------
st.set_page_config(
    page_title="Synapse Tutor – Jornada Guiada v2",
    layout="wide",
)

st.title("🧭 Synapse Tutor — Jornada Guiada Interativa (DFD)")
st.markdown("""
O **Synapse Tutor v2** coleta respostas e gera um rascunho textual do **Documento de Formalização da Demanda (DFD)**,
agora com **validação semântica automática** e **rascunho orientado**.
""")

# -------------------------------
# Helpers
# -------------------------------
def _load_api_client():
    """
    Mesmo padrão de obtenção da chave usado em synapse_chat_vNext.py:
    primeiro variável de ambiente, depois Secrets do Streamlit.
    """
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        st.warning("⚠️ Para executar a validação semântica, defina OPENAI_API_KEY (env ou secrets).")
        return None
    return OpenAI(api_key=api_key)

def _load_question_bank():
    try:
        with open(os.path.join("journey", "question_bank.yaml"), "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
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

# -------------------------------
# Carregar banco de perguntas
# -------------------------------
question_bank = _load_question_bank()
dfd_questions = question_bank.get("dfd", {})
total_questions = len(dfd_questions)

st.divider()
st.subheader("🧾 Preencha as respostas para as perguntas abaixo")

answered_count = 0
for key, question_text in dfd_questions.items():
    campo_key = f"resp_{key}"
    resposta = st.text_area(
        question_text,
        value=st.session_state["respostas"].get(campo_key, ""),
        height=80
    )
    if resposta.strip():
        st.session_state["respostas"][campo_key] = resposta
        answered_count += 1

progress = (answered_count / total_questions) if total_questions else 0
st.progress(progress, text=f"Progresso: {answered_count}/{total_questions} respostas")

# -------------------------------
# Geração do DFD
# -------------------------------
st.divider()
st.subheader("📄 Geração do Documento DFD")

colA, colB = st.columns([0.45, 0.55], gap="large")

with colA:
    if st.button("Gerar Documento DFD", type="primary"):
        r = st.session_state["respostas"]
        if not r:
            st.warning("⚠️ Nenhuma resposta preenchida.")
        else:
            dfd_text = f"""
# Documento de Formalização da Demanda (DFD)
**Data:** {datetime.now().strftime('%d/%m/%Y')}  
**Unidade Solicitante:** {r.get('resp_unidade_demandante', 'Não informado')}  
**Responsável pela Solicitação:** {r.get('resp_responsavel', 'Não informado')}

---

## 1️⃣ Descrição do Objeto
{r.get('resp_objeto', 'Não informado')}

---

## 2️⃣ Justificativa da Necessidade
{r.get('resp_justificativa', 'Não informado')}

---

## 3️⃣ Quantidade, Urgência e Riscos
- **Quantidade ou escopo:** {r.get('resp_quantidade_ou_escopo', 'Não informado')}
- **Condição de urgência:** {r.get('resp_condicao_urgencia', 'Não informado')}
- **Riscos se não atendido:** {r.get('resp_riscos', 'Não informado')}

---

## 4️⃣ Alinhamento Institucional
{r.get('resp_alinhamento_planejamento', 'Não informado')}

---

## 5️⃣ Documentos de Suporte
{r.get('resp_documentos_suporte', 'Não informado')}

---

_Gerado automaticamente pelo Synapse Tutor — SAAB/TJSP, versão POC 2025_
""".strip()

            st.session_state["dfd_text"] = dfd_text
            st.success("✅ Documento gerado. Veja a prévia ao lado.")

with colB:
    st.markdown("### 🔎 Prévia do rascunho (MD)")
    if st.session_state["dfd_text"]:
        st.markdown(st.session_state["dfd_text"])
        st.download_button(
            "⬇️ Baixar rascunho (.md)",
            data=st.session_state["dfd_text"].encode("utf-8"),
            file_name=f"DFD_rascunho_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown"
        )
    else:
        st.info("O rascunho será exibido aqui após a geração.")

# -------------------------------
# Validação semântica (engine)
# -------------------------------
st.divider()
st.subheader("✅ Validação e Rascunho Orientado")

col1, col2 = st.columns([0.35, 0.65], gap="large")

with col1:
    run_validation = st.button("Executar validação semântica")
    if run_validation:
        if not st.session_state["dfd_text"]:
            st.warning("⚠️ Gere o documento DFD antes de validar.")
        else:
            client = _load_api_client()
            if client is None:
                st.stop()
            with st.spinner("Executando validação…"):
                try:
                    # Usamos o mesmo contrato da página sinapse_chat_vNext.py (validate_document)
                    # para manter o padrão de retorno e UX.
                    result = validate_document(st.session_state["dfd_text"], "DFD", client)
                    st.session_state["validation_result"] = result
                    st.success("Validação concluída com sucesso!")
                except Exception as e:
                    st.error(f"Falha na validação: {e}")

with col2:
    vr = st.session_state.get("validation_result")
    if vr:
        # KPIs
        c1, c2 = st.columns(2)
        c1.metric("Score Rígido", f"{vr.get('rigid_score', 0):.1f}%")
        c2.metric("Score Semântico", f"{vr.get('semantic_score', 0):.1f}%")

        # Tabelas (render simples)
        st.markdown("#### 🧩 Itens Avaliados (Rígidos)")
        rigid_rows = []
        for it in vr.get("rigid_result", []):
            rigid_rows.append({
                "Critério": it.get("descricao", ""),
                "Obrigatório": "✅" if it.get("obrigatorio") else "—",
                "Presente": "✅" if it.get("presente") else "❌"
            })
        st.table(rigid_rows)

        st.markdown("#### 💡 Itens Avaliados (Semânticos)")
        sem_rows = []
        for it in vr.get("semantic_result", []):
            sem_rows.append({
                "Critério": it.get("descricao", ""),
                "Presente": "✅" if it.get("presente") else "❌",
                "Nota": it.get("adequacao_nota", 0),
                "Justificativa": it.get("justificativa", "")
            })
        st.table(sem_rows)

        st.markdown("#### 📝 Rascunho orientado (markdown)")
        st.markdown(vr.get("guided_markdown", ""))

        st.download_button(
            "⬇️ Baixar rascunho orientado (.md)",
            data=vr.get("guided_markdown", "").encode("utf-8", errors="ignore"),
            file_name=f"{vr.get('guided_doc_title','Rascunho')}_DFD_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown"
        )
    else:
        st.info("Execute a validação para ver scores, tabelas e o rascunho orientado.")

st.divider()
st.caption("Versão POC • Tribunal de Justiça de São Paulo • SAAB • Synapse.IA 2025")
