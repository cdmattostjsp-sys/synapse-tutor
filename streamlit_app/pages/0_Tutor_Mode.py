"""
0_Tutor_Mode.py
--------------------------------
Interface do modo Tutor Adaptativo do Synapse.IA
Permite que o usuário descreva sua necessidade em linguagem natural
e receba orientações dinâmicas para construção dos artefatos (DFD, ETP, TR).
"""

import streamlit as st
import json
import os
import sys

# Adicionar o caminho base para importar os agentes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.guide_agent import generate_guidance

# ---------------------------------------------
# CONFIGURAÇÃO INICIAL DO APP
# ---------------------------------------------
st.set_page_config(
    page_title="Synapse Tutor — Jornada Guiada",
    page_icon="🧭",
    layout="wide"
)

st.title("🧭 Synapse Tutor — Jornada Guiada")
st.markdown("""
O **Synapse Tutor** é um assistente adaptativo que orienta o usuário
na elaboração de documentos técnicos da fase interna da licitação
(DFD → ETP → TR).  
Descreva abaixo sua necessidade e veja as perguntas que o sistema
gerará para ajudar na construção do artefato adequado.
""")

# ---------------------------------------------
# ÁREA DE ENTRADA DO USUÁRIO
# ---------------------------------------------
user_input = st.text_area(
    "✍️ Descreva sua necessidade ou problema:",
    placeholder="Exemplo: precisamos substituir mesas de audiência danificadas no Fórum de Sorocaba...",
    height=180
)

col1, col2 = st.columns([1, 1])

with col1:
    generate_button = st.button("🔍 Detectar etapa e gerar perguntas")

with col2:
    st.markdown("")

# ---------------------------------------------
# AÇÃO PRINCIPAL — EXECUÇÃO DO AGENTE
# ---------------------------------------------
if generate_button and user_input.strip():
    with st.spinner("Analisando sua descrição e preparando orientações..."):
        guidance = generate_guidance(user_input)

    if "error" in guidance:
        st.error(f"❌ Erro: {guidance['error']}")
    else:
        # ---------------------------------------------
        # EXIBIÇÃO DOS RESULTADOS
        # ---------------------------------------------
        st.success(f"✅ Etapa detectada: **{guidance['etapa_atual'].upper()}**")
        st.write(f"**Próximo passo:** {guidance['proximo_passo']}")
        st.info(f"🧩 Documento em foco: **{guidance['documento_em_foco']}**")
        st.markdown(f"📘 {guidance['descricao_etapa']}")

        # ---------------------------------------------
        # PROGRESSO
        # ---------------------------------------------
        campos = guidance.get("campos_minimos", [])
        total_campos = len(campos)
        progresso = 0.0 if total_campos == 0 else (1 / total_campos)
        st.progress(progresso, text="Progresso inicial da jornada")

        # ---------------------------------------------
        # PERGUNTAS RECOMENDADAS
        # ---------------------------------------------
        st.subheader("🧠 Perguntas recomendadas")
        perguntas = guidance.get("perguntas_recomendadas", {})

        if perguntas:
            for chave, pergunta in perguntas.items():
                st.markdown(f"- **{pergunta}**")
        else:
            st.warning("Nenhuma pergunta encontrada para esta etapa.")

        # ---------------------------------------------
        # VISUALIZAÇÃO TÉCNICA (debug opcional)
        # ---------------------------------------------
        with st.expander("🧩 Ver estrutura técnica da resposta"):
            st.json(guidance)

else:
    st.info("💡 Digite uma necessidade e clique em **Detectar etapa e gerar perguntas** para iniciar a jornada.")

# ---------------------------------------------
# RODAPÉ
# ---------------------------------------------
st.markdown("---")
st.caption("Versão POC • Tribunal de Justiça de São Paulo • SAAB • Synapse.IA 2025")
# placeholder for 0_Tutor_Mode.py

