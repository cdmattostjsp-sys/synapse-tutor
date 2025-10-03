# knowledge/validators/edital_semantic_validator.py
# Validador semântico para Edital, agora com suporte a PDF carregado.

from __future__ import annotations
from typing import List, Dict, Tuple
from pathlib import Path
import json
import re
import yaml

# Dependência para extração de PDF
import PyPDF2

CHECKLIST_PATH = Path("knowledge/validators/edital_checklist.yml")

def load_checklist_items() -> List[Dict]:
    """Carrega os itens do checklist do edital a partir do YAML."""
    data = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    return data.get("itens", [])

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrai texto de um PDF carregado."""
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        return f"❌ Erro ao extrair texto do PDF: {e}"
    return text

def _truncate(text: str, max_chars: int = 12000) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return head + "\n\n[[...texto truncado...]]\n\n" + tail

def _extract_json(s: str) -> dict:
    """Extrai JSON puro de respostas do modelo."""
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

def semantic_validate_edital(doc_input: str, client) -> Tuple[float, List[Dict]]:
    """
    Valida semanticamente o EDITAL.
    - doc_input pode ser texto ou caminho para um PDF.
    Retorna (score, results).
    """
    itens = load_checklist_items()
    if not itens:
        return 0.0, []

    # Detecta se é PDF
    if doc_input.lower().endswith(".pdf"):
        doc_text = extract_text_from_pdf(doc_input)
    else:
        doc_text = doc_input

    doc_trim = _truncate(doc_text, max_chars=12000)

    checklist_compacto = [
        {"id": it["id"], "descricao": it["descricao"], "obrigatorio": bool(it.get("obrigatorio", True))}
        for it in itens
    ]

    system_msg = (
        "Você é um auditor técnico-jurídico especializado em licitações, "
        "na Lei 14.133/2021 e nas Resoluções CNJ nº 651/2025 e nº 652/2025. "
        "Avalie se o EDITAL atende, de forma SEMÂNTICA, cada item do CHECKLIST. "
        "Considere sinônimos, redações equivalentes e conteúdo implícito. "
        "Se o conceito estiver presente mas incompleto, marque presente=true e adequacao_nota < 100, explicando. "
        "Se não houver evidência suficiente, presente=false e adequacao_nota=0. "
        "Responda EXCLUSIVAMENTE em JSON com o formato:\n"
        "{ 'itens': [ { 'id': '<id>', 'presente': true/false, 'adequacao_nota': 0-100, 'justificativa': 'texto curto', 'faltantes': [] } ] }"
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
        max_tokens=1800,
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
        nota = max(0, min(100, int(rmatch.get("adequacao_nota", 0))))

        if it["obrigatorio"]:
            notas.append(nota)

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
