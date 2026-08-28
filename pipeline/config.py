"""Language config loader — N corpora, one pipeline.

languages/<id>/config.yaml is the only per-language diff (~20 lines).
Ingest, unicode mapping, and comparative bridges read from here.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# repo root = two levels up from pipeline/
REPO_ROOT = Path(__file__).resolve().parent.parent
LANGUAGES_DIR = REPO_ROOT / "languages"


def config_path(language: str) -> Path:
    return LANGUAGES_DIR / language / "config.yaml"


def mapping_csv_path(language: str) -> Path | None:
    """Return mapping.csv path for language, or None if no mapping (alphabetic)."""
    cfg = load_config(language)
    rel = cfg.get("mapping")
    if not rel:
        return None
    # relative to languages/<id>/
    return LANGUAGES_DIR / language / rel


def load_config(language: str = "linear-a") -> dict[str, Any]:
    """Load languages/<language>/config.yaml."""
    p = config_path(language)
    if not p.exists():
        raise FileNotFoundError(f"Language config not found: {p}")
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def list_languages() -> list[str]:
    """List available language ids (subdirs with config.yaml)."""
    if not LANGUAGES_DIR.exists():
        return []
    return sorted(
        d.name for d in LANGUAGES_DIR.iterdir() if (d / "config.yaml").exists()
    )


def resolve_db_path(language: str = "linear-a", override: str | Path | None = None) -> Path:
    if override:
        return Path(override)
    cfg = load_config(language)
    rel = cfg.get("pipeline", {}).get("db", f"data/database/{language}.db")
    # db path is relative to repo root per plan
    return REPO_ROOT / rel


def resolve_corpus_paths(language: str = "linear-a") -> dict[str, Path | None]:
    """Return {'raw': Path, 'supplement': Path|None} resolved against repo root."""
    cfg = load_config(language)
    corpus = cfg.get("corpus", {})
    raw_rel = corpus.get("raw")
    supp_rel = corpus.get("supplement")
    out: dict[str, Path | None] = {}
    out["raw"] = (REPO_ROOT / raw_rel) if raw_rel else None
    out["supplement"] = (REPO_ROOT / supp_rel) if supp_rel else None
    out["format"] = corpus.get("format", "sigla-json")
    out["id_field"] = corpus.get("id_field", "name")
    return out  # type: ignore

def resolve_analysis_dir(language: str = "linear-a", analysis: str | None = None) -> Path:
    """Return analysis output dir for language. e.g. data/analysis/cypro-minoan or data/analysis/cypro-minoan/<analysis>"""
    base = REPO_ROOT / "data" / "analysis" / language if language != "linear-a" else REPO_ROOT / "data" / "analysis"
    if analysis:
        return base / analysis
    # for linear-a legacy: analysis subdir is category, e.g. positional
    # for other languages: nested under language
    if language == "linear-a":
        return REPO_ROOT / "data" / "analysis"
    return REPO_ROOT / "data" / "analysis" / language

def _resolve_db_and_out(common_language: str, db: str | None, out: str | None, default_db: str, default_out: str) -> tuple[str, str]:
    """Helper for CLI scripts: resolve --language vs explicit --db/--out."""
    if common_language and common_language != "linear-a":
        # resolve via config
        cfg_db = str(resolve_db_path(common_language)) if db is None else db
        # out: data/analysis/<lang>/<category>  (infer category from default_out basename)
        if out is None:
            cat = Path(default_out).name
            cfg_out = str(resolve_analysis_dir(common_language, cat))
        else:
            cfg_out = out
        return cfg_db, cfg_out
    return (db or default_db, out or default_out)
