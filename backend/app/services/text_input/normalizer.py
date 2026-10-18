import re
import unicodedata


class TextNormalizer:
    def normalize(self, text: str) -> str:
        if not text:
            return ""
        # Normalize unicode
        text = unicodedata.normalize("NFKC", text)
        # Fix line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Collapse multiple spaces
        text = re.sub(r'[ \t]+', ' ', text)
        # Collapse multiple newlines
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        return text.strip()
