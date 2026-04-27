# AGENTS.md

## Project Overview

Pi-hole DNS daily report generator. A bash script queries the Pi-hole SQLite database for per-client DNS activity, then uses an LLM (Zhipu, MiniMax, DeepSeek, or Gemini) to analyze the report for age-inappropriate content and emails the HTML result.

## Language / Stack

- **Shell (bash)** — entry point and orchestration (`daily-report.sh`)
- **Python 3** — LLM integration and report analysis (`analyze_report.py`, `llm/`)
- **HTML/CSS** — email report template (`res/analysis_template.html`)

## Commands

```bash
# Full pipeline (requires Pi-hole DB access, LLM API key, and mail setup)
./daily-report.sh --email "a@b.com" --ips "192.168.1.100 192.168.1.101" --dir "/home/pi/reports"

# AI analysis standalone (given an existing report file)
python3 analyze_report.py <report_file> res/analysis_template.html

# Install Python dependencies
pip3 install -r requirements.txt
```

There is no test suite, linter, or type-checker configured for this project.

## Architecture

```
daily-report.sh          # Entry point. Queries Pi-hole DB, orchestrates analysis, sends email.
analyze_report.py        # Builds LLM prompt, calls provider, outputs HTML.
config.ini               # LLM model names under [llm] section.
llm/
  __init__.py
  zhipu.py               # Zhipu API client
  minimax.py             # MiniMax API client
  deepseek.py            # DeepSeek API client
  gemini.py              # Gemini API client
res/
  prompt.txt             # Prompt template with {date}, {dns_white_list}, {report_content}, {analysis_template} placeholders
  analysis_template.html # HTML/CSS template for the email report
reports/                 # Generated reports (gitignored)
```

## Key Conventions

- **LLM module interface**: Every provider in `llm/` must expose `call(prompt, api_key) -> str` and a module-level `MODEL` constant loaded from `config.ini` at import time.
- **Retry policy**: All LLM calls use `tenacity` with `stop_after_attempt(3)` and `wait_exponential(multiplier=1, min=2, max=10)`.
- **Provider fallback**: `analyze_report.py` tries providers in order: Zhipu > MiniMax > DeepSeek > Gemini, using the first one with a non-empty API key env var. If it fails, it falls through to the next.
- **Environment variables**: `ZHIPU_API_KEY`, `MINIMAX_API_KEY`, `DEEPSEEK_API_KEY`, `GEMINI_API_KEY` — at least one must be set for AI analysis.
- **DNS whitelist**: Hardcoded list `DNS_WHITE_LIST` in `analyze_report.py` is injected into the prompt at runtime.
- **Output format**: LLM output is HTML. The raw DNS report is appended as a `<pre>` block inside the HTML before the closing `</body>` tag.
- **Logging**: All scripts log to stderr with a `[tag]` prefix (e.g., `[analyze]`, `[zhipu]`).
- **Reports are gitignored**: `reports/`, `summary_*.txt`, `analysis_*.txt`, and per-IP directories are excluded from git.

## Code Style

- Python: standard library + `requests` + `tenacity`. No frameworks.
- No type annotations used.
- No comments in code (follow existing convention).
- Shell script uses `getopt` for argument parsing, `log()` helper for timestamped output.
- Error handling: LLM failures log a warning and fall through to the next provider; if all fail, the script exits with code 1.
