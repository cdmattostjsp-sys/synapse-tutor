"""
utils/recommender_engine.py (v3.3)
----------------------------------
Gera sugestões de complementação a partir da análise semântica do validator_engine_vNext.

Novidades:
- Modo Tutor (gera sugestões mesmo quando não há lacunas)
- Modo Avaliador (gera sugestões apenas quando há falhas)
- Sugestões mais legíveis e organizadas por seção
"""

from typing import Dict, Any, List
import re

# ---------- Biblioteca de sugestões ----------
SUGGESTION_LIBRARY = [
    {
        "key": "legislacao",
        "triggers": ["legislação", "lei 14.133", "fundamento legal"],
        "title": "Fundamento Legal",
        "text": (
            "💡 *Sugestão:* Cite a **Lei nº 14.133/2021** e a **IN SAAB nº 12/2025**, destacando a conformidade "
            "com os princípios da fase interna e a vinculação ao planejamento anual de contratações."
        ),
        "section_hint": ["Justificativa", "Introdução", "Alinhamento"]
    },
    {
        "key": "alternativas",
        "triggers": ["alternativas", "análise de alternativas"],
        "title": "Análise de Alternativas",
        "text": (
            "💡 *Sugestão:* Descreva as **alternativas consideradas** (reutilização, remanejamento, ata de registro de preços), "
            "indicando o motivo da escolha adotada."
        ),
        "section_hint": ["Descrição", "Justificativa"]
    },
    {
        "key": "especificacoes",
        "triggers": ["especificações", "características técnicas"],
        "title": "Especificações Técnicas",
        "text": (
            "💡 *Sugestão:* Detalhe as **especificações técnicas essenciais** (dimensões, materiais, padrões de qualidade, "
            "garantia, conformidade e acessibilidade)."
        ),
        "section_hint": ["Descrição"]
    },
    {
        "key": "custos",
        "triggers": ["estimativa de custos", "orçamento", "custo"],
        "title": "Estimativa de Custos",
        "text": (
            "💡 *Sugestão:* Adicione **estimativa de custos**, fontes de pesquisa e justificativa orçamentária "
            "(pesquisa de mercado, atas vigentes, contratações similares)."
        ),
        "section_hint": ["Justificativa", "Alinhamento"]
    },
    {
        "key": "sustentabilidade",
        "triggers": ["sustentabilidade", "esg"],
        "title": "Sustentabilidade",
        "text": (
            "💡 *Sugestão:* Mencione **aspectos de sustentabilidade** (materiais recicláveis, eficiência energética, "
            "gestão de resíduos e logística reversa)."
        ),
        "section_hint": ["Descrição", "Benefícios"]
    },
    {
        "key": "riscos",
        "triggers": ["matriz de riscos", "riscos"],
        "title": "Matriz de Riscos",
        "text": (
            "💡 *Sugestão:* Inclua uma **matriz de riscos** com eventos, impactos e medidas de mitigação."
        ),
        "section_hint": ["Riscos", "Justificativa"]
    },
    {
        "key": "beneficios",
        "triggers": ["benefícios", "vantagens"],
        "title": "Benefícios Esperados",
        "text": (
            "💡 *Sugestão:* Explique os **benefícios institucionais e indicadores de desempenho** esperados após a contratação."
        ),
        "section_hint": ["Benefícios"]
    },
    {
        "key": "criterios",
        "triggers": ["critérios de avaliação", "indicadores"],
        "title": "Critérios de Avaliação",
        "text": (
            "💡 *Sugestão:* Defina **critérios de avaliação e medição**, incluindo desempenho, prazos e conformidade técnica."
        ),
        "section_hint": ["Critérios", "Benefícios"]
    },
]

# ---------- Funções internas ----------
def _normalize(txt: str) -> str:
    return (txt or "").strip().lower()


def _pick_suggestions_from_semantic(semantic_result: List[Dict[str, Any]], force_mode=False) -> List[Dict[str, str]]:
    picked = []
    for item in semantic_result or []:
        desc = _normalize(item.get("descricao", ""))
        if item.get("presente", False) and not force_mode:
            continue
        for sug in SUGGESTION_LIBRARY:
            if any(trig in desc for trig in [t.lower() for t in sug["triggers"]]):
                picked.append(sug)
                break

    # Em modo tutor, gera 2 exemplos mesmo se tudo estiver completo
    if force_mode and not picked:
        picked = [SUGGESTION_LIBRARY[0], SUGGESTION_LIBRARY[3]]

    # Remove duplicatas
    seen = set()
    unique = []
    for s in picked:
        if s["title"] not in seen:
            unique.append(s)
            seen.add(s["title"])
    return unique


SECTION_PATTERNS = [
    (re.compile(r"(?i)##?.*justificativa"), "Justificativa"),
    (re.compile(r"(?i)##?.*riscos"), "Riscos"),
    (re.compile(r"(?i)##?.*descrição"), "Descrição"),
    (re.compile(r"(?i)##?.*benef"), "Benefícios"),
    (re.compile(r"(?i)##?.*alinhamento"), "Alinhamento"),
    (re.compile(r"(?i)##?.*documentos"), "Documentos"),
]


def _inject_after_section(md_text: str, section_label: str, insertion: str) -> str:
    for pattern, label in SECTION_PATTERNS:
        if label == section_label:
            match = pattern.search(md_text)
            if match:
                pos = match.end()
                return md_text[:pos] + "\n\n" + insertion.strip() + "\n" + md_text[pos:]
    return md_text


# ---------- Função principal ----------
def enhance_markdown(guided_md: str, validation_result: Dict[str, Any],
                     include_suggestions: bool = True, tutor_mode: bool = False) -> str:
    """
    Retorna markdown aprimorado com sugestões construtivas.
    tutor_mode=True => força sugestões mesmo sem lacunas.
    """
    md = guided_md or ""
    if not include_suggestions:
        return md

    suggestions = _pick_suggestions_from_semantic(
        validation_result.get("semantic_result"), force_mode=tutor_mode
    )

    if not suggestions:
        return md + "\n\n---\n💬 *Nenhuma sugestão identificada nesta etapa.*"

    pending = []
    for s in suggestions:
        inserted = False
        for section_hint in s["section_hint"]:
            new_md = _inject_after_section(md, section_hint, s["text"])
            if new_md != md:
                md = new_md
                inserted = True
                break
        if not inserted:
            pending.append(s)

    if pending:
        md += "\n\n## Sugestões de Complementação\n"
        for s in pending:
            md += f"- **{s['title']}** — {s['text']}\n"

    return md
