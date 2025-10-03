# knowledge/validators/dfd_semantic_validator.py
# Validador semântico para DFD: usa LLM para avaliar presença e adequação de critérios básicos.

from __future__ import annotations
from typing import List, Dict, Tuple
from openai import OpenAI
import json
import re

def _extract_json(s: str) -> list:
    """
    Extrai JSON válido da resposta do modelo.
    Retorna sempre uma lista de dicionários.
    """
    s = s.strip().strip("`").replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(s)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "itens" in data:
            return data["itens"]
    except Exception:
        pass

    # fallback regex
    m = re.search(r"(\[.*\])", s, flags=re.S)
    if m:
        return json.loads(m.group(1))

    raise ValueError("❌ Não foi possível extrair JSON válido da resposta do modelo.")

def semantic_validate_dfd(doc_text: str, client: OpenAI) -> Tuple[float, List[Dict]]:
    """
    Retorna (score, results), onde:
      - score: média das notas (0..100) atribuídas aos critérios avaliados
      - results: lista com id, descricao, presente, adequacao_nota, justificativa
    """
    if not doc_text.strip():
        return 0.0, []

    system_msg = (
        "Você é um avaliador técnico especializado em conformidade administrativa e Resoluções CNJ. "
        "Analise o DOCUMENTO DE FORMALIZAÇÃO DA DEMANDA (DFD) e dê notas de 0 a 100 "
        "para cada critério, explicando em até 3 frases."
    )

    user_msg = f"""
    Documento (DFD):
    \"\"\"{doc_text}\"\"\"

    Critérios:
    1. Clareza da Identificação da Unidade Demandante (se consta órgão, responsável, data).
    2. Clareza e objetividade do Objeto da Contratação (se está descrito sem ambiguidades).
    3. Adequação da Justificativa (se está alinhada ao planejamento institucional e fundamentada).

    Responda SOMENTE em JSON no formato:
    [
      {{"id": "identificacao", "descricao": "Clareza da Identificação da Unidade Demandante", "adequacao_nota": X, "justificativa": "..."}},
      {{"id": "objeto", "descricao": "Clareza e objetividade do Objeto da Contratação", "adequacao_nota": X, "justificativa": "..."}},
      {{"id": "justificativa", "descricao": "Adequação da Justificativa", "adequacao_nota": X, "justificativa": "..."}}
    ]
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.2,
            max_tokens=1000
        )

        raw = resp.choices[0].message.content
        parsed = _extract_json(raw)

        results: List[Dict] = []
        notas = []

        for item in parsed:
            nota = max(0, min(100, int(item.get("adequacao_nota", 0))))
            notas.append(nota)

            results.append({
                "id": item.get("id", ""),
                "descricao": item.get("descricao", ""),
                "presente": nota > 0,
                "adequacao_nota": nota,
                "justificativa": item.get("justificativa", ""),
            })

        score = round(sum(notas) / len(notas), 1) if notas else 0.0
        return score, results

    except Exception as e:
        return 0.0, [{
            "id": "erro",
            "descricao": "Falha na validação semântica do DFD",
            "presente": False,
            "adequacao_nota": 0,
            "justificativa": str(e)
        }]
