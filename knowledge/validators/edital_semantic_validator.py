from __future__ import annotations
from typing import List, Dict, Tuple
from pathlib import Path
import json
import re
import yaml

# Caminho para checklist do Edital
CHECKLIST_PATH = Path("knowledge/edital_checklist.yml")

def load_checklist_items() -> List[Dict]:
    data = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    return data.get("items", [])

def _truncate(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return head + "\n\n[[...texto truncado...]]\n\n" + tail

def _extract_json(s: str) -> dict:
    """
    Extrai JSON de uma string que pode vir com blocos ```json ou texto extra.
    Retorna sempre um dict com a chave "itens".
    """
    s = s.strip().strip("`").replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(s)
        if isinstance(data, dict) and "itens" in data:
            return data
        if isinstance(data, list):
            return {"itens": data}
    except Exception:
        pass

    m = re.search(r"(\{.*\})", s, flags=re.S)
    if m:
        return json.loads(m.group(1))

    m2 = re.search(r"(\[.*\])", s, flags=re.S)
    if m2:
        return {"itens": json.loads(m2.group(1))}

    raise ValueError("❌ Não foi possível extrair JSON válido da resposta do modelo.")

def semantic_validate_edital(doc_text: str, client) -> Tuple[float, List[Dict]]:
    """
    Retorna (score, results), onde:
      - score: média das notas de adequação (0..100) dos itens obrigatórios
      - results: lista com campos: id, descricao, presente (bool), adequacao_nota (0..100), justificativa (str), faltantes (list[str])
    """
    itens = load_checklist_items()
    if not itens:
        return 0.0, []

    doc_trim = _truncate(doc_text, max_chars=12000)

    checklist_compacto = [
        {"id": it["id"], "descricao": it["descricao"], "obrigatorio": bool(it.get("obrigatorio", True))}
        for it in itens
    ]

    system_msg = (
        "Você é um auditor técnico-jurídico especializado em licitações (Lei 14.133/2021). "
        "Avalie se o DOCUMENTO atende, de forma SEMÂNTICA, cada item do CHECKLIST. "
        "Considere sinônimos, redações equivalentes e conteúdo implícito. "
        "Use três níveis claros de nota:\n"
        "- 100 = totalmente atendido (texto completo e claro)\n"
        "- 50 a 90 = parcialmente atendido (há referência, mas incompleta ou insuficiente)\n"
        "- 0 = ausente (nenhuma evidência suficiente)\n"
        "Responda EXCLUSIVAMENTE em JSON no formato:\n"
        "{\n"
        '  "itens": [\n'
        '    {\n'
        '      "id": "<id do checklist>",\n'
        '      "presente": true/false,\n'
        '      "adequacao_nota": 0-100,\n'
        '      "justificativa": "texto curto (máx. 3 frases)",\n'
        '      "faltantes": ["lista opcional de pontos que faltam"]\n'
        "    }, ...\n"
        "  ]\n"
        "}"
    )

    user_msg = (
        "CHECKLIST:\n"
        + json.dumps(checklist_compacto, ensure_ascii=False)
        + "\n\nDOCUMENTO (EDITAL):\n"
        + doc_trim
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        max_tokens=1500,
    )

    raw = resp.choices[0].message.content
    data = _extract_json(raw)

    results: List[Dict] = []
    obrigatorios = [it for it in checklist_compacto if it["obrigatorio"]]
    notas = []

    for it in checklist_compacto:
        rmatch = None
        for r in data.get("itens", []):
            if r.get("id") == it["id"]:
                rmatch = r
                break

        if rmatch is None:
            rmatch = {
                "id": it["id"],
                "presente": False,
                "adequacao_nota": 0,
                "justificativa": "Não avaliado.",
                "faltantes": []
            }

        presente = bool(rmatch.get("presente", False))
        nota = max(0, min(100, int(rmatch.get("adequacao_nota", 0))))  # garante nota 0..100

        if it["obrigatorio"]:
            notas.append(nota)  # inclui até os 0 (ausentes)

        results.append({
            "id": it["id"],
            "descricao": it["descricao"],
            "presente": presente,
            "adequacao_nota": nota,
            "justificativa": rmatch.get("justificativa", ""),
            "faltantes": rmatch.get("faltantes", []),
        })

    score = round(sum(notas) / len(obrigatorios), 1) if obrigatorios else 0.0
    return score, results
