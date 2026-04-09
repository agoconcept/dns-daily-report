import os
import sys
import configparser
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_config = configparser.ConfigParser()
_config.read(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
MODEL = _config['llm']['minimax_model']

def log(msg):
    print(f"[minimax] {msg}", file=sys.stderr)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.HTTPError, RuntimeError))
)
def call(prompt, api_key):
    log(f"Calling {MODEL}...")
    url = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(url, json={
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }, headers=headers)
    response.raise_for_status()
    result = response.json()
    if not result.get('choices'):
        err = result.get('base_resp', {})
        raise RuntimeError(f"MiniMax API error: {err.get('status_code')} {err.get('status_msg')}")
    content = result['choices'][0]['message']['content']
    log(f"Response received: {len(content)} chars")
    return content
