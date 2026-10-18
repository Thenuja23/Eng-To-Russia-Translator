import re


class LanguageDetector:
    def detect(self, text: str) -> str:
        if not text:
            return "unknown"
        # Count Cyrillic vs Latin
        cyr = len(re.findall(r'[а-яёА-ЯЁ]', text))
        lat = len(re.findall(r'[a-zA-Z]', text))
        total = len(re.findall(r'[a-zA-Zа-яёА-ЯЁ]', text))
        if total == 0:
            return "unknown"
        if cyr > lat:
            return "ru"
        if lat > cyr:
            return "en"
        return "mixed"
    
    def detect_per_line(self, text: str) -> list:
        lines = text.split('\n')
        results = []
        for line in lines:
            results.append({
                'line': line,
                'lang': self.detect(line)
            })
        return results
