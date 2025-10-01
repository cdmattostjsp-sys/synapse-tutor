# knowledge/validators/tr_validator.py
from pathlib import Path
import re
import yaml
from typing import Dict, List, Tuple

CHECKLIST_PATH = Path("knowledge/tr_checklist.yml")

_PATTERNS = {
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
}

def load_checklist() -> List[Dict]:
    data = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    return data.get("itens", [])

def _present(text: str, patterns: List[str]) -> bool:
    return all(re.search(p, text, flags=re.I | re.S) for p in patterns)

def score_tr(doc_text: str) -> Tuple[float, List[Dict]]:
    itens = load_checklist()
    results = []
    total = len([i for i in itens if i.get("obrigatorio", True)])
    hits = 0

    for item in itens:
        pid = item["id"]
        pats = _PATTERNS.get(pid, [])
        ok = _present(doc_text, pats) if pats else False
        if item.get("obrigatorio", True):
            hits += 1 if ok else 0
        results.append({"id": pid, "descricao": item["descricao"], "ok": ok, "obrigatorio": item.get("obrigatorio", True)})

    score = round((hits / total) * 100, 1) if total else 0.0
    return score, results

def missing_items(results: List[Dict]) -> List[str]:
    return [f"{r['id']} – {r['descricao']}" for r in results if r.get("obrigatorio", True) and not r["ok"]]
