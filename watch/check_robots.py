"""Weekly robots.txt watcher for AI agents.

Downloads robots.txt for every site in watch/sites.txt, keeps only the rules for
known AI agents, compares them with last week's snapshot and writes:
  - snapshots/<domain>.txt   the full robots.txt as downloaded
  - snapshots/<domain>.json  the AI-agent rules, used for the comparison
  - a Markdown report (--report) and one issue body per changed site (--issues-dir)

It never edits data/events.csv: it only proposes rows inside the issues.
Uses only the Python standard library.
"""
import argparse
import csv
import datetime
import io
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITES_FILE = ROOT / "watch" / "sites.txt"
EXTRA_AGENTS_FILE = ROOT / "watch" / "extra_agents.txt"
SNAPSHOTS = ROOT / "snapshots"
AGENTS_CACHE = SNAPSHOTS / "_ai_agents.json"
WATCHED_FILE = SNAPSHOTS / "_watched_agents.json"  # every agent checked in the last run

AGENTS_URL = "https://raw.githubusercontent.com/ai-robots-txt/ai.robots.txt/main/robots.json"
USER_AGENT = "AgentAccessTracker/1.0 (+https://github.com/NeirenL/agent-access-tracker)"
TIMEOUT = 20
MAX_BYTES = 1_000_000
PAUSE_SECONDS = 2  # between sites, to stay polite
NOT_LISTED = "(not listed)"
NOTE = "detected in robots.txt, no public statement"


def read_list(path):
    """Non-empty, non-comment lines of a text file, split on '|'."""
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            rows.append([part.strip() for part in line.split("|")])
    return rows


def fetch(url, retries=1):
    """Return (status, final_url, text). Retries once on network errors; raises on HTTP errors."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.geturl(), resp.read(MAX_BYTES).decode("utf-8", errors="replace")
    except urllib.error.HTTPError:
        raise
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        if retries <= 0:
            raise
        time.sleep(5)
        return fetch(url, retries - 1)


def failure_reason(e):
    """Short, readable reason for a failed download."""
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}"
    if isinstance(e, urllib.error.URLError):
        return f"network error ({e.reason})"
    if isinstance(e, ValueError):
        return str(e)
    return type(e).__name__


def clean_operator(text):
    """'[OpenAI](https://openai.com)' -> 'OpenAI'; unknown operators -> ''."""
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text or "").strip()
    return "" if not text or text.lower().startswith("unclear") else text


def load_previous_watched():
    """Lowercase names of the agents checked in the last run, or None if unknown.

    Only agents watched in both runs are compared, so an agent that is new to the
    ai.robots.txt list (or dropped from it) never looks like a robots.txt change.
    """
    if WATCHED_FILE.exists():
        return {n.lower() for n in json.loads(WATCHED_FILE.read_text(encoding="utf-8"))}
    if AGENTS_CACHE.exists():  # runs before _watched_agents.json existed: cached list + extras
        names = set(json.loads(AGENTS_CACHE.read_text(encoding="utf-8")))
        names |= {row[0] for row in read_list(EXTRA_AGENTS_FILE)}
        return {n.lower() for n in names}
    return None


def load_agents():
    """Map lowercase agent name -> (name, operator). Falls back to the cached list if the download fails."""
    agents, source = {}, "ai.robots.txt"
    try:
        _, _, text = fetch(AGENTS_URL)
        data = json.loads(text)
        for name, info in data.items():
            agents[name.lower()] = (name, clean_operator(info.get("operator", "")))
        SNAPSHOTS.mkdir(exist_ok=True)
        cache = {name: op for name, op in sorted(agents.values())}
        AGENTS_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as e:  # network error or bad JSON: use last week's copy
        source = f"cached copy (download failed: {type(e).__name__})"
        if AGENTS_CACHE.exists():
            for name, op in json.loads(AGENTS_CACHE.read_text(encoding="utf-8")).items():
                agents[name.lower()] = (name, op)
    for row in read_list(EXTRA_AGENTS_FILE):
        agents.setdefault(row[0].lower(), (row[0], row[1] if len(row) > 1 else ""))
    return agents, source


def parse_groups(text):
    """Split robots.txt into (user_agents, rules) groups. Only Allow/Disallow rules are kept."""
    groups, agents, rules, had_rules = [], [], [], False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if had_rules:  # a new User-agent after rules starts a new group
                groups.append((agents, rules))
                agents, rules, had_rules = [], [], False
            agents.append(value)
        elif key in ("allow", "disallow") and agents:
            rules.append(f"{key.capitalize()}: {value}")
            had_rules = True
    if agents:
        groups.append((agents, rules))
    return groups


def ai_rules(text, agents):
    """Rules per AI agent named in the file, e.g. {'GPTBot': ['Disallow: /']}. Wildcard (*) groups are ignored."""
    found = {}
    for names, rules in parse_groups(text):
        for name in names:
            known = agents.get(name.lower())
            if known:
                bucket = found.setdefault(known[0], [])
                bucket.extend(r for r in rules if r not in bucket)
    return dict(sorted(found.items(), key=lambda kv: kv[0].lower()))


def blocks_all_robots(text):
    """True if the User-agent: * group disallows the whole site."""
    rules = [r for names, group in parse_groups(text) if "*" in names for r in group]
    return proposed_estado(rules) == "bloquea"


def looks_like_robots(text):
    return re.search(r"^\s*(user-agent|disallow|allow|sitemap)\s*:", text, re.I | re.M) is not None


def proposed_estado(rules):
    """Only a whole-site block is mapped automatically; everything else needs a human decision."""
    if "Disallow: /" in rules and not any(r.startswith("Allow: ") and r != "Allow: " for r in rules):
        return "bloquea"
    return "TO DECIDE"


def csv_row(values):
    out = io.StringIO()
    csv.writer(out, lineterminator="").writerow(values)
    return out.getvalue()


def fence(rules):
    return "```\n" + ("\n".join(rules) if rules else NOT_LISTED) + "\n```"


def issue_for(domain, name, pais, url, changes, agents, today, all_robots=None):
    """Issue text. `all_robots` is (before, after) when the User-agent: * whole-site block changed."""
    what = [c[0] for c in changes] + (["User-agent: *"] if all_robots else [])
    lines = [
        f"robots.txt change for AI agents: {domain} ({', '.join(what)})",
        "",
        f"**Site:** {name} ({domain})",
        f"**robots.txt:** {url}",
        f"**Detected:** {today} (date of the weekly check, not necessarily the date of the change)",
        "",
        "### What changed",
    ]
    rows = []
    if all_robots:
        state = lambda blocked: "Disallow: / (whole site blocked for all robots)" if blocked else "no whole-site block"
        lines += [
            "#### User-agent: * (all robots, AI agents included)",
            "**Before**",
            f"```\n{state(all_robots[0])}\n```",
            "**After**",
            f"```\n{state(all_robots[1])}\n```",
            "",
        ]
        estado = "bloquea" if all_robots[1] else "TO DECIDE"
        rows.append(csv_row([today, name, pais, "All robots (User-agent: *)", "", "", estado, "robots.txt", "oficial", url, NOTE]))
    for agent, before, after in changes:
        operator = next((op for n, op in agents.values() if n == agent), "")
        lines += [f"#### {agent}" + (f" ({operator})" if operator else ""), "**Before**", fence(before), "**After**", fence(after), ""]
        estado = proposed_estado(after) if after else "TO DECIDE"
        rows.append(csv_row([today, name, pais, agent, operator, "", estado, "robots.txt", "oficial", url, NOTE]))
    lines += [
        "### Proposed rows for `data/events.csv`",
        "Review before adding anything. `TO DECIDE` means the change is not a clear whole-site block "
        "(partial rules, an Allow, or the agent was removed): pick the right `estado` by hand. "
        "`pais` comes from watch/sites.txt; `TO DECIDE` there means the site has no country yet. "
        "`tipo_agente` is left empty on purpose.",
        "",
        "```csv",
        *rows,
        "```",
        "",
        "_Opened automatically by the weekly robots.txt watcher (`watch/check_robots.py`). It never edits `data/events.csv`._",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", default="robots-report.md", help="where to write the Markdown report")
    parser.add_argument("--issues-dir", default="robots-issues", help="where to write one issue body per changed site")
    parser.add_argument("--only", nargs="*", help="check only these domains")
    args = parser.parse_args()

    today = datetime.date.today().isoformat()
    previous_watched = load_previous_watched()  # read before load_agents() refreshes the cache
    agents, agents_source = load_agents()
    new_agents = 0 if previous_watched is None else len(set(agents) - previous_watched)

    def watched_both_weeks(agent):
        return agent.lower() in agents and (previous_watched is None or agent.lower() in previous_watched)
    sites = [(row[0].lower(), row[1] if len(row) > 1 and row[1] else row[0], row[2].upper() if len(row) > 2 and row[2] else "TO DECIDE")
             for row in read_list(SITES_FILE)]
    if args.only:
        sites = [s for s in sites if s[0] in {d.lower() for d in args.only}]

    SNAPSHOTS.mkdir(exist_ok=True)
    issues_dir = Path(args.issues_dir)
    issues_dir.mkdir(parents=True, exist_ok=True)

    results = []  # (domain, status text, ai agent count, whole-site blocks)
    for n, (domain, name, pais) in enumerate(sites):
        if n:
            time.sleep(PAUSE_SECONDS)
        url = f"https://{domain}/robots.txt"
        try:
            status, final_url, text = fetch(url)
            if not looks_like_robots(text):
                if re.search(r"captcha|are you a robot|access denied", text, re.I):
                    raise ValueError("blocked by a bot check (CAPTCHA/denied page instead of robots.txt)")
                raise ValueError("response is not a robots.txt file")
        except Exception as e:  # HTTP error, timeout, DNS, TLS, not a robots.txt...
            # The previous snapshot is kept as is, so a failure never looks like a change.
            results.append((domain, f"⚠️ failed: {failure_reason(e)}", "–", "–", "–"))
            continue

        rules = ai_rules(text, agents)
        all_blocked = blocks_all_robots(text)
        snap_json = SNAPSHOTS / f"{domain}.json"
        old = json.loads(snap_json.read_text(encoding="utf-8")) if snap_json.exists() else None
        previous = old["ai_rules"] if old else None
        previous_all = old.get("all_robots_blocked") if old else None  # missing in snapshots older than this check

        (SNAPSHOTS / f"{domain}.txt").write_text(text, encoding="utf-8")
        snap_json.write_text(
            json.dumps({"url": final_url, "all_robots_blocked": all_blocked, "ai_rules": rules}, indent=2, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )

        blocks = sum(1 for r in rules.values() if proposed_estado(r) == "bloquea")
        all_cell = "yes" if all_blocked else "no"
        if previous is None:
            results.append((domain, "📸 first snapshot (baseline, no issue)", len(rules), blocks, all_cell))
            continue
        changes = [
            (agent, previous.get(agent, []), rules.get(agent, []))
            for agent in sorted(set(previous) | set(rules), key=str.lower)
            if watched_both_weeks(agent) and previous.get(agent, []) != rules.get(agent, [])
        ]
        all_change = (previous_all, all_blocked) if previous_all is not None and previous_all != all_blocked else None
        if changes or all_change:
            (issues_dir / f"{domain}.md").write_text(
                issue_for(domain, name, pais, final_url, changes, agents, today, all_change), encoding="utf-8"
            )
            what = [c[0] for c in changes] + (["User-agent: *"] if all_change else [])
            results.append((domain, f"🔔 changed: {', '.join(what)}", len(rules), blocks, all_cell))
        else:
            results.append((domain, "✅ no change", len(rules), blocks, all_cell))

    if not args.only:  # a partial run must not shrink the list used next week
        WATCHED_FILE.write_text(json.dumps(sorted({n for n, _ in agents.values()}, key=str.lower), indent=2) + "\n", encoding="utf-8")

    failed = sum(1 for r in results if r[1].startswith("⚠️"))
    changed = sum(1 for r in results if r[1].startswith("🔔"))
    report = [
        f"## robots.txt watch · {today}",
        "",
        f"{len(results)} sites checked · {changed} changed · {failed} failed · "
        f"{len(agents)} AI agents watched (list from {agents_source}"
        + (f"; {new_agents} new this week, recorded as baseline only" if new_agents else "")
        + ")",
        "",
        "| Site | Result | AI agents named | Whole-site blocks | All robots blocked (`*`) |",
        "|---|---|---|---|---|",
        *[f"| {d} | {s} | {a} | {b} | {w} |" for d, s, a, b, w in results],
        "",
    ]
    Path(args.report).write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
