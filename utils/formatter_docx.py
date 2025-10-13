"""
utils/formatter_docx.py (v3.2)
-------------------------------
Converte markdown institucional em documento Word (.docx) com:
- Suporte a títulos hierárquicos (#, ##, ###)
- Estilo visual institucional (TJSP/SAAB)
- Destaque colorido para sugestões 💡
- Suporte básico a negrito, itálico e listas
- Cabeçalho e rodapé automáticos do Synapse Tutor
"""

from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX


def markdown_to_docx(markdown_text: str, title: str = "Documento Institucional") -> BytesIO:
    """
    Converte o markdown do Synapse Tutor em DOCX formatado.
    Retorna um buffer BytesIO pronto para download.
    """

    # ---------------------------
    # Inicialização do documento
    # ---------------------------
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # Cabeçalho institucional
    header = section.header
    header_para = header.paragraphs[0]
    header_para.text = "Tribunal de Justiça de São Paulo – SAAB | Synapse Tutor v2"
    header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header_para.style.font.size = Pt(9)
    header_para.style.font.color.rgb = RGBColor(90, 90, 90)

    # Rodapé institucional
    footer = section.footer
    footer_para = footer.paragraphs[0]
    footer_para.text = "Documento gerado automaticamente – Synapse.IA | SAAB | TJSP"
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_para.style.font.size = Pt(8)
    footer_para.style.font.color.rgb = RGBColor(100, 100, 100)

    # Título principal
    doc.add_heading(title, level=1).alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ---------------------------
    # Processamento linha a linha
    # ---------------------------
    lines = markdown_text.splitlines()

    for line in lines:
        text = line.strip()
        if not text:
            doc.add_paragraph()
            continue

        # ---------- Cabeçalhos ----------
        if text.startswith("# "):
            p = doc.add_heading(text.replace("# ", "").strip(), level=1)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif text.startswith("## "):
            p = doc.add_heading(text.replace("## ", "").strip(), level=2)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif text.startswith("### "):
            p = doc.add_heading(text.replace("### ", "").strip(), level=3)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # ---------- Sugestões 💡 ----------
        elif text.startswith("💡"):
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(0, 0, 0)
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.left_indent = Inches(0.3)

        # ---------- Listas ----------
        elif text.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            run = p.add_run(text.replace("- ", "").strip())
            _apply_inline_formatting(run)

        elif text.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            run = p.add_run(text.replace("* ", "").strip())
            _apply_inline_formatting(run)

        elif text.startswith("1.") or text.startswith("1️⃣"):
            p = doc.add_paragraph(style="List Number")
            run = p.add_run(text)
            _apply_inline_formatting(run)

        # ---------- Texto comum ----------
        else:
            p = doc.add_paragraph()
            run = p.add_run(text)
            _apply_inline_formatting(run)

    # ---------------------------
    # Formatação final
    # ---------------------------
    for paragraph in doc.paragraphs:
        paragraph_format = paragraph.paragraph_format
        paragraph_format.space_after = Pt(6)
        paragraph_format.line_spacing = 1.25

    # ---------------------------
    # Geração do buffer
    # ---------------------------
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def _apply_inline_formatting(run):
    """
    Aplica negrito, itálico e remoção de marcadores markdown básicos
    dentro de uma linha.
    """
    text = run.text

    # Negrito (**texto**)
    if "**" in text:
        parts = text.split("**")
        formatted_text = ""
        for i, part in enumerate(parts):
            if i % 2 == 1:
                formatted_text += f"<b>{part}</b>"
            else:
                formatted_text += part
        text = formatted_text

    # Itálico (*texto*)
    if "*" in text:
        parts = text.split("*")
        formatted_text = ""
        for i, part in enumerate(parts):
            if i % 2 == 1:
                formatted_text += f"<i>{part}</i>"
            else:
                formatted_text += part
        text = formatted_text

    # Remove símbolos visuais de markdown remanescentes
    run.text = text.replace("**", "").replace("*", "").replace("`", "")
