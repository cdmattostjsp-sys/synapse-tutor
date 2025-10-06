# -*- coding: utf-8 -*-
# =============================================================================
# Synapse.IA – Streamlit App
# Versão POC 1.1 – Revisão de desempenho e lógica de validação (05/10/2025)
#
# Este arquivo mantém 100% do layout aprovado e integra:
# - Execução do agente
# - Exibição dos scores e fichas (rígida e semântica)
# - Documento Orientado (Markdown) com lacunas e marcadores
# - Controle de estado para evitar renderização duplicada
# =============================================================================

import streamlit as st
from openai import OpenAI
import base64, os, io

from knowledge.validators.validator_engine import validate_document

# ===============================
# CONFIG DA PÁGINA
# ===============================
st.set_page_config(page_title="Synapse.IA", page_icon="🧠", layout="wide")

# ===============================
# UTILS
# ===============================
def img_to_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def get_openai_client():
    """
    Recupera a API Key do Streamlit Secrets (preferencial) ou do ambiente.
    Mantém compatibilidade com o motor de análise profunda no validator_engine.
    """
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("🔴 OPENAI_API_KEY ausente. Cadastre em Settings → Secrets (ou defina variável de ambiente).")
        return None
    return OpenAI(api_key=api_key)

def extract_text_from_uploads(files):
    """
    Extrai texto básico de arquivos comuns (txt, pdf, docx). Para planilhas/CSV,
    a POC atual mantém a abordagem mínima (sem parsing tabular complexo).
    """
    if not files:
        return ""
    texts = []
    for f in files:
        name = (f.name or "").lower()
        data = f.read()
        try:
            if name.endswith(".txt"):
                texts.append(data.decode("utf-8", errors="ignore"))
            elif name.endswith(".pdf"):
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(io.BytesIO(data))
                    texts.append("\n".join([(p.extract_text() or "") for p in reader.pages]))
                except Exception:
                    # Fallback leve
                    texts.append("")
            elif name.endswith(".docx"):
                try:
                    import docx
                    doc = docx.Document(io.BytesIO(data))
                    texts.append("\n".join([p.text for p in doc.paragraphs]))
                except Exception:
                    texts.append("")
            else:
                # Fallback: tenta decodificar como texto
                texts.append(data.decode("utf-8", errors="ignore"))
        except Exception:
            pass
    return "\n\n".join(texts).strip()

# ===============================
# ASSETS (LOGO)
# ===============================
LOGO_PATH = "logo_synapse.png"
logo_b64 = ""
try:
    logo_b64 = img_to_b64(LOGO_PATH)
except Exception:
    logo_b64 = ""

# ===============================
# CSS – layout aprovado (inalterado)
# ===============================
st.markdown(
    """
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
    .badge { display:inline-block;padding:6px 10px;border-radius:8px;margin-right:8px;
             font-weight:700;color:#fff; }
    .badge-rigid { background:#0ea5e9; }
    .badge-sem { background:#22c55e; }
    table { font-size: 0.94rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===============================
# BRANDING BAR (inalterado)
# ===============================
st.markdown(
    f"""
    <div class="branding-bar">
        {'<img src="data:image/png;base64,' + logo_b64 + '" alt="Logo" width="66" style="border-radius:6px;">' if logo_b64 else ''}
        <div style="display:flex;flex-direction:column;">
            <h1 class="branding-title">Synapse.IA</h1>
            <p class="branding-subtitle">Tribunal de Justiça de São Paulo</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ===============================
# SEÇÃO: INSUMOS
# ===============================
st.markdown(
    """
    <div class="section-title"><div style="font-size:1.6rem;">📥</div>Insumos Manuais</div>
    <div class="section-subtext">Descreva o objeto, justificativa, requisitos, prazos, critérios etc.</div>
    """,
    unsafe_allow_html=True,
)
insumos = st.text_area("", height=180)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ===============================
# SEÇÃO: UPLOAD
# ===============================
st.markdown(
    """
    <div class="section-title"><div style="font-size:1.6rem;">📂</div>Upload de Documento (opcional)</div>
    <div class="section-subtext">Envie PDF, DOCX, XLSX ou CSV (ex.: ETP, TR, Contrato, Obras etc.)</div>
    """,
    unsafe_allow_html=True,
)
uploads = st.file_uploader(
    "Arraste ou selecione arquivos",
    type=["pdf","docx","xlsx","csv","txt"],
    accept_multiple_files=True,
)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ===============================
# SEÇÃO: AGENTE
# ===============================
st.markdown(
    f"""
    <div class="section-title">
        {'<img src="data:image/png;base64,' + logo_b64 + '" width="32" style="transform: translateY(2px);">' if logo_b64 else '<div style="font-size:1.6rem;">🧠</div>'}
        Selecionar Agente
    </div>
    """,
    unsafe_allow_html=True,
)
agente = st.selectbox(
    "Escolha o agente:",
    ["ETP","DFD","TR","CONTRATO","EDITAL","PESQUISA_PRECOS","FISCALIZACAO","OBRAS","MAPA_RISCOS","PCA"],
    index=0
)
validar_semantica = st.checkbox("Executar validação semântica", value=True)

# ===============================
# CONTROLE DE ESTADO (evita duplicidade)
# ===============================
if "result_token" not in st.session_state:
    st.session_state.result_token = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ===============================
# EXECUÇÃO
# ===============================
run = st.button("Executar Agente")

if run:
    import uuid
    st.session_state.result_token = uuid.uuid4().hex

    if not insumos and not uploads:
        st.warning("⚠️ Insira texto ou anexe ao menos um arquivo.")
    else:
        texto = (insumos or "").strip()
        extra = extract_text_from_uploads(uploads)
        if extra:
            texto = (texto + "\n\n" + extra).strip()

        client = get_openai_client()
        if client is None:
            st.stop()

        with st.spinner(f"Executando validação do artefato {agente}..."):
            try:
                # A engine aplica análise profunda no semântico; layout permanece igual.
                result = validate_document(texto, agente, client)
                st.session_state.last_result = {
                    "token": st.session_state.result_token,
                    "agente": agente,
                    "texto": texto,
                    "data": result,
                }
            except Exception as e:
                st.session_state.last_result = {
                    "token": st.session_state.result_token,
                    "agente": agente,
                    "texto": texto,
                    "data": {"error": str(e)},
                }

# ===============================
# RENDERIZAÇÃO (uma vez por execução)
# ===============================
if st.session_state.last_result and st.session_state.last_result.get("token") == st.session_state.result_token:
    payload = st.session_state.last_result.get("data", {})
    if "error" in payload:
        st.error(f"❌ Erro ao processar o agente {st.session_state.last_result.get('agente')}: {payload['error']}")
    else:
        st.success(f"✅ Agente **{st.session_state.last_result.get('agente')}** executado com sucesso!")
        st.markdown("### 🧾 Resultado da Análise")

        rigid_score = float(payload.get("rigid_score", 0) or 0.0)
        semantic_score = float(payload.get("semantic_score", 0) or 0.0)

        st.markdown(
            f"""
            <div>
              <span class="badge badge-rigid">Score Rígido: {rigid_score:.1f}%</span>
              <span class="badge badge-sem">Score Semântico: {semantic_score:.1f}%</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ----- Tabela Rígida -----
        rigid = payload.get("rigid_result", []) or []
        st.markdown("#### 🧩 Itens Avaliados (Rígidos)")
        if rigid:
            rigid_rows = [
                {
                    "Critério": r.get("descricao", ""),
                    "Obrigatório": "✅" if r.get("obrigatorio") else "—",
                    "Presente": "✅" if r.get("presente") else "❌",
                } for r in rigid
            ]
            st.table(rigid_rows)
        else:
            st.info("Nenhum item rígido retornado.")

        # ----- Tabela Semântica -----
        sem = payload.get("semantic_result", []) or []
        st.markdown("#### 💡 Itens Avaliados (Semânticos)")
        if sem:
            sem_rows = [
                {
                    "Critério": s.get("descricao", ""),
                    "Presente": "✅" if s.get("presente") else "❌",
                    "Nota": s.get("adequacao_nota", 0),
                    "Justificativa": s.get("justificativa", ""),
                } for s in sem
            ]
            st.table(sem_rows)
        else:
            st.info("Nenhum item semântico retornado.")

        # ----- Documento orientado -----
        improved_doc = payload.get("improved_document", "") or ""
        st.markdown("### 📄 Documento Orientado (com lacunas)")
        if improved_doc.strip():
            st.code(improved_doc, language="markdown")

            # Download como .md (compatível, sem dependência extra)
            md_bytes = improved_doc.encode("utf-8")
            st.download_button(
                label="⬇️ Baixar rascunho (.md)",
                data=md_bytes,
                file_name=f"rascunho_{st.session_state.last_result.get('agente','doc')}.md",
                mime="text/markdown"
            )
        else:
            st.info("Nenhum rascunho orientado foi gerado.")
