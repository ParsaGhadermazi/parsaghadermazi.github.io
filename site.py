#!/usr/bin/env python3
"""Static site tool for parsaghadermazi.github.io.

Commands:
    sync    Pull publications from Google Scholar into data/publications.json
    build   Render data + markdown posts into static HTML pages
    new     Interactively create a new post (with image resize / positioning)

Run via the ./tool wrapper, e.g. `./tool build`.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

import markdown as md
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
POSTS_DIR = ROOT / "posts"
TEMPLATES = ROOT / "templates"
CONFIG_PATH = DATA / "config.json"
PUBS_PATH = DATA / "publications.json"

AUTHOR_NAME = "Parsa Ghadermazi"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "post"


def extract_scholar_id(value: str) -> str:
    """Accept a bare Scholar ID or a full profile URL and return the ID."""
    value = (value or "").strip()
    match = re.search(r"user=([^&]+)", value)
    return match.group(1) if match else value


def bold_author(authors: str) -> str:
    if not authors:
        return authors
    return authors.replace(AUTHOR_NAME, f"<strong>{AUTHOR_NAME}</strong>")


def parse_post(path: Path) -> dict:
    """Parse a markdown post with optional YAML frontmatter."""
    raw = path.read_text(encoding="utf-8")
    meta: dict = {}
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2]
    body = body.strip()
    renderer = md.Markdown(
        extensions=["attr_list", "fenced_code", "tables", "sane_lists"]
    )
    html = renderer.convert(body)

    # First image in the post becomes the card thumbnail.
    thumb_match = re.search(r"!\[([^\]]*)\]\(([^)\s]+)", body)
    thumb = thumb_match.group(2) if thumb_match else None
    thumb_alt = thumb_match.group(1) if thumb_match else ""

    return {
        "title": meta.get("title", path.stem),
        "date": str(meta.get("date", "")),
        "html": html,
        "slug": path.stem,
        "thumb": thumb,
        "thumb_alt": thumb_alt,
        "excerpt": _excerpt(body),
    }


def _excerpt(body: str, limit: int = 160) -> str:
    """Build a short plain-text preview from markdown body."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?", "", body)  # drop images
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links -> text
    text = re.sub(r"[#>*`_]", "", text)  # strip md markers
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return text


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #
def build() -> None:
    config = load_json(CONFIG_PATH)
    config["scholar_id"] = extract_scholar_id(config.get("scholar_id", ""))
    year = _dt.date.today().year
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )
    common = {"config": config, "year": year}

    # --- index / about ---
    _render(env, "index.html", {**common, "page": "index.html"})

    # --- posts (listing + one page per post) ---
    posts = [parse_post(p) for p in sorted(POSTS_DIR.glob("*.md"))]
    posts.sort(key=lambda p: p["date"], reverse=True)
    _render(env, "posts.html", {**common, "page": "posts.html", "posts": posts})
    for post in posts:
        _render(
            env,
            "post.html",
            {**common, "page": "posts.html", "post": post},
            out=f"{post['slug']}.html",
        )

    # --- publications (grouped by year, newest first) ---
    pubs = load_json(PUBS_PATH).get("publications", [])
    for pub in pubs:
        pub["authors_html"] = bold_author(pub.get("authors", ""))
    groups = _group_by_year(pubs)
    _render(
        env,
        "publications.html",
        {**common, "page": "publications.html", "groups": groups},
    )

    # --- contact ---
    _render(env, "contact.html", {**common, "page": "contact.html"})

    print(f"Built 4 pages, {len(posts)} post pages, {len(pubs)} publications.")


def _render(env: Environment, name: str, ctx: dict, out: str | None = None) -> None:
    html = env.get_template(name).render(**ctx)
    (ROOT / (out or name)).write_text(html, encoding="utf-8")


def _group_by_year(pubs: list[dict]) -> list[dict]:
    buckets: dict[str, list] = {}
    for pub in pubs:
        buckets.setdefault(str(pub.get("year", "")), []).append(pub)
    years = sorted(buckets, key=lambda y: (y != "", y), reverse=True)
    return [{"year": y or "Other", "pubs": buckets[y]} for y in years]


# --------------------------------------------------------------------------- #
# sync (Google Scholar)
# --------------------------------------------------------------------------- #
def sync() -> None:
    config = load_json(CONFIG_PATH)
    scholar_id = extract_scholar_id(config.get("scholar_id", ""))
    if not scholar_id:
        sys.exit(
            "No scholar_id in data/config.json. Add your Google Scholar profile "
            "ID (the `user=` value from your profile URL) and re-run."
        )

    from scholarly import scholarly  # imported lazily; heavy dependency

    print(f"Fetching Google Scholar profile {scholar_id} ...")
    author = scholarly.search_author_id(scholar_id)
    author = scholarly.fill(author, sections=["publications"])
    raw_pubs = author.get("publications", [])
    print(f"Found {len(raw_pubs)} publications. Fetching details ...")

    publications = []
    for i, pub in enumerate(raw_pubs, 1):
        filled = scholarly.fill(pub)
        bib = filled.get("bib", {})
        title = bib.get("title", "").strip()
        url = filled.get("pub_url") or filled.get("eprint_url") or ""
        links = [{"label": "Web", "url": url, "style": "secondary"}] if url else []
        publications.append(
            {
                "title": title,
                "authors": bib.get("author", "").replace(" and ", ", "),
                "venue": bib.get("venue", "") or bib.get("journal", ""),
                "year": str(bib.get("pub_year", "")),
                "abstract": bib.get("abstract", ""),
                "links": links,
            }
        )
        print(f"  [{i}/{len(raw_pubs)}] {title[:70]}")

    publications.sort(key=lambda p: p.get("year", ""), reverse=True)
    payload = {
        "synced_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "source": f"google-scholar:{scholar_id}",
        "publications": publications,
    }
    PUBS_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nWrote {len(publications)} publications to {PUBS_PATH.relative_to(ROOT)}")
    print("Review the file, then run `./tool build`.")


# --------------------------------------------------------------------------- #
# new post
# --------------------------------------------------------------------------- #
ALIGN_CLASS = {"r": "post-img-right", "l": "post-img-left", "c": "post-img-center"}


def new_post() -> None:
    print("New post\n--------")
    title = input("Title: ").strip()
    if not title:
        sys.exit("Title is required.")
    default_date = _dt.date.today().isoformat()
    date = input(f"Date [{default_date}]: ").strip() or default_date
    slug = input(f"Filename slug [{slugify(title)}]: ").strip() or slugify(title)

    print("\nWrite a short body now (single line is fine; edit the file later for more).")
    body = input("Body: ").strip() or "Write your post here."

    images = []
    print(
        "\nAdd images. For each: path, alignment (right/left/center), and width in px.\n"
        "Press Enter on the path to stop."
    )
    while True:
        path = input("  Image path (e.g. img/foo.png): ").strip()
        if not path:
            break
        if not (ROOT / path).exists():
            print(f"  ! Warning: {path} not found (you can add the file later).")
        alt = input("  Alt text: ").strip() or title
        align = input("  Align [r]ight / [l]eft / [c]enter [r]: ").strip().lower() or "r"
        cls = ALIGN_CLASS.get(align[0], "post-img-right")
        width = input("  Width in px [280]: ").strip() or "280"
        images.append(f'![{alt}]({path}){{: .{cls} width="{width}"}}')

    POSTS_DIR.mkdir(exist_ok=True)
    out = POSTS_DIR / f"{slug}.md"
    lines = ["---", f"title: {title}", f"date: {date}", "---", ""]
    # Images go before the body so text wraps beside left/right-floated images.
    for image in images:
        lines += [image, ""]
    lines.append(body)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nCreated {out.relative_to(ROOT)}")
    print("Edit it for longer content, then run `./tool build`.")


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("sync", help="Pull publications from Google Scholar")
    sub.add_parser("build", help="Render static HTML")
    sub.add_parser("new", help="Create a new post interactively")
    args = parser.parse_args()

    if args.command == "sync":
        sync()
    elif args.command == "build":
        build()
    elif args.command == "new":
        new_post()


if __name__ == "__main__":
    main()
