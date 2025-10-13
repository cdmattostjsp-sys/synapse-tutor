"""
utils/formatter_docx.py (v3.4)
-------------------------------
Conversor Markdown → DOCX institucional com:
- Cabeçalho e rodapé TJSP/SAAB
- Sugestões 💡 destacadas em amarelo
- Suporte a negrito/itálico reais
- Remoção automática de tags HTML
- Campo final 'Resumo da Análise'
"""

from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX


def markdown_to_docx(markdown_text: str, title: str = "Documento Institucional",
                     summary_text: str = "") -> BytesIO:
    """
    Converte o markdown do Synapse Tutor em DOCX formatado.
    Retorna um buffer BytesIO pronto para download.
    """

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # Cabeçalho institucional
    header = section.header.paragraphs[0]
    header.text = "Tribunal de Justiça de São Paulo – SAAB | Synapse Tutor v2"
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header.style.font.size = Pt(9)
    header.style.font.color.rgb = RGBColor(90, 90, 90)

    # Rodapé institucional
    footer = section.footer.paragraphs[0]
    footer.text = "Documento gerado automaticamente — Synapse.IA | SAAB | TJSP"
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.style.font.size = Pt(8)
    footer.style.font.color.rgb = RGBColor(100, 100, 100)

    # Título
    doc.add_heading(title, level=1).alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Pré-processamento do texto
    markdown_text = markdown_text.replace("<b>", "").replace("</b>", "")
    markdown_text = markdown_text.replace("<i>", "").replace("</i>", "")
    markdown_text = markdown_text.replace("**", "").replace("*", "")

    lines = markdown_text.splitlines()
    for line in lines:
        text = line.strip()
        if not text:
            doc.add_paragraph()
            continue

        if text.startswith("# "):
            doc.add_heading(text[2:].strip(), level=1)
        elif text.startswith("## "):
            doc.add_heading(text[3:].strip(), level=2)
        elif text.startswith("### "):
            doc.add_heading(text[4:].strip(), level=3)
        elif text.startswith("💡"):
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
        elif text.startswith("- "):
            p = doc.add_paragraph(text[2:].strip(), style="List Bullet")
        else:
            p = doc.add_paragraph(text)

        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.25

    # Campo final – resumo da análise
    if summary_text:
        doc.add_page_break()
        doc.add_heading("📊 Resumo da Análise", level=2)
        doc.add_paragraph(summary_text)

    # Salvar buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
