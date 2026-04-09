import os
import sys
import configparser
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_config = configparser.ConfigParser()
_config.read(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
MODEL = _config['llm']['gemini_model']

def log(msg):
    print(f"[gemini] {msg}", file=sys.stderr)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.HTTPError))
)
def call(prompt, api_key):
    log(f"Calling {MODEL}...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={api_key}"
    response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
    response.raise_for_status()
    result = response.json()
    content = result['candidates'][0]['content']['parts'][0]['text']
    log(f"Response received: {len(content)} chars")
    return content
