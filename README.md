# 🛡️ Agent Access Tracker

**A public, sourced record of which platforms block or allow AI agents, and when.**

🌐 **Live page:** https://neirenl.github.io/agent-access-tracker/

AI agents now browse, click and buy on our behalf: cloud agents, agentic browsers, and agents that run on phones. Platforms are responding in different ways. Some block them, some welcome them, some set conditions. This project keeps a dated log of those decisions, with a source for every entry, so anyone can see where things stand.

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
| `tipo_agente` | Where the agent runs | `nube` (cloud) · `navegador` (browser) · `teléfono` (phone) |
| `estado` | The platform's stance | `bloquea` (blocks) · `permite` (allows) · `permite con condiciones` (allows with conditions) · `opt-out` |
| `mecanismo` | How it is enforced | e.g. `robots.txt`, `Terms of Service`, `CAPTCHA`, `API` |
| `verificacion` | How the event is confirmed | `oficial` (official) · `reportado por medios` (media report) · `reportado por usuarios` (user reports) |
| `fuente_url` | Link to the source | Full `https://` URL |
| `notas` | Extra context | Free text (wrap in quotes if it contains commas) |

## 🤝 How to contribute

Know of a platform blocking or allowing an AI agent? **[Open an issue](https://github.com/NeirenL/agent-access-tracker/issues/new/choose)** and include:

1. The platform and the agent
2. What happened (blocks, allows, conditions, opt-out) and the date
3. **A link to the source.** This is required. Official announcements, terms of service, or reputable media are best.

Entries without a verifiable source won't be added. If you spot an error or a dead link, open an issue too.

Every Monday, an automated check visits each `fuente_url` and opens an issue if any link is broken.

## 📄 License

The data and content in this repository are licensed under [**Creative Commons Attribution 4.0 International (CC BY 4.0)**](https://creativecommons.org/licenses/by/4.0/). You are free to share and adapt them for any purpose, as long as you give appropriate credit:

> Agent Access Tracker, https://github.com/NeirenL/agent-access-tracker (CC BY 4.0)
