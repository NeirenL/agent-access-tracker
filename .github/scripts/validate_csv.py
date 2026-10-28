"""Validate data/events.csv and data/agents.csv and fail with a clear message pointing at the line.

Uses only the Python standard library. Errors are also printed as GitHub
annotations so they show up on the file in pull requests.
"""
import csv
import os
import re
import sys
from datetime import datetime

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "data/events.csv"
AGENTS_PATH = sys.argv[2] if len(sys.argv) > 2 else (os.path.dirname(CSV_PATH) or ".") + "/agents.csv"

COLUMNS = [
    "date", "platform", "country", "agent", "agent_company", "agent_type",
    "status", "mechanism", "verification", "source_url", "notes",
]
# Keep in sync with STATUS, TYPE, MECH and VERIF in index.html.
ALLOWED = {
    # Empty is allowed for agent_type and mechanism when the source doesn't say.
    "agent_type": {"", "cloud", "browser", "phone", "crawler"},
    "status": {"blocks", "allows", "allows with conditions", "opt-out"},
    "mechanism": {
        "", "robots.txt", "terms of service", "technical block",
        "permission protocol", "network/CDN block", "lawsuit",
    },
    "verification": {"official", "media report", "user reports"},
}
REQUIRED = ["platform", "agent"]
# country: two-letter ISO 3166-1 code of the operational headquarters of the company that operates
# the site or app, not the holding company or legal seat (e.g. US, MX, CN), or GLOBAL when there
# is no clear operator. A different legal seat goes in notes.
COUNTRY_RE = re.compile(r"^(?:[A-Z]{2}|GLOBAL)$")

# data/agents.csv: one row per specific agent named in events.csv (groups of agents get no row).
# Every value comes from an official source; "unknown" when the source doesn't give it.
AGENT_COLUMNS = [
    "agent", "company", "type", "type_source", "what_it_does", "user_agent", "launch_date", "source_url",
    "available_countries", "excluded_countries", "availability_source_url", "availability_source_type",
    "availability_notes", "checked_date", "tracking",
]
AGENT_TYPES = {"cloud", "local", "crawler", "unknown"}
# type_source: "official" when the source states the type, "inferred" when we deduced it, "unknown" with type unknown.
TYPE_SOURCES = {"official", "inferred"}
UNKNOWN = "unknown"
# Availability comes only from official help pages or docs; "no data" when there is none.
NO_DATA = "no data"
AVAIL_SOURCES = {"help_page", "changelog", "none"}  # availability_source_type
CODE_RE = re.compile(r"^[A-Z]{2}$")
OPTIONAL_AGENT_COLUMNS = {"availability_notes"}
# tracking: "event" agents must be named in events.csv; "watchlist" agents are watched before any event exists.
TRACKING = {"event", "watchlist"}

errors = []  # (file, line, message)
current_file = CSV_PATH
event_agents = []  # agent text of every event, to check that "event" agents appear there


def error(line, message):
    errors.append((current_file, line, message))


def fmt_allowed(column):
    values = ", ".join(f'"{v}"' for v in sorted(ALLOWED[column]) if v)
    return values + (" (or empty)" if "" in ALLOWED[column] else "")


def is_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return len(value) == 10
    except ValueError:
        return False


def read_rows(path, columns):
    """Yield (line, {column: value}) for every non-empty record, after checking the header.

    `line` is the first line of the record, since quoted fields may span lines.
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            error(1, "File is empty")
            return
        if [h.strip() for h in header] != columns:
            error(1, "Header must be exactly: " + ",".join(columns) + "\n    Found: " + ",".join(header))
        prev_end = reader.line_num
        for row in reader:
            line = prev_end + 1
            prev_end = reader.line_num
            if not any(cell.strip() for cell in row):
                continue
            if len(row) != len(columns):
                error(line, f"Expected {len(columns)} columns but found {len(row)}. "
                            "Check for missing commas, or wrap text containing commas in double quotes.")
                continue
            yield line, {col: value.strip() for col, value in zip(columns, row)}


def validate_events():
    seen_rows = {}
    seen_keys = {}
    platform_country = {}  # platform -> (country, line where it was first seen)
    count = 0
    for line, r in read_rows(CSV_PATH, COLUMNS):
        count += 1
        event_agents.append(r["agent"])

        if not is_date(r["date"]):
            error(line, f'date "{r["date"]}" is not a valid date in YYYY-MM-DD format (e.g. 2026-01-31)')

        for col in REQUIRED:
            if not r[col]:
                error(line, f"{col} must not be empty")

        for col in ALLOWED:
            if r[col] not in ALLOWED[col]:
                error(line, f'{col} "{r[col]}" is not allowed. Use one of: {fmt_allowed(col)}')

        if not COUNTRY_RE.match(r["country"]):
            error(line, f'country "{r["country"]}" must be a two-letter uppercase country code (e.g. US, MX, CN) or GLOBAL')
        elif r["platform"]:
            first = platform_country.setdefault(r["platform"].casefold(), (r["country"], line))
            if first[0] != r["country"]:
                error(line, f'country "{r["country"]}" differs from "{first[0]}" used for {r["platform"]} on line {first[1]}; '
                            "a platform keeps the same country in every row")

        if not r["source_url"].startswith("https://") or len(r["source_url"]) <= len("https://"):
            error(line, f'source_url "{r["source_url"]}" must start with https://')

        exact = tuple(r.values())
        if exact in seen_rows:
            error(line, f"Duplicate row: identical to line {seen_rows[exact]}")
        else:
            seen_rows[exact] = line
            key = tuple(r[c].casefold() for c in ("date", "platform", "agent", "status"))
            if key in seen_keys:
                error(line, f"Duplicate event: same date, platform, agent and status as line {seen_keys[key]}")
            else:
                seen_keys[key] = line
    return count


def validate_agents():
    seen = {}
    count = 0
    for line, r in read_rows(AGENTS_PATH, AGENT_COLUMNS):
        count += 1
        for col in AGENT_COLUMNS:
            if not r[col] and col not in OPTIONAL_AGENT_COLUMNS:
                error(line, f'{col} must not be empty; write "{UNKNOWN}" or "{NO_DATA}" if the official source does not say')

        name = r["agent"].casefold()
        if name in seen:
            error(line, f'Duplicate agent "{r["agent"]}": already on line {seen[name]}')
        seen.setdefault(name, line)

        if r["type"] and r["type"] not in AGENT_TYPES:
            error(line, f'type "{r["type"]}" is not allowed. Use one of: ' + ", ".join(f'"{t}"' for t in sorted(AGENT_TYPES)))

        if r["type"] == UNKNOWN and r["type_source"] and r["type_source"] != UNKNOWN:
            error(line, f'type_source "{r["type_source"]}" must be "{UNKNOWN}" when type is "{UNKNOWN}"')
        elif r["type"] in AGENT_TYPES - {UNKNOWN} and r["type_source"] not in TYPE_SOURCES:
            error(line, f'type_source "{r["type_source"]}" must be "official" (the source states the type) '
                        'or "inferred" (deduced, shown as "likely" on the page)')

        if r["launch_date"] and r["launch_date"] != UNKNOWN and not is_date(r["launch_date"]):
            error(line, f'launch_date "{r["launch_date"]}" must be YYYY-MM-DD or "{UNKNOWN}"')

        # One or more official sources separated by " ; ", or "unknown".
        if r["source_url"] and r["source_url"] != UNKNOWN:
            for url in (u.strip() for u in r["source_url"].split(";")):
                if not url.startswith("https://") or len(url) <= len("https://"):
                    error(line, f'source_url "{url}" must start with https:// (separate several sources with " ; ")')

        validate_availability(line, r)

        if r["tracking"] and r["tracking"] not in TRACKING:
            error(line, f'tracking "{r["tracking"]}" is not allowed. Use "event" or "watchlist"')
        elif r["tracking"] == "event" and r["agent"] and not named_in_events(r["agent"]):
            error(line, f'agent "{r["agent"]}" has tracking "event" but no event in events.csv names it; '
                        'add the event or use "watchlist"')
    return count


def named_in_events(name):
    """True if some event's agent text names this agent as a whole word, the way the page matches them
    ("ChatGPT" does not count inside "ChatGPT-User")."""
    pattern = re.compile(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])")
    return any(pattern.search(text) for text in event_agents)


def country_list(line, column, value, allow_global):
    """Codes separated by ";" (e.g. US;MX), "GLOBAL" if allowed, or "no data"."""
    if not value or value == NO_DATA or (allow_global and value == "GLOBAL"):
        return
    codes = [c.strip() for c in value.split(";")]
    bad = [c for c in codes if not CODE_RE.match(c)]
    if bad:
        error(line, f'{column} has invalid codes {bad}: use two-letter uppercase codes separated by ";"'
                    + (', "GLOBAL"' if allow_global else "") + f' or "{NO_DATA}"')
    dupes = sorted({c for c in codes if codes.count(c) > 1})
    if dupes:
        error(line, f"{column} repeats {dupes}")


def validate_availability(line, r):
    country_list(line, "available_countries", r["available_countries"], allow_global=True)
    country_list(line, "excluded_countries", r["excluded_countries"], allow_global=False)

    kind, url = r["availability_source_type"], r["availability_source_url"]
    if kind and kind not in AVAIL_SOURCES:
        error(line, f'availability_source_type "{kind}" is not allowed. Use one of: "help_page", "changelog", "none"')
    if url and url != NO_DATA and not (url.startswith("https://") and len(url) > len("https://")):
        error(line, f'availability_source_url "{url}" must start with https:// or be "{NO_DATA}"')
    if kind == "none" and url and url != NO_DATA:
        error(line, 'availability_source_type is "none" but availability_source_url has a link')
    if kind in ("help_page", "changelog") and url == NO_DATA:
        error(line, f'availability_source_type "{kind}" needs a link in availability_source_url')
    has_data = (r["available_countries"] not in ("", NO_DATA)) or (r["excluded_countries"] not in ("", NO_DATA))
    if has_data and url == NO_DATA:
        error(line, "Countries need an official source in availability_source_url")

    if r["checked_date"] and not is_date(r["checked_date"]):
        error(line, f'checked_date "{r["checked_date"]}" must be YYYY-MM-DD')


def main():
    global current_file
    if not os.path.exists(CSV_PATH):
        print(f"::error::{CSV_PATH} not found")
        sys.exit(1)

    counts = {}
    current_file = CSV_PATH
    counts[CSV_PATH] = validate_events()
    if os.path.exists(AGENTS_PATH):
        current_file = AGENTS_PATH
        counts[AGENTS_PATH] = validate_agents()

    if errors:
        errors.sort()
        for path, line, message in errors:
            print(f"::error file={path},line={line}::{message.splitlines()[0]}")
        for path in counts:
            found = [(line, message) for p, line, message in errors if p == path]
            if found:
                print(f"\n{path}: {len(found)} problem(s) found\n")
                for line, message in found:
                    print(f"  Line {line}: {message}")
        sys.exit(1)

    for path, count in counts.items():
        print(f"{path}: OK ({count} rows checked)")


if __name__ == "__main__":
    main()
