import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from openai import OpenAI

# --- CHECKLISTS DISPONÍVEIS ---
CHECKLIST_FILES: Dict[str, Path] = {
    "ETP": Path("knowledge/etp_checklist.yml"),
    "TR": Path("knowledge/tr_checklist.yml"),
}

# --- PADRÕES RÍGIDOS ---
RIGID_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "ETP": {
        "referencia_normativa": [
            r"Lei\s*14\.?133/?\s*2021",
            r"Decreto\s*67\.?381/?\s*2022",
            r"(Provimento|Prov\.)\s*CSM\s*2724/?\s*2023",
        ],
        "alternativas": [r"alternativa[s]? poss[ií]veis", r"op[cç][oõ]es analisad"],
        "riscos_matriz": [r"matriz.*risc", r"probabil", r"impacto", r"mitiga"],
        "pesquisa_precos": [r"pesquisa de pre[cç]os", r"pain[eé]is? de pre[cç]os", r"contratos? similares"],
        "especificacoes": [r"especifica[cç][oõ]es t[eé]cnicas", r"requisitos m[ií]nimos"],
        "sustentabilidade": [r"sustentabilidade", r"efici[eê]ncia energ[eé]tica", r"Procel|Energy\s*Star"],
    },
    "TR": {
        "base_legal": [
            r"Lei\s*14\.?133/?\s*2021",
            r"Decreto\s*67\.?381/?\s*2022",
            r"(Provimento|Prov\.)\s*CSM\s*2724/?\s*2023",
        ],
        "objeto": [r"\bobje(to|to da contrata)"],
        "justificativa": [r"justificativa|motivação"],
        "escopo_entregas": [r"escopo|entreg[áa]veis|quantidad"],
        "requisitos_tecnicos": [r"requisitos t[eé]cnicos|especifica(ç|c)[oõ]es|caracter[íi]sticas t[eé]cnicas"],
        "niveis_servico_sla": [r"SLA|n[ií]veis? de servi[çc]o|tempo de resposta|tempo de solu"],
        "criterios_julgamento": [r"crit[eé]rios de julgament|menor pre[cç]o|t[eé]cnica e pre[cç]o|melhor t[eé]cnica"],
        "estimativa_custos": [r"estimativa de custos|planilha|pesquisa de pre[cç]os|metodologi"],
        "prazos_execucao": [r"prazo|cronograma|entrega|execu[çc][aã]o"],
        "obrigacoes_partes": [r"obriga[cç][oõ]es|responsabil|deveres da contratada|obriga[cç][aã]o da administra[cç][aã]o"],
        "sustentabilidade": [r"sustentabil|Procel|Energy\s*Star|log[íi]stica reversa|descarte"],
        "riscos_matriz": [r"matriz.*risc|probabil|impacto|mitiga"],
        "fiscalizacao": [r"fiscaliza[cç][aã]o|acompanhamento|gestor do contrato|fiscal do contrato|aceite"],
        "garantias_penalidades": [r"garantia|penalidade|multa|glosa"],
        "vigencia_reajuste": [r"vig[eê]ncia|reajuste|repactua[cç][aã]o"],
    },
}

# --- FUNÇÕES DE SUPORTE ---

def load_checklist(agent: str) -> List[Dict]:
    path = CHECKLIST_FILES.get(agent)
    if not path or not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def engine_rigid_validate(text: str, agent: str) -> Tuple[float, List[Dict]]:
    """Validação rígida por regex"""
    patterns = RIGID_PATTERNS.get(agent, {})
    results = []
    total = len(patterns)
    acertos = 0

    for item, regex_list in patterns.items():
        found = any(re.search(rgx, text, flags=re.IGNORECASE) for rgx in regex_list)
        results.append({"id": item, "ok": found, "descricao": item})
        if found:
            acertos += 1

    score = round((acertos / total) * 100, 1) if total > 0 else 0.0
    return score, results

def engine_missing_rigid(results: List[Dict]) -> List[str]:
    return [r["descricao"] for r in results if not r["ok"]]

def engine_semantic_validate(text: str, agent: str, client: OpenAI) -> Tuple[float, List[Dict]]:
    """Validação semântica via LLM"""
    checklist = load_checklist(agent)
    if not checklist:
        return 0.0, []

    prompt = f"""
Você é um avaliador de conformidade de documentos de licitação.
Analise o seguinte documento do tipo {agent} e verifique cada item do checklist abaixo.

Documento:
{text}

Checklist:
{yaml.dump(checklist, allow_unicode=True)}

Para cada item, responda em JSON com:
- id: identificador do item
- descricao: descrição resumida
- presente: true/false se o item aparece
- adequacao_nota: 0 a 100 sobre a qualidade do detalhamento
- justificativa: breve explicação
- faltantes: lista de pontos que faltam detalhar
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um avaliador técnico especialista em licitações."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=1800
    )

    try:
        parsed = yaml.safe_load(response.choices[0].message.content)
        if not isinstance(parsed, list):
            return 0.0, []
    except Exception:
        return 0.0, []

    notas = [p.get("adequacao_nota", 0) for p in parsed]
    score = round(sum(notas) / len(notas), 1) if notas else 0.0
    return score, parsed
