"""Check that every source_url in the dataset (events.csv and agents.csv) still responds.

Writes a Markdown report and sets the `broken` step output for the workflow.
"""
import csv
import os
import sys
import urllib.error
import urllib.request

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "data/events.csv"
REPORT_PATH = sys.argv[2] if len(sys.argv) > 2 else "report.md"
AGENTS_PATH = sys.argv[3] if len(sys.argv) > 3 else (os.path.dirname(CSV_PATH) or ".") + "/agents.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}
# Many sites answer automated requests with these codes even when the page exists,
# so they are reported as "could not verify" instead of broken.
BOT_BLOCK_CODES = {401, 403, 429, 999}


def check(url):
    """Return the HTTP status code, or an error description."""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.status
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 404, 405, 501):
                continue  # some servers reject HEAD; retry with GET
            return e.code
        except Exception as e:  # DNS failure, timeout, TLS error...
            if method == "HEAD":
                continue
            return type(e).__name__
    return "unknown"


def main():
    urls = {}
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        for line, row in enumerate(csv.DictReader(f), start=2):
            url = (row.get("source_url") or "").strip()
            if url:
                urls.setdefault(url, []).append(f"{line} ({(row.get('platform') or '').strip()})")
    # agents.csv: its sources (several may be separated by ";") and its availability source.
    if os.path.exists(AGENTS_PATH):
        with open(AGENTS_PATH, newline="", encoding="utf-8-sig") as f:
            for line, row in enumerate(csv.DictReader(f), start=2):
                sources = (row.get("source_url") or "") + ";" + (row.get("availability_source_url") or "")
                for url in sources.split(";"):
                    url = url.strip()
                    if url.startswith("http"):
                        urls.setdefault(url, []).append(f"agents.csv {line} ({(row.get('agent') or '').strip()})")

    broken, unverified = [], []
    for url, where in urls.items():
        result = check(url)
        print(f"{result}\t{url}")
        if isinstance(result, int) and result < 400:
            continue
        entry = f"| {url} | `{result}` | {', '.join(where)} |"
        (unverified if result in BOT_BLOCK_CODES else broken).append(entry)

    table_head = "| URL | Result | CSV line (platform or agent) |\n|---|---|---|"
    report = [f"Weekly link check: **{len(broken)} broken** out of {len(urls)} source URLs.\n"]
    if broken:
        report += ["### ❌ Broken links", table_head, *broken, ""]
    if unverified:
        report += ["### ⚠️ Could not verify (site may block automated checks)", table_head, *unverified, ""]
    report.append("Please replace dead links with a working source or an archived copy (e.g. web.archive.org).")
    text = "\n".join(report)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text + "\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"broken={'true' if broken else 'false'}\n")


if __name__ == "__main__":
    main()
