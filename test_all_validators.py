"""
===============================================================================
TJSP - Tribunal de Justiça de São Paulo
Projeto: Synapse.IA – POC de Validação Automatizada
Arquivo: test_all_validators.py
Finalidade:
    Executa testes automáticos de validação (rígida e semântica)
    em todos os artefatos suportados pelo Synapse.IA,
    usando textos simulados baseados em documentos reais (Lei 14.133/2021).
===============================================================================
"""

from knowledge.validators.validator_engine import validate_document
from openai import OpenAI

# ---------------------------------------------------------------------------
# CLIENTE OPENAI
# ---------------------------------------------------------------------------
client = OpenAI()  # Usa a variável de ambiente OPENAI_API_KEY

# ---------------------------------------------------------------------------
# TEXTOS DE TESTE (simulações mais realistas)
# ---------------------------------------------------------------------------
documentos_teste = {
    "ETP": """
    Estudo Técnico Preliminar elaborado conforme a Lei nº 14.133/2021.
    O objeto visa a aquisição de equipamentos de informática destinados
    à modernização dos sistemas administrativos do TJSP.
    A necessidade está alinhada ao Plano de Contratações Anual (PCA)
    e ao Plano Estratégico Institucional (PEI 2021-2026),
    buscando eficiência e redução de custos operacionais.
    Foram realizadas pesquisas de preços em três fontes distintas.
    """,

    "TR": """
    Termo de Referência elaborado conforme Lei 14.133/2021 e Decreto Estadual 67.381/2022.
    Objeto: contratação de empresa especializada em suporte técnico de TI.
    Justificativa: necessidade de garantir disponibilidade dos sistemas críticos.
    Escopo: suporte remoto e presencial, atendimento 24x7.
    Critério de julgamento: menor preço global.
    Prazos: 12 meses de vigência, prorrogável conforme interesse público.
    Obrigações: acompanhamento por gestor e fiscal designado.
    """,

    "EDITAL": """
    O edital segue o rito da Lei 14.133/2021 e o Decreto Estadual 67.381/2022.
    Critério de julgamento: menor preço por item.
    A sessão pública ocorrerá na plataforma BEC/SP.
    O prazo para apresentação de propostas é de 10 dias úteis.
    Inclui minuta de contrato e anexos técnicos.
    """,

    "CONTRATO": """
    O presente contrato administrativo decorre do Edital nº 45/2025,
    regido pela Lei nº 14.133/2021.
    Objeto: aquisição de equipamentos de informática.
    Vigência: 12 meses.
    Garantia: 36 meses on-site.
    Penalidades: advertência, multa e rescisão contratual.
    Gestão: fiscal nomeado e gestor do contrato.
    """,

    "PESQUISA_PRECOS": """
    Pesquisa de preços realizada conforme o art. 23 da Lei 14.133/2021.
    Foram coletadas cotações de três fornecedores distintos,
    com análise de variação, média e mediana.
    As cotações foram obtidas via portal BEC/SP e sites oficiais.
    """,

    "DFD": """
    Documento de Formalização da Demanda (DFD) elaborado pela unidade requisitante.
    Necessidade: substituição de equipamentos de informática obsoletos.
    Justificativa: alinhamento ao Plano de Contratações Anual.
    Estimativa de valor baseada em pesquisa de preços.
    """,

    "PCA": """
    Plano de Contratações Anual (PCA) do exercício de 2025.
    Inclui todas as contratações previstas, alinhadas ao PEI e à LDO.
    Contém cronograma de execução, classificação por tipo de despesa e unidade gestora.
    """,

    "FISCALIZACAO": """
    A fiscalização será exercida por servidor designado como fiscal de contrato,
    com apoio do gestor responsável.
    Serão exigidas evidências documentais de cumprimento das obrigações.
    Haverá relatórios periódicos e verificação de indicadores de desempenho.
    """,

    "OBRAS": """
    O projeto executivo segue as normas técnicas da ABNT e a Lei 14.133/2021.
    Contém memorial descritivo, planilha orçamentária e cronograma físico-financeiro.
    Inclui ART do responsável técnico e previsão de mitigação de riscos.
    """,

    "MAPA_RISCOS": """
    Mapa de riscos elaborado conforme a Instrução Normativa nº 02/2021.
    Identificados riscos operacionais e financeiros com probabilidade e impacto.
    Definidas ações de mitigação e responsáveis por monitoramento.
    """,

    "CONTRATO_TECNICO": """
    Contrato de suporte técnico especializado.
    Regido pela Lei 14.133/2021.
    Define SLA, níveis de atendimento, penalidades e reajuste anual.
    Vigência de 12 meses, podendo ser prorrogado.
    """,

    "ITF": """
    Instrumento de Transferência de Fundos firmado entre órgãos do Poder Judiciário.
    Define objeto, metas, indicadores e cronograma de desembolso.
    Regido pela Lei 14.133/2021.
    """,
}

# ---------------------------------------------------------------------------
# EXECUÇÃO DOS TESTES
# ---------------------------------------------------------------------------
print("\n=== TESTE GLOBAL DE VALIDADORES SYNAPSE.IA ===\n")

for artefato, texto in documentos_teste.items():
    print(f"🧩 Testando artefato: {artefato}")
    resultado = validate_document(texto, artefato, client)

    print(f"   → Score rígido: {resultado['rigid_score']:.2f}")
    print(f"   → Score semântico: {resultado['semantic_score']:.2f}")

    if resultado["semantic_score"] > 0:
        amostra = resultado["semantic_result"][:2]  # mostra só 2 justificativas por artefato
        for item in amostra:
            print(f"      - {item['descricao']} → nota: {item.get('adequacao_nota', 0)} | justificativa: {item.get('justificativa', '')[:100]}...")
    print("------------------------------------------------------------")

print("\n✅ Teste global concluído. Todos os validadores executados.\n")
