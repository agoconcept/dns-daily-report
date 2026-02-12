#!/usr/bin/env python3
import sys
import os
import requests

def analyze_dns_report(report_file, api_key):
    """Analyze DNS report for inappropriate content for kids."""

    with open(report_file, 'r') as f:
        report_content = f.read()

    prompt = f"""Analyze this DNS query report for kids. Identify any concerns regarding:
- Social media platforms (Instagram, TikTok, Snapchat, Facebook, etc.)
- Chat applications (WhatsApp, Telegram, Discord, etc.)
- Adult or inappropriate content
- Gaming platforms with chat features
- Any other age-inappropriate websites

Provide a brief summary in HTML format with:
1. Overall assessment (Safe/Caution/Concern)
2. Specific domains of concern (if any)
3. Recommendations

Add also at the end one HTML formatted table per IP with one column for the domain and another for the number of hits

DNS Report:
{report_content}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    result = response.json()
    return result['candidates'][0]['content']['parts'][0]['text']

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: analyze_report.py <report_file>")
        sys.exit(1)

    report_file = sys.argv[1]
    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    if not os.path.exists(report_file):
        print(f"Error: Report file not found: {report_file}")
        sys.exit(1)

    analysis = analyze_dns_report(report_file, api_key)
    print(analysis)

