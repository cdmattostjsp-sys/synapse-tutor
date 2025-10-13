"""
utils/formatter_docx.py (v3.4.1)
--------------------------------
Conversor Markdown → DOCX institucional (Synapse Tutor v2)

Melhorias desta versão:
- Correção de erro UnboundLocalError (p não inicializado)
- Tolerância a linhas vazias e separadores ("---")
- Destaque automático 💡 para sugestões
- Cabeçalho e rodapé institucionais TJSP/SAAB
- Campo final “Resumo da Análise”
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

    # --------------------------
    # Configura margens da página
    # --------------------------
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # --------------------------
    # Cabeçalho institucional
    # --------------------------
    header = section.header.paragraphs[0]
    header.text = "Tribunal de Justiça de São Paulo – SAAB | Synapse Tutor v2"
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header.style.font.size = Pt(9)
    header.style.font.color.rgb = RGBColor(90, 90, 90)

    # --------------------------
    # Rodapé institucional
    # --------------------------
    footer = section.footer.paragraphs[0]
    footer.text = "Documento gerado automaticamente — Synapse.IA | SAAB | TJSP"
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.style.font.size = Pt(8)
    footer.style.font.color.rgb = RGBColor(100, 100, 100)

    # --------------------------
    # Título principal
    # --------------------------
    doc.add_heading(title, level=1).alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --------------------------
    # Limpeza básica de Markdown
    # --------------------------
    markdown_text = markdown_text.replace("<b>", "").replace("</b>", "")
    markdown_text = markdown_text.replace("<i>", "").replace("</i>", "")
    markdown_text = markdown_text.replace("**", "").replace("*", "")

    # --------------------------
    # Conversão linha a linha
    # --------------------------
    lines = markdown_text.splitlines()
    for line in lines:
        p = None  # garante que a variável exista
        text = line.strip()

        # Linha vazia → quebra de parágrafo
        if not text:
            doc.add_paragraph()
            continue

        # Hierarquia de títulos
        if text.startswith("# "):
            doc.add_heading(text[2:].strip(), level=1)
        elif text.startswith("## "):
            doc.add_heading(text[3:].strip(), level=2)
        elif text.startswith("### "):
            doc.add_heading(text[4:].strip(), level=3)

        # Sugestões destacadas 💡
        elif text.startswith("💡"):
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)

        # Listas
        elif text.startswith("- "):
            p = doc.add_paragraph(text[2:].strip(), style="List Bullet")

        # Linhas separadoras (“---”)
        elif text.startswith("---"):
            sep = doc.add_paragraph("―" * 30)
            sep.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Texto comum
        else:
            p = doc.add_paragraph(text)

        # Aplica espaçamento apenas se p foi criado
        if p:
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.25

    # --------------------------
    # Campo final: Resumo da Análise
    # --------------------------
    if summary_text:
        doc.add_page_break()
        doc.add_heading("📊 Resumo da Análise", level=2)
        doc.add_paragraph(summary_text)

    # --------------------------
    # Exporta buffer
    # --------------------------
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
