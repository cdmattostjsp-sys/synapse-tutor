# knowledge/validators/validator_engine.py
# Engine unificado para rodar validações rígidas (checklist YAML)

from __future__ import annotations
from typing import List, Dict, Tuple
from pathlib import Path
import yaml

# Mapear artefatos suportados → arquivos checklist
SUPPORTED_ARTEFACTS = {
    "ETP": "knowledge/etp_checklist.yml",
    "TR": "knowledge/tr_checklist.yml",
    "CONTRATO": "knowledge/contrato_checklist.yml",
    "OBRAS": "knowledge/obras_checklist.yml",
}

def load_checklist(artefato: str) -> List[Dict]:
    """
    Carrega os itens do checklist YAML para o artefato.
    """
    path = SUPPORTED_ARTEFACTS.get(artefato.upper())
    if not path:
        raise ValueError(f"Artefato não suportado: {artefato}")
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data.get("itens", [])

def validate_document(artefato: str, doc_text: str) -> Tuple[float, List[Dict]]:
    """
    Valida documento contra checklist rígido (palavras-chave exatas).
    Retorna (score, results), onde:
      - score: % de itens obrigatórios encontrados
      - results: lista com campos: id, descricao, obrigatorio, presente
    """
    itens = load_checklist(artefato)
    if not itens:
        return 0.0, []

    doc_lower = doc_text.lower() if doc_text else ""
    results: List[Dict] = []
    obrigatorios = [it for it in itens if it.get("obrigatorio", True)]
    atendidos = 0

    for it in itens:
        termo = it["descricao"].split()[0].lower()  # pega primeira palavra como "âncora"
        presente = termo in doc_lower
        if it.get("obrigatorio", True) and presente:
            atendidos += 1

        results.append({
            "id": it["id"],
            "descricao": it["descricao"],
            "obrigatorio": bool(it.get("obrigatorio", True)),
            "presente": presente
        })

    score = round((atendidos / len(obrigatorios)) * 100, 1) if obrigatorios else 0.0
    return score, results
