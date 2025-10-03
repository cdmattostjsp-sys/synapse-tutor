from openai import OpenAI

def validate_semantic_dfd(text, checklist, client: OpenAI):
    """
    Executa a validação semântica do Documento de Formalização da Demanda (DFD).
    Retorna lista de dicionários com id, descricao, presente, adequacao_nota, status e justificativa.
    """
    prompt = f"""
    Você é um avaliador de conformidade de Documentos de Formalização da Demanda (DFD).
    Analise o texto abaixo e verifique se cada item do checklist está presente e adequado.

    Texto a validar:
    -----------------
    {text}
    -----------------

    Para cada item do checklist, retorne no formato JSON:
    - id: o identificador do item
    - descricao: a descrição do item do checklist
    - presente: true ou false
    - adequacao_nota: nota de 0 a 100 (quanto mais completo e adequado, maior a nota)
    - status: "Adequado", "Parcial" ou "Ausente"
    - justificativa: explicação objetiva sobre a avaliação
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Você é um avaliador jurídico especializado em contratações públicas."},
                  {"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=1200
    )

    import json
    try:
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception:
        return []
