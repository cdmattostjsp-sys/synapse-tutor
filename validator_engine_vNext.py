# -*- coding: utf-8 -*-
"""
validator_engine_vNext.py
POC Synapse.IA – Engine de Validação e Geração de Rascunho
-------------------------------------------------------------------------------
Principais melhorias
- Leitura contextual da biblioteca local (knowledge_base/) por tipo de artefato.
- Prompt tuning com injeção de contextos (top-k snippets).
- Supressão de duplicidades: se as lacunas já estão listadas, não repetir
  na seção de “Marcadores para preenchimento”.
- Estrutura de retorno unificada para o front-end (sinapse_chat).
- Compatível com OpenAI (client passado pelo chamador) e seleção de modelo
  por variável de ambiente (OPENAI_MODEL), com fallback seguro.

Estrutura do retorno de validate_document():
{
  "rigid_score": float,   # 0..100
  "semantic_score": float,# 0..100
  "rigid_result": [ {id, descricao, obrigatorio, presente}... ],
  "semantic_result":[ {id, descricao, presente, adequacao_nota, justificativa, faltantes}... ],
  "guided_markdown": "texto markdown sem repetições",
  "guided_doc_title": "Rascunho Orientado – <tipo>",
  "debug": { "model": "...", "used_context_files": [...] }
}
-------------------------------------------------------------------------------
"""

from __future__ import annotations
import os
import re
import glob
import math
import json
import pathlib
from typing import Dict, List, Tuple, Any

# ---------------------------------------------------------------------------
# (1) utilitários de I/O
# ---------------------------------------------------------------------------

REPO_ROOT = pathlib.Path(__file__).resolve().parent
KB_ROOT = REPO_ROOT / "knowledge_base"

def _read_text_file(fp: pathlib.Path) -> str:
    try:
        return fp.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        try:
            return fp.read_text(encoding="latin-1", errors="ignore")
        except Exception:
            return ""

def _gather_kb_snippets(doc_type: str, topk: int = 10, max_chars: int = 6000) -> Tuple[str, List[str]]:
    """
    Lê textos de knowledge_base/<pasta_do_tipo> e seleciona os N primeiros por ordem de nome,
    concatenando até o limite de caracteres.
    """
    used_files: List[str] = []
    if not KB_ROOT.exists():
        return "", used_files

    # Mapeamento simples de tipo -> pasta. Se não houver match, usa raiz.
    folder_map = {
        "ETP": "ETP",
        "DFD": "DFD",
        "TR": "TR",
        "EDITAL": "instrucoes_normativas",
        "CONTRATO": "manuais_modelos"
    }
    folder = folder_map.get(doc_type.upper(), "")
    search_dir = KB_ROOT / folder if folder else KB_ROOT

    files = sorted(search_dir.rglob("*.txt")) + sorted(search_dir.rglob("*.md"))
    buff, count = [], 0
    size = 0
    for f in files:
        if count >= topk:
            break
        txt = _read_text_file(f)
        if not txt.strip():
            continue
        would = size + len(txt)
        buff.append(txt)
        used_files.append(str(f.relative_to(KB_ROOT)))
        size = would
        count += 1
        if size >= max_chars:
            break

    return "\n\n---\n".join(buff), used_files

# ---------------------------------------------------------------------------
# (2) prompts
# ---------------------------------------------------------------------------

BASE_SYSTEM = (
    "Você é um validador técnico do TJSP. Analise o texto fornecido e avalie dois conjuntos:\n"
    "1) Itens RÍGIDOS (checklist objetivo: presença/ausência de critérios obrigatórios)\n"
    "2) Itens SEMÂNTICOS (qualidade do conteúdo: presente/nota/justificativa/lacunas)\n"
    "Retorne JSON *válido* no formato solicitado SEM acrescentar comentários fora do JSON."
)

RIGID_CHECKLIST_ETP = [
    {"id": "referencia_normativa", "descricao": "Citar expressamente a Lei 14.133/2021 e normativos aplicáveis.", "obrigatorio": True},
    {"id": "justificativa", "descricao": "Justificar a contratação, alinhada ao PCA/PEI.", "obrigatorio": True},
    {"id": "alternativas", "descricao": "Apresentar estudo de alternativas possíveis com análise comparativa.", "obrigatorio": True},
    {"id": "especificacoes", "descricao": "Incluir especificações técnicas ou requisitos mínimos dos bens/serviços pretendidos.", "obrigatorio": True},
    {"id": "estimativa_custos", "descricao": "Apresentar estimativa de custos com metodologia e fontes.", "obrigatorio": True},
    {"id": "sustentabilidade", "descricao": "Incluir critérios de sustentabilidade e eficiência energética (quando aplicável).", "obrigatorio": False},
    {"id": "riscos_matriz", "descricao": "Apresentar matriz de riscos com responsáveis e mitigação.", "obrigatorio": True},
    {"id": "beneficios", "descricao": "Elencar benefícios esperados.", "obrigatorio": True},
    {"id": "avaliacao", "descricao": "Definir critérios de medição e avaliação.", "obrigatorio": True},
    {"id": "conclusao", "descricao": "Conclusão e recomendação final.", "obrigatorio": True},
]

SEMANTIC_GUIDE = (
    "Para cada critério, avalie:\n"
    "- presente: true/false\n"
    "- adequacao_nota: 0..100 (quanto o conteúdo atende)\n"
    "- justificativa: explique sucintamente\n"
    "- faltantes: lista de elementos concretos que faltam\n"
)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "rigid_score": {"type": "number"},
        "rigid_result": {"type": "array"},
        "semantic_score": {"type": "number"},
        "semantic_result": {"type": "array"},
        "lacunas_lista": {"type": "array"},  # lista consolidada de lacunas encontradas
    },
    "required": ["rigid_score", "rigid_result", "semantic_score", "semantic_result"]
}

# ---------------------------------------------------------------------------
# (3) core LLM call (com fallback de modelo)
# ---------------------------------------------------------------------------

def _pick_model() -> str:
    # Permite override por env
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def _chat_completion(client, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
    """
    Compatível com SDKs recentes. Tenta .chat.completions e faz fallback para .responses se existir.
    """
    model = _pick_model()
    # Tentativa 1 – interface chat tradicional
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content
    except Exception:
        pass

    # Tentativa 2 – interface responses (modelos novos)
    try:
        resp = client.responses.create(
            model=model,
            input=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return resp.output_text
    except Exception as e:
        raise RuntimeError(f"Falha ao consultar o modelo: {e}")

# ---------------------------------------------------------------------------
# (4) montagem do prompt e pós-processamento
# ---------------------------------------------------------------------------

def _build_user_prompt(doc_type: str, raw_text: str, kb_context: str) -> str:
    checklist = RIGID_CHECKLIST_ETP if doc_type.upper() == "ETP" else RIGID_CHECKLIST_ETP
    checklist_json = json.dumps(checklist, ensure_ascii=False, indent=2)
    schema_json = json.dumps(RESPONSE_SCHEMA, ensure_ascii=False)

    return (
        f"TIPO_DO_DOCUMENTO: {doc_type}\n\n"
        f"CHECKLIST_RIGIDO (JSON):\n{checklist_json}\n\n"
        f"GUIA_SEMANTICO:\n{SEMANTIC_GUIDE}\n\n"
        "Sua tarefa:\n"
        "1) Avaliar o texto do usuário (a seguir), aplicando o checklist rígido e a avaliação semântica.\n"
        "2) Calcular rigid_score = % de itens obrigatórios presentes.\n"
        "3) Calcular semantic_score = média das notas adequacao_nota (0..100).\n"
        "4) Retornar JSON estritamente aderente ao SCHEMA abaixo (sem comentários).\n\n"
        f"JSON_SCHEMA:\n{schema_json}\n\n"
        "=== CONTEXTO DE REFERÊNCIA (trechos relevantes da base local) ===\n"
        f"{kb_context}\n"
        "=== FIM DO CONTEXTO ===\n\n"
        "=== TEXTO DO USUÁRIO ===\n"
        f"{raw_text}\n"
        "=== FIM DO TEXTO ==="
    )

def _safe_json_loads(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        # tentativa de recuperar JSON em meio a texto
        m = re.search(r"\{.*\}", s, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        raise ValueError("Resposta do modelo não pôde ser convertida em JSON.")

def _suppress_marker_duplicates(lacunas: List[str], markers_section: str) -> str:
    """
    Remove marcadores duplicados quando já listados nas lacunas.
    Mantém a seção apenas se restarem marcadores distintos.
    """
    if not markers_section.strip():
        return ""

    # extrai os <<<INSERIR: ...>>> do texto
    found = re.findall(r"<<<INSERIR:\s*(.+?)\s*>>>", markers_section)
    if not found:
        return ""

    # normalização simples
    norm_lac = {re.sub(r"\W+", " ", i).strip().lower() for i in lacunas}
    kept = []
    for item in found:
        norm = re.sub(r"\W+", " ", item).strip().lower()
        if norm not in norm_lac:
            kept.append(item)

    if not kept:
        return ""  # tudo redundante – remove seção inteira

    lines = ["## 3) Marcadores para preenchimento no texto",
             "> Copie e cole os marcadores nos pontos adequados do documento, preenchendo com o conteúdo necessário.",
             ""]
    for k in kept:
        lines.append(f"<<<INSERIR: {k}.>>>")
    lines.append("")
    return "\n".join(lines)

def _build_guided_markdown(doc_type: str, raw_text: str, semantic_result: List[Dict[str, Any]]) -> Tuple[str, str]:
    title = f"Rascunho Orientado – {doc_type}"
    # 2.1) Lacunas consolidadas
    lacunas = []
    for it in semantic_result:
        if not it.get("presente"):
            d = it.get("descricao", "").strip()
            if d:
                lacunas.append(d)

    # 2.2) texto base (documento original)
    sec1 = [
        f"# {title}",
        "",
        "## 1) Documento Original",
        "> Use este texto como base e edite no Word, incluindo as marcações abaixo.",
        "",
        "---",
        raw_text.strip(),
        "---",
        ""
    ]

    # 2.3) seção 2 – lacunas
    sec2 = ["## 2) Lacunas Detectadas (inserir/ajustar)"]
    if lacunas:
        for l in lacunas:
            sec2.append(f"• {l}")
    else:
        sec2.append("Nenhuma lacuna obrigatória identificada.")
    sec2.append("")

    # 2.4) seção 3 – marcadores (sem duplicidades)
    # gera uma seção bruta de marcadores a partir das lacunas
    raw_markers = []
    for l in lacunas:
        raw_markers.append(f"<<<INSERIR: {l}.>>>")
    markers_md = ""
    if raw_markers:
        block = ["## 3) Marcadores para preenchimento no texto",
                 "> Copie e cole os marcadores nos pontos adequados do documento, preenchendo com o conteúdo necessário.",
                 ""]
        block.extend(raw_markers)
        block.append("")
        markers_md = "\n".join(block)

    # remove duplicidades (seção 3 só fica se tiver realmente algo diferente do item 2)
    markers_md = _suppress_marker_duplicates(lacunas, markers_md)

    # final
    guided_md = "\n".join(sec1 + sec2 + ([markers_md] if markers_md else []))
    return guided_md, title

# ---------------------------------------------------------------------------
# (5) API pública
# ---------------------------------------------------------------------------

def validate_document(raw_text: str, doc_type: str, client) -> Dict[str, Any]:
    """
    Executa a validação rígida e semântica e gera rascunho orientado (markdown).
    """
    # contextos da KB
    kb_text, used_files = _gather_kb_snippets(doc_type, topk=12, max_chars=9000)
    user_prompt = _build_user_prompt(doc_type, raw_text, kb_text)
    messages = [
        {"role": "system", "content": BASE_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]

    content = _chat_completion(client, messages, temperature=0.1)
    parsed = _safe_json_loads(content)

    # sanitização mínima
    rigid_result = parsed.get("rigid_result", [])
    semantic_result = parsed.get("semantic_result", [])
    rigid_score = float(parsed.get("rigid_score", 0.0))
    semantic_score = float(parsed.get("semantic_score", 0.0))

    # markdown guiado (sem repetições)
    guided_md, title = _build_guided_markdown(doc_type, raw_text, semantic_result)

    return {
        "rigid_score": max(0.0, min(100.0, rigid_score)),
        "semantic_score": max(0.0, min(100.0, semantic_score)),
        "rigid_result": rigid_result,
        "semantic_result": semantic_result,
        "guided_markdown": guided_md,
        "guided_doc_title": title,
        "debug": {
            "model": _pick_model(),
            "used_context_files": used_files
        }
    }
