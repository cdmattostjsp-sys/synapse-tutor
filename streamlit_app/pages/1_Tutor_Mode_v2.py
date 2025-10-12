import streamlit as st
import yaml
import json
import os
from datetime import datetime

# ============================================================
# Synapse Tutor v2 - Jornada Guiada Interativa (POC TJSP)
# Compatível com estrutura YAML em chave-valor (DFD, ETP, TR)
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
# 3. Formulário interativo - compatível com YAML chave-valor
# ------------------------------------------------------------
st.subheader("🧾 Preencha as respostas para as perguntas abaixo:")

dfd_questions = question_bank.get("dfd", {})
total_questions = len(dfd_questions)
answered_count = 0

for key, question_text in dfd_questions.items():
    campo_key = f"resp_{key}"
    resposta = st.text_area(question_text, value=st.session_state["respostas"].get(campo_key, ""), height=80)
    if resposta.strip():
        st.session_state["respostas"][campo_key] = resposta
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

    # Montagem do texto em formato institucional, usando chaves do YAML
    dfd_text = f"""
# Documento de Formalização da Demanda (DFD)
**Data:** {datetime.now().strftime('%d/%m/%Y')}  
**Unidade Solicitante:** {respostas.get('resp_unidade_demandante', 'Não informado')}  
**Responsável pela Solicitação:** {respostas.get('resp_responsavel', 'Não informado')}

---

## 1️⃣ Descrição do Objeto
{respostas.get('resp_objeto', 'Não informado')}

---

## 2️⃣ Justificativa da Necessidade
{respostas.get('resp_justificativa', 'Não informado')}

---

## 3️⃣ Quantidade, Urgência e Riscos
- **Quantidade ou escopo:** {respostas.get('resp_quantidade_ou_escopo', 'Não informado')}
- **Condição de urgência:** {respostas.get('resp_condicao_urgencia', 'Não informado')}
- **Riscos se não atendido:** {respostas.get('resp_riscos', 'Não informado')}

---

## 4️⃣ Alinhamento Institucional
{respostas.get('resp_alinhamento_planejamento', 'Não informado')}

---

## 5️⃣ Documentos de Suporte
{respostas.get('resp_documentos_suporte', 'Não informado')}

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
