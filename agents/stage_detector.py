"""
stage_detector.py
--------------------------------
Responsável por identificar em qual etapa da jornada o usuário se encontra:
- início (nenhum dado técnico)
- dfd_incomplete / dfd_ready
- etp_incomplete / etp_ready
- tr_incomplete / tr_ready
Com base no texto descritivo ou nos insumos fornecidos.
"""

import json
import os
import re
import yaml

# Caminho base do diretório journey
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "journey")

def detect_stage(user_input: str) -> str:
    """
    Analisa o texto de entrada do usuário e retorna o estágio atual da jornada.
    """
    user_input_lower = user_input.lower()

    # Regras simples baseadas em palavras-chave
    if any(word in user_input_lower for word in ["problema", "necessidade", "solicitação", "compra", "reparo", "substituição"]):
        if any(word in user_input_lower for word in ["etp", "estudo técnico", "termo de referência", "tr"]):
            return "etp_incomplete"
        if any(word in user_input_lower for word in ["dfd", "documento de formalização", "demanda"]):
            return "dfd_incomplete"
        return "inicio"

    if "dfd" in user_input_lower and "completo" in user_input_lower:
        return "dfd_ready"

    if "etp" in user_input_lower and "completo" in user_input_lower:
        return "etp_ready"

    if "tr" in user_input_lower and "completo" in user_input_lower:
        return "tr_ready"

    return "inicio"


def get_next_stage(current_stage: str) -> dict:
    """
    Consulta o arquivo journey_config.json para determinar a próxima etapa.
    """
    try:
        config_path = os.path.join(BASE_DIR, "journey_config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config["transitions"].get(current_stage, {})
    except Exception as e:
        return {"error": f"Erro ao carregar journey_config.json: {str(e)}"}


def get_required_fields(stage: str) -> list:
    """
    Retorna os campos mínimos exigidos para o documento em elaboração (DFD, ETP ou TR).
    """
    schema_path = os.path.join(BASE_DIR, "schemas", f"{stage}.min.json")
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("required_fields", [])
    except FileNotFoundError:
        return []
