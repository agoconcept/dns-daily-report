import os
import sys
import time
import configparser
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_config = configparser.ConfigParser()
_config.read(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
MODEL = _config['llm']['zhipu_model']

def log(msg):
    print(f"[zhipu] {msg}", file=sys.stderr)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def call(prompt, api_key):
    url = "https://api.z.ai/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(5):
        log(f"Calling {MODEL} (attempt {attempt + 1}/5)...")
        response = requests.post(url, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }, headers=headers)
        if response.status_code == 429 and attempt < 4:
            retry_after = int(response.headers.get('Retry-After', 30))
            log(f"Rate limited, retrying in {retry_after}s...")
            time.sleep(retry_after)
            continue
        break
    response.raise_for_status()
    result = response.json()
    content = result['choices'][0]['message']['content']
    log(f"Response received: {len(content)} chars")
    return content
