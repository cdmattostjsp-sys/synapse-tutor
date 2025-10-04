"""
Teste rápido para validar o funcionamento do validator_engine.py
Autor: Synapse.IA - TJSP
Data: outubro/2025
"""

from knowledge.validators.validator_engine import validate_document
from openai import OpenAI

# 1. Inicializa o cliente OpenAI (usa a variável de ambiente OPENAI_API_KEY)
client = OpenAI()

# 2. Documento de teste (texto simples, só para simular)
documento_exemplo = """
Este é um Termo de Referência (TR) fictício.
Ele descreve requisitos, justificativa, objeto e prazo.
"""

# 3. Artefato que vamos testar (pode trocar para "ETP", "EDITAL", "CONTRATO" etc.)
artefato = "TR"

# 4. Executa validação
resultado = validate_document(documento_exemplo, artefato, client)

# 5. Exibe resultados no terminal
print("\n=== RESULTADO DO TESTE ===")
print(f"Artefato testado: {artefato}")
print(f"Score rígido: {resultado['rigid_score']:.2f}")
print(f"Score semântico: {resultado['semantic_score']:.2f}")
print("\nItens avaliados (rígidos):")
for item in resultado["rigid_result"]:
    print(f" - {item['descricao']} → presente: {item['presente']}")

print("\nItens avaliados (semânticos):")
for item in resultado["semantic_result"]:
    print(f" - {item['descricao']} → nota: {item.get('adequacao_nota', 0)} | justificativa: {item.get('justificativa', '')}")
