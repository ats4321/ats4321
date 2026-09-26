#!/usr/bin/env python3
"""Render the GitHub stats cards (dark + light) into assets/ and refresh the live
numbers in README.md. Stdlib only. Token: GITHUB_TOKEN / GH_TOKEN."""
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

LOGIN = "ats4321"
ROOT = Path(__file__).resolve().parent.parent
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MARKUP = {"HTML", "CSS", "Jupyter Notebook"}  # byte-heavy, not really "languages I write"

THEMES = {
    "dark": dict(bg="#0D1117", border="#30363D", text="#E6EDF3", muted="#8B949E", accent="#818CF8", track="#21262D",
                 ramp=["#6366F1", "#818CF8", "#A5B4FC", "#8B5CF6", "#C4B5FD", "#4F46E5"]),
    "light": dict(bg="#FFFFFF", border="#D0D7DE", text="#1F2328", muted="#59636E", accent="#4F46E5", track="#EAEEF2",
                  ramp=["#4F46E5", "#6366F1", "#818CF8", "#7C3AED", "#A78BFA", "#3730A3"]),
}


def gql(query):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN or GH_TOKEN is required")
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
    longest, run, start, best = 0, 0, None, (None, None)
    for d in sorted(days):
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


def svg(w, h, body, t):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">
<style>text{{font-family:{FONT};fill:{t['text']}}} .m{{fill:{t['muted']}}} .t{{font-size:16px;font-weight:600;fill:{t['accent']}}} .b{{font-weight:600}}</style>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="8" fill="{t['bg']}" stroke="{t['border']}"/>
{body}
</svg>
"""


def txt(x, y, s, size, cls="", anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" text-anchor="{anchor}">{escape(str(s))}</text>'


def stats_card(s, t):
    rows = [("Contributions (all time)", f"{sum(s['days'].values()):,}"), ("Pull requests", f"{s['prs']:,}"),
            ("Issues", f"{s['issues']:,}"), ("Contributed to", f"{s['contributed']} repos"),
            ("Member since", s["since"].strftime("%b %Y"))]
    body = txt(24, 36, "GitHub Stats", 16, "t")
    for i, (k, v) in enumerate(rows):
        y = 70 + i * 26
        body += txt(24, y, k, 14, "m") + txt(386, y, v, 14, "b", "end")
    return svg(410, 190, body, t)


def langs_card(s, t):
    top = sorted(s["langs"].items(), key=lambda kv: -kv[1])[:6]
    total = sum(v for _, v in top) or 1
    body = txt(24, 36, "Top Languages", 16, "t")
    body += f'<clipPath id="bar"><rect x="24" y="54" width="362" height="8" rx="4"/></clipPath><g clip-path="url(#bar)">'
    x = 24
    for (_, v), c in zip(top, t["ramp"]):
        body += f'<rect x="{x:.2f}" y="54" width="{362 * v / total + .5:.2f}" height="8" fill="{c}"/>'
        x += 362 * v / total
    body += "</g>"
    for i, ((name, v), c) in enumerate(zip(top, t["ramp"])):
        cx, cy = 24 + (i % 2) * 186, 96 + (i // 2) * 30
        body += (f'<circle cx="{cx + 5}" cy="{cy - 5}" r="5" fill="{c}"/>' + txt(cx + 18, cy, name, 14)
                 + txt(cx + 172, cy, f"{100 * v / total:.1f}%", 14, "m", "end"))
    return svg(410, 190, body, t)


def streak_card(s, today, t):
    w, h = 830, 160
    cur, cur_start, longest, l_start, l_end = streaks(s["days"], today)
    active = sum(1 for d, c in s["days"].items() if c and d.startswith(str(today.year)))
    fmt = lambda d: dt.date.fromisoformat(str(d)).strftime("%b %-d")
    cols = [(active, f"Active days in {today.year}", f"Jan 1 to {fmt(today)}"),
            (cur, "Current streak", f"{fmt(cur_start)} to {fmt(today)}" if cur else "No streak right now"),
            (longest, "Longest streak", f"{fmt(l_start)} to {fmt(l_end)}" if longest else "None yet")]
    body = ""
    for i, (num, label, sub) in enumerate(cols):
        x = w / 6 + i * w / 3
        if i:
            body += f'<line x1="{i * w / 3:.1f}" y1="32" x2="{i * w / 3:.1f}" y2="{h - 32}" stroke="{t["border"]}"/>'
        if i == 1:  # ring shows current streak as a share of the longest
            frac = min(cur / max(longest, 1), 1)
            body += (f'<circle cx="{x}" cy="62" r="34" fill="none" stroke="{t["track"]}" stroke-width="5"/>'
                     f'<circle cx="{x}" cy="62" r="34" fill="none" stroke="{t["accent"]}" stroke-width="5" stroke-linecap="round" '
                     f'stroke-dasharray="{frac * 213.6:.1f} 214" transform="rotate(-90 {x} 62)"/>'
                     + txt(x, 72, num, 28, "b", "middle"))
            ly = 120
        else:
            body += txt(x, 74, num, 32, "b", "middle")
            ly = 108
        body += txt(x, ly, label, 14, "", "middle") + txt(x, ly + 20, sub, 12, "m", "middle")
    return svg(w, h, body, t)


def patch_readme(s, today):
    p = ROOT / "README.md"
    text = p.read_text()
    text = re.sub(r"(GitHub \.+ )\d+ repos, \d+ stars, \d+ followers",
                  rf"\g<1>{s['repos']} repos, {s['stars']} stars, {s['followers']} followers", text)
    text = re.sub(r"(Commits \.+ )\d+ in \d{4}", rf"\g<1>{s['commits']} in {today.year}", text)
    text = re.sub(r"(<!--updated-->).*?(<!--/updated-->)", rf"\g<1>{today:%B %-d, %Y}\g<2>", text)
    p.write_text(text)


def main():
    today = dt.datetime.now(dt.timezone.utc).date()
    s = fetch(today)
    (ROOT / "assets").mkdir(exist_ok=True)
    for name, t in THEMES.items():
        (ROOT / f"assets/stats-{name}.svg").write_text(stats_card(s, t))
        (ROOT / f"assets/langs-{name}.svg").write_text(langs_card(s, t))
        (ROOT / f"assets/streak-{name}.svg").write_text(streak_card(s, today, t))
    patch_readme(s, today)
    print("rendered cards and patched README")


if __name__ == "__main__":
    main()
