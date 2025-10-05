import streamlit as st
from openai import OpenAI
import base64
import os
from knowledge.validators.validator_engine import validate_document

# ===================== CONFIGURAÇÃO DO APLICATIVO =====================

st.set_page_config(
    page_title="Synapse.IA - Tribunal de Justiça de São Paulo",
    page_icon="⚖️",
    layout="wide"
)

LOGO_PATH = "logo_synapse.png"

def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def branding_bar():
    """Cabeçalho institucional com logo e identidade visual"""
    logo_base64 = get_base64_of_bin_file(LOGO_PATH)
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;background-color:#f8f8f8;
                    padding:8px 18px;border-radius:6px;margin-bottom:10px;">
            <img src="data:image/png;base64,{logo_base64}" width="55" style="margin-right:15px;">
            <div style="display:flex;flex-direction:column;line-height:1.1;">
                <h2 style="margin:0;font-size:28px;color:#003366;">Synapse.IA</h2>
                <h4 style="margin:0;font-weight:normal;font-size:17px;color:#555;">
                    Tribunal de Justiça de São Paulo
                </h4>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

branding_bar()

# ===================== INTERFACE PRINCIPAL =====================

st.markdown("### 📥 Insumos Manuais")
texto_usuario = st.text_area(
    "Insira o texto do artefato (ex: ETP, TR, Contrato, etc.)",
    height=300,
    placeholder="Cole aqui o texto completo para análise..."
)

st.markdown("### 🗂️ Upload de Documento (opcional)")
uploaded_file = st.file_uploader("Selecione um arquivo .txt, .docx ou .pdf", type=["txt", "docx", "pdf"])

st.markdown("### 🧠 Selecionar Agente")
opcao_agente = st.selectbox(
    "Escolha o agente para análise",
    ["ETP", "TR", "EDITAL", "CONTRATO", "PESQUISA_PRECOS", "DFD", "PCA", "FISCALIZACAO", "OBRAS", "MAPA_RISCOS"]
)

executar = st.button("🚀 Executar Agente")

# ===================== LÓGICA DE EXECUÇÃO =====================

if executar:
    st.info(f"Agente {opcao_agente} executado com sucesso. Gerando análise, aguarde...")

    # Obter texto final (insumo manual ou arquivo enviado)
    texto_final = texto_usuario
    if uploaded_file:
        texto_final = uploaded_file.read().decode("utf-8", errors="ignore")

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resultado = validate_document(texto_final, opcao_agente, client)

        # ===================== EXIBIÇÃO FORMATADA DO RESULTADO =====================
        st.markdown("## 🧾 Resultado da Análise")

        rigid_score = resultado.get("rigid_score", 0)
        semantic_score = resultado.get("semantic_score", 0)

        st.markdown(
            f"""
            <div style="background-color:#eef5ff;padding:10px 20px;border-radius:8px;
                        border-left:6px solid #003366;margin-bottom:20px;">
                <h4 style="margin:0;">🔍 Resumo Geral</h4>
                <p style="margin:5px 0;">Score Rígido: <b>{rigid_score:.1f}</b></p>
                <p style="margin:0;">Score Semântico: <b>{semantic_score:.1f}</b></p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # --- Tabela de Itens Rígidos ---
        st.markdown("### 🧱 Itens Avaliados (Rígidos)")
        rigid_result = resultado.get("rigid_result", [])
        if rigid_result:
            rigid_data = [
                {
                    "Critério": item["descricao"],
                    "Obrigatório": "✅" if item["obrigatorio"] else "—",
                    "Presente": "✔️" if item["presente"] else "❌",
                }
                for item in rigid_result
            ]
            st.table(rigid_data)
        else:
            st.warning("Nenhum item rígido encontrado.")

        # --- Tabela de Itens Semânticos ---
        st.markdown("### 💡 Itens Avaliados (Semânticos)")
        semantic_result = resultado.get("semantic_result", [])
        if semantic_result:
            semantic_data = [
                {
                    "Critério": item["descricao"],
                    "Presente": "✔️" if item["presente"] else "❌",
                    "Nota": f"{item.get('adequacao_nota', 0):.1f}",
                    "Justificativa": item.get("justificativa", ""),
                }
                for item in semantic_result
            ]
            st.dataframe(semantic_data, use_container_width=True)
        else:
            st.warning("Nenhum item semântico encontrado.")

        st.success("✅ Análise concluída com sucesso!")

    except Exception as e:
        st.error("Ocorreu um erro ao executar o agente.")
        st.exception(e)
