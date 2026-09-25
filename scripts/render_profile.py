#!/usr/bin/env python3
"""Render every profile SVG (dark + light) into assets/. Stdlib only.

Live data comes from the GitHub GraphQL API. Token: GITHUB_TOKEN / GH_TOKEN.
Run with --static to skip the API and render only the non-live assets.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

LOGIN = "ats4321"
OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
CHAR = 0.6  # monospace advance per px of font-size
MARKUP = {"HTML", "CSS", "Jupyter Notebook"}  # byte-heavy, not really "languages I write"

THEMES = {
    "dark": dict(bg="#0D1117", panel="#161B22", border="#262C36", grid="#1C2230",
                 text="#E6EDF3", muted="#8B949E", indigo="#6366F1", violet="#8B5CF6",
                 cyan="#22D3EE",
                 ramp=["#6366F1", "#8B5CF6", "#22D3EE", "#A78BFA", "#818CF8", "#67E8F9"]),
    "light": dict(bg="#FFFFFF", panel="#F6F8FA", border="#D0D7DE", grid="#EEF0F4",
                  text="#1F2328", muted="#59636E", indigo="#4F46E5", violet="#7C3AED",
                  cyan="#0891B2",
                  ramp=["#4F46E5", "#7C3AED", "#0891B2", "#8B5CF6", "#6366F1", "#06B6D4"]),
}


def tw(text, size, spacing=0):
    return len(text) * (size * CHAR + spacing)


def svg(w, h, body, t, css=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">
<style>
text{{font-family:{FONT};fill:{t['text']}}}
.m{{fill:{t['muted']}}} .i{{fill:{t['indigo']}}} .v{{fill:{t['violet']}}} .c{{fill:{t['cyan']}}} .b{{font-weight:700}}
{css}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
</style>
<defs><linearGradient id="grad" x1="0" x2="1"><stop offset="0" stop-color="{t['indigo']}"/><stop offset="1" stop-color="{t['violet']}"/></linearGradient></defs>
{body}
</svg>
"""


def frame(w, h, t):
    return f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>'


def txt(x, y, s, size, cls="", anchor="start", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" text-anchor="{anchor}" {extra}>{escape(str(s))}</text>'


# ---------------------------------------------------------------- static assets

def hero(t):
    w, h = 830, 220
    tagline = "Building where physics, AI, and software meet"
    cx, cy = 700, 84
    orbits = "".join(
        f'<g transform="translate({cx} {cy}) rotate({rot})">'
        f'<ellipse rx="{rx}" ry="{ry}" fill="none" stroke="{t["border"]}" stroke-width="1.2"/>'
        f'<ellipse rx="{rx}" ry="{ry}" fill="none" stroke="{t["cyan"]}" stroke-width="2.5" stroke-linecap="round" '
        f'pathLength="100" stroke-dasharray="7 93" class="comet" style="animation-duration:{dur}s"/></g>'
        for rx, ry, rot, dur in [(96, 30, -20, 7), (70, 22, 28, 5)])
    corners = "".join(
        f'<path d="M{x} {y + 14 * sy}V{y}H{x + 14 * sx}" fill="none" stroke="{t["indigo"]}" stroke-width="2"/>'
        for x, y, sx, sy in [(16, 16, 1, 1), (w - 16, 16, -1, 1), (16, h - 16, 1, -1), (w - 16, h - 16, -1, -1)])
    css = f"""
.scan{{animation:scan 6s linear infinite}} @keyframes scan{{from{{transform:translateY(-10px)}}to{{transform:translateY({h}px)}}}}
.comet{{animation:orbit 6s linear infinite}} @keyframes orbit{{from{{stroke-dashoffset:100}}to{{stroke-dashoffset:0}}}}
.cur{{animation:blink 1.1s steps(1) infinite}} @keyframes blink{{50%{{opacity:0}}}}
.pulse{{animation:pulse 3s ease-in-out infinite}} @keyframes pulse{{50%{{opacity:.55}}}}"""
    body = f"""{frame(w, h, t)}
<defs><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="{t['grid']}"/></pattern>
<linearGradient id="sl" x1="0" x2="1"><stop offset="0" stop-color="{t['cyan']}" stop-opacity="0"/><stop offset=".5" stop-color="{t['cyan']}"/><stop offset="1" stop-color="{t['cyan']}" stop-opacity="0"/></linearGradient>
<radialGradient id="planet" cx=".35" cy=".35"><stop offset="0" stop-color="{t['cyan']}"/><stop offset="1" stop-color="{t['indigo']}"/></radialGradient>
<clipPath id="clip"><rect width="{w}" height="{h}" rx="12"/></clipPath></defs>
<g clip-path="url(#clip)"><rect width="{w}" height="{h}" fill="url(#grid)"/>
<rect class="scan" width="{w}" height="2" fill="url(#sl)" opacity=".45"/></g>
{corners}
{orbits}
<circle cx="{cx}" cy="{cy}" r="20" fill="url(#planet)" class="pulse"/>
{txt(44, 58, "> SYS.ONLINE // github.com/" + LOGIN, 13, "c", extra='letter-spacing="1.5"')}
<text x="42" y="118" font-size="46" class="b" fill="url(#grad)" style="fill:url(#grad)" letter-spacing="3">ATIKSH SHUKLA</text>
{txt(44, 176, tagline, 24)}
<rect class="cur" x="{44 + tw(tagline, 24) + 6}" y="156" width="12" height="24" fill="{t['cyan']}"/>"""
    return svg(w, h, body, t, css)


def buttons():
    # ponytail: theme-neutral gradient buttons, one file each so each can be its own link
    t = THEMES["dark"]
    out = {}
    for key, label in [("portfolio", "PORTFOLIO"), ("linkedin", "LINKEDIN"), ("x", "X / @ATSHUU21"),
                       ("youtube", "WATCH ON YOUTUBE"), ("email", "EMAIL")]:
        label += " ↗"
        w, h = int(tw(label, 13, 1.2) + 36), 34
        body = (f'<rect width="{w}" height="{h}" rx="8" fill="url(#grad)"/>'
                f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="7" fill="none" stroke="#FFFFFF" stroke-opacity=".18"/>'
                f'<text x="{w/2}" y="22" font-size="13" text-anchor="middle" letter-spacing="1.2" class="b" style="fill:#FFFFFF">{escape(label)}</text>')
        out[f"btn-{key}.svg"] = svg(w, h, body, t)
    return out


def chips(items, t):
    pad, gap, h = 16, 10, 38
    widths = [int(tw(s, 14) + pad * 2 + 14) for s in items]
    w = sum(widths) + gap * (len(items) - 1) + 2
    x, body = 1, ""
    for s, cw in zip(items, widths):
        body += (f'<rect x="{x}" y="1" width="{cw}" height="{h}" rx="9" fill="{t["panel"]}" stroke="{t["border"]}"/>'
                 f'<rect x="{x + pad}" y="{h/2 - 3}" width="7" height="7" rx="1.5" fill="{t["cyan"]}" transform="rotate(45 {x + pad + 3.5} {h/2 + .5})"/>'
                 + txt(x + pad + 16, h / 2 + 6, s, 14))
        x += cw + gap
    return svg(w, h + 2, body, t)


def youtube_strip(t):
    w, h = 830, 110
    body = frame(w, h, t)
    for i, (num, label) in enumerate([("30K+", "SUBSCRIBERS"), ("215+", "VIDEOS"), ("217K+", "VIEWS")]):
        x = w / 6 + i * w / 3
        if i:
            body += f'<line x1="{i * w / 3}" y1="24" x2="{i * w / 3}" y2="{h - 24}" stroke="{t["border"]}"/>'
        body += (f'<text x="{x}" y="58" font-size="34" text-anchor="middle" class="b" style="fill:url(#grad)">{num}</text>'
                 + txt(x, 84, label, 12, "m", "middle", 'letter-spacing="2"'))
    return svg(w, h, body, t)


# ---------------------------------------------------------------- live data

def gql(query):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN or GH_TOKEN is required (or pass --static)")
    req = urllib.request.Request("https://api.github.com/graphql", json.dumps({"query": query}).encode(),
                                 {"Authorization": f"bearer {token}", "User-Agent": LOGIN})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    if data.get("errors"):
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]


def fetch(today):
    # ponytail: first 100 owned repos only; paginate if the account ever passes 100
    u = gql(f"""{{user(login:"{LOGIN}"){{
      createdAt followers{{totalCount}} pullRequests{{totalCount}} issues{{totalCount}}
      all: repositories(ownerAffiliations:OWNER, privacy:PUBLIC){{totalCount}}
      own: repositories(ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false, first:100){{nodes{{
        stargazerCount languages(first:10, orderBy:{{field:SIZE, direction:DESC}}){{edges{{size node{{name}}}}}}}}}}
      repositoriesContributedTo(contributionTypes:[COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]){{totalCount}}
      contributionsCollection{{contributionYears}}}}}}""")
    years = u["contributionsCollection"]["contributionYears"]
    cal = gql(f'{{user(login:"{LOGIN}"){{' + "".join(
        f'y{y}: contributionsCollection(from:"{y}-01-01T00:00:00Z", to:"{y}-12-31T23:59:59Z"){{'
        f'totalCommitContributions contributionCalendar{{weeks{{contributionDays{{date contributionCount}}}}}}}}'
        for y in years) + "}}")
    days = {}
    for y in years:
        for wk in cal[f"y{y}"]["contributionCalendar"]["weeks"]:
            for d in wk["contributionDays"]:
                if d["date"] <= today.isoformat():
                    days[d["date"]] = d["contributionCount"]
    langs = {}
    for r in u["own"]["nodes"]:
        for e in r["languages"]["edges"]:
            if e["node"]["name"] not in MARKUP:
                langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    return dict(
        repos=u["all"]["totalCount"], followers=u["followers"]["totalCount"],
        stars=sum(r["stargazerCount"] for r in u["own"]["nodes"]),
        commits=cal.get(f"y{today.year}", {}).get("totalCommitContributions", 0),
        prs=u["pullRequests"]["totalCount"], issues=u["issues"]["totalCount"],
        since=dt.date.fromisoformat(u["createdAt"][:10]),
        contributed=u["repositoriesContributedTo"]["totalCount"],
        days=days, langs=langs)


def streaks(days, today):
    """-> (current, current_start, longest, longest_start, longest_end). A zero today doesn't break the streak."""
    dates = sorted(days)
    longest, run, start, best = 0, 0, None, (None, None)
    for d in dates:
        if days[d]:
            run += 1
            start = start if run > 1 else d
            if run > longest:
                longest, best = run, (start, d)
        else:
            run = 0
    cur, d = 0, today
    if not days.get(d.isoformat()):
        d -= dt.timedelta(days=1)
    while days.get(d.isoformat()):
        cur += 1
        d -= dt.timedelta(days=1)
    return cur, (d + dt.timedelta(days=1)), longest, best[0], best[1]


# ---------------------------------------------------------------- live assets

def neofetch(s, today, t):
    w, h = 830, 300
    cx, cy = 150, 172
    atom = "".join(f'<ellipse cx="{cx}" cy="{cy}" rx="78" ry="26" fill="none" stroke="{c}" stroke-width="1.6" '
                   f'transform="rotate({r} {cx} {cy})"/>' for r, c in [(0, t["indigo"]), (60, t["violet"]), (120, t["cyan"])])
    rows = [("OS", "macOS · Phoenix, AZ"), ("Role", "Founder @ Gainloom"),
            ("Focus", "Quantum AI · Aerospace · Software"), ("Philosophy", "Ship in all three."), None,
            ("GitHub", f"{s['repos']} repos · {s['stars']} stars · {s['followers']} followers"),
            ("Commits", f"{s['commits']} in {today.year}"), ("Synced", f"{today.isoformat()} UTC")]
    x, y, lines = 300, 108, ""
    for r in rows:
        if r:
            k, v = r
            lines += (f'<text x="{x}" y="{y}" font-size="14"><tspan class="i b">{escape(k)}</tspan>'
                      f'<tspan class="m"> {"." * (12 - len(k))} </tspan>'
                      f'<tspan class="{"m" if k == "Synced" else ""}">{escape(v)}</tspan></text>')
        y += 22
    blocks = "".join(f'<rect x="{x + i * 30}" y="{y - 6}" width="24" height="12" rx="2" fill="{c}"/>'
                     for i, c in enumerate(t["ramp"] + [t["muted"], t["text"]]))
    body = f"""{frame(w, h, t)}
<path d="M.5 36V12.5a12 12 0 0 1 12-12h805a12 12 0 0 1 12 12V36z" fill="{t['panel']}"/>
<line x1="0" y1="36" x2="{w}" y2="36" stroke="{t['border']}"/>
{"".join(f'<circle cx="{22 + i * 18}" cy="18" r="5.5" fill="{c}"/>' for i, c in enumerate([t['indigo'], t['violet'], t['cyan']]))}
{txt(w / 2, 23, "atiksh@shukla: ~ — zsh", 12, "m", "middle")}
<text x="24" y="66" font-size="14"><tspan class="c b">~ $</tspan> neofetch</text>
{atom}<circle cx="{cx}" cy="{cy}" r="9" fill="url(#grad)"/>
<text x="{x}" y="72" font-size="16" class="b"><tspan class="c">atiksh</tspan><tspan class="m">@</tspan><tspan class="i">shukla</tspan></text>
<line x1="{x}" y1="84" x2="{w - 40}" y2="84" stroke="{t['border']}" stroke-dasharray="4 4"/>
{lines}{blocks}"""
    return svg(w, h, body, t)


def stats_card(s, t):
    w, h = 410, 200
    total = sum(s["days"].values())
    rows = [("Contributions (all time)", total), ("Pull requests", s["prs"]), ("Issues", s["issues"]),
            ("Contributed to (repos)", s["contributed"]), ("Member since", s["since"].strftime("%b %Y"))]
    body = frame(w, h, t) + txt(24, 36, "// telemetry", 15, "i b")
    for i, (k, v) in enumerate(rows):
        y = 72 + i * 27
        body += (f'<rect x="24" y="{y - 9}" width="6" height="6" rx="1" fill="{t["cyan"]}"/>'
                 + txt(40, y, k, 13, "m") + txt(w - 24, y, f"{v:,}" if isinstance(v, int) else v, 14, "b", "end"))
    return svg(w, h, body, t)


def langs_card(s, t):
    w, h = 410, 200
    top = sorted(s["langs"].items(), key=lambda kv: -kv[1])[:6]
    total = sum(v for _, v in top) or 1
    body = frame(w, h, t) + txt(24, 36, "// top.languages", 15, "i b")
    body += f'<clipPath id="bar"><rect x="24" y="54" width="{w - 48}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">'
    x = 24
    for (name, v), c in zip(top, t["ramp"]):
        bw = (w - 48) * v / total
        body += f'<rect x="{x}" y="54" width="{bw + .5}" height="10" fill="{c}"/>'
        x += bw
    body += "</g>"
    for i, ((name, v), c) in enumerate(zip(top, t["ramp"])):
        cx, cy = 24 + (i % 2) * 190, 100 + (i // 2) * 32
        body += (f'<circle cx="{cx + 5}" cy="{cy - 5}" r="5" fill="{c}"/>' + txt(cx + 18, cy, name, 13)
                 + txt(cx + 172, cy, f"{100 * v / total:.1f}%", 13, "m", "end"))
    return svg(w, h, body, t)


def streak_card(s, today, t):
    w, h = 830, 170
    cur, cur_start, longest, l_start, l_end = streaks(s["days"], today)
    active = sum(1 for d, c in s["days"].items() if c and d.startswith(str(today.year)))
    fmt = lambda d: dt.date.fromisoformat(str(d)).strftime("%b %-d") if d else "—"
    cols = [(str(active), f"ACTIVE DAYS · {today.year}", f"Jan 1 – {fmt(today)}"),
            (str(cur), "CURRENT STREAK", f"{fmt(cur_start)} – {fmt(today)}" if cur else "start one today"),
            (str(longest), "LONGEST STREAK", f"{fmt(l_start)} – {fmt(l_end)}" if longest else "—")]
    body = frame(w, h, t)
    for i, (num, label, sub) in enumerate(cols):
        x = w / 6 + i * w / 3
        if i:
            body += f'<line x1="{i * w / 3}" y1="28" x2="{i * w / 3}" y2="{h - 28}" stroke="{t["border"]}"/>'
        if i == 1:
            body += (f'<circle cx="{x}" cy="66" r="38" fill="none" stroke="{t["border"]}" stroke-width="5"/>'
                     f'<circle cx="{x}" cy="66" r="38" fill="none" stroke="url(#grad)" stroke-width="5" '
                     f'stroke-dasharray="{min(cur / max(longest, 1), 1) * 238.8:.1f} 240" stroke-linecap="round" transform="rotate(-90 {x} 66)"/>'
                     f'<text x="{x}" y="78" font-size="32" text-anchor="middle" class="b">{num}</text>')
            ly = 128
        else:
            body += f'<text x="{x}" y="80" font-size="36" text-anchor="middle" class="b" style="fill:url(#grad)">{num}</text>'
            ly = 112
        body += txt(x, ly, label, 12, "c b", "middle", 'letter-spacing="1.5"') + txt(x, ly + 20, sub, 12, "m", "middle")
    return svg(w, h, body, t)


def main():
    OUT.mkdir(exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).date()
    files = buttons()
    for name, t in THEMES.items():
        files[f"header-{name}.svg"] = hero(t)
        files[f"stack-ai-{name}.svg"] = chips(["LangChain", "Pinecone", "OpenAI", "Anthropic", "Gemini", "Ollama"], t)
        files[f"stack-special-{name}.svg"] = chips(["Quantum Optimization · QUBO", "Orbital Mechanics · SGP4", "Prompt Engineering"], t)
        files[f"youtube-{name}.svg"] = youtube_strip(t)
    if "--static" not in sys.argv:
        s = fetch(today)
        for name, t in THEMES.items():
            files[f"neofetch-{name}.svg"] = neofetch(s, today, t)
            files[f"stats-{name}.svg"] = stats_card(s, t)
            files[f"langs-{name}.svg"] = langs_card(s, t)
            files[f"streak-{name}.svg"] = streak_card(s, today, t)
    for fn, content in files.items():
        (OUT / fn).write_text(content)
    print(f"wrote {len(files)} files to {OUT}")


if __name__ == "__main__":
    main()
