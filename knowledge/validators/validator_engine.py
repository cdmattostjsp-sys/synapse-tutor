# knowledge/validators/validator_engine.py
# Engine unificado para rodar validações rígidas (checklist YAML) e opcionais (semântica via LLM)
from __future__ import annotations
from typing import List, Dict, Tuple
from pathlib import Path
import yaml

# Importa validadores semânticos disponíveis
from knowledge.validators.semantic_validator import semantic_validate_etp
from knowledge.validators.tr_semantic_validator import semantic_validate_tr
from knowledge.validators.contrato_semantic_validator import semantic_validate_contrato
from knowledge.validators.obras_semantic_validator import semantic_validate_obras
# futuramente: dfd_semantic_validator etc.

# Mapear artefatos suportados → arquivos checklist
SUPPORTED_ARTEFACTS = {
    "ETP": "knowledge/etp_checklist.yml",
    "TR": "knowledge/tr_checklist.yml",
    "CONTRATO": "knowledge/contrato_checklist.yml",
    "OBRAS": "knowledge/obras_checklist.yml",
    "DFD": "knowledge/dfd_checklist.yml",
    "CONTRATO_TECNICO": "knowledge/contrato_checklist.yml"  # usa o mesmo checklist por enquanto
}

def load_checklist(artefato: str) -> List[Dict]:
    """
    Carrega os itens do checklist YAML para o artefato.
    """
    path = SUPPORTED_ARTEFACTS.get(artefato.upper())
    if not path:
        return []
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

def run_semantic(artefato: str, doc_text: str, client) -> Tuple[float, List[Dict]]:
    """
    Seleciona o validador semântico correto para o artefato.
    """
    artefato_up = artefato.upper()
    if artefato_up == "ETP":
        return semantic_validate_etp(doc_text, client)
    elif artefato_up == "TR":
        return semantic_validate_tr(doc_text, client)
    elif artefato_up == "CONTRATO":
        return semantic_validate_contrato(doc_text, client)
    elif artefato_up == "OBRAS":
        return semantic_validate_obras(doc_text, client)
    elif artefato_up == "DFD":
        # futuramente semantic_validate_dfd
        return 0.0, [{"id": "info", "descricao": "Validação semântica para DFD ainda não implementada."}]
    elif artefato_up == "CONTRATO_TECNICO":
        # reutiliza contrato por enquanto
        return semantic_validate_contrato(doc_text, client)
    else:
        return 0.0, [{"id": "info", "descricao": f"Validação semântica para {artefato} ainda não implementada."}]

def validate_document(artefato: str, doc_text: str, use_semantic: bool = False, client=None) -> Dict:
    """
    Engine unificado de validação.
    Retorna sempre um dicionário com score rígido e semântico (se solicitado).
    """
    # --- Rígido ---
    rigid = rigid_validate(artefato, doc_text)

    # --- Semântico ---
    semantic_score = 0.0
    semantic_result: List[Dict] = []
    if use_semantic and client is not None:
        try:
            semantic_score, semantic_result = run_semantic(artefato, doc_text, client)
        except Exception as e:
            semantic_result = [{"id": "erro", "descricao": f"Erro na validação semântica: {e}"}]

    # --- Compatibilidade com synapse_chat.py ---
    return {
        "rigid_score": rigid.get("score", 0.0),
        "rigid_result": rigid.get("results", []),
        "semantic_score": semantic_score,
        "semantic_result": semantic_result,
    }
