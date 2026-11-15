#!/usr/bin/env python3
"""Generate dynamic SVG metrics card and sync ORCID publications into README.md."""

from __future__ import annotations

import html
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USERNAME = "Sbolivar16"
ORCID_ID = "0000-0002-3772-7604"
ROOT = Path(__file__).resolve().parents[2]


def fetch_json(url: str, headers: dict[str, str] | None = None) -> dict | list:
    req_headers = {"User-Agent": "Sbolivar16-Profile-Updater/1.0"}
    if headers:
        req_headers.update(headers)
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        req_headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def generate_stats_svg() -> None:
    user = fetch_json(f"https://api.github.com/users/{USERNAME}")
    repos = fetch_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner")

    public_repos = [r for r in repos if not r.get("private") and r.get("name") != USERNAME]
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)
    followers = user.get("followers", 0)

    lang_counts: dict[str, int] = {}
    for r in public_repos:
        lang = r.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    total_lang_repos = sum(lang_counts.values()) or 1
    sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:4]
    lang_colors = {
        "Jupyter Notebook": "#f97316",
        "Python": "#38bdf8",
        "HTML": "#2dd4bf",
        "JavaScript": "#facc15",
        "CSS": "#818cf8",
        "Shell": "#4ade80",
    }

    # Build stacked bar segments (width 460)
    bar_width = 460
    x_offset = 0
    bar_rects = []
    legend_items = []
    for idx, (lang, count) in enumerate(sorted_langs):
        pct = (count / total_lang_repos) * 100
        seg_w = max(8, round((count / total_lang_repos) * bar_width))
        if idx == len(sorted_langs) - 1:
            seg_w = max(8, bar_width - x_offset)
        color = lang_colors.get(lang, "#94a3b8")
        bar_rects.append(
            f'<rect x="{x_offset}" y="0" width="{seg_w}" height="10" fill="{color}"/>'
        )
        lx = (idx % 2) * 235
        ly = (idx // 2) * 22
        legend_items.append(
            f'<g transform="translate({lx}, {ly})">'
            f'<circle cx="5" cy="6" r="4.5" fill="{color}"/>'
            f'<text x="16" y="10" class="ltxt">{html.escape(lang)} ({pct:.0f}%)</text>'
            f"</g>"
        )
        x_offset += seg_w

    updated_str = datetime.now(timezone.utc).strftime("%Y-%m-%d UTC")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 175" width="100%" height="175" role="img" aria-label="Live GitHub Research Metrics for {USERNAME}">
  <defs>
    <linearGradient id="sbg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0b1522"/>
      <stop offset="100%" stop-color="#0f2438"/>
    </linearGradient>
    <clipPath id="barClip">
      <rect x="0" y="0" width="{bar_width}" height="10" rx="5"/>
    </clipPath>
  </defs>
  <style>
    .kicker {{ font: 700 11px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; fill: #2dd4bf; letter-spacing: 1.6px; }}
    .val {{ font: 800 30px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; fill: #f8fafc; }}
    .lbl {{ font: 500 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; fill: #94a3b8; }}
    .ltxt {{ font: 500 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; fill: #cbd5e1; }}
    .meta {{ font: 500 10.5px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; fill: #64748b; }}
  </style>

  <rect width="1200" height="175" rx="14" fill="url(#sbg)" stroke="#1e3a5f" stroke-width="1"/>
  <text x="32" y="30" class="kicker">LIVE OPEN-SOURCE IMPACT · AUTO-SYNCED VIA GITHUB ACTIONS</text>
  <text x="1168" y="30" text-anchor="end" class="meta">Updated {updated_str}</text>

  <!-- 4 Metric Tiles -->
  <g transform="translate(32, 50)">
    <rect width="142" height="92" rx="10" fill="#08121e" stroke="#38bdf8" stroke-opacity="0.3"/>
    <text x="18" y="44" class="val">{total_stars}</text>
    <text x="18" y="70" class="lbl">★ Total Stars</text>
  </g>
  <g transform="translate(190, 50)">
    <rect width="142" height="92" rx="10" fill="#08121e" stroke="#2dd4bf" stroke-opacity="0.3"/>
    <text x="18" y="44" class="val">{total_forks}</text>
    <text x="18" y="70" class="lbl">⑂ Total Forks</text>
  </g>
  <g transform="translate(348, 50)">
    <rect width="142" height="92" rx="10" fill="#08121e" stroke="#818cf8" stroke-opacity="0.3"/>
    <text x="18" y="44" class="val">{len(public_repos)}</text>
    <text x="18" y="70" class="lbl">◫ Scientific Repos</text>
  </g>
  <g transform="translate(506, 50)">
    <rect width="142" height="92" rx="10" fill="#08121e" stroke="#38bdf8" stroke-opacity="0.3"/>
    <text x="18" y="44" class="val">{followers}</text>
    <text x="18" y="70" class="lbl">◉ Followers</text>
  </g>

  <!-- Language Distribution -->
  <g transform="translate(684, 52)">
    <text x="0" y="14" class="kicker">PRIMARY SCIENTIFIC STACK</text>
    <g transform="translate(0, 28)" clip-path="url(#barClip)">
      {''.join(bar_rects)}
    </g>
    <g transform="translate(0, 52)">
      {''.join(legend_items)}
    </g>
  </g>
</svg>
"""
    out_path = ROOT / "assets" / "stats-card.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
    print(f"Wrote {out_path} (stars={total_stars}, forks={total_forks}, repos={len(public_repos)})")


def sync_orcid_publications() -> None:
    readme_path = ROOT / "README.md"
    if not readme_path.exists():
        return

    data = fetch_json(
        f"https://pub.orcid.org/v3.0/{ORCID_ID}/works",
        headers={"Accept": "application/json"},
    )
    groups = data.get("group", [])
    rows = []
    for g in groups:
        ws = (g.get("work-summary") or [{}])[0]
        title = (ws.get("title") or {}).get("title", {}).get("value", "").strip()
        year = ((ws.get("publication-date") or {}).get("year") or {}).get("value", "—")
        journal = (ws.get("journal-title") or {}).get("value", "Journal Article")
        doi = ""
        for ext in (ws.get("external-ids") or {}).get("external-id", []):
            if ext.get("external-id-type") == "doi":
                doi = ext.get("external-id-value", "")
                break
        if title:
            doi_badge = (
                f"[![DOI](https://img.shields.io/badge/DOI-{doi.replace('-', '--')}-0ea5e9?style=flat-square)](https://doi.org/{doi})"
                if doi
                else "—"
            )
            rows.append(f"| **{year}** | {title} | *{journal}* | {doi_badge} |")

    if not rows:
        return

    block = (
        "<!-- ORCID_PUBLICATIONS:START -->\n"
        "| Year | Publication | Journal | Link |\n"
        "|:---:|---|---|---|\n"
        + "\n".join(rows)
        + "\n<!-- ORCID_PUBLICATIONS:END -->"
    )
    content = readme_path.read_text(encoding="utf-8")
    new_content = re.sub(
        r"<!-- ORCID_PUBLICATIONS:START -->.*?<!-- ORCID_PUBLICATIONS:END -->",
        block,
        content,
        flags=re.DOTALL,
    )
    if new_content != content:
        readme_path.write_text(new_content, encoding="utf-8")
        print(f"Updated ORCID publications in {readme_path} ({len(rows)} works)")


if __name__ == "__main__":
    generate_stats_svg()
    sync_orcid_publications()
