#!/usr/bin/env python3
import sys
import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

#LLM = "gemini-flash-latest"
LLM = "gemini-3.1-pro-preview"

DNS_WHITE_LIST = [
    "graph.facebook.com",                   # Used just for login screens
    "capcutapi.us",                         # CapCut video editing
    "youtube.com", "googlevideo.com",       # YouTube videos
    "spotify.com",                          # Spotify
    "pinterest.com", "pinimg.com",          # Pinterest
    "amazon.es"                             # Amazon
]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.HTTPError))
)
def call_gemini_api(url, payload):
    """Call Gemini API with retry logic."""
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def analyze_dns_report(report_file, analysis_template_file, api_key):
    """Analyze DNS report for inappropriate content for kids."""

    with open(report_file, 'r') as f:
        report_content = f.read()

    with open(analysis_template_file, 'r') as f:
        analysis_template = f.read()

    prompt = f"""Analyze the DNS report to detect potential inappropriate
content for an 11 year-old girl.  Identify any concerns regarding:
- Social media platforms (Instagram, TikTok, Snapchat, Facebook, etc.)
- Chat applications (WhatsApp, Telegram, Discord, etc.)
- Potentially unhealthy diet habits
- Adult or inappropriate content
- Gaming platforms with chat features
- Any other age-inappropriate websites

Provide a summary in a nice HTML format with the following sections:
1. Overall assessment (Safe/Caution/Concern)
2. Specific domains of concern (if any)
3. Recommendations

The whole report must be formatted in HTML format, ready to be sent by email,
with a layout of one box for each section. The boxes must have a light gray
colored background. I send an example of how it should be formatted below.

I have already setup a Pi-hole to reduce ads, so ad content should be minimum.
Pi-hole already contains "OISD" (Full) blocklist, and I have sent
YouTube domains to 216.239.38.119 (for Moderate restricted mode).

If some traffic is already blocked, so my daughter cannot access to that
specific domain, do not consider that domain as a potential issue.

Ignore in the analysis this list of domains. I have checked that they are ok:
{DNS_WHITE_LIST}
-----

DNS Report:
{report_content}
-----

This is the analysis template to use as a reference:
{analysis_template}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM}:generateContent?key={api_key}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    result = call_gemini_api(url, payload)
    return result['candidates'][0]['content']['parts'][0]['text']

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: analyze_report.py <report_file> <analysis_template_file>")
        sys.exit(1)

    report_file = sys.argv[1]
    analysis_template_file = sys.argv[2]
    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    if not os.path.exists(report_file):
        print(f"Error: Report file not found: {report_file}")
        sys.exit(1)

    analysis = analyze_dns_report(report_file, analysis_template_file, api_key)
    print(analysis + "<br/>***<br/>" + report_content)

