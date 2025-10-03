from __future__ import annotations
from typing import List, Dict, Tuple
from pathlib import Path
import json, re, yaml

CHECKLIST_PATH = Path("knowledge/pesquisa_precos_checklist.yml")

def load_checklist_items() -> List[Dict]:
    data = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    return data.get("itens", [])

def _truncate(text: str, max_chars: int = 12000) -> str:
    return text if len(text) <= max_chars else text[:max_chars//2] + "\n\n[[...texto truncado...]]\n\n" + text[-max_chars//2:]

def _extract_json(s: str) -> dict:
    s = s.strip().strip("`").replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(s)
        if isinstance(data, dict) and "itens" in data: return data
        if isinstance(data, list): return {"itens": data}
    except: pass
    m = re.search(r"(\{.*\})", s, flags=re.S)
    if m: return json.loads(m.group(1))
    m2 = re.search(r"(\[.*\])", s, flags=re.S)
    if m2: return {"itens": json.loads(m2.group(1))}
    raise ValueError("❌ Não foi possível extrair JSON válido da resposta do modelo.")

def semantic_validate_pesquisa_precos(doc_text: str, client) -> Tuple[float, List[Dict]]:
    itens = load_checklist_items()
    if not itens: return 0.0, []
    doc_trim = _truncate(doc_text)

    checklist = [{"id":it["id"],"descricao":it["descricao"],"obrigatorio":bool(it.get("obrigatorio",True))} for it in itens]

    system_msg = (
        "Você é um auditor técnico especializado em pesquisa de preços conforme a Lei 14.133/2021 e TCU. "
        "Avalie semanticamente o DOCUMENTO contra o CHECKLIST. "
        "Responda exclusivamente em JSON no formato já definido."
    )

    user_msg = "CHECKLIST:\n"+json.dumps(checklist,ensure_ascii=False)+"\n\nDOCUMENTO (Pesquisa de Preços):\n"+doc_trim

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system_msg},{"role":"user","content":user_msg}],
        temperature=0.0,max_tokens=1500
    )

    raw = resp.choices[0].message.content
    data = _extract_json(raw)

    results, notas = [], []
    obrigatorios=[i for i in checklist if i["obrigatorio"]]

    for it in checklist:
        r = next((r for r in data.get("itens",[]) if r.get("id")==it["id"]), None) or {
            "id":it["id"],"presente":False,"adequacao_nota":0,"justificativa":"Não avaliado.","faltantes":[]}
        presente=bool(r.get("presente",False))
        nota=max(0,min(100,int(r.get("adequacao_nota",0))))
        if it["obrigatorio"]: notas.append(nota)
        results.append({"id":it["id"],"descricao":it["descricao"],"presente":presente,"adequacao_nota":nota,
                        "justificativa":r.get("justificativa",""),"faltantes":r.get("faltantes",[])})
    score=round(sum(notas)/len(obrigatorios),1) if obrigatorios else 0.0
    return score, results
