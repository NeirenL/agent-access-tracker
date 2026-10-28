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
    "fecha", "plataforma", "pais", "agente", "empresa_agente", "tipo_agente",
    "estado", "mecanismo", "verificacion", "fuente_url", "notas",
]
ALLOWED = {
    # Empty is allowed for tipo_agente and mecanismo when the source doesn't say.
    "tipo_agente": {"", "nube", "navegador", "teléfono", "crawler"},
    "estado": {"bloquea", "permite", "permite con condiciones", "opt-out"},
    "mecanismo": {
        "", "robots.txt", "términos de servicio", "bloqueo técnico",
        "protocolo de permisos", "bloqueo de red/CDN", "demanda",
    },
    "verificacion": {"oficial", "reportado por medios", "reportado por usuarios"},
}
# Accepted spellings that mean an official value.
# Keep in sync with TYPE_ALIASES and MECH_ALIASES in index.html.
ALIASES = {
    "tipo_agente": {"telefono": "teléfono"},
    "mecanismo": {
        "terminos de servicio": "términos de servicio",
        "bloqueo tecnico": "bloqueo técnico",
    },
}
REQUIRED = ["plataforma", "agente"]
# pais: two-letter ISO 3166-1 code of the operational headquarters of the company that operates
# the site or app, not the holding company or legal seat (e.g. US, MX, CN), or GLOBAL when there
# is no clear operator. A different legal seat goes in notas.
PAIS_RE = re.compile(r"^(?:[A-Z]{2}|GLOBAL)$")

# data/agents.csv: one row per specific agent named in events.csv (groups of agents get no row).
# Every value comes from an official source; "unknown" when the source doesn't give it.
AGENT_COLUMNS = [
    "agente", "empresa", "tipo", "tipo_fuente", "que_hace", "user_agent", "fecha_lanzamiento", "fuente_url",
    "paises_disponibles", "paises_excluidos", "disponibilidad_fuente_url", "disponibilidad_tipo_fuente",
    "disponibilidad_notas", "fecha_revisado",
]
AGENT_TIPOS = {"nube", "local", "crawler", "unknown"}
# tipo_fuente: "official" when the source states the type, "inferred" when we deduced it, "unknown" with tipo unknown.
TIPO_FUENTES = {"official", "inferred"}
UNKNOWN = "unknown"
# Availability comes only from official help pages or docs; "sin dato" when there is none.
NO_DATA = "sin dato"
AVAIL_SOURCES = {"help_page", "changelog", "none"}  # disponibilidad_tipo_fuente
COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
OPTIONAL_AGENT_COLUMNS = {"disponibilidad_notas"}

errors = []  # (file, line, message)
current_file = CSV_PATH


def error(line, message):
    errors.append((current_file, line, message))


def fmt_allowed(column):
    extras = [f'"{alias}" for "{value}"' for alias, value in ALIASES.get(column, {}).items()]
    if "" in ALLOWED[column]:
        extras.append("empty")
    return ", ".join(f'"{v}"' for v in sorted(ALLOWED[column]) if v) + (
        f" (also accepted: {', '.join(extras)})" if extras else ""
    )


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
    platform_pais = {}  # platform -> (pais, line where it was first seen)
    count = 0
    for line, r in read_rows(CSV_PATH, COLUMNS):
        count += 1
        for col, aliases in ALIASES.items():
            r[col] = aliases.get(r[col], r[col])

        if not is_date(r["fecha"]):
            error(line, f'fecha "{r["fecha"]}" is not a valid date in YYYY-MM-DD format (e.g. 2026-01-31)')

        for col in REQUIRED:
            if not r[col]:
                error(line, f"{col} must not be empty")

        for col in ALLOWED:
            if r[col] not in ALLOWED[col]:
                error(line, f'{col} "{r[col]}" is not allowed. Use one of: {fmt_allowed(col)}')

        if not PAIS_RE.match(r["pais"]):
            error(line, f'pais "{r["pais"]}" must be a two-letter uppercase country code (e.g. US, MX, CN) or GLOBAL')
        elif r["plataforma"]:
            first = platform_pais.setdefault(r["plataforma"].casefold(), (r["pais"], line))
            if first[0] != r["pais"]:
                error(line, f'pais "{r["pais"]}" differs from "{first[0]}" used for {r["plataforma"]} on line {first[1]}; '
                            "a platform keeps the same country in every row")

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
    return count


def validate_agents():
    seen = {}
    count = 0
    for line, r in read_rows(AGENTS_PATH, AGENT_COLUMNS):
        count += 1
        for col in AGENT_COLUMNS:
            if not r[col] and col not in OPTIONAL_AGENT_COLUMNS:
                error(line, f'{col} must not be empty; write "{UNKNOWN}" if the official source does not say')

        name = r["agente"].casefold()
        if name in seen:
            error(line, f'Duplicate agente "{r["agente"]}": already on line {seen[name]}')
        seen.setdefault(name, line)

        if r["tipo"] and r["tipo"] not in AGENT_TIPOS:
            error(line, f'tipo "{r["tipo"]}" is not allowed. Use one of: ' + ", ".join(f'"{t}"' for t in sorted(AGENT_TIPOS)))

        if r["tipo"] == UNKNOWN and r["tipo_fuente"] and r["tipo_fuente"] != UNKNOWN:
            error(line, f'tipo_fuente "{r["tipo_fuente"]}" must be "{UNKNOWN}" when tipo is "{UNKNOWN}"')
        elif r["tipo"] in AGENT_TIPOS - {UNKNOWN} and r["tipo_fuente"] not in TIPO_FUENTES:
            error(line, f'tipo_fuente "{r["tipo_fuente"]}" must be "official" (the source states the type) '
                        'or "inferred" (deduced, shown as "likely" on the page)')

        if r["fecha_lanzamiento"] and r["fecha_lanzamiento"] != UNKNOWN and not is_date(r["fecha_lanzamiento"]):
            error(line, f'fecha_lanzamiento "{r["fecha_lanzamiento"]}" must be YYYY-MM-DD or "{UNKNOWN}"')

        # One or more official sources separated by " ; ", or "unknown".
        if r["fuente_url"] and r["fuente_url"] != UNKNOWN:
            for url in (u.strip() for u in r["fuente_url"].split(";")):
                if not url.startswith("https://") or len(url) <= len("https://"):
                    error(line, f'fuente_url "{url}" must start with https:// (separate several sources with " ; ")')

        validate_availability(line, r)
    return count


def country_list(line, column, value, allow_global):
    """Codes separated by ";" (e.g. US;MX), "GLOBAL" if allowed, or "sin dato"."""
    if not value or value == NO_DATA or (allow_global and value == "GLOBAL"):
        return
    codes = [c.strip() for c in value.split(";")]
    bad = [c for c in codes if not COUNTRY_RE.match(c)]
    if bad:
        error(line, f'{column} has invalid codes {bad}: use two-letter uppercase codes separated by ";"'
                    + (', "GLOBAL"' if allow_global else "") + f' or "{NO_DATA}"')
    dupes = sorted({c for c in codes if codes.count(c) > 1})
    if dupes:
        error(line, f"{column} repeats {dupes}")


def validate_availability(line, r):
    country_list(line, "paises_disponibles", r["paises_disponibles"], allow_global=True)
    country_list(line, "paises_excluidos", r["paises_excluidos"], allow_global=False)

    kind, url = r["disponibilidad_tipo_fuente"], r["disponibilidad_fuente_url"]
    if kind and kind not in AVAIL_SOURCES:
        error(line, f'disponibilidad_tipo_fuente "{kind}" is not allowed. Use one of: "help_page", "changelog", "none"')
    if url and url != NO_DATA and not (url.startswith("https://") and len(url) > len("https://")):
        error(line, f'disponibilidad_fuente_url "{url}" must start with https:// or be "{NO_DATA}"')
    if kind == "none" and url and url != NO_DATA:
        error(line, f'disponibilidad_tipo_fuente is "none" but disponibilidad_fuente_url has a link')
    if kind in ("help_page", "changelog") and url == NO_DATA:
        error(line, f'disponibilidad_tipo_fuente "{kind}" needs a link in disponibilidad_fuente_url')
    has_data = (r["paises_disponibles"] not in ("", NO_DATA)) or (r["paises_excluidos"] not in ("", NO_DATA))
    if has_data and url == NO_DATA:
        error(line, "Countries need an official source in disponibilidad_fuente_url")

    if r["fecha_revisado"] and not is_date(r["fecha_revisado"]):
        error(line, f'fecha_revisado "{r["fecha_revisado"]}" must be YYYY-MM-DD')


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
