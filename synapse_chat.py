import streamlit as st
from PIL import Image
import base64, os, io
from openai import OpenAI
from knowledge.validators.validator_engine import validate_document

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(page_title="Synapse.IA", page_icon="🧠", layout="wide")

# ===============================
# FUNÇÕES AUXILIARES
# ===============================
def img_to_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

LOGO_PATH = "logo_synapse.png"
logo_b64 = ""
try:
    logo_b64 = img_to_b64(LOGO_PATH)
except:
    logo_b64 = ""

# ===============================
# CSS - mantém layout aprovado
# ===============================
st.markdown("""
<style>
.block-container {
    padding-top: 0.9rem;
    padding-bottom: 0rem;
    padding-left: 2rem;
    padding-right: 2rem;
}
.branding-bar {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 0 12px 0;
    background: linear-gradient(180deg, #10151e 0%, #0E1117 100%);
    border-bottom: 1px solid #303030; margin-bottom: 10px;
}
.branding-title {font-size: 2rem; font-weight: 800; color: #fff; margin: 0;}
.branding-subtitle {font-size: 1rem; color: #bdbdbd; margin: 0;}
.section-title {
    display: flex; align-items: center; gap: 10px;
    font-size: 1.7rem; font-weight: 700; color: #fff;
    margin-top: 1.6rem; margin-bottom: 0.35rem;
    text-shadow: 0 0 8px rgba(0,150,255,0.22);
}
.section-subtext {color:#aaa;font-size:0.95rem;margin-top:-4px;margin-bottom:10px;}
.section-divider {height:1px;width:100%;background:#1d4ed8;opacity:0.35;margin:12px 0;}
textarea, .stTextArea textarea {
    background-color:#1E1E1E;color:#fff;border-radius:8px;
    border:1px solid #444;min-height:150px;
}
.stFileUploader {background-color:#2C2C2C;border-radius:10px;padding:12px;}
.stButton>button {
    background-color:#007BFF;color:#fff;border:none;border-radius:8px;
    padding:0.6rem 1.2rem;font-weight:600;
}
.stButton>button:hover {background-color:#3399FF;}
</style>
""", unsafe_allow_html=True)

# ===============================
# CABEÇALHO
# ===============================
st.markdown(f"""
<div class="branding-bar">
    {'<img src="data:image/png;base64,' + logo_b64 + '" alt="Logo Synapse.IA" width="66" style="border-radius:6px;">' if logo_b64 else ''}
    <div style="display:flex;flex-direction:column;">
        <h1 class="branding-title">Synapse.IA</h1>
        <p class="branding-subtitle">Tribunal de Justiça de São Paulo</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ===============================
# INSUMOS MANUAIS
# ===============================
st.markdown("""
<div class="section-title"><div style="font-size:1.6rem;">📥</div>Insumos Manuais</div>
<div class="section-subtext">Descreva o objeto, justificativa, requisitos, prazos, critérios etc.</div>
""", unsafe_allow_html=True)
insumos = st.text_area("", height=180)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ===============================
# UPLOAD DE DOCUMENTOS
# ===============================
st.markdown("""
<div class="section-title"><div style="font-size:1.6rem;">📂</div>Upload de Documento (opcional)</div>
<div class="section-subtext">Envie PDF, DOCX, XLSX ou CSV (ex.: ETP, TR, Contrato, Obras etc.)</div>
""", unsafe_allow_html=True)
uploaded_files = st.file_uploader("Arraste ou selecione arquivos", type=["pdf","docx","xlsx","csv","txt"], accept_multiple_files=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ===============================
# SELECIONAR AGENTE
# ===============================
st.markdown(f"""
<div class="section-title">
    {'<img src="data:image/png;base64,' + logo_b64 + '" width="32" style="transform: translateY(2px);">' if logo_b64 else '<div style="font-size:1.6rem;">🧠</div>'}
    Selecionar Agente
</div>
""", unsafe_allow_html=True)
agente = st.selectbox("Escolha o agente:", ["ETP","DFD","TR","CONTRATO","EDITAL","PESQUISA_PRECOS","FISCALIZACAO","OBRAS","MAPA_RISCOS","PCA"])
validar_semantica = st.checkbox("Executar validação semântica", value=True)

# ===============================
# FUNÇÕES AUXILIARES
# ===============================
def extract_text_from_uploads(files):
    if not files: return ""
    texts = []
    for f in files:
        name = (f.name or "").lower()
        data = f.read()
        try:
            if name.endswith(".txt"):
                texts.append(data.decode("utf-8", errors="ignore"))
            elif name.endswith(".pdf"):
                from PyPDF2 import PdfReader
                reader = PdfReader(io.BytesIO(data))
                texts.append("\n".join([p.extract_text() or "" for p in reader.pages]))
            elif name.endswith(".docx"):
                import docx
                doc = docx.Document(io.BytesIO(data))
                texts.append("\n".join([p.text for p in doc.paragraphs]))
        except Exception:
            try: texts.append(data.decode("utf-8", errors="ignore"))
            except: pass
    return "\n\n".join(texts).strip()

def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("🔴 OPENAI_API_KEY ausente. Configure em Settings → Secrets.")
        return None
    return OpenAI(api_key=api_key)

# ===============================
# BOTÃO – EXECUTAR
# ===============================
if st.button("Executar Agente"):
    if not insumos and not uploaded_files:
        st.warning("⚠️ Insira texto ou envie um arquivo.")
    else:
        texto = (insumos or "") + "\n\n" + extract_text_from_uploads(uploaded_files)
        client = get_openai_client()
        if not client: st.stop()

        with st.spinner(f"Executando validação do artefato {agente}..."):
            try:
                resultado = validate_document(texto.strip(), agente, client)
                if not resultado:
                    st.error("O validador não retornou resultado.")
                else:
                    st.success(f"✅ Agente **{agente}** executado com sucesso!")
                    st.markdown("### 🧾 Resultado da Análise")

                    # === Renderiza fichas ===
                    rigid = resultado.get("rigid_result", [])
                    sem = resultado.get("semantic_result", [])
                    rigid_score = resultado.get("rigid_score", 0)
                    sem_score = resultado.get("semantic_score", 0)

                    st.markdown(f"**Score Rígido:** {rigid_score:.1f}% | **Score Semântico:** {sem_score:.1f}%")

                    # Tabela 1
                    st.markdown("#### 🧩 Itens Avaliados (Rígidos)")
                    st.table([{ "Critério": r["descricao"], "Obrigatório": "✅" if r["obrigatorio"] else "—", "Presente": "✅" if r["presente"] else "❌"} for r in rigid])

                    # Tabela 2
                    st.markdown("#### 💡 Itens Avaliados (Semânticos)")
                    st.table([{ "Critério": s["descricao"], "Presente": "✅" if s["presente"] else "❌", "Nota": s["adequacao_nota"], "Justificativa": s["justificativa"]} for s in sem])

            except Exception as e:
                st.error(f"❌ Erro: {e}")
