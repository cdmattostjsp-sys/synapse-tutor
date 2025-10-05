import streamlit as st
from openai import OpenAI
import base64
import os

# ==========================================================
# CONFIGURAÇÕES GERAIS
# ==========================================================
st.set_page_config(
    page_title="Synapse.IA - TJSP",
    page_icon="🧠",
    layout="wide"
)

# Inicializa cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================
def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        return base64.b64encode(f.read()).decode()

def branding_bar():
    LOGO_PATH = "logo_synapse.png"
    if os.path.exists(LOGO_PATH):
        logo_base64 = get_base64_of_bin_file(LOGO_PATH)
        st.markdown(
            f"""
            <div style="
                display: flex;
                align-items: center;
                background-color: #f8f9fa;
                padding: 10px 25px;
                border-radius: 12px;
                margin-bottom: 20px;
            ">
                <img src="data:image/png;base64,{logo_base64}" style="height:60px; margin-right:15px;">
                <div style="line-height:1;">
                    <h1 style="margin:0; font-size:32px; color:#2a2a2a;">Synapse.IA</h1>
                    <h3 style="margin:0; font-size:18px; color:#5a5a5a;">Tribunal de Justiça de São Paulo</h3>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("⚠️ Logo não encontrado. Verifique se o arquivo 'logo_synapse.png' está na raiz do projeto.")

# ==========================================================
# INTERFACE PRINCIPAL
# ==========================================================
branding_bar()

st.markdown("## 📨 Insumos Manuais")
insumos = st.text_area(
    "Descreva aqui o objeto, justificativa e requisitos do documento",
    placeholder="Exemplo: Aquisição de 50 computadores desktop padrão corporativo...",
    height=180
)

st.markdown("## 📂 Upload de Documento (opcional)")
uploaded_file = st.file_uploader("Carregue um documento (PDF, DOCX ou TXT)", type=["pdf", "docx", "txt"])

st.markdown("## 🧠 Selecionar Agente")
agente = st.selectbox(
    "Escolha o tipo de artefato que deseja gerar:",
    ["ETP", "TR", "DFD", "PESQUISA_PRECOS", "CONTRATO", "EDITAL", "MAPA_RISCOS", "PCA", "FISCALIZACAO", "OBRAS"]
)

# ==========================================================
# EXECUÇÃO DO AGENTE
# ==========================================================
if st.button("🚀 Executar Agente"):
    if not insumos and not uploaded_file:
        st.warning("⚠️ Insira algum texto ou faça upload de um documento para análise.")
    else:
        with st.spinner(f"Executando agente {agente}... isso pode levar alguns segundos."):
            try:
                # Carrega texto base
                texto_base = insumos

                # Caso tenha upload de arquivo
                if uploaded_file:
                    file_data = uploaded_file.read().decode("utf-8", errors="ignore")
                    texto_base += "\n\n" + file_data

                # ==================================================
                # ENVIA TEXTO PARA OPENAI GPT-4o
                # ==================================================
                prompt = f"""
                Você é um agente institucional do Tribunal de Justiça de São Paulo chamado Synapse.IA.
                Sua função é analisar e gerar **{agente}** de forma técnica e completa,
                seguindo a Lei nº 14.133/2021 e demais normas aplicáveis.
                
                Abaixo estão os insumos fornecidos pelo usuário:
                ----------------------
                {texto_base}
                ----------------------

                Gere um texto estruturado e completo do artefato solicitado ({agente}),
                com linguagem formal e detalhada, mantendo clareza e coerência institucional.
                """

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Você é um especialista em contratações públicas do TJSP."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=2200
                )

                resultado = response.choices[0].message.content
                st.success(f"✅ Agente **{agente}** executado com sucesso!")
                st.markdown("### 🧾 Resultado da Análise")
                st.markdown(resultado)

            except Exception as e:
                st.error(f"❌ Erro ao processar o agente: {e}")
