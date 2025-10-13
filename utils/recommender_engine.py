"""
utils/recommender_engine.py  (v3.1)
-----------------------------------
Gera sugestões de complementação a partir do validator_engine_vNext
e injeta essas sugestões no markdown antes da exportação.

Atualização 3.1:
- Ajuste fino nas correspondências de seções.
- Marcadores visuais aprimorados.
- Compatível com opção "incluir/excluir sugestões".
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
            "💡 *Sugestão:* Incluir referência à **Lei nº 14.133/2021** e à **IN SAAB nº 12/2025**, "
            "destacando a conformidade da demanda com os princípios da fase interna."
        ),
        "section_hint": ["Justificativa", "Introdução", "Alinhamento"]
    },
    {
        "key": "alternativas",
        "triggers": ["alternativas", "análise de alternativas"],
        "title": "Análise de Alternativas",
        "text": (
            "💡 *Sugestão:* Descrever as **alternativas consideradas** (reutilização, solução interna, contratação direta ou atas), "
            "indicando o motivo da escolha."
        ),
        "section_hint": ["Descrição", "Justificativa"]
    },
    {
        "key": "especificacoes",
        "triggers": ["especificações", "características técnicas"],
        "title": "Especificações Técnicas",
        "text": (
            "💡 *Sugestão:* Detalhar **especificações técnicas essenciais** (dimensões, materiais, padrões de qualidade, "
            "garantia e conformidade normativa)."
        ),
        "section_hint": ["Descrição"]
    },
    {
        "key": "custos",
        "triggers": ["estimativa de custos", "orçamento", "custo"],
        "title": "Estimativa de Custos",
        "text": (
            "💡 *Sugestão:* Adicionar **estimativa de custos**, indicando fonte de pesquisa, "
            "método de cálculo e dotação orçamentária prevista."
        ),
        "section_hint": ["Justificativa", "Alinhamento"]
    },
    {
        "key": "sustentabilidade",
        "triggers": ["sustentabilidade", "esg"],
        "title": "Sustentabilidade",
        "text": (
            "💡 *Sugestão:* Apontar **aspectos de sustentabilidade** (materiais, reaproveitamento, certificações, "
            "logística reversa) conforme diretrizes do TJSP."
        ),
        "section_hint": ["Descrição", "Benefícios"]
    },
    {
        "key": "riscos",
        "triggers": ["matriz de riscos", "riscos", "gestão de riscos"],
        "title": "Matriz de Riscos",
        "text": (
            "💡 *Sugestão:* Incluir **matriz de riscos** com eventos, impactos e estratégias de mitigação."
        ),
        "section_hint": ["Riscos", "Justificativa"]
    },
    {
        "key": "beneficios",
        "triggers": ["benefícios", "vantagens"],
        "title": "Benefícios Esperados",
        "text": (
            "💡 *Sugestão:* Descrever **benefícios institucionais e impactos positivos**, "
            "com indicadores quando possível."
        ),
        "section_hint": ["Benefícios"]
    },
    {
        "key": "criterios",
        "triggers": ["critérios de avaliação", "indicadores"],
        "title": "Critérios de Avaliação",
        "text": (
            "💡 *Sugestão:* Definir **critérios de avaliação e medição**, "
            "incluindo prazos, conformidade técnica e qualidade do serviço."
        ),
        "section_hint": ["Critérios", "Benefícios"]
    },
]

# ---------- Funções internas ----------
def _normalize(txt: str) -> str:
    return (txt or "").strip().lower()

def _pick_suggestions_from_semantic(semantic_result: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    picked = []
    for item in semantic_result or []:
        desc = _normalize(item.get("descricao", ""))
        if item.get("presente", False):
            continue
        for sug in SUGGESTION_LIBRARY:
            if any(trig in desc for trig in [t.lower() for t in sug["triggers"]]):
                picked.append(sug)
                break
    # remove duplicados
    titles_seen = set()
    unique = []
    for s in picked:
        if s["title"] not in titles_seen:
            unique.append(s)
            titles_seen.add(s["title"])
    return unique

# ---------- Mapeamento de seções ----------
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

# ---------- Função pública ----------
def enhance_markdown(guided_md: str, validation_result: Dict[str, Any], include_suggestions: bool = True) -> str:
    """
    Retorna markdown aprimorado com sugestões construtivas.
    """
    md = guided_md or ""
    if not include_suggestions:
        return md

    suggestions = _pick_suggestions_from_semantic(validation_result.get("semantic_result"))
    if not suggestions:
        return md + "\n\n---\n💬 *Nenhuma sugestão identificada nesta etapa. Revise critérios e indicadores.*"

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
