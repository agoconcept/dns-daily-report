#!/usr/bin/env python3
import sys
import os
from google import generativeai as genai

def analyze_dns_report(report_file, api_key):
    """Analyze DNS report for inappropriate content for an 11-year-old."""
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    with open(report_file, 'r') as f:
        report_content = f.read()
    
    prompt = f"""Analyze this DNS query report for an 11-year-old child. Identify any concerns regarding:
- Social media platforms (Instagram, TikTok, Snapchat, Facebook, etc.)
- Chat applications (WhatsApp, Telegram, Discord, etc.)
- Adult or inappropriate content
- Gaming platforms with chat features
- Any other age-inappropriate websites

Provide a brief summary with:
1. Overall assessment (Safe/Caution/Concern)
2. Specific domains of concern (if any)
3. Recommendations

DNS Report:
{report_content}
"""
    
    response = model.generate_content(prompt)
    return response.text

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
