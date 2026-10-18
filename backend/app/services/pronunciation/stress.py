# Basic stress dictionary for common words (placeholder)
STRESS_DICT = {
    'привет': "при'вет",
    'мир': "мир",
    'спасибо': "спаси'бо",
    'пожалуйста': "пожа'луйста",
}


class StressMarker:
    def mark_stress(self, text: str) -> str:
        # Simple word-level stress marking
        words = text.split()
        res = []
        for w in words:
            # Remove punctuation for lookup
            clean = w.strip('.,!?;:')
            if clean.lower() in STRESS_DICT:
                stressed = STRESS_DICT[clean.lower()]
                # Preserve trailing punctuation
                trailing = w[len(clean):]
                res.append(stressed + trailing)
            else:
                res.append(w)
        return ' '.join(res)
