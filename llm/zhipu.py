import os
import configparser
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_config = configparser.ConfigParser()
_config.read(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
MODEL = _config['llm']['zhipu_model']

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.HTTPError))
)
def call(prompt, api_key):
    url = "https://api.z.ai/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(url, json={
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }, headers=headers)
    response.raise_for_status()
    result = response.json()
    return result['choices'][0]['message']['content']
