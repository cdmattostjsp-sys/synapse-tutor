import yaml
import os
import importlib
import pandas as pd

CHECKLIST_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")

def load_checklist(agent_name):
    filepath = os.path.join(CHECKLIST_DIR, f"{agent_name.lower()}_checklist.yml")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_validator(agent_name, document, semantic=False):
    checklist = load_checklist(agent_name)
    if not checklist:
        return None, None

    validator_module = f"knowledge.validators.{agent_name.lower()}_validator"
    try:
        validator = importlib.import_module(validator_module)
    except ModuleNotFoundError:
        return None, None

    df_rigido = validator.validate(document, checklist)

    df_sem = None
    if semantic:
        semantic_module = f"knowledge.validators.{agent_name.lower()}_semantic_validator"
        try:
            semantic_validator = importlib.import_module(semantic_module)
            df_sem = semantic_validator.validate(document, checklist)

            # 🔧 Garantir que todas as colunas necessárias existam
            required_cols = ["id", "descricao", "presente", "adequacao_nota", "status", "justificativa"]
            for col in required_cols:
                if col not in df_sem.columns:
                    if col in ["adequacao_nota"]:
                        df_sem[col] = 0
                    elif col in ["presente"]:
                        df_sem[col] = False
                    elif col in ["status"]:
                        df_sem[col] = "Ausente"
                    else:
                        df_sem[col] = ""

            # Reordenar colunas na saída
            df_sem = df_sem[required_cols]

        except ModuleNotFoundError:
            pass

    return df_rigido, df_sem
