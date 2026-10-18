import re


class DirectionDetector:
    def detect(self, text: str) -> str:
        if not text:
            return "auto"
        # Russian/English are LTR; detect strong RTL if any (not expected here)
        rtl_chars = len(re.findall(r'[\u0590-\u05FF\u0600-\u06FF\u0700-\u074F\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
        if rtl_chars > 0 and rtl_chars > len(re.findall(r'[a-zA-Zа-яёА-ЯЁ0-9]', text)) * 0.3:
            return "rtl"
        return "ltr"
