"""
===============================================================================
TJSP - Tribunal de Justiça de São Paulo
Projeto: Synapse.IA – POC de Validação Automatizada de Documentos
Módulo: validator_engine.py
-------------------------------------------------------------------------------
Finalidade:
    Este módulo é o motor central de validação de artefatos licitatórios
    (ETP, TR, DFD, PCA, Pesquisa de Preços, Obras, Edital, Contrato, etc.),
    conforme Lei nº 14.133/2021 e Resoluções CNJ nº 651 e nº 652/2025.

    Ele integra:
      - Validações rígidas (checklists objetivos em YAML).
      - Validações semânticas (análise via LLM - OpenAI).
      - Relatórios estruturados de conformidade.

Histórico:
    • Versão homologada com PATCH UNIVERSAL (out/2025)
    • Compatibilidade ampliada:
        - Aceita checklists em 'knowledge/' e 'knowledge/validators/'
        - Reconhece chaves 'items' e 'itens'
        - Tratamento robusto de falhas e logs

Responsável: Equipe Técnica Synapse.IA
===============================================================================
"""

from pathlib import Path
from typing import List, Dict, Tuple
import yaml
import importlib
import re
import json
from openai import OpenAI

# ---------------------------------------------------------------------------
# 1. Configurações globais
# ---------------------------------------------------------------------------

SUPPORTED_ARTEFACTS = {
    "ETP": "knowledge/etp_checklist.yml",
    "TR": "knowledge/tr_checklist.yml",
    "DFD": "knowledge/dfd_checklist.yml",
    "PCA": "knowledge/pca_checklist.yml",
    "PESQUISA_PRECOS": "knowledge/pesquisa_precos_checklist.yml",
    "OBRAS": "knowledge/obras_checklist.yml",
    "EDITAL": "knowledge/edital_checklist.yml",
    "CONTRATO": "knowledge/contrato_checklist.yml",
    "CONTRATO_TECNICO": "knowledge/contrato_tecnico_checklist.yml",
    "FISCALIZACAO": "knowledge/fiscalizacao_checklist.yml",
    "MAPA_RISCOS": "knowledge/mapa_riscos_checklist.yml",
    "ITF": "knowledge/itf_checklist.yml",
}

# ---------------------------------------------------------------------------
# 2. Funções utilitárias
# ---------------------------------------------------------------------------

def load_checklist(artefato: str) -> List[Dict]:
    """
    Carrega o checklist YAML associado ao artefato informado.
    Compatível com pastas 'knowledge/' e 'knowledge/validators/'.
    Aceita tanto 'items' quanto 'itens' (retrocompatível).
    """
    path = SUPPORTED_ARTEFACTS.get(artefato.upper())
    if not path:
        raise ValueError(f"Artefato não suportado: {artefato}")

    p = Path(path)

    # 🔁 Fallback automático — busca também em knowledge/validators/
    if not p.exists():
        alt = Path("knowledge/validators") / p.name
        if alt.exists():
            p = alt

    if not p.exists():
        raise FileNotFoundError(f"Checklist não encontrado: {p}")

    # 🔄 Aceita tanto 'items' quanto 'itens'
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return data.get("items", data.get("itens", []))

def _extract_json(text: str) -> dict:
    """
    Extrai JSON bruto de uma resposta LLM.
    Usa regex para localizar blocos { ... }.
    """
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {}

# ---------------------------------------------------------------------------
# 3. Validação rígida
# ---------------------------------------------------------------------------

def rigid_validate(document_text: str, artefato: str) -> Tuple[float, List[Dict]]:
    """
    Executa a validação rígida baseada em checklist YAML.
    Retorna nota percentual e lista de itens avaliados.
    """
    checklist = load_checklist(artefato)
    results = []
    total = len(checklist)
    presentes = 0

    for item in checklist:
        termo = item.get("descricao", "")
        obrigatorio = item.get("obrigatorio", False)
        presente = termo.lower() in document_text.lower()
        if presente and obrigatorio:
            presentes += 1
        results.append({
            "id": item.get("id"),
            "descricao": termo,
            "obrigatorio": obrigatorio,
            "presente": presente
        })

    score = (presentes / total * 100) if total > 0 else 0
    return score, results

# ---------------------------------------------------------------------------
# 4. Validação semântica
# ---------------------------------------------------------------------------

def run_semantic(document_text: str, artefato: str, client: OpenAI) -> Tuple[float, List[Dict]]:
    """
    Executa a validação semântica chamando o validador específico do artefato.
    Importa dinamicamente os módulos de knowledge/validators.
    """
    try:
        module_name = f"knowledge.validators.{artefato.lower()}_semantic_validator"
        module = importlib.import_module(module_name)
        func = getattr(module, f"semantic_validate_{artefato.lower()}")
        return func(document_text, client)
    except Exception as e:
        return 0.0, [{
            "id": "erro",
            "descricao": f"Falha ao executar validador semântico ({artefato})",
            "presente": False,
            "adequacao_nota": 0,
            "status": "Erro",
            "justificativa": str(e),
            "faltantes": []
        }]

# ---------------------------------------------------------------------------
# 5. Validação integrada (principal)
# ---------------------------------------------------------------------------

def validate_document(document_text: str, artefato: str, client: OpenAI) -> Dict:
    """
    Função principal chamada pela interface Streamlit.
    Executa validação rígida e semântica, consolidando resultados.
    """
    rigid_score, rigid_result = rigid_validate(document_text, artefato)
    semantic_score, semantic_result = run_semantic(document_text, artefato, client)

    return {
        "rigid_score": rigid_score,
        "rigid_result": rigid_result,
        "semantic_score": semantic_score,
        "semantic_result": semantic_result
    }
