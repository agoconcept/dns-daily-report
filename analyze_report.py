#!/usr/bin/env python3
import sys
import os
import llm.gemini as gemini
import llm.deepseek as deepseek

DNS_WHITE_LIST = [
    "graph.facebook.com",                   # Used just for login screens
    "capcutapi.us",                         # CapCut video editing
    "youtube.com", "googlevideo.com",       # YouTube videos
    "spotify.com",                          # Spotify
    "pinterest.com", "pinimg.com",          # Pinterest
    "amazon.es"                             # Amazon
]

def analyze_dns_report(report_file, analysis_template_file):
    with open(report_file, 'r') as f:
        report_content = f.read()
    with open(analysis_template_file, 'r') as f:
        analysis_template = f.read()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, 'res', 'prompt.txt'), 'r') as f:
        prompt = f.read() \
            .replace('{dns_white_list}', str(DNS_WHITE_LIST)) \
            .replace('{report_content}', report_content) \
            .replace('{analysis_template}', analysis_template)

    gemini_key = os.getenv('GEMINI_API_KEY')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')

    if gemini_key:
        return gemini.call(prompt, gemini_key)
    elif deepseek_key:
        return deepseek.call(prompt, deepseek_key)
    else:
        print("Error: neither GEMINI_API_KEY nor DEEPSEEK_API_KEY is set")
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
    print(analysis + "<hr/><pre>" + report_content + "</pre>")
