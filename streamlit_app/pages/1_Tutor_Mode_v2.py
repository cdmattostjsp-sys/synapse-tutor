import sys
import os

# =========================================
# Ajuste de PATH para permitir imports da raiz do projeto
# =========================================
# Detecta o caminho raiz do projeto (duas pastas acima)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Agora os imports do projeto funcionam normalmente
from datetime import datetime
import streamlit as st
import yaml
from openai import OpenAI

from validator_engine_vNext import validate_document  # ✅ Agora acessível
from utils.formatter_docx import markdown_to_docx


# -------------------------------
# Configuração da página
# -------------------------------
st.set_page_config(
    page_title="Synapse Tutor – Jornada Guiada v2",
    layout="wide",
)

st.title("🧭 Synapse Tutor — Jornada Guiada Interativa (DFD)")
st.markdown("""
O **Synapse Tutor v2** coleta respostas e gera um rascunho textual do **Documento de Formalização da Demanda (DFD)**,
com **validação semântica automática** e **exportação institucional em .docx**.
""")

# -------------------------------
# Funções auxiliares
# -------------------------------
def _load_api_client():
    """
    Obtém a chave da API (usando o mesmo padrão de synapse_chat_vNext.py)
    """
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        st.warning("⚠️ Para executar a validação semântica, defina OPENAI_API_KEY (env ou secrets).")
        return None
    return OpenAI(api_key=api_key)


def _load_question_bank():
    """
    Carrega o arquivo journey/question_bank.yaml
    """
    try:
        with open(os.path.join("journey", "question_bank.yaml"), "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        st.error("❌ Arquivo 'journey/question_bank.yaml' não encontrado.")
        st.stop()


# -------------------------------
# Estado da sessão
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
                    result = validate_document(st.session_state["dfd_text"], "DFD", client)
                    st.session_state["validation_result"] = result
                    st.success("Validação concluída com sucesso!")
                except Exception as e:
                    st.error(f"Falha na validação: {e}")

with col2:
    vr = st.session_state.get("validation_result")
    if vr:
        # Métricas principais
        c1, c2 = st.columns(2)
        c1.metric("Score Rígido", f"{vr.get('rigid_score', 0):.1f}%")
        c2.metric("Score Semântico", f"{vr.get('semantic_score', 0):.1f}%")

        # Itens avaliados (rígidos)
        st.markdown("#### 🧩 Itens Avaliados (Rígidos)")
        rigid_rows = []
        for it in vr.get("rigid_result", []):
            rigid_rows.append({
                "Critério": it.get("descricao", ""),
                "Obrigatório": "✅" if it.get("obrigatorio") else "—",
                "Presente": "✅" if it.get("presente") else "❌"
            })
        st.table(rigid_rows)

        # Itens avaliados (semânticos)
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

        # Rascunho orientado
        st.markdown("#### 📝 Rascunho orientado (markdown)")
        st.markdown(vr.get("guided_markdown", ""))

        # Botão de download em Markdown
        st.download_button(
            "⬇️ Baixar rascunho orientado (.md)",
            data=vr.get("guided_markdown", "").encode("utf-8", errors="ignore"),
            file_name=f"{vr.get('guided_doc_title','Rascunho')}_DFD_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown"
        )

        # =========================================
        # Novo botão: exportar como Word (.docx)
        # =========================================
        try:
            buffer = markdown_to_docx(
                vr.get("guided_markdown", ""),
                title="Documento de Formalização da Demanda – DFD (Rascunho Orientado)",
                meta={
                    "Score Rígido": f"{vr.get('rigid_score', 0):.1f}%",
                    "Score Semântico": f"{vr.get('semantic_score', 0):.1f}%",
                    "Data": datetime.now().strftime('%d/%m/%Y %H:%M')
                }
            )

            st.download_button(
                "⬇️ Baixar como .docx",
                data=buffer,
                file_name=f"DFD_orientado_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        except Exception as e:
            st.error(f"Erro ao gerar o arquivo DOCX: {e}")

    else:
        st.info("Execute a validação para ver scores, tabelas e o rascunho orientado.")

st.divider()
st.caption("Versão POC • Tribunal de Justiça de São Paulo • SAAB • Synapse.IA 2025")
