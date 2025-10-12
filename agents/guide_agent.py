"""
guide_agent.py
--------------------------------
Agente tutor responsável por:
1. Ler o estágio atual detectado (via stage_detector).
2. Carregar perguntas do question_bank.yaml.
3. Gerar orientações dinâmicas para o usuário preencher lacunas.
"""

import os
import yaml
from .stage_detector import detect_stage, get_next_stage, get_required_fields

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "journey")

def load_questions(stage: str) -> dict:
    """
    Carrega as perguntas específicas para o estágio (DFD, ETP, TR).
    """
    try:
        path = os.path.join(BASE_DIR, "question_bank.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get(stage.lower(), {})
    except Exception as e:
        return {"error": f"Erro ao carregar question_bank.yaml: {str(e)}"}


def generate_guidance(user_input: str) -> dict:
    """
    Gera orientações personalizadas com base no estágio atual e no texto do usuário.
    """
    stage = detect_stage(user_input)
    next_stage = get_next_stage(stage)
    doc_type = next_stage.get("doc", "dfd")

    # Carregar perguntas do banco
    questions = load_questions(doc_type)
    required_fields = get_required_fields(doc_type)

    # Construir retorno
    guidance = {
        "etapa_atual": stage,
        "proximo_passo": next_stage.get("next", "fim"),
        "descricao_etapa": next_stage.get("descricao", ""),
        "documento_em_foco": doc_type.upper(),
        "campos_minimos": required_fields,
        "perguntas_recomendadas": questions
    }

    return guidance


if __name__ == "__main__":
    # Exemplo de teste local
    texto_exemplo = """
    Gostaria de registrar uma solicitação de compra de mesas de audiência
    para o Fórum de Sorocaba. As atuais estão danificadas e representam risco.
    """
    resposta = generate_guidance(texto_exemplo)
    print(resposta)

