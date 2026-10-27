"""Validate data/events.csv and fail with a clear message pointing at the line.

Uses only the Python standard library. Errors are also printed as GitHub
annotations so they show up on the file in pull requests.
"""
import csv
import os
import sys
from datetime import datetime

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "data/events.csv"

COLUMNS = [
    "fecha", "plataforma", "agente", "empresa_agente", "tipo_agente",
    "estado", "mecanismo", "verificacion", "fuente_url", "notas",
]
ALLOWED = {
    # Empty is allowed for tipo_agente when the source doesn't say.
    "tipo_agente": {"", "nube", "navegador", "teléfono"},
    "estado": {"bloquea", "permite", "permite con condiciones", "opt-out"},
    "verificacion": {"oficial", "reportado por medios", "reportado por usuarios"},
}
REQUIRED = ["plataforma", "agente"]

errors = []


def error(line, message):
    errors.append((line, message))


def fmt_allowed(column):
    return ", ".join(f'"{v}"' for v in sorted(ALLOWED[column]) if v) + (
        " (or empty)" if "" in ALLOWED[column] else ""
    )


def main():
    if not os.path.exists(CSV_PATH):
        print(f"::error::{CSV_PATH} not found")
        sys.exit(1)

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            error(1, "File is empty")
            header = None

        if header is not None and [h.strip() for h in header] != COLUMNS:
            error(1, "Header must be exactly: " + ",".join(COLUMNS) + "\n    Found: " + ",".join(header))

        seen_rows = {}
        seen_keys = {}
        count = 0
        prev_end = reader.line_num
        for row in reader:
            line = prev_end + 1  # first line of this record (quoted fields may span lines)
            prev_end = reader.line_num
            if not any(cell.strip() for cell in row):
                continue
            count += 1

            if len(row) != len(COLUMNS):
                error(line, f"Expected {len(COLUMNS)} columns but found {len(row)}. "
                            "Check for missing commas, or wrap text containing commas in double quotes.")
                continue

            r = {col: value.strip() for col, value in zip(COLUMNS, row)}

            try:
                datetime.strptime(r["fecha"], "%Y-%m-%d")
                if len(r["fecha"]) != 10:
                    raise ValueError
            except ValueError:
                error(line, f'fecha "{r["fecha"]}" is not a valid date in YYYY-MM-DD format (e.g. 2026-01-31)')

            for col in REQUIRED:
                if not r[col]:
                    error(line, f"{col} must not be empty")

            for col in ALLOWED:
                if r[col] not in ALLOWED[col]:
                    error(line, f'{col} "{r[col]}" is not allowed. Use one of: {fmt_allowed(col)}')

            if not r["fuente_url"].startswith("https://") or len(r["fuente_url"]) <= len("https://"):
                error(line, f'fuente_url "{r["fuente_url"]}" must start with https://')

            exact = tuple(r.values())
            if exact in seen_rows:
                error(line, f"Duplicate row: identical to line {seen_rows[exact]}")
            else:
                seen_rows[exact] = line
                key = tuple(r[c].casefold() for c in ("fecha", "plataforma", "agente", "estado"))
                if key in seen_keys:
                    error(line, f"Duplicate event: same fecha, plataforma, agente and estado as line {seen_keys[key]}")
                else:
                    seen_keys[key] = line

    if errors:
        errors.sort()
        for line, message in errors:
            print(f"::error file={CSV_PATH},line={line}::{message.splitlines()[0]}")
        print(f"\n{CSV_PATH}: {len(errors)} problem(s) found\n")
        for line, message in errors:
            print(f"  Line {line}: {message}")
        sys.exit(1)

    print(f"{CSV_PATH}: OK ({count} rows checked)")


if __name__ == "__main__":
    main()
