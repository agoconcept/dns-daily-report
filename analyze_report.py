#!/usr/bin/env python3
import sys
import os
from datetime import date
import llm.zhipu as zhipu
import llm.minimax as minimax
import llm.deepseek as deepseek
import llm.gemini as gemini

DNS_WHITE_LIST = [
    "graph.facebook.com",                   # Used just for login screens
    "capcutapi.us",                         # CapCut video editing
    "youtube.com", "googlevideo.com",       # YouTube videos
    "spotify.com",                          # Spotify
    "pinterest.com", "pinimg.com",          # Pinterest
    "amazon.es",                            # Amazon
    "supercell.com",                        # Brawl Stars / Supercell games
    "poki.com",                             # Poki online games
    "skype.com", "skypedata.akadns.net",    # Skype
]

def log(msg):
    print(f"[analyze] {msg}", file=sys.stderr)

def analyze_dns_report(report_file, analysis_template_file):
    with open(report_file, 'r') as f:
        report_content = f.read()
    log(f"Loaded report: {len(report_content)} chars")

    with open(analysis_template_file, 'r') as f:
        analysis_template = f.read()

    whitelist_str = '\n'.join(f'- {d}' for d in DNS_WHITE_LIST)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, 'res', 'prompt.txt'), 'r') as f:
        prompt = f.read() \
            .replace('{date}', date.today().strftime('%Y-%m-%d')) \
            .replace('{dns_white_list}', whitelist_str) \
            .replace('{report_content}', report_content) \
            .replace('{analysis_template}', analysis_template)
    log(f"Prompt built: {len(prompt)} chars")

    zhipu_key = os.getenv('ZHIPU_API_KEY')
    minimax_key = os.getenv('MINIMAX_API_KEY')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    errors = []
    providers = [
        ("Zhipu", zhipu_key, zhipu),
        ("MiniMax", minimax_key, minimax),
        ("DeepSeek", deepseek_key, deepseek),
        ("Gemini", gemini_key, gemini),
    ]
    for name, key, module in providers:
        if key:
            try:
                log(f"Using {name} ({module.MODEL})")
                result = module.call(prompt, key)
                log(f"Analysis received: {len(result)} chars")
                return result
            except Exception as e:
                errors.append(f"{name}: {e}")
                log(f"WARNING: {name} failed: {e}")
                if any(k for _, k, _ in providers[providers.index((name, key, module))+1:]):
                    log("Trying next provider...")
    log(f"ERROR: All providers failed:\n" + "\n".join(f"  {e}" for e in errors))
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: analyze_report.py <report_file> <analysis_template_file>")
        sys.exit(1)

    report_file, analysis_template_file = sys.argv[1], sys.argv[2]

    if not os.path.exists(report_file):
        print(f"Error: Report file not found: {report_file}")
        sys.exit(1)

    with open(report_file, 'r') as f:
        report_content = f.read()

    analysis = analyze_dns_report(report_file, analysis_template_file)
    raw_injection = f"<hr/><h2>Raw DNS Report</h2><pre>{report_content}</pre>"
    if '</body>' in analysis:
        print(analysis.replace('</body>', f'{raw_injection}</body>'))
    else:
        print(analysis + raw_injection)
