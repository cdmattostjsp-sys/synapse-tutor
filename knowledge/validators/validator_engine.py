# -*- coding: utf-8 -*-
# =============================================================================
# Synapse.IA – Validator Engine
# Versão POC 1.1 – Revisão de desempenho e lógica de validação (05/10/2025)
#
# O que há de novo:
# - Normalização robusta de texto para reduzir falsos-negativos no rígido.
# - Regex tolerantes para padrões frequentes (ex.: Lei 14.133/2021).
# - Validação semântica com análise profunda (gpt-4o, temperature=0).
# - Geração de "Documento Orientado" (Markdown) sem duplicidades.
# - Retorno estruturado compatível com synapse_chat.py:
#     rigid_score, rigid_result, semantic_score, semantic_result, improved_document
# =============================================================================
from __future__ import annotations

import os
import re
import glob
import json
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

# YAML
try:
    import yaml  # pyyaml
except Exception:
    yaml = None  # mantemos o engine funcional mesmo sem pyyaml (mas recomendamos instalar)

# OpenAI (SDK 2024+)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # o chamador deve informar o client válido


# =============================================================================
# Utilitários de normalização e suporte
# =============================================================================
def normalize_text(text: str) -> str:
    """Normaliza texto para melhorar matching no rígido."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)

    # Substituições comuns (Word/PDF)
    replacements = {
        "\u00A0": " ",   # non-breaking space
        "\u200B": "",    # zero width space
        "–": "-", "—": "-",  # dashes → hífen
        "“": '"', "”": '"', "‘": "'", "’": "'",  # aspas curvas → retas
    }
    for k, v in replacements.items():
        t = t.replace(k, v)

    # Colapsa múltiplos espaços e arruma quebras
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"\n\s+", "\n", t)
    return t


def remove_accents(s: str) -> str:
    """Remove acentos (opcional, quando se desejar matching mais agressivo)."""
    if not s:
        return s
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def slug_from_artefato(artefato: str) -> str:
    return artefato.strip().lower().replace(" ", "_")


# =============================================================================
# Carregamento do checklist (YAML)
# =============================================================================
def find_checklist_file(artefato: str) -> Optional[str]:
    """
    Procura o arquivo do checklist no padrão:
      knowledge/validators/{slug}_checklist*.yml
    e prioriza o nome "simples" se houver múltiplos.
    """
    base_dir = os.path.join("knowledge", "validators")
    slug = slug_from_artefato(artefato)
    candidates = glob.glob(os.path.join(base_dir, f"{slug}_checklist*.yml"))
    if candidates:
        candidates.sort(key=lambda p: (len(os.path.basename(p)), p))
        return candidates[0]
    default_path = os.path.join(base_dir, f"{slug}_checklist.yml")
    return default_path if os.path.exists(default_path) else None


def load_checklist(artefato: str) -> List[Dict[str, Any]]:
    """Carrega a lista de itens do checklist do artefato."""
    if yaml is None:
        return []
    path = find_checklist_file(artefato)
    if not path or not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Aceita "items", "itens" ou lista raiz
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "items" in data:
            return data.get("items") or []
        if "itens" in data:
            return data.get("itens") or []
    return []


# =============================================================================
# Validação Rígida
# =============================================================================
def build_tolerant_pattern(padrao: str) -> str:
    """
    Ajusta regex frequentes para ficarem mais tolerantes a variações de digitação.
    Exemplos simples incluídos; podem ser estendidos conforme as necessidades.
    """
    if not padrao:
        return ""

    # Lei 14.133/2021 – várias formas de aparecer
    if "14.133/2021" in padrao or "Lei 14.133" in padrao or "Lei nº 14.133" in padrao:
        # lei (opcional nº) 14(. ou espaço ou vírgula)133 / 2021
        return r"lei\s*(n[ºo]\s*)?14[\s\.\,]*133\s*\/\s*2021"

    # Decreto Estadual 67.381/2022
    if "67.381/2022" in padrao or "Decreto Estadual 67.381/2022" in padrao:
        return r"(decreto\s*(estadual)?\s*)?67[\s\.\,]*381\s*\/\s*2022"

    # Provimento CSM 2724/2023
    if "2724/2023" in padrao or "Provimento CSM 2724/2023" in padrao:
        return r"(provimento\s*csm\s*)?2724\s*\/\s*2023"

    # Resolução CNJ 651/2025
    if "651/2025" in padrao or "Resolução CNJ 651/2025" in padrao:
        return r"(resolu[cç][aã]o\s*cnj\s*)?651\s*\/\s*2025"

    # Resolução CNJ 652/2025
    if "652/2025" in padrao or "Resolução CNJ 652/2025" in padrao:
        return r"(resolu[cç][aã]o\s*cnj\s*)?652\s*\/\s*2025"

    # Em outros casos, mantém o padrão original
    return padrao


def rigid_validate(document_text: str, artefato: str) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Validação rígida: utiliza regex (padrões no YAML) com normalização robusta.
    """
    text = normalize_text(document_text or "")
    text_no_accents = remove_accents(text).lower()

    checklist = load_checklist(artefato)
    results: List[Dict[str, Any]] = []
    total = len(checklist) if checklist else 0
    hits = 0

    for item in (checklist or []):
        desc = item.get("descricao", "").strip()
        obrig = bool(item.get("obrigatorio", False))
        padrao = (item.get("padrao") or item.get("pattern") or "").strip()
        presente = False

        if padrao:
            # padrão tolerante
            rx = build_tolerant_pattern(padrao)
            try:
                if re.search(rx, text, flags=re.IGNORECASE | re.DOTALL):
                    presente = True
                else:
                    # fallback agressivo: remove acentos
                    if re.search(remove_accents(rx), text_no_accents, flags=re.IGNORECASE | re.DOTALL):
                        presente = True
            except re.error:
                # regex malformada no YAML → tenta contains simples (em textos normalizados)
                if rx.lower() in text.lower() or remove_accents(rx).lower() in text_no_accents:
                    presente = True
        else:
            # fallback heurístico mínimo: primeiras palavras significativas da descrição
            tokens = [w for w in re.split(r"\W+", desc.lower()) if len(w) > 4]
            presente = any(tok in text_no_accents for tok in tokens[:3])

        if presente:
            hits += 1

        results.append(
            {
                "id": item.get("id") or "",
                "descricao": desc,
                "obrigatorio": obrig,
                "presente": presente,
            }
        )

    score = (hits / total * 100.0) if total > 0 else 0.0
    return round(score, 1), results


# =============================================================================
# Validação Semântica (LLM – análise profunda)
# =============================================================================
SEMANTIC_SYSTEM = (
    "Você é um especialista em contratações públicas brasileiras e valida documentos "
    "conforme a Lei 14.133/2021, Decreto Estadual 67.381/2022, Provimentos CSM aplicáveis, "
    "e Resoluções CNJ 651/2025 e 652/2025. Responda de forma objetiva e auditável."
)

def semantic_validate(
    document_text: str,
    artefato: str,
    checklist: List[Dict[str, Any]],
    client: Optional[OpenAI],
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Avaliação semântica item a item usando LLM.
    Retorna lista padronizada + score (média das notas de adequação).
    """
    if client is None:
        return 0.0, []

    text = normalize_text(document_text or "")

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

    instructions = (
        "Avalie cada item do CHECKLIST no DOCUMENTO. "
        "Para cada item, devolva um objeto JSON com os campos: "
        "id (string), descricao (string), presente (bool), adequacao_nota (0-100, número), "
        "justificativa (string curta e específica) e faltantes (lista de strings objetivas, opcional). "
        "Responda SOMENTE uma lista JSON (sem comentários ou texto fora do JSON)."
    )

    user_content = f"""
DOCUMENTO:
\"\"\"{text}\"\"\"

CHECKLIST:
{json.dumps(itens, ensure_ascii=False, indent=2)}

{instructions}
"""

    try:
        # Análise profunda – gpt-4o (temperature 0 para consistência e auditabilidade)
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SEMANTIC_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
            max_tokens=2200,
        )
        raw = resp.choices[0].message.content or "[]"
        # Extrai JSON (alguns modelos incluem rodeios)
        m = re.search(r"\[.*\]", raw, flags=re.DOTALL)
        data = json.loads(m.group(0) if m else raw)
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []

    notas: List[float] = []
    for it in data:
        try:
            notas.append(float(it.get("adequacao_nota", 0) or 0.0))
        except Exception:
            notas.append(0.0)

    score = round(sum(notas) / len(notas), 1) if notas else 0.0
    return score, data


# =============================================================================
# Documento orientado (rascunho sem duplicidades)
# =============================================================================
def _dedup_preserving_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for s in items:
        k = s.strip()
        if not k:
            continue
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def generate_augmented_document(
    document_text: str,
    artefato: str,
    result_dict: Dict[str, Any],
) -> str:
    """
    Gera rascunho orientado (Markdown) com:
      1) Documento original (como base)
      2) Lacunas Detectadas (deduplicadas)
      3) Marcadores <<<INSERIR: ...>>> (deduplicados)
    """
    text = normalize_text(document_text or "")
    rigid = result_dict.get("rigid_result", []) or []
    sem = result_dict.get("semantic_result", []) or []

    # 2a. Faltas (rígidas ausentes)
    faltas: List[str] = []
    for r in rigid:
        if not r.get("presente"):
            fal = r.get("descricao", "(sem descrição)").strip()
            if fal:
                faltas.append(f"• {fal}")

    # 2b. Faltas (semânticas ausentes/nota baixa)
    for s in sem:
        pres = bool(s.get("presente"))
        try:
            nota = float(s.get("adequacao_nota", 0) or 0.0)
        except Exception:
            nota = 0.0
        if (not pres) or (nota < 60.0):
            desc = s.get("descricao", "(sem descrição)").strip()
            if desc:
                faltas.append(f"• {desc}")
            for ff in (s.get("faltantes") or []):
                if isinstance(ff, str) and ff.strip():
                    faltas.append(f"   - {ff.strip()}")

    faltas = _dedup_preserving_order(faltas)
    faltas_md = "\n".join(faltas) if faltas else "Nenhuma lacuna crítica detectada."

    # 3) Marcadores (deduplicados)
    marcadores: List[str] = []
    for r in rigid:
        if not r.get("presente"):
            d = r.get("descricao") or "Item incompleto"
            marcadores.append(f"<<<INSERIR: {d}>>>")
    for s in sem:
        pres = bool(s.get("presente"))
        try:
            nota = float(s.get("adequacao_nota", 0) or 0.0)
        except Exception:
            nota = 0.0
        if (not pres) or (nota < 60.0):
            d = s.get("descricao") or "Item semântico incompleto"
            marcadores.append(f"<<<INSERIR: {d}>>>")

    marcadores = _dedup_preserving_order(marcadores)
    marcadores_md = "\n".join(marcadores) if marcadores else "—"

    md = f"""# Rascunho Orientado – {artefato}

## 1) Documento Original
> Use este texto como base e edite no Word, incluindo as marcações abaixo.

---
{text}
---

## 2) Lacunas Detectadas (inserir/ajustar)
{faltas_md}

## 3) Marcadores para preenchimento no texto
> Copie e cole os marcadores nos pontos adequados do documento, preenchendo com o conteúdo necessário.

{marcadores_md}

---

> Dica: após preencher, volte ao Synapse.IA e rode a validação novamente.
"""
    return md.strip()


# =============================================================================
# Função principal (API consumida pelo Streamlit)
# =============================================================================
def validate_document(document_text: str, artefato: str, client: Optional[OpenAI]) -> Dict[str, Any]:
    """
    Retorna dicionário com:
      - rigid_score (float)
      - rigid_result (lista de itens rígidos)
      - semantic_score (float)
      - semantic_result (lista de itens semânticos)
      - improved_document (Markdown com lacunas e marcadores)
    """
    artefato = (artefato or "").strip().upper()
    text = document_text or ""
    checklist = load_checklist(artefato)

    rigid_score, rigid_result = rigid_validate(text, artefato)
    semantic_score, semantic_result = semantic_validate(text, artefato, checklist, client)

    payload: Dict[str, Any] = {
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
