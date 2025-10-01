# knowledge/validators/tr_semantic_validator.py
from __future__ import annotations
from typing import List, Dict, Tuple
from pathlib import Path
import json, re, yaml

CHECKLIST_PATH = Path("knowledge/tr_checklist.yml")

def load_checklist_items() -> List[Dict]:
    data = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    return data.get("itens", [])

def _truncate(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars: return text
    return text[: max_chars // 2] + "\n\n[[...texto truncado...]]\n\n" + text[-max_chars // 2 :]

def _extract_json(s: str) -> dict:
    m = re.search(r"```json\s*(\{.*?\})\s*```", s, flags=re.S | re.I)
    if m: return json.loads(m.group(1))
    m2 = re.search(r"(\{.*\})", s, flags=re.S)
    if m2:
        try: return json.loads(m2.group(1))
        except Exception: pass
    m3 = re.search(r"(\[.*\])", s, flags=re.S)
    if m3: return {"itens": json.loads(m3.group(1))}
    raise ValueError("Não foi possível extrair JSON da resposta do modelo.")

def semantic_validate_tr(doc_text: str, client) -> Tuple[float, List[Dict]]:
    itens = load_checklist_items()
    if not itens: return 0.0, []
    doc_trim = _truncate(doc_text)

    checklist = [
        {"id": it["id"], "descricao": it["descricao"], "obrigatorio": bool(it.get("obrigatorio", True))}
        for it in itens
    ]

    system_msg = (
        "Você é auditor técnico-jurídico (Lei 14.133/2021) especialista em Termo de Referência. "
        "Avalie SEMANTICAMENTE se o DOCUMENTO atende cada item do CHECKLIST. "
        "Considere sinônimos e redações equivalentes. "
        "Se presente mas incompleto, presente=true e adequacao_nota<100. "
        "Responda SOMENTE JSON no formato: "
        "{'itens':[{'id':'...', 'presente':bool, 'adequacao_nota':0-100, 'justificativa':'...', 'faltantes':['...']}]}."
    )

    user_msg = "CHECKLIST:\n" + json.dumps(checklist, ensure_ascii=False) + "\n\nDOCUMENTO (TR):\n" + doc_trim

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}],
        temperature=0.0,
        max_tokens=1500,
    )

    data = _extract_json(resp.choices[0].message.content)

    obrigatorios = [i for i in checklist if i["obrigatorio"]]
    notas = []
    results: List[Dict] = []

    for it in checklist:
        r = next((x for x in data.get("itens", []) if x.get("id") == it["id"]), None) or {
            "presente": False, "adequacao_nota": 0, "justificativa": "Não avaliado.", "faltantes": []
        }
        nota = max(0, min(100, int(r.get("adequacao_nota", 0))))
        if it["obrigatorio"]: notas.append(nota)

        results.append({
            "id": it["id"],
            "descricao": it["descricao"],
            "presente": bool(r.get("presente", False)),
            "adequacao_nota": nota,
            "justificativa": r.get("justificativa", ""),
            "faltantes": r.get("faltantes", []),
        })

    score = round(sum(notas) / len(obrigatorios), 1) if obrigatorios else 0.0
    return score, results
