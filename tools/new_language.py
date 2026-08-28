#!/usr/bin/env python3
"""
tools/new_language.py — Phase 5 template: one pipeline, N configs, <30s scaffold.

    uv run python tools/new_language.py --id my-lang --name "My Lang" --sign-system syllabary
    uv run python tools/new_language.py --id my-lang --sign-system alphabet --mapping-null

Creates languages/<id>/ from template/language/ with placeholder substitution.
No cookiecutter/copier dep — stdlib only (ponytail).

ponytail: single-file scaffold; split to N standalone repos only when oracle >1.5×.
"""
from __future__ import annotations
import argparse, pathlib, shutil, sys

REPO = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "template" / "language"

def render(text: str, ctx: dict) -> str:
    for k,v in ctx.items():
        text = text.replace("{{"+k+"}}", str(v))
    return text

def main():
    p = argparse.ArgumentParser(description="Scaffold new language from template/language/")
    p.add_argument("--id", required=True, help="Language id, e.g. eteocypriot, my-lang (used as dir name)")
    p.add_argument("--name", default=None, help="Human name, e.g. 'My Lang' (default: id)")
    p.add_argument("--sign-system", default="syllabary", choices=["syllabary","alphabet","hieroglyphic","logographic"])
    p.add_argument("--mapping-null", action="store_true", help="Set mapping: null (alphabet, no CSV)")
    p.add_argument("--period-range", default="Uncertain")
    p.add_argument("--force", action="store_true", help="Overwrite existing languages/<id>/")
    args = p.parse_args()

    lid = args.id.strip()
    if not lid or "/" in lid or " " in lid:
        sys.exit("id must be a simple slug like 'my-lang'")

    name = args.name or lid.replace("-"," ").title()
    sign_system = args.sign_system
    mapping = "null" if args.mapping_null else "mapping.csv"
    period_range = args.period_range

    dest = REPO / "languages" / lid
    if dest.exists() and not args.force:
        sys.exit(f"exists: {dest} (use --force to overwrite)")

    ctx = {"id": lid, "name": name, "sign_system": sign_system, "mapping": mapping, "period_range": period_range}

    # copy template
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(TEMPLATE, dest)

    # render config.yaml, README.md, mapping.csv
    for rel in ["config.yaml", "README.md", "mapping.csv"]:
        fp = dest / rel
        if fp.exists():
            fp.write_text(render(fp.read_text(encoding="utf-8"), ctx), encoding="utf-8")

    # ensure data dirs + placeholder corpus
    (dest / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (dest / "data" / "database").mkdir(parents=True, exist_ok=True)
    placeholder = dest / "data" / "raw" / "corpus.json"
    if not placeholder.exists():
        placeholder.write_text('[\n  ["EXAMPLE 001", {\n    "name": "EXAMPLE 001",\n    "site": "Unknown",\n    "findspot": "Unknown",\n    "context": "",\n    "support": "Tablet",\n    "parsedInscription": "EXAMPLE",\n    "words": ["EXAMPLE"],\n    "transcription": "EXAMPLE",\n    "images": [],\n    "names": ["EXAMPLE 001"]\n  }]\n]\n', encoding="utf-8")
    # .gitkeep for empty dirs
    (dest / "data" / "raw" / ".gitkeep").touch(exist_ok=True)
    (dest / "data" / "database" / ".gitkeep").touch(exist_ok=True)

    # if mapping: null, remove mapping.csv stub
    if args.mapping_null:
        mp = dest / "mapping.csv"
        if mp.exists():
            mp.unlink()
            print(f"removed {mp} (mapping: null)")

    print(f"✓ Scaffolded languages/{lid}/")
    print(f"  id={lid} name={name} sign_system={sign_system} mapping={mapping}")
    print(f"  next:")
    print(f"    uv run python -m pipeline.cli unicode validate --language {lid}")
    print(f"    uv run python -m pipeline.ingest --language {lid}")
    # also print template source
    print(f"  template: template/language/ → languages/{lid}/")

if __name__ == "__main__":
    main()
