"""Azure AI Translator (Text translation, API version 3.0)."""
from __future__ import annotations

import time
import uuid
from pathlib import Path

import requests

from cscaf.translation.machine_translator import MachineTranslator
from cscaf.translation.rate_limiter import RateLimiter


class AzureTranslator(MachineTranslator):
    """Translate paragraphs into English with Azure AI Translator.

    The free tier (F0) gives 2,000,000 characters a month. The service does not report what is left
    through the translation API, so the caller keeps a `UsageLedger`.

    One request takes at most 100 texts and 50,000 characters in total, which is the documented limit
    of the `translate` endpoint. The region header is required for a resource created in a region,
    which is the normal case; a global resource takes "global".
    """

    DEFAULT_ENDPOINT = "https://api.cognitive.microsofttranslator.com"
    RETRY_WAITS = (2, 5, 15, 45, 90, 180)
    TRANSIENT = (429, 500, 502, 503, 504)

    name = "Azure AI Translator v3.0"
    max_texts = 100
    max_characters = 45_000
    monthly_characters = 2_000_000
    characters_per_minute = 30_000

    def __init__(self, key: str, region: str | None = None, endpoint: str = DEFAULT_ENDPOINT,
                 target: str = "en"):
        self.key = key
        self.region = region
        self.endpoint = endpoint.rstrip("/")
        self.target = target
        self.limiter = RateLimiter(self.characters_per_minute)

    @classmethod
    def from_files(cls, folder: Path, target: str = "en") -> "AzureTranslator":
        """Read the credentials from the data folder, or from the environment.

        `AZURE_TRANSLATOR_KEY` / `azure_translator_key.txt` and
        `AZURE_TRANSLATOR_REGION` / `azure_translator_region.txt` (for example "westeurope", or
        "global" for a resource without a region). The endpoint is the global one unless
        `azure_translator_endpoint.txt` names another, which a private or regional endpoint does.
        """
        keys = folder / "keys"
        key = MachineTranslator.read_credential("AZURE_TRANSLATOR_KEY",
                              keys / "azure_translation_key.txt", keys / "azure_translator_key.txt")
        region = MachineTranslator.read_credential("AZURE_TRANSLATOR_REGION",
                                 keys / "azure_translation_region.txt", keys / "azure_translator_region.txt",
                                 required=False)
        endpoint = MachineTranslator.read_credential("AZURE_TRANSLATOR_ENDPOINT",
                                   keys / "azure_translation_endpoint.txt",
                                   keys / "azure_translator_endpoint.txt",
                                   required=False) or cls.DEFAULT_ENDPOINT
        return cls(key, region, endpoint=endpoint, target=target)

    def check(self) -> str:
        """Translate four characters, to prove the key, the region and the endpoint work together."""
        return self.translate(["Test"])[0]

    def translate(self, texts: list[str], source: str | None = None) -> list[str]:
        """Translate one batch into English, retrying while the service asks to slow down.

        `source` names the language of the batch (ISO 639-1, e.g. "nl"); without it Azure detects the
        language itself, and on a paragraph full of English technical terms it may take Dutch or French
        for English and return the text unchanged.
        """
        url = f"{self.endpoint}/translate"
        parameters = {"api-version": "3.0", "to": self.target, "textType": "plain"}
        if source:
            parameters["from"] = source
        headers = {"Ocp-Apim-Subscription-Key": self.key,
                   "Content-Type": "application/json",
                   "X-ClientTraceId": str(uuid.uuid4())}
        if self.region:
            headers["Ocp-Apim-Subscription-Region"] = self.region
        body = [{"Text": text} for text in texts]
        self.limiter.take(sum(len(text) for text in texts))
        for attempt, wait in enumerate((*self.RETRY_WAITS, None)):
            try:
                response = requests.post(url, params=parameters, headers=headers, json=body, timeout=120)
            except requests.RequestException as problem:
                if wait is None:
                    raise SystemExit(f"Azure could not be reached: {problem}")
                print(f"   Azure could not be reached ({type(problem).__name__}), waiting {wait}s "
                      f"(attempt {attempt + 1})")
                time.sleep(wait)
                continue
            if response.status_code in self.TRANSIENT and wait is not None:
                pause = int(response.headers.get("Retry-After", wait))
                print(f"   Azure returned {response.status_code}, waiting {pause}s (attempt {attempt + 1})")
                time.sleep(pause)
                continue
            if response.status_code == 401 and not self.region:
                raise SystemExit("Azure refused the key (401). A resource created in a region needs its "
                                 "region as well: put it in keys/azure_translation_region.txt (the "
                                 "\"Location/Region\" on the resource's Keys and Endpoint page).")
            if response.status_code == 403:
                raise SystemExit("Azure refused the request (403). The monthly free allowance is "
                                 "probably used up, or the key is not valid for this region.")
            if response.status_code >= 400:
                raise SystemExit(f"Azure returned {response.status_code}: {response.text[:400]}")
            return [item["translations"][0]["text"] for item in response.json()]
        raise SystemExit("Azure kept asking to slow down. Stopping; the cache holds what was done.")
