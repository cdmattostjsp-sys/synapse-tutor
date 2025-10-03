from openai import OpenAI

def semantic_validate(text, client: OpenAI = None):
    """
    Validador semântico para Documento de Formalização da Demanda (DFD).
    Analisa o texto do DFD e retorna conformidade em relação a critérios qualitativos.
    """

    if client is None:
        client = OpenAI()

    # Prompt de análise semântica
    prompt = f"""
    Você é um especialista em licitações públicas e em normas do CNJ.
    Analise o seguinte DOCUMENTO DE FORMALIZAÇÃO DA DEMANDA (DFD) e dê notas de 0 a 10
    para cada critério abaixo, explicando brevemente o motivo:

    Texto do DFD:
    \"\"\"{text}\"\"\"

    Critérios:
    1. Clareza da Identificação da Unidade Demandante (se consta órgão, responsável, data).
    2. Clareza e objetividade do Objeto da Contratação (se está descrito sem ambiguidades).
    3. Adequação da Justificativa (se está alinhada ao planejamento institucional e fundamentada).

    Responda no seguinte formato JSON:
    [
      {{"id": "identificacao", "descricao": "Clareza da Identificação da Unidade Demandante", "adequacao_nota": X, "justificativa": "..." }},
      {{"id": "objeto", "descricao": "Clareza e objetividade do Objeto da Contratação", "adequacao_nota": X, "justificativa": "..." }},
      {{"id": "justificativa", "descricao": "Adequação da Justificativa", "adequacao_nota": X, "justificativa": "..." }}
    ]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # pode ser ajustado para outro modelo disponível
            messages=[
                {"role": "system", "content": "Você é um avaliador especializado em conformidade de documentos administrativos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        raw_output = response.choices[0].message.content

        import json
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            # fallback simples se vier em texto e não JSON válido
            data = [{
                "id": "erro",
                "descricao": "Não foi possível interpretar a resposta do modelo",
                "adequacao_nota": 0,
                "justificativa": raw_output
            }]

        return data

    except Exception as e:
        return [{
            "id": "erro",
            "descricao": "Falha na validação semântica do DFD",
            "adequacao_nota": 0,
            "justificativa": str(e)
        }]
