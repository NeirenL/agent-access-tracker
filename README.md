# 🛡️ Agent Access Tracker

[![Screenshot of the Agent Access Tracker page](docs/screenshot.png)](https://neirenl.github.io/agent-access-tracker/)

**A public, sourced record of which platforms block or allow AI agents, and when.**

🌐 **Live page:** https://neirenl.github.io/agent-access-tracker/<br>
📅 **Last updated:** 2026-10-27

## 🧭 Why this exists

AI agents now browse, compare and buy on people's behalf, and platforms are deciding, often quietly, whether to let them in.
Those decisions are scattered across robots.txt files, terms of service, blog posts and lawsuits.
This project collects them in one dated, sourced place, so anyone can see who blocks what and how it changes over time.

---

## 📊 The data

Everything lives in a single file: [`data/events.csv`](data/events.csv). Each row is one **event**, meaning a platform changed (or announced) its stance toward an agent. The page shows the most recent event per platform as its current status.

The column names and values are kept in Spanish, the language the dataset was started in. The page translates them.

| Column | Meaning | Allowed values / format |
|---|---|---|
| `fecha` | Date of the event | `YYYY-MM-DD` |
| `plataforma` | Platform taking the action | e.g. `Amazon`, `LinkedIn` |
| `agente` | The AI agent affected | e.g. `Comet`, `Grok Bot` |
| `empresa_agente` | Company behind the agent | e.g. `Perplexity`, `xAI` |
| `tipo_agente` | Where the agent runs | `nube` (cloud) · `navegador` (browser) · `teléfono` (phone) · `crawler`. `telefono` without the accent is also accepted and treated as `teléfono`. Leave empty if the source doesn't say. |
| `estado` | The platform's stance | `bloquea` (blocks) · `permite` (allows) · `permite con condiciones` (allows with conditions) · `opt-out` |
| `mecanismo` | How it is enforced | `robots.txt` · `términos de servicio` (terms of service) · `bloqueo técnico` (technical block) · `protocolo de permisos` (permission protocol) · `bloqueo de red/CDN` (network/CDN block) · `demanda` (lawsuit). `terminos de servicio` and `bloqueo tecnico` without accents are also accepted. Leave empty if the source doesn't say; put details in `notas`. |
| `verificacion` | How the event is confirmed | `oficial` (official) · `reportado por medios` (media report) · `reportado por usuarios` (user reports) |
| `fuente_url` | Link to the source | Full `https://` URL |
| `notas` | Extra context | Free text (wrap in quotes if it contains commas) |

## 🤝 How to contribute

Know of a platform blocking or allowing an AI agent? **[Open an issue](https://github.com/NeirenL/agent-access-tracker/issues/new/choose)** and include:

1. The platform and the agent
2. What happened (blocks, allows, conditions, opt-out) and the date
3. **A link to the source.** This is required. Official announcements, terms of service, or reputable media are best.

Entries without a verifiable source won't be added. If you spot an error or a dead link, open an issue too.

Editing the CSV directly? Every push and pull request runs an automatic check on `data/events.csv` (exact columns, `YYYY-MM-DD` dates, allowed values, `https://` sources, no duplicates). If it fails, the log tells you which line to fix. `tipo_agente` and `mecanismo` may be left empty when the source doesn't say.

Every Monday, an automated check visits each `fuente_url` and opens an issue if any link is broken.

## 📄 License

The data and content in this repository are licensed under [**Creative Commons Attribution 4.0 International (CC BY 4.0)**](https://creativecommons.org/licenses/by/4.0/). You are free to share and adapt them for any purpose, as long as you give appropriate credit:

> Agent Access Tracker, https://github.com/NeirenL/agent-access-tracker (CC BY 4.0)
