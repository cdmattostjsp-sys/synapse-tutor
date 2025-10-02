# knowledge/validators/validator_engine.py
# Engine unificado para rodar validações rígidas (checklist YAML) e opcionais (semântica via LLM)

from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import yaml

# Importa validadores semânticos disponíveis
from knowledge.validators.semantic_validator import semantic_validate_etp
from knowledge.validators.tr_semantic_validator import semantic_validate_tr
from knowledge.validators.contrato_semantic_validator import semantic_validate_contrato
# (futuramente: obras_semantic_validator)

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

def rigid_validate(artefato: str, doc_text: str) -> Dict:
    """
    Validação RÍGIDA (checagem simples por palavras-chave).
    Retorna dict com score e resultados item a item.
    """
    itens = load_checklist(artefato)
    if not itens:
        return {"score": 0.0, "results": []}

    doc_lower = doc_text.lower() if doc_text else ""
    results: List[Dict] = []
    obrigatorios = [it for it in itens if it.get("obrigatorio", True)]
    atendidos = 0

    for it in itens:
        termo = it["descricao"].split()[0].lower()  # pega primeira palavra como âncora
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
    return {"score": score, "results": results}

def validate_document(artefato: str, doc_text: str, use_semantic: bool = False, client=None) -> Dict:
    """
    Engine unificado de validação.
    Retorna sempre um dicionário com score rígido e semântico (se solicitado).
    """
    # --- Rígido ---
    rigid = rigid_validate(artefato, doc_text)

    semantic_score = 0.0
    semantic_result: List[Dict] = []

    # --- Semântico (opcional) ---
    if use_semantic and client is not None:
        try:
            if artefato.upper() == "ETP":
                semantic_score, semantic_result = semantic_validate_etp(doc_text, client)
            elif artefato.upper() == "TR":
                semantic_score, semantic_result = semantic_validate_tr(doc_text, client)
            elif artefato.upper() == "CONTRATO":
                semantic_score, semantic_result = semantic_validate_contrato(doc_text, client)
            elif artefato.upper() == "OBRAS":
                semantic_result = [{"id": "info", "descricao": "Validação semântica para OBRAS ainda não implementada."}]
        except Exception as e:
            semantic_result = [{"id": "erro", "descricao": f"Erro na validação semântica: {e}"}]

    return {
        "rigid_score": rigid["score"],
        "rigid_result": rigid["results"],
        "semantic_score": semantic_score,
        "semantic_result": semantic_result,
    }
