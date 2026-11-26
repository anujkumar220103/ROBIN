# Conservatively cleans extracted PDF text without removing meaning.

import re
import unicodedata


def clean_text(text: str) -> str:
    # Modern embedding models ko context chahiye, isliye stop words ya
    # punctuation aggressively remove nahi karte.
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", "")
    text = "".join(ch for ch in text if ch in "\n\r\t" or not (ord(ch) < 32))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()
