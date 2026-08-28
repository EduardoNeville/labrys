#!/usr/bin/env python3
"""
Generic ingest — one pipeline, N corpora.

    uv run python -m pipeline.ingest --language linear-a
    uv run python pipeline/ingest.py --language linear-a --db /tmp/test.db

Reads languages/<id>/config.yaml for period_map/support_map/corpus paths
and delegates to ingest_lineara parsing. Monkey-patches ingest_lineara
globals so all callers are fixed in one place (root-cause, not per-caller).

ponytail: wrapper, not rewrite; ingest_lineara.py stays canonical for linear-a
until next language needs a divergent JSON format — then extract.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# allow `python pipeline/ingest.py` direct execution
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.config import load_config, resolve_corpus_paths, resolve_db_path
from pipeline.database import LinearADatabase
from pipeline.unicode_utils import validate_mapping, validate_mapping_for_language

import ingest_lineara as la

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def ingest_language(
    language: str = "linear-a",
    raw_override: str | Path | None = None,
    supplement_override: str | Path | None = None,
    db_override: str | Path | None = None,
) -> Path:
    cfg = load_config(language)
    corpus = resolve_corpus_paths(language)
    raw_path = Path(raw_override) if raw_override else corpus["raw"]
    supp_path = Path(supplement_override) if supplement_override else corpus["supplement"]  # type: ignore
    db_path = resolve_db_path(language, db_override)

    # Apply config maps to the shared parser — one patch covers every caller.
    ingest_cfg = cfg.get("ingest", {})
    if ingest_cfg.get("period_map"):
        la.PERIOD_MAP = ingest_cfg["period_map"]
    if ingest_cfg.get("support_map"):
        la.SUPPORT_MAP = ingest_cfg["support_map"]

    # Ensure DB dir exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # ---- switch Unicode mapping to requested language (CSV-driven) ----
    if language != "linear-a":
        try:
            from pipeline.unicode_utils import use_language_mapping
            use_language_mapping(language)
        except Exception as _e:  # noqa: BLE001
            logger.warning("Failed to switch mapping for %s: %s (using linear-a fallback)", language, _e)

    # ---- validate mapping (CSV-driven if present) ----
    errors = validate_mapping_for_language(language) if language != "linear-a" else validate_mapping()
    if errors:
        logger.warning("Mapping validation: %d error(s)", len(errors))
        for e in errors[:5]:
            logger.warning("  %s", e)
    else:
        logger.info("Mapping: %d entries OK (%s)", len(la.validate_mapping.__code__.co_consts), language)  # fallback
        from pipeline.unicode_utils import BENNETT_TO_UNICODE

        logger.info("Mapping entries: %d", len(BENNETT_TO_UNICODE))

    # ---- load raw ----
    if raw_path is None or not Path(raw_path).exists():
        raise FileNotFoundError(f"Raw corpus not found for {language}: {raw_path}")

    raw_entries = la.load_inscriptions_json(str(raw_path))
    supp_data = {}
    if supp_path and Path(supp_path).exists():
        supp_data = la.load_supplement(str(supp_path))
        logger.info("Loaded %d raw + %d supplement", len(raw_entries), len(supp_data))
    else:
        logger.info("Loaded %d raw (no supplement)", len(raw_entries))

    # ---- parse ----
    inscriptions = []
    failed = 0
    if cfg.get("mapping") is None:  # alphabet languages: eteocretan, eteocypriot (mapping: null) — each letter/syllable = syllabogram for generic pipeline
        # Alphabetic language: each latin letter = a sign (no Bennett lookup)
        from pipeline.models import Inscription, Findspot, DateInfo, SignInstance
        for entry in raw_entries:
            try:
                if isinstance(entry, list) and len(entry) >= 2:
                    eid, edata = str(entry[0]), entry[1]
                elif isinstance(entry, dict):
                    eid = entry.get("name", entry.get("gorilaId", "UNKNOWN"))
                    edata = entry
                else:
                    failed += 1
                    continue
                # Findspot / Site
                site = edata.get("site", "") or edata.get("findspot", "") or "Unknown"
                findspot_str = edata.get("findspot", "")
                full_site = site
                if findspot_str and findspot_str != site:
                    full_site = f"{site} - {findspot_str}" if site else findspot_str
                from pipeline.models import Findspot as _Findspot
                findspot = _Findspot(site=full_site or site or "Unknown")
                # Date / Period
                context = edata.get("context", "")
                period = la.PERIOD_MAP.get(context, context if context else "Uncertain")
                from pipeline.models import DateInfo as _DateInfo
                date_info = _DateInfo(minoanPeriod=period)
                # Material & Object Type
                support = edata.get("support", "")
                object_type = la.SUPPORT_MAP.get(support, support or None)
                material = la.guess_material_from_support(support) if hasattr(la, "guess_material_from_support") else None
                # Signs from words: each latin letter is a sign
                words = edata.get("words", [])
                signs = []
                seq = 0
                for word_str in words:
                    if word_str in ("|", "\n"):
                        if word_str == "|":
                            signs.append(SignInstance(sequence=seq, bennettId="WORD_DIV", signType="word divider", character="|", transliteration="|"))
                            seq += 1
                        continue
                    for ch in word_str:
                        if not ch.strip():
                            continue
                        # treat each letter as alphabetic sign
                        ben = ch.lower()
                        signs.append(SignInstance(sequence=seq, bennettId=ben, character=ch, transliteration=ch, signType="syllabogram", unicode=f"U+{ord(ch):04X}"))  # ponytail: map alphabet letters to syllabogram so generic pipeline reuses same code path
                        seq += 1
                # Create Inscription
                alt_ids = edata.get("names", [])
                name = edata.get("name", eid)
                if name in alt_ids:
                    alt_ids.remove(name)
                inscription = Inscription(gorilaId=name, alternativeIds=alt_ids, findspot=findspot, date=date_info, material=material, objectType=object_type, signs=signs, source="eteocretan")
                inscriptions.append(inscription)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to parse eteocretan %s: %s", eid, exc)
                failed += 1
    else:
        for entry in raw_entries:
            if isinstance(entry, list) and len(entry) >= 2:
                eid, edata = str(entry[0]), entry[1]
            elif isinstance(entry, dict):
                eid = entry.get("name", entry.get("gorilaId", "UNKNOWN"))
                edata = entry
            else:
                failed += 1
                continue
            ins = la.parse_lineara_inscription(eid, edata, supp_data)
            if ins:
                inscriptions.append(ins)
            else:
                failed += 1

    total_signs = sum(len(i.signs) for i in inscriptions)
    logger.info("Parsed %d inscriptions, %d failed, %d signs", len(inscriptions), failed, total_signs)

    # ---- import to DB ----
    if db_path.exists():
        db_path.unlink()
        logger.info("Removed existing DB %s", db_path)

    db = LinearADatabase(str(db_path))
    db.connect()
    for idx, ins in enumerate(inscriptions):
        try:
            db.insert_inscription(ins)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to import %s: %s", ins.gorilaId, exc)
        if (idx + 1) % 200 == 0:
            db.conn.commit()
    db.conn.commit()
    db.close()
    logger.info("Imported %d inscriptions → %s", len(inscriptions), db_path)

    # ---- stats ----
    db = LinearADatabase(str(db_path))
    db.connect()
    stats = db.stats()
    db.close()
    logger.info("Stats: %s", json.dumps(stats, ensure_ascii=False))
    return db_path


def main() -> None:
    p = argparse.ArgumentParser(description="Generic ingest — languages/<id>/config.yaml driven")
    p.add_argument("--language", default="linear-a", help="Language id (languages/<id>/config.yaml)")
    p.add_argument("--raw", dest="raw", default=None, help="Override raw JSON path")
    p.add_argument("--supplement", default=None, help="Override supplement JSON path")
    p.add_argument("--db", dest="db", default=None, help="Override output DB path")
    p.add_argument("--sync", action="store_true", help="Reserved: future SigLA live sync")
    args = p.parse_args()

    if args.sync:
        logger.info("--sync: live SigLA pull not yet wired (stub, Phase 2)")

    out = ingest_language(
        language=args.language,
        raw_override=args.raw,
        supplement_override=args.supplement,
        db_override=args.db,
    )
    print(f"Done: {out}")


if __name__ == "__main__":
    main()
