# =========================================
# utils/formatter_docx.py – v3.6-safe
# =========================================
# Correções:
# - Garante existência de pastas exports/rascunhos e exports/logs
# - Corrige FileNotFoundError (get_next_rascunho_number)
# - Numeração incremental segura (DFD_001, DFD_002…)
# - Compatível com formatter_docx.py v3.5.1 e Tutor v2.5
# - Adiciona logging básico de geração

import os
import io
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

try:
    import pypandoc
except ImportError:
    pypandoc = None


# -------------------------------
# Diretórios principais
# -------------------------------
EXPORT_BASE = os.path.join("exports")
RASC_DIR = os.path.join(EXPORT_BASE, "rascunhos")
LOG_DIR = os.path.join(EXPORT_BASE, "logs")

os.makedirs(RASC_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


# -------------------------------
# Funções auxiliares
# -------------------------------
def get_next_rascunho_number(rasc_dir: str) -> str:
    """
    Retorna o próximo número de rascunho (ex: '001').
    Cria o diretório caso não exista.
    """
    os.makedirs(rasc_dir, exist_ok=True)
    existing = [f for f in os.listdir(rasc_dir) if f.startswith("DFD_") and f.endswith(".docx")]
    if not existing:
        return "001"
    try:
        last_num = max(int(f.split("_")[1].split(".")[0]) for f in existing if "_" in f)
        return f"{last_num + 1:03d}"
    except Exception:
        return "001"


def log_generation(file_name: str, summary: str):
    """
    Registra log simples de geração de documento.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, "tutor_logs.txt")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {file_name} – {summary[:180]}\n")


# -------------------------------
# Função principal
# -------------------------------
def markdown_to_docx(markdown_text: str, titulo: str = "Documento", summary: str = ""):
    """
    Converte markdown para Word (.docx) e opcionalmente para PDF (se pypandoc disponível).
    Retorna um buffer (.docx) e o caminho do PDF (ou None).
    """
    numero = get_next_rascunho_number(RASC_DIR)
    base_name = f"DFD_{numero}_{datetime.now():%Y%m%d_%H%M%S}"
    docx_path = os.path.join(RASC_DIR, f"{base_name}.docx")
    pdf_path = os.path.join(RASC_DIR, f"{base_name}.pdf")

    # Criação do documento Word
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # Cabeçalho
    title = doc.add_paragraph(titulo)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.style = doc.styles["Heading 1"]

    # Corpo principal
    for line in markdown_text.split("\n"):
        p = doc.add_paragraph(line.strip())
        p.paragraph_format.space_after = Pt(6)

    # Rodapé
    doc.add_paragraph("")
    doc.add_paragraph("_Gerado automaticamente pelo Synapse Tutor – SAAB/TJSP_")

    # Salvar DOCX
    doc.save(docx_path)
    log_generation(base_name, summary or "Documento gerado sem resumo.")

    # Exportação via buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    # Tentativa de gerar PDF (opcional)
    if pypandoc:
        try:
            pypandoc.convert_text(markdown_text, "pdf", format="md", outputfile=pdf_path)
        except Exception:
            pdf_path = None
    else:
        pdf_path = None

    return buffer, pdf_path
