# =========================================
# Synapse Tutor – Runner de Homologação via Código
# =========================================
# Permite executar testes automáticos do Synapse Tutor
# sem necessidade de interface Streamlit (útil para GitHub Codespaces / CI/CD)
# =========================================

import os
import json
from datetime import datetime
from validator_engine_vNext import validate_document
from utils.formatter_docx import markdown_to_docx

def run_tutor_testset(input_path: str, output_dir: str = "exports/tests"):
    """
    Executa um teste automatizado do Synapse Tutor.
    Lê respostas de um arquivo JSON, gera o DFD, executa validação e exporta resultados.
    """

    os.makedirs(output_dir, exist_ok=True)
    with open(input_path, "r", encoding="utf-8") as f:
        respostas = json.load(f)

    # Montagem do DFD base
    dfd_text = f"""
# Documento de Formalização da Demanda (DFD)
**Data:** {datetime.now():%d/%m/%Y}  
**Unidade Solicitante:** {respostas.get('unidade', 'Não informado')}  
**Responsável:** {respostas.get('responsavel', 'Não informado')}

## 1️⃣ Descrição do Objeto
{respostas.get('objeto', '')}

## 2️⃣ Justificativa da Necessidade
{respostas.get('justificativa', '')}

## 3️⃣ Quantidade, Urgência e Riscos
- Quantidade: {respostas.get('quantidade', '')}
- Urgência: {respostas.get('urgencia', '')}
- Riscos: {respostas.get('riscos', '')}

## 4️⃣ Alinhamento Institucional
{respostas.get('alinhamento', '')}

## 5️⃣ Documentos de Suporte
{respostas.get('suporte', '')}
"""

    print("🔍 Executando validação automática...")
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    vr = validate_document(dfd_text, "DFD", client)

    summary = vr.get("summary", "")
    enhanced = vr.get("guided_markdown", "")
    buffer, pdf_path = markdown_to_docx(enhanced, "DFD (Homologação)", summary)

    # Exportação dos resultados
    base_name = f"DFD_HOMOLOGACAO_{datetime.now():%Y%m%d_%H%M%S}"
    docx_path = os.path.join(output_dir, f"{base_name}.docx")
    json_path = os.path.join(output_dir, f"{base_name}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(vr, f, ensure_ascii=False, indent=2)

    with open(docx_path, "wb") as f:
        f.write(buffer)

    print(f"✅ Teste concluído! Resultados exportados para:\n{docx_path}\n{json_path}")

if __name__ == "__main__":
    run_tutor_testset("tests/sample_respostas.json")
