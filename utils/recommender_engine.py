"""
utils/recommender_engine.py (v3.5)
-----------------------------------
Inclui geração de resumo com nome do responsável.
"""

from typing import Dict, Any
import re


def enhance_markdown(
    guided_md: str,
    validation_result: Dict[str, Any],
    include_suggestions: bool = True,
    tutor_mode: bool = False,
) -> str:
    """Insere sugestões construtivas no markdown."""
    md = guided_md or ""
    if not include_suggestions:
        return md

    semantic = validation_result.get("semantic_result", [])
    has_gaps = any(not item.get("presente", True) for item in semantic)

    suggestions = [
        ("💡 *Sugestão:* Cite a **Lei nº 14.133/2021** e a **IN SAAB nº 12/2025**."),
        ("💡 *Sugestão:* Descreva alternativas consideradas e critérios de escolha."),
        ("💡 *Sugestão:* Inclua especificações técnicas essenciais."),
        ("💡 *Sugestão:* Adicione estimativa de custos e justificativa orçamentária."),
        ("💡 *Sugestão:* Mencione aspectos de sustentabilidade e ESG."),
    ]

    if tutor_mode or has_gaps:
        for s in suggestions:
            if s not in md:
                md += f"\n\n{s}"

    return md


def generate_summary(validation_result: Dict[str, Any], tutor_mode: bool, responsavel: str) -> str:
    """Resumo de análise institucional com nome do responsável."""
    rigid = validation_result.get("rigid_score", 0)
    semantic = validation_result.get("semantic_score", 0)
    mode = "Tutor Orientador" if tutor_mode else "Avaliador Institucional"
    status = "Completo e sem lacunas detectadas." if semantic >= 80 else "Possui pontos de melhoria."
    return (
        f"🧩 Modo: {mode}\n"
        f"👤 Responsável pela elaboração: {responsavel}\n"
        f"📅 Data: {validation_result.get('timestamp', 'Registro automático')}\n"
        f"📊 Score Rígido: {rigid:.1f}% | Score Semântico: {semantic:.1f}%\n"
        f"📈 Avaliação geral: {status}"
    )
