def validate_rigid(document_text: str):
    return [{
        "id": "placeholder",
        "descricao": "Validação rígida ainda não implementada para este agente.",
        "obrigatorio": False,
        "presente": False
    }]

def validate_semantic(document_text: str, client=None):
    return [{
        "id": "placeholder",
        "descricao": "Validação semântica ainda não implementada para este agente.",
        "presente": False,
        "adequacao_nota": 0,
        "status": "Não implementado",
        "justificativa": "A validação será adicionada futuramente."
    }]
