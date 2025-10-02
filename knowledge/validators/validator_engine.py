import os
import yaml
import re
from openai import OpenAI

# Inicializa cliente OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ Chave da OpenAI não encontrada. Configure a variável OPENAI_API_KEY.")
client = OpenAI(api_key=api_key)

# Pasta onde estão os checklists
KNOWLEDGE_PATH = "knowledge"

# Carregar checklist de um artefato
def load_checklist(artefato):
    filepath = os.path.join(KNOWLEDGE_PATH, f"{artefato.lower()}_checklist.yml")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Checklist não encontrado para {artefato}: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Validador rígido (keywords)
def rigid_validate(artefato, texto):
    checklist = load_checklist(artefato)
    resultados = []
    atendidos = 0

    for item in checklist["itens"]:
        padrao = item["descricao"].split(":")[0].lower()
        presente = bool(re.search(padrao, texto.lower()))
        resultados.append({
            "id": item["id"],
            "descricao": item["descricao"],
            "obrigatorio": item["obrigatorio"],
            "presente": presente
        })
        if presente and item["obrigatorio"]:
            atendidos += 1

    obrigatorios = sum(1 for i in checklist["itens"] if i["obrigatorio"])
    score = (atendidos / obrigatorios * 100) if obrigatorios > 0 else 100
    return score, resultados

# Validador semântico (via GPT)
def semantic_validate(artefato, texto):
    checklist = load_checklist(artefato)
    prompt = f"""
Você é um avaliador especializado em licitações e contratos do setor público.
Analise o texto a seguir e verifique a presença e a qualidade dos seguintes itens do checklist {artefato}:

{yaml.dump(checklist['itens'], allow_unicode=True)}

Responda em JSON com a seguinte estrutura:
[
  {{
    "id": "...",
    "descricao": "...",
    "obrigatorio": true/false,
    "avaliacao": "presente/ausente/incompleto",
    "justificativa": "explicação breve"
  }}
]
Texto a ser avaliado:
---
{texto}
---
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Você é um avaliador jurídico especializado."},
                  {"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=1200
    )
    try:
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Erro na validação semântica: {e}"

# Função principal
def validate_document(artefato, texto, use_semantic=False):
    rigid_score, rigid_result = rigid_validate(artefato, texto)
    semantic_result = None
    if use_semantic:
        semantic_result = semantic_validate(artefato, texto)

    return {
        "artefato": artefato,
        "rigid_score": rigid_score,
        "rigid_result": rigid_result,
        "semantic_result": semantic_result
    }

# Artefatos suportados
SUPPORTED_ARTEFACTS = [
    "ETP",
    "TR",
    "CONTRATO",
    "OBRAS"
]
