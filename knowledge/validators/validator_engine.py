# knowledge/validators/validator_engine.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import re, json, yaml

# --- Cadastro de checklists por tipo de documento (começando com ETP) ---
CHECKLIST_FILES: Dict[str, Path] = {
    "ETP": Path("knowledge/etp_checklist.yml"),
    # "TR": Path("knowledge/tr_checklist.yml"),  # adicionaremos ao migrar o TR
}

# --- Padrões rígidos por tipo (regex) — iniciando com ETP (mesmo do validador atual) ---
RIGID_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "ETP": {
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
}

# ---------------------- utilidades ----------------------
def _load_checklist(doc_type: str) -> List[Dict]:
    if doc_type not in CHECKLIST_FILES:
        raise ValueError(f"Checklist não configurado para doc_type={doc_type}.")
    data = yaml.safe_load(CHECKLIST_FILES[doc_type].read_text(encoding="utf-8"))
    return data.get("itens", [])

def _present(text: str, patterns: List[str]) -> bool:
    return all(re.search(p, text, flags=re.I | re.S) for p in patterns)

def _truncate(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return head + "\n\n[[...texto truncado...]]\n\n" + tail

def _extract_json(s: str) -> dict:
    m = re.search(r"```json\s*(\{.*?\})\s*```", s, flags=re.S | re.I)
    if m:
        return json.loads(m.group(1))
    m2 = re.search(r"(\{.*\})", s, flags=re.S)
    if m2:
        try:
            return json.loads(m2.group(1))
        except Exception:
            pass
    m3 = re.search(r"(\[.*\])", s, flags=re.S)
    if m3:
        return {"itens": json.loads(m3.group(1))}
    raise ValueError("Não foi possível extrair JSON da resposta do modelo.")

# ---------------------- validação rígida genérica ----------------------
def rigid_validate(doc_text: str, doc_type: str) -> Tuple[float, List[Dict]]:
    itens = _load_checklist(doc_type)
    patterns = RIGID_PATTERNS.get(doc_type, {})
    results = []
    obrigatorios = [i for i in itens if i.get("obrigatorio", True)]
    hits = 0

    for item in itens:
        pid = item["id"]
        pats = patterns.get(pid, [])
        ok = _present(doc_text, pats) if pats else False
        if item.get("obrigatorio", True) and ok:
            hits += 1
        results.append({
            "id": pid,
            "descricao": item["descricao"],
            "ok": ok,
            "obrigatorio": item.get("obrigatorio", True)
        })

    score = round((hits / len(obrigatorios)) * 100, 1) if obrigatorios else 0.0
    return score, results

def missing_items_rigid(results: List[Dict]) -> List[str]:
    return [f"{r['id']} – {r['descricao']}" for r in results if r.get("obrigatorio", True) and not r["ok"]]

# ---------------------- validação semântica genérica ----------------------
def semantic_validate(doc_text: str, doc_type: str, client) -> Tuple[float, List[Dict]]:
    itens = _load_checklist(doc_type)
    if not itens:
        return 0.0, []

    checklist = [
        {"id": it["id"], "descricao": it["descricao"], "obrigatorio": bool(it.get("obrigatorio", True))}
        for it in itens
    ]

    doc_trim = _truncate(doc_text, 12000)

    system_msg = (
        "Você é um auditor técnico-jurídico da Lei 14.133/2021. "
        "Avalie SEMANTICAMENTE se o DOCUMENTO atende cada item do CHECKLIST. "
        "Considere sinônimos/redações equivalentes. "
        "Se presente porém incompleto, use presente=true e adequacao_nota<100, explicando. "
        "Responda SOMENTE JSON no formato:\n"
        "{'itens':[{'id':'<id>', 'presente':bool, 'adequacao_nota':0-100, 'justificativa':'...','faltantes':['...']}]}"
    )

    user_msg = "DOC_TYPE: " + doc_type + "\nCHECKLIST:\n" + json.dumps(checklist, ensure_ascii=False) + "\n\nDOCUMENTO:\n" + doc_trim

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        max_tokens=1500,
    )

    data = _extract_json(resp.choices[0].message.content)

    obrigatorios = [i for i in checklist if i["obrigatorio"]]
    notas = []
    results: List[Dict] = []

    for it in checklist:
        found = next((x for x in data.get("itens", []) if x.get("id") == it["id"]), None)
        if not found:
            found = {"presente": False, "adequacao_nota": 0, "justificativa": "Não avaliado.", "faltantes": []}

        nota = max(0, min(100, int(found.get("adequacao_nota", 0))))
        if it["obrigatorio"]:
            notas.append(nota)

        results.append({
            "id": it["id"],
            "descricao": it["descricao"],
            "presente": bool(found.get("presente", False)),
            "adequacao_nota": nota,
            "justificativa": found.get("justificativa", ""),
            "faltantes": found.get("faltantes", []),
        })

    score = round(sum(notas) / len(obrigatorios), 1) if obrigatorios else 0.0
    return score, results
