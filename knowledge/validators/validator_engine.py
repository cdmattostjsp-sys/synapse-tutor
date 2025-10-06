# knowledge/validators/validator_engine.py
# v3.0 – Estável para POC: normalização robusta, validação rígida via YAML, validação semântica via LLM,
# retorno estruturado e geração de "documento orientado" (rascunho com lacunas).
from __future__ import annotations

import os, re, json, glob, unicodedata
from typing import Dict, Any, List, Tuple, Optional

try:
    import yaml
except Exception:
    yaml = None  # o Streamlit pode não ter pyyaml — mas recomendamos usar

# A POC usa OpenAI (biblioteca oficial de 2024+)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # tratado em runtime

# -----------------------------------------------------------
# Util: Normalização robusta para casar regex em textos colados
# -----------------------------------------------------------
def normalize_text(text: str) -> str:
    if not text:
        return ""
    # Normaliza unicode e substitui caracteres "problemáticos"
    t = unicodedata.normalize("NFKC", text)

    # substituições comuns em textos vindos de Word/PDF
    replacements = {
        "\u00A0": " ",   # non-breaking space
        "\u200B": "",    # zero width space
        "–": "-", "—": "-",  # dashes → hífen simples
        "“": '"', "”": '"', "‘": "'", "’": "'",  # aspas curvas → retas
    }
    for k, v in replacements.items():
        t = t.replace(k, v)

    # Colapsa múltiplos espaços/linhas
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"\n\s+", "\n", t)

    return t

# -----------------------------------------------------------
# Carregamento do checklist (YAML) por artefato
# -----------------------------------------------------------
def slug_from_artefato(artefato: str) -> str:
    return artefato.strip().lower().replace(" ", "_")

def find_checklist_file(artefato: str) -> Optional[str]:
    """
    Busca o arquivo YAML do checklist no padrão:
    knowledge/validators/{slug}_checklist*.yml
    """
    base_dir = os.path.join("knowledge", "validators")
    slug = slug_from_artefato(artefato)
    candidates = glob.glob(os.path.join(base_dir, f"{slug}_checklist*.yml"))
    if candidates:
        # escolhe o mais "simples" (sem sufixos) se existir
        candidates.sort(key=lambda x: (len(os.path.basename(x)), x))
        return candidates[0]
    # fallback (compatibilidade)
    path_default = os.path.join(base_dir, f"{slug}_checklist.yml")
    return path_default if os.path.exists(path_default) else None

def load_checklist(artefato: str) -> List[Dict[str, Any]]:
    if yaml is None:
        return []
    path = find_checklist_file(artefato)
    if not path or not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # aceita "items" ou "itens"
    items = data.get("items") if isinstance(data, dict) else None
    if items is None:
        items = data.get("itens") if isinstance(data, dict) else None
    # fallback: se o YAML estiver "solto" (sem chave raiz)
    if items is None and isinstance(data, list):
        items = data
    return items or []

# -----------------------------------------------------------
# Validação Rígida (regex do checklist)
# -----------------------------------------------------------
def build_tolerant_pattern(padrao: str) -> str:
    """
    Ajusta algumas regex comuns para serem mais tolerantes,
    por exemplo para lei 14.133/2021 escrita de formas variadas.
    """
    if not padrao:
        return ""
    # Exemplo específico (Lei 14.133/2021):
    lei_pattern = r"lei\s*(n[ºo]\s*)?14[\s\.\,]*133\s*\/\s*2021"
    if "14.133/2021" in padrao or "14.133/2021" in padrao:
        return lei_pattern
    return padrao

def rigid_validate(document_text: str, artefato: str) -> Tuple[float, List[Dict[str, Any]]]:
    text = normalize_text(document_text)
    checklist = load_checklist(artefato)
    results = []
    total = len(checklist) if checklist else 0
    hits = 0

    for item in checklist:
        desc = item.get("descricao", "")
        obrig = bool(item.get("obrigatorio", False))
        padrao = item.get("padrao", "") or item.get("pattern", "")
        presente = False

        if padrao:
            rx = build_tolerant_pattern(padrao)
            try:
                if re.search(rx, text, flags=re.IGNORECASE | re.DOTALL):
                    presente = True
            except re.error:
                # se a regex do YAML estiver inválida, tenta um contains simples
                presente = rx.lower() in text.lower()
        else:
            # fallback mínimo: contains da primeira palavra significativa
            tokens = [w for w in re.split(r"\W+", desc.lower()) if len(w) > 4]
            presente = any(tok in text.lower() for tok in tokens[:3])

        if presente:
            hits += 1

        results.append({
            "id": item.get("id") or "",
            "descricao": desc,
            "obrigatorio": obrig,
            "presente": presente
        })

    score = (hits / total * 100) if total > 0 else 0.0
    return round(score, 1), results

# -----------------------------------------------------------
# Validação Semântica (LLM)
# -----------------------------------------------------------
SEMANTIC_SYSTEM = (
    "Você é um assistente especializado em contratações públicas brasileiras "
    "e valida documentos segundo a Lei 14.133/2021 e resoluções CNJ 651/652/2025."
)

def semantic_validate(document_text: str, artefato: str, checklist: List[Dict[str, Any]], client: OpenAI) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Usa LLM para avaliar presença/adequação de cada item do checklist,
    retornando uma lista padronizada e um score médio.
    """
    if client is None:
        return 0.0, []

    text = normalize_text(document_text)
    itens = [
        {
            "id": i.get("id", f"item_{idx}"),
            "descricao": i.get("descricao", ""),
            "obrigatorio": bool(i.get("obrigatorio", False)),
        }
        for idx, i in enumerate(checklist or [])
    ]
    if not itens:
        return 0.0, []

    instr = (
        "Avalie cada item do checklist abaixo no DOCUMENTO fornecido. "
        "Para cada item, responda JSON com: id, descricao, presente (true/false), "
        "adequacao_nota (0 a 100), justificativa (curta), faltantes (lista opcional). "
        "Responda SOMENTE JSON em lista."
    )
    user_content = f"""
DOCUMENTO:
\"\"\"{text}\"\"\"

CHECKLIST (itens):
{json.dumps(itens, ensure_ascii=False, indent=2)}

{instr}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",  # rápido e suficiente para scoring
            messages=[
                {"role": "system", "content": SEMANTIC_SYSTEM},
                {"role": "user", "content": user_content}
            ],
            temperature=0.0,
            max_tokens=1600
        )
        raw = resp.choices[0].message.content or "[]"
        # Tenta extrair JSON (muitos modelos já retornam JSON puro)
        # Se vier com texto, extrai bloco de colchetes
        m = re.search(r"\[.*\]", raw, flags=re.DOTALL)
        data = json.loads(m.group(0) if m else raw)
        if not isinstance(data, list):
            data = []
    except Exception:
        # fallback conservador
        data = []

    # Score: média de adequacao_nota dos obrigatórios presentes; se nenhum presente, média geral
    notas = []
    for it in data:
        try:
            nota = float(it.get("adequacao_nota", 0) or 0)
        except Exception:
            nota = 0.0
        notas.append(nota)
    score = round(sum(notas) / len(notas), 1) if notas else 0.0
    return score, data

# -----------------------------------------------------------
# Documento orientado (rascunho com lacunas)
# -----------------------------------------------------------
def generate_augmented_document(document_text: str, artefato: str, result_dict: Dict[str, Any]) -> str:
    """
    Retorna um 'rascunho orientado' em Markdown: o texto original,
    seguido de um quadro de 'Lacunas Detectadas' com marcadores
    <<<INSERIR: ...>>> para orientar o preenchimento.
    """
    text = normalize_text(document_text)
    rigid = result_dict.get("rigid_result", []) or []
    sem = result_dict.get("semantic_result", []) or []

    faltas: List[str] = []
    # Rígidos ausentes
    for r in rigid:
        if not r.get("presente"):
            faltas.append(f"• {r.get('descricao','(sem descrição)')}")

    # Semânticos com nota baixa ou ausentes
    for s in sem:
        pres = bool(s.get("presente"))
        nota = float(s.get("adequacao_nota", 0) or 0.0)
        if (not pres) or (nota < 60):
            falt = s.get("faltantes") or []
            faltas.append(f"• {s.get('descricao','(sem descrição)')}")
            for ff in falt:
                faltas.append(f"   - {ff}")

    faltas_md = "\n".join(faltas) if faltas else "Nenhuma lacuna crítica detectada."

    draft = f"""# Rascunho Orientado – {artefato}

## 1) Documento Original
> Use este texto como base e edite no Word, incluindo as marcações abaixo.

---
{text}

---

## 2) Lacunas Detectadas (inserir/ajustar)
{faltas_md}

## 3) Marcadores para preenchimento no texto
> Copie e cole os marcadores nos pontos adequados do documento, preenchendo com o conteúdo necessário.

{"".join([f'<<<INSERIR: {d.get("descricao") or "Item incompleto"}>>>\n' for d in rigid if not d.get("presente")])}
{"".join([f'<<<INSERIR: {s.get("descricao") or "Item semântico incompleto"}>>>\n' for s in sem if (not s.get("presente")) or float(s.get("adequacao_nota",0) or 0) < 60])}

---

> Dica: após preencher, volte ao Synapse.IA e rode a validação novamente.
"""
    return draft.strip()

# -----------------------------------------------------------
# Função principal
# -----------------------------------------------------------
def validate_document(document_text: str, artefato: str, client: Optional[OpenAI]) -> Dict[str, Any]:
    """
    Retorna dicionário com:
      - rigid_score (float)
      - rigid_result (lista de itens rígidos)
      - semantic_score (float)
      - semantic_result (lista de itens semânticos)
      - improved_document (Markdown com lacunas)
    """
    artefato = artefato.strip().upper()
    text = document_text or ""
    checklist = load_checklist(artefato)

    rigid_score, rigid_result = rigid_validate(text, artefato)
    semantic_score, semantic_result = semantic_validate(text, artefato, checklist, client)

    payload = {
        "rigid_score": rigid_score,
        "rigid_result": rigid_result,
        "semantic_score": semantic_score,
        "semantic_result": semantic_result,
    }

    try:
        payload["improved_document"] = generate_augmented_document(text, artefato, payload)
    except Exception:
        payload["improved_document"] = text or ""

    return payload
