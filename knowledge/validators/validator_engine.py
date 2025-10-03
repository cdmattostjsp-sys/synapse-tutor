# knowledge/validators/validator_engine.py
# Engine unificado para rodar validações rígidas (checklist YAML) e semânticas (LLM)

from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import yaml

# Importa validadores semânticos específicos
from knowledge.validators.etp_semantic_validator import semantic_validate_etp
from knowledge.validators.tr_semantic_validator import semantic_validate_tr
from knowledge.validators.contrato_semantic_validator import semantic_validate_contrato
from knowledge.validators.obras_semantic_validator import semantic_validate_obras
from knowledge.validators.dfd_semantic_validator import semantic_validate_dfd
from knowledge.validators.pca_semantic_validator import semantic_validate_pca
from knowledge.validators.pesquisa_precos_semantic_validator import semantic_validate_pesquisa_precos
from knowledge.validators.edital_semantic_validator import semantic_validate_edital
from knowledge.validators.fiscalizacao_semantic_validator import semantic_validate_fiscalizacao
from knowledge.validators.itf_semantic_validator import semantic_validate_itf
from knowledge.validators.mapa_riscos_semantic_validator import semantic_validate_mapa_riscos

# Mapear artefatos suportados → arquivos checklist
SUPPORTED_ARTEFACTS = {
    "ETP": "knowledge/etp_checklist.yml",
    "TR": "knowledge/tr_checklist.yml",
    "CONTRATO": "knowledge/contrato_checklist.yml",
    "CONTRATO_TECNICO": "knowledge/contrato_tecnico_checklist.yml",
    "OBRAS": "knowledge/obras_checklist.yml",
    "DFD": "knowledge/dfd_checklist.yml",
    "PCA": "knowledge/pca_checklist.yml",
    "PESQUISA_PRECOS": "knowledge/pesquisa_precos_checklist.yml",
    "EDITAL": "knowledge/edital_checklist.yml",
    "FISCALIZACAO": "knowledge/fiscalizacao_checklist.yml",
    "ITF": "knowledge/itf_checklist.yml",
    "MAPA_RISCOS": "knowledge/mapa_riscos_checklist.yml",
}

# --------------------------------------------------------------------
# Funções auxiliares
# --------------------------------------------------------------------

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

# --------------------------------------------------------------------
# Semântico (seleciona validador correto)
# --------------------------------------------------------------------
def run_semantic(artefato: str, doc_text: str, client) -> (float, List[Dict]):
    """
    Seleciona e executa a validação semântica apropriada.
    """
    artefato = artefato.upper()

    if artefato == "ETP":
        return semantic_validate_etp(doc_text, client)
    elif artefato == "TR":
        return semantic_validate_tr(doc_text, client)
    elif artefato == "CONTRATO":
        return semantic_validate_contrato(doc_text, client)
    elif artefato == "CONTRATO_TECNICO":
        # pode usar o mesmo validador de contrato até criar um específico
        return semantic_validate_contrato(doc_text, client)
    elif artefato == "OBRAS":
        return semantic_validate_obras(doc_text, client)
    elif artefato == "DFD":
        return semantic_validate_dfd(doc_text, client)
    elif artefato == "PCA":
        return semantic_validate_pca(doc_text, client)
    elif artefato == "PESQUISA_PRECOS":
        return semantic_validate_pesquisa_precos(doc_text, client)
    elif artefato == "EDITAL":
        return semantic_validate_edital(doc_text, client)
    elif artefato == "FISCALIZACAO":
        return semantic_validate_fiscalizacao(doc_text, client)
    elif artefato == "ITF":
        return semantic_validate_itf(doc_text, client)
    elif artefato == "MAPA_RISCOS":
        return semantic_validate_mapa_riscos(doc_text, client)

    return 0.0, [{"id": "info", "descricao": f"Validação semântica para {artefato} ainda não implementada."}]

# --------------------------------------------------------------------
# Engine Unificado
# --------------------------------------------------------------------
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
            semantic_score, semantic_result = run_semantic(artefato, doc_text, client)
        except Exception as e:
            semantic_result = [{"id": "erro", "descricao": f"Erro na validação semântica: {e}"}]

    return {
        "rigid_score": rigid["score"],
        "rigid_result": rigid["results"],
        "semantic_score": semantic_score,
        "semantic_result": semantic_result,
    }
