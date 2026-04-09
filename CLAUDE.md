# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pi-hole DNS daily report generator. A bash script queries the Pi-hole SQLite database for per-client DNS activity, then optionally uses an LLM (Zhipu, MiniMax, DeepSeek, or Gemini) to analyze the report for age-inappropriate content and emails the HTML result.

## Running

```bash
# Full pipeline (queries Pi-hole DB, runs AI analysis, sends email)
./daily-report.sh --email "a@b.com" --ips "192.168.1.100 192.168.1.101" --dir "/home/pi/reports"

# AI analysis standalone
python3 analyze_report.py <report_file> res/analysis_template.html
```

Requires env var `ZHIPU_API_KEY`, `MINIMAX_API_KEY`, `DEEPSEEK_API_KEY`, or `GEMINI_API_KEY` for AI analysis. Provider precedence: Zhipu > MiniMax > DeepSeek > Gemini.

## Dependencies

```bash
pip3 install -r requirements.txt   # requests, tenacity
```

System: `sqlite3`, `mailutils`, `ssmtp`, Pi-hole with user in `pihole` group.

## Architecture

- **`daily-report.sh`** — Entry point. Queries `/etc/pihole/pihole-FTL.db` via sqlite3 for each client IP (top 500 domains). Writes per-IP and combined summary files. Calls `analyze_report.py` if any LLM API key is set, then emails the HTML output.
- **`analyze_report.py`** — Reads the combined report, builds a prompt from `res/prompt.txt` (substituting `{dns_white_list}`, `{report_content}`, `{analysis_template}`), calls the first available LLM provider, and outputs HTML with the raw report appended.
- **`llm/`** — One module per provider, each exposing a `call(prompt, api_key)` function with tenacity retry (3 attempts, exponential backoff). Models are read from `config.ini`.
- **`config.ini`** — LLM model names under `[llm]` section.
- **`res/prompt.txt`** — Analysis prompt template with placeholder tokens.
- **`res/analysis_template.html`** — HTML template for formatting the analysis output.

## Key Conventions

- All LLM modules follow the same interface: `call(prompt, api_key) -> str`.
- Model names are loaded from `config.ini` at module import time.
- The DNS whitelist in `analyze_report.py` (`DNS_WHITE_LIST`) is injected into the prompt at runtime.
- Analysis output is HTML sent via `mail` with `Content-Type: text/html`.
- Script runs as a cron job; errors go to stderr (captured in the analysis file).
