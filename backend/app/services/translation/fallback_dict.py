from .base import Translator, TranslationResult
from .token_protector import TokenProtector
import re

# Small, honest offline glossary used ONLY when no neural model is available.
# It is a limited word/phrase lookup - every response is flagged in meta as
# {"fallback": "dictionary"} so the caller never mistakes it for MT output.
# Extend this list freely; it is not meant to replace Opus-MT/NLLB.

EN_RU_PHRASES = {
    "hello world": "привет мир",
    "thank you": "спасибо",
    "thank you very much": "большое спасибо",
    "good morning": "доброе утро",
    "good evening": "добрый вечер",
    "good night": "спокойной ночи",
    "good afternoon": "добрый день",
    "how are you": "как дела",
    "my name is": "меня зовут",
    "nice to meet you": "приятно познакомиться",
    "excuse me": "извините",
    "i am sorry": "извините",
    "i love you": "я тебя люблю",
    "see you": "до свидания",
    "see you later": "до встречи",
    "how much is it": "сколько это стоит",
    "i dont understand": "я не понимаю",
    "do you speak english": "вы говорите по-английски",
    "where is the metro": "где метро",
    "i am a student": "я студент",
    "good night": "спокойной ночи",
}

EN_RU = {
    # greetings / basics
    "hello": "привет",
    "hi": "привет",
    "goodbye": "до свидания",
    "bye": "пока",
    "yes": "да",
    "no": "нет",
    "please": "пожалуйста",
    "thanks": "спасибо",
    "thank": "спасибо",
    "sorry": "извините",
    "welcome": "добро пожаловать",
    "morning": "утро",
    "evening": "вечер",
    "night": "ночь",
    "day": "день",
    "good": "хороший",
    "bad": "плохой",
    "great": "отлично",
    # nouns
    "world": "мир",
    "peace": "мир",
    "friend": "друг",
    "friend.": "друг",
    "student": "студент",
    "teacher": "учитель",
    "university": "университет",
    "school": "школа",
    "book": "книга",
    "house": "дом",
    "home": "дом",
    "city": "город",
    "street": "улица",
    "metro": "метро",
    "water": "вода",
    "bread": "хлеб",
    "tea": "чай",
    "coffee": "кофе",
    "food": "еда",
    "money": "деньги",
    "time": "время",
    "year": "год",
    "month": "месяц",
    "week": "неделя",
    "today": "сегодня",
    "tomorrow": "завтра",
    "yesterday": "вчера",
    "name": "имя",
    "language": "язык",
    "word": "слово",
    "letter": "буква",
    "text": "текст",
    "language.": "язык",
    # pronouns
    "i": "я",
    "you": "ты",
    "he": "он",
    "she": "она",
    "it": "это",
    "we": "мы",
    "they": "они",
    "my": "мой",
    "your": "твой",
    "our": "наш",
    # verbs
    "am": "",
    "is": "",
    "are": "",
    "be": "быть",
    "have": "иметь",
    "want": "хотеть",
    "need": "нужно",
    "know": "знать",
    "love": "любить",
    "like": "нравиться",
    "go": "идти",
    "come": "прийти",
    "see": "видеть",
    "read": "читать",
    "write": "писать",
    "speak": "говорить",
    "say": "сказать",
    "learn": "учить",
    "study": "учиться",
    "work": "работать",
    "live": "жить",
    "eat": "есть",
    "drink": "пить",
    # adjectives / misc
    "russian": "русский",
    "language,": "язык,",
    "english": "английский",
    "new": "новый",
    "old": "старый",
    "big": "большой",
    "small": "маленький",
    "and": "и",
    "or": "или",
    "but": "но",
    "the": "",
    "a": "",
    "an": "",
    "of": "",
    "to": "",
    "in": "в",
    "on": "на",
    "at": "в",
    "with": "с",
    "for": "для",
    "from": "из",
    "very": "очень",
    "not": "не",
    "all": "все",
    "here": "здесь",
    "there": "там",
    # campus / student vocabulary
    "lesson": "урок",
    "lecture": "лекция",
    "exam": "экзамен",
    "test": "тест",
    "homework": "домашняя работа",
    "course": "курс",
    "group": "группа",
    "professor": "профессор",
    "dean": "декан",
    "office": "офис",
    "dormitory": "общежитие",
    "dorm": "общежитие",
    "room": "комната",
    "library": "библиотека",
    "classroom": "аудитория",
    "schedule": "расписание",
    "timetable": "расписание",
    "passport": "паспорт",
    "visa": "виза",
    "document": "документ",
    "form": "форма",
    "signature": "подпись",
    "address": "адрес",
    "phone": "телефон",
    "number": "номер",
    "question": "вопрос",
    "answer": "ответ",
    "example": "пример",
    "exercise": "упражнение",
    "page": "страница",
    "chapter": "глава",
    "note": "записка",
    "pencil": "карандаш",
    "pen": "ручка",
    "paper": "бумага",
    "notebook": "тетрадь",
    "dictionary": "словарь",
    "translate": "переводить",
    "translation": "перевод",
    "understand": "понимать",
    "repeat": "повторять",
    "help": "помощь",
    "please help": "помогите",
    "open": "открыть",
    "close": "закрыть",
    "begin": "начать",
    "finish": "закончить",
    "important": "важный",
    "easy": "лёгкий",
    "difficult": "трудный",
    "difficult.": "трудный",
    "hard": "трудный",
    "easy.": "легко",
    "beautiful": "красивый",
    "beautiful.": "красивый",
    "quickly": "быстро",
    "slowly": "медленно",
    "always": "всегда",
    "never": "никогда",
    "sometimes": "иногда",
    "right": "правильно",
    "wrong": "неправильно",
    "again": "снова",
    "also": "тоже",
    "also,": "тоже,",
    "because": "потому что",
    "because,": "потому что,",
    "when": "когда",
    "where": "где",
    "what": "что",
    "who": "кто",
    "why": "почему",
    "how": "как",
    "many": "много",
    "much": "много",
    "few": "мало",
    "one": "один",
    "two": "два",
    "three": "три",
    "four": "четыре",
    "five": "пять",
    "ten": "десять",
    "twenty": "двадцать",
    "hundred": "сто",
}

# reverse map for ru->en (drop empties and duplicates keep first)
RU_EN = {}
for _en, _ru in EN_RU.items():
    if _ru and _ru not in RU_EN:
        RU_EN[_ru] = _en


class FallbackTranslator(Translator):
    """Offline glossary translator. Used only when neural models are unavailable.
    Every result is flagged as a limited fallback, never presented as full MT.
    """

    def __init__(self):
        self.protector = TokenProtector(prefix="FBK_")
        self.name = "fallback-dictionary"

    def supports(self, src_lang: str, tgt_lang: str) -> bool:
        s, t = src_lang.lower(), tgt_lang.lower()
        return (s == "en" and t == "ru") or (s == "ru" and t == "en")

    def _map_word(self, word: str, table: dict) -> str:
        low = word.lower()
        candidates = [low]
        # simple English plural handling ("documents" -> "document")
        if low.endswith("es") and low[:-2] in table:
            candidates.append(low[:-2])
        if low.endswith("s") and low[:-1] in table:
            candidates.append(low[:-1])
        for c in candidates:
            if c in table:
                trans = table[c]
                if trans == "":
                    return ""
                if word[:1].isupper():
                    return trans[:1].upper() + trans[1:]
                return trans
        return word

    def translate(self, text: str, src_lang: str = "ru", tgt_lang: str = "en", **kwargs) -> TranslationResult:
        if not text or text.strip() == "":
            return TranslationResult(text="", confidence=1.0, meta={"model": self.name})

        s, t = src_lang.lower(), tgt_lang.lower()
        if not self.supports(s, t):
            return TranslationResult(text=text, confidence=0.0, meta={"model": self.name, "error": "unsupported pair"})

        table = EN_RU if s == "en" else RU_EN

        # protect tokens first so numbers/emails/dates survive
        protected, mapping = self.protector.protect(text)

        # 1) phrase-level first (whole protected string match)
        lowered = protected.lower().strip()
        if s == "en":
            phrases = {k.lower(): v for k, v in EN_RU_PHRASES.items()}
        else:
            phrases = {ru.lower(): en for en, ru in EN_RU_PHRASES.items() if ru}
            phrases["привет мир"] = "hello world"

        out_parts = []
        if lowered in phrases:
            out_parts = [phrases[lowered]]
        else:
            # 2) word-level
            tokens = re.split(r"(\s+)", protected)
            for tok in tokens:
                if tok.strip() == "":
                    out_parts.append(tok)
                    continue
                # split trailing punctuation
                m = re.match(r"^([^\wА-Яа-яЁё]+)?([\wА-Яа-яЁё-]+)([^\wА-Яа-яЁё]+)?$", tok)
                if m:
                    pre, core, post = m.group(1) or "", m.group(2), m.group(3) or ""
                    mapped = self._map_word(core, table)
                    out_parts.append(f"{pre}{mapped}{post}")
                else:
                    out_parts.append(self._map_word(tok, table))
        translated = "".join(out_parts)

        restored, all_restored = self.protector.restore(translated, mapping)
        # collapse double spaces created by dropped articles
        restored = re.sub(r"\s{2,}", " ", restored).strip()

        meta = {
            "model": self.name,
            "engine": self.name,
            "fallback": "offline_glossary",
            "notice": "Limited offline glossary - not full machine translation. Install Opus-MT for real quality.",
            "all_placeholders_restored": all_restored,
            "src": src_lang,
            "tgt": tgt_lang,
        }
        # confidence lower than a real model, so UI can flag it
        return TranslationResult(restored, confidence=0.5, meta=meta)
