# validators/etp_validator.py
# Validador simples para ETP: lê checklist YAML e verifica presença de termos-chave no texto final.
from pathlib import Path
import re
import yaml
from typing import Dict, List, Tuple

CHECKLIST_PATH = Path("knowledge/etp_checklist.yml")

_PATTERNS = {
    "base_legal": [
        r"Lei\s*14\.?133/?\s*2021",
        r"Decreto\s*67\.?381/?\s*2022",
        r"(Provimento|Prov\.)\s*CSM\s*2724/?\s*2023",
    ],
    "alternativas": [
        r"alternativa",
        r"manuten",
        r"locaç",
        r"aquisiç",
    ],
    "riscos_matriz": [
        r"matriz.*risc",
        r"probabil",
        r"impacto",
        r"mitiga",
    ],
    "sustentabilidade": [
        r"sustentabil",
        r"Procel",
        r"Energy\s*Star",
        r"descarte",
    ],
    "pesquisa_precos": [
        r"pesquisa de preços|metodologi",
        r"fornecedor|fontes|painel",
        r"m[eé]dia|mediana|amostra",
    ],
    "especificacoes_minimas": [
        r"processador",
        r"mem[oó]ria",
        r"SSD",
        r"monitor",
        r"sistema operacional|Windows|Linux",
    ],
}

def load_checklist() -> List[Dict]:
    data = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    return data.get("itens", [])

def _present(text: str, patterns: List[str]) -> bool:
    return all(re.search(p, text, flags=re.I|re.S) for p in patterns)

def score_etp(doc_text: str) -> Tuple[float, List[Dict]]:
    itens = load_checklist()
    results = []
    total = len(itens)
    hits = 0

    for item in itens:
        pid = item["id"]
        pats = _PATTERNS.get(pid, [])
        ok = _present(doc_text, pats) if pats else False
        hits += 1 if ok else 0
        results.append({
            "id": pid,
            "descricao": item["descricao"],
            "ok": ok
        })

    score = round((hits / total) * 100, 1) if total else 0.0
    return score, results

def missing_items(results: List[Dict]) -> List[str]:
    return [f"{r['id']} – {r['descricao']}" for r in results if not r["ok"]]
