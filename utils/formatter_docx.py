"""
formatter_docx.py
-----------------------------------
Conversor de texto Markdown → DOCX
para o Synapse Tutor v2 (TJSP – SAAB).
Compatível com o padrão institucional.

Dependências: python-docx, markdown, beautifulsoup4
pip install python-docx markdown beautifulsoup4
"""

import io
from datetime import datetime
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import markdown
from bs4 import BeautifulSoup


def markdown_to_docx(md_text: str, title: str = "Rascunho DFD", meta: dict = None) -> io.BytesIO:
    """
    Converte texto markdown em arquivo DOCX com cabeçalho institucional.

    Args:
        md_text (str): Texto em formato markdown.
        title (str): Título principal do documento.
        meta (dict): Dicionário com informações de metadados (score, data, autor, etc.).

    Returns:
        io.BytesIO: Buffer do arquivo DOCX pronto para download.
    """
    if not md_text:
        raise ValueError("Texto vazio fornecido para conversão.")

    meta = meta or {}

    # Cria documento Word
    doc = Document()

    # ------------------------------
    # Cabeçalho Institucional
    # ------------------------------
    header = doc.sections[0].header
    p = header.paragraphs[0]
    p.text = "TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO – SAAB\nPROJETO SYNAPSE.IA – TUTOR v2"
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.runs[0]
    run.font.size = Pt(9)
    run.font.name = "Calibri"

    # ------------------------------
    # Título
    # ------------------------------
    title_paragraph = doc.add_paragraph(title)
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_paragraph.runs[0].bold = True
    title_paragraph.runs[0].font.size = Pt(14)
    doc.add_paragraph("")  # espaçamento

    # ------------------------------
    # Metadados (scores e data)
    # ------------------------------
    if meta:
        meta_paragraph = doc.add_paragraph()
        for k, v in meta.items():
            meta_paragraph.add_run(f"{k}: ").bold = True
            meta_paragraph.add_run(f"{v}\n")
        doc.add_paragraph("")

    # ------------------------------
    # Conversão Markdown → HTML
    # ------------------------------
    html = markdown.markdown(md_text)
    soup = BeautifulSoup(html, "html.parser")

    for element in soup.recursiveChildGenerator():
        if element.name == "h1":
            doc.add_heading(element.text.strip(), level=1)
        elif element.name == "h2":
            doc.add_heading(element.text.strip(), level=2)
        elif element.name == "h3":
            doc.add_heading(element.text.strip(), level=3)
        elif element.name == "p":
            doc.add_paragraph(element.text.strip())
        elif element.name == "ul":
            for li in element.find_all("li"):
                doc.add_paragraph(li.text.strip(), style="List Bullet")
        elif element.name == "ol":
            for li in element.find_all("li"):
                doc.add_paragraph(li.text.strip(), style="List Number")

    # ------------------------------
    # Rodapé
    # ------------------------------
    footer = doc.sections[0].footer
    p = footer.paragraphs[0]
    p.text = f"Gerado automaticamente pelo Synapse Tutor v2 • {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.runs[0]
    run.font.size = Pt(8)
    run.font.name = "Calibri"

    # ------------------------------
    # Exportação para memória
    # ------------------------------
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
