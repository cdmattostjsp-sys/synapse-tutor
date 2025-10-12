import streamlit as st
import yaml
import json
import os
from datetime import datetime

# ============================================================
# Synapse Tutor v2 - Jornada Guiada Interativa (POC TJSP)
# ============================================================

st.set_page_config(
    page_title="Synapse Tutor – Jornada Guiada v2",
    layout="wide",
)

st.title("🧭 Synapse Tutor — Jornada Guiada Interativa")
st.markdown("""
O **Synapse Tutor v2** é um assistente adaptativo que **coleta respostas do usuário** e gera automaticamente
um rascunho textual do **Documento de Formalização da Demanda (DFD)**, com base nas informações preenchidas.
""")

# ------------------------------------------------------------
# 1. Carregar banco de perguntas (journey/question_bank.yaml)
# ------------------------------------------------------------
try:
    with open(os.path.join("journey", "question_bank.yaml"), "r", encoding="utf-8") as file:
        question_bank = yaml.safe_load(file)
except FileNotFoundError:
    st.error("❌ Arquivo 'question_bank.yaml' não encontrado. Verifique o caminho da pasta journey/.")
    st.stop()

# ------------------------------------------------------------
# 2. Inicializar variáveis de sessão
# ------------------------------------------------------------
if "respostas" not in st.session_state:
    st.session_state["respostas"] = {}

if "etapa" not in st.session_state:
    st.session_state["etapa"] = "DFD"

st.divider()

# ------------------------------------------------------------
# 3. Formulário interativo
# ------------------------------------------------------------
st.subheader("🧾 Preencha as respostas para as perguntas abaixo:")

questions = question_bank.get("dfd", {}).get("questions", [])
total_questions = len(questions)
answered_count = 0

for q in questions:
    question_text = q.get("text", "")
    key = f"resp_{question_text[:40]}"  # chave única curta para sessão
    response = st.text_area(question_text, value=st.session_state["respostas"].get(key, ""), height=80)
    if response.strip():
        st.session_state["respostas"][key] = response
        answered_count += 1

# ------------------------------------------------------------
# 4. Barra de progresso
# ------------------------------------------------------------
progress = (answered_count / total_questions) if total_questions > 0 else 0
st.progress(progress, text=f"Progresso: {answered_count}/{total_questions} respostas")

# ------------------------------------------------------------
# 5. Botão para gerar documento textual
# ------------------------------------------------------------
st.divider()
st.subheader("📄 Geração do Documento DFD")

if st.button("Gerar Documento DFD"):
    respostas = st.session_state["respostas"]

    if not respostas:
        st.warning("⚠️ Nenhuma resposta foi preenchida ainda.")
        st.stop()

    # Montagem do texto em formato institucional
    dfd_text = f"""
# Documento de Formalização da Demanda (DFD)
**Data:** {datetime.now().strftime('%d/%m/%Y')}  
**Unidade Solicitante:** {respostas.get('resp_Qual é a unidade solicitante', 'Não informado')}

---

## 1️⃣ Descrição do Objeto
{respostas.get('resp_O que exatamente precisa ser adquirido ou contratado', 'Não informado')}

---

## 2️⃣ Justificativa da Necessidade
{respostas.get('resp_Por que essa aquisição é necessária agora', 'Não informado')}

---

## 3️⃣ Urgência e Risco
{respostas.get('resp_Há urgência ou prazo limite', 'Não informado')}
{respostas.get('resp_Há riscos identificados caso o pedido não seja atendido', '')}

---

## 4️⃣ Alinhamento Institucional
{respostas.get('resp_Há relação com algum projeto', 'Não informado')}

---

## 5️⃣ Informações Complementares
{respostas.get('resp_Você possui fotos', 'Não informado')}

---

_Gerado automaticamente pelo Synapse Tutor — SAAB/TJSP, versão POC 2025_
"""

    st.success("✅ Documento gerado com sucesso!")
    st.markdown(dfd_text)

    # Exibe também o JSON técnico da jornada
    with st.expander("📘 Estrutura técnica (JSON consolidado)"):
        st.json(respostas)

st.divider()
st.caption("Versão POC • Tribunal de Justiça de São Paulo • SAAB • Synapse.IA 2025")
