# =========================================
# Synapse Tutor – Módulo de Exemplos Pedagógicos (v2.8)
# =========================================

def build_example_snippets(lacunas: list[str]) -> dict:
    """
    Gera exemplos ilustrativos (não vinculantes) com base nas lacunas detectadas.
    Retorna um dicionário {tema: exemplo_textual}.
    """

    exemplos = {}
    for lacuna in lacunas:
        if "Lei 14.133" in lacuna:
            exemplos[lacuna] = (
                "🧩 Exemplo ilustrativo (não vinculante): "
                "“A presente demanda atende ao disposto no art. 18 da Lei nº 14.133/2021, "
                "que prevê a elaboração prévia do Documento de Formalização da Demanda como "
                "instrumento essencial ao planejamento da contratação.”"
            )
        elif "especificações técnicas" in lacuna:
            exemplos[lacuna] = (
                "🧩 Exemplo ilustrativo: “As mesas deverão ser confeccionadas em madeira tipo mogno, "
                "com espessura mínima de 3 cm e acabamento em verniz fosco, garantindo durabilidade e segurança.”"
            )
        elif "estimativa de custos" in lacuna:
            exemplos[lacuna] = (
                "🧩 Exemplo ilustrativo: “A estimativa orçamentária foi realizada com base em três cotações de mercado, "
                "obtidas junto a fornecedores locais, totalizando o valor médio de R$ 18.500,00.”"
            )
        elif "sustentabilidade" in lacuna:
            exemplos[lacuna] = (
                "🧩 Exemplo ilustrativo: “A aquisição priorizará materiais provenientes de manejo sustentável, "
                "observando critérios de eficiência energética e redução de resíduos.”"
            )
        else:
            exemplos[lacuna] = (
                f"🧩 Exemplo ilustrativo: “Descreva informações complementares para a seção relacionada a '{lacuna}'.”"
            )

    return exemplos
