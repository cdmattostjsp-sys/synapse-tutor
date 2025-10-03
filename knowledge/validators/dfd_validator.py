import yaml
import os

def load_checklist():
    base_dir = os.path.dirname(__file__)
    checklist_path = os.path.join(base_dir, "dfd_checklist.yml")
    with open(checklist_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_rigid(document_text: str):
    """
    Validação Rígida (checagem literal).
    Verifica se os itens obrigatórios estão presentes no texto.
    """
    checklist = load_checklist()
    results = []
    for item in checklist:
        presente = item["palavra_chave"].lower() in document_text.lower()
        results.append({
            "id": item["id"],
            "descricao": item["descricao"],
            "obrigatorio": item.get("obrigatorio", True),
            "presente": presente
        })
    return results

def validate_semantic(document_text: str, client=None):
    """
    Validação Semântica (checagem com IA).
    Aqui você pode integrar com modelo de linguagem para validar por similaridade.
    """
    checklist = load_checklist()
    results = []
    for item in checklist:
        # Placeholder: por enquanto marca todos como não implementados
        results.append({
            "id": item["id"],
            "descricao": item["descricao"],
            "presente": False,
            "adequacao_nota": 0,
            "status": "Não implementado",
            "justificativa": "Validação semântica para este item ainda não implementada."
        })
    return results
