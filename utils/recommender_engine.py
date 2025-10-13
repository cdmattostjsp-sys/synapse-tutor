"""
utils/recommender_engine.py (v3.4)
-----------------------------------
Modo Tutor / Modo Avaliador + suporte a logs.
Agora inclui:
- Geração de resumo de análise para logs e rodapé
- Sugestões com títulos mais claros e formato uniforme
"""

from typing import Dict, Any, List
import re


SUGGESTION_LIBRARY = [
    {
        "key": "legislacao",
        "title": "Fundamento Legal",
        "text": "💡 *Sugestão:* Cite a **Lei nº 14.133/2021** e a **IN SAAB nº 12/2025**.",
        "section_hint": ["Justificativa", "Alinhamento"],
    },
    {
        "key": "alternativas",
        "title": "Análise de Alternativas",
        "text": "💡 *Sugestão:* Descreva as **alternativas consideradas** e o motivo da escolha.",
        "section_hint": ["Descrição", "Justificativa"],
    },
    {
        "key": "especificacoes",
        "title": "Especificações Técnicas",
        "text": "💡 *Sugestão:* Detalhe as **especificações técnicas essenciais**.",
        "section_hint": ["Descrição"],
    },
    {
        "key": "custos",
        "title": "Estimativa de Custos",
        "text": "💡 *Sugestão:* Adicione **estimativa de custos e justificativa orçamentária**.",
        "section_hint": ["Justificativa"],
    },
    {
        "key": "sustentabilidade",
        "title": "Sustentabilidade",
        "text": "💡 *Sugestão:* Mencione **aspectos de sustentabilidade e ESG**.",
        "section_hint": ["Descrição", "Benefícios"],
    },
    {
        "key": "riscos",
        "title": "Matriz de Riscos",
        "text": "💡 *Sugestão:* Inclua **matriz de riscos** com mitigação e impacto.",
        "section_hint": ["Riscos", "Justificativa"],
    },
]


def enhance_markdown(
    guided_md: str,
    validation_result: Dict[str, Any],
    include_suggestions: bool = True,
    tutor_mode: bool = False,
) -> str:
    """Gera markdown aprimorado com sugestões construtivas."""

    md = guided_md or ""
    if not include_suggestions:
        return md

    semantic = validation_result.get("semantic_result", [])
    has_gaps = any(not item.get("presente", True) for item in semantic)

    suggestions = []
    if tutor_mode or has_gaps:
        for s in SUGGESTION_LIBRARY[:4 if tutor_mode else len(SUGGESTION_LIBRARY)]:
            text = f"{s['text']}"
            for section_hint in s["section_hint"]:
                if re.search(rf"(?i){section_hint}", md):
                    md = re.sub(rf"(?i)({section_hint}.*?)$", r"\1\n\n" + text, md, 1)
                    break
            else:
                suggestions.append(s)

    # Caso não haja sugestões específicas
    if not suggestions and not has_gaps:
        md += "\n\n---\n💬 *Documento completo: nenhuma sugestão necessária.*"

    return md


def generate_summary(validation_result: Dict[str, Any], tutor_mode: bool) -> str:
    """Gera um resumo textual para inclusão nos logs e no rodapé do DOCX."""
    rigid = validation_result.get("rigid_score", 0)
    semantic = validation_result.get("semantic_score", 0)
    mode = "Tutor Orientador" if tutor_mode else "Avaliador Institucional"
    status = "Completo e sem lacunas detectadas." if semantic >= 80 else "Possui pontos de melhoria."
    return (
        f"🧩 Modo: {mode}\n"
        f"📅 Data: Registro automático de execução.\n"
        f"📊 Score Rígido: {rigid:.1f}% | Score Semântico: {semantic:.1f}%\n"
        f"📈 Avaliação geral: {status}"
    )
