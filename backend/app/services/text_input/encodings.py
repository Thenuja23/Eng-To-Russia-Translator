class EncodingDetector:
    def detect(self, data: bytes) -> str:
        if not data:
            return "utf-8"
        # Simple heuristic for Windows-1251/Cyrillic
        try:
            # Try utf-8 first
            data.decode('utf-8')
            return 'utf-8'
        except UnicodeError:
            # Fall back to cp1251 (common for Russian)
            return 'cp1251'
