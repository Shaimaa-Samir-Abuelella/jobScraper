import requests, json, re, time

class LLMClient:
    def __init__(self, api_base, api_key, model):
        self.api_base = api_base
        self.api_key = api_key
        self.model = model


    def generate_json(self, prompt):

        if not self.api_key:
            raise RuntimeError("LLM_API_KEY missing")

        url = f"{self.api_base}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional freelance consultant."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mostaql-bid-bot.local",
            "X-Title": "Mostaql Bid Bot",
        }

        for attempt in range(1, 4):

            r = requests.post(url, headers= headers, json=payload, timeout=60)

            if not r.ok:
                raise RuntimeError(
                    f"LLM HTTP {r.status_code}: {r.text[:200]}"
                )

            data = r.json()

            content = data["choices"][0]["message"].get("content", "")

            try:
                cleaned = self._clean(content)
                return json.loads(cleaned)

            except Exception as e:

                print(
                    "[LLM] JSON parse failed. Raw response:\n",
                    content[:500],
                )

                if attempt == 3:
                    raise

                time.sleep(2 * attempt)

    def _clean(self, text):
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z0-9]*", "", text)
            text = re.sub(r"```$", "", text)
        s, e = text.find("{"), text.rfind("}")
        return text[s:e+1]
