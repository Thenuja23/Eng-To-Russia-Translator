"""Curated Russian dictionary used by the offline vocabulary engine.

Each line is one word in a pipe-separated format:

    word|pos|pronunciation|english|sinhala|grammar|ru1|en1|si1|ru2|en2|si2

Keeping the data as text makes it easy to extend by hand and keeps the module
readable. Entries are looked up by their dictionary form; inflected forms are
matched by the small lemmatiser in ``morphology.py``.

Lines starting with ``#`` are comments. A line that does not have all twelve
fields is ignored, so a typo can never break the whole assistant.
"""
from __future__ import annotations

from typing import Dict, List

_RAW = """
# ---------------------------------------------------------------- pronouns
я|pronoun|ya|I|මම|Personal pronoun, first person singular. It is the subject "I". Russian verb endings already show the person, so "я" can be left out when the meaning is clear.|Я студент.|I am a student.|මම සිසුවෙක්.|Я живу в Москве.|I live in Moscow.|මම මොස්කව්හි ජීවත් වෙමි.
ты|pronoun|ty|you (informal, one person)|ඔයා|Personal pronoun, second person singular, used with friends, family and children. Use "вы" with strangers and older people.|Ты говоришь по-русски?|Do you speak Russian?|ඔයා රුසියානු කතා කරනවාද?|Как ты?|How are you?|ඔයාට කොහොමද?
вы|pronoun|vy|you (polite / plural)|ඔබ / ඔබලා|Personal pronoun, second person plural. It is also the polite "you" for one person you do not know well.|Вы студент?|Are you a student?|ඔබ සිසුවෙක්ද?|Вы говорите по-английски?|Do you speak English?|ඔබ ඉංග්‍රීසි කතා කරනවාද?
он|pronoun|on|he|ඔහු|Personal pronoun, third person masculine singular. It replaces a masculine noun.|Он мой друг.|He is my friend.|ඔහු මගේ මිතුරාය.|Он работает здесь.|He works here.|ඔහු මෙහි වැඩ කරයි.
она|pronoun|a-NA|she|ඇය|Personal pronoun, third person feminine singular. It replaces a feminine noun.|Она студентка.|She is a student.|ඇය සිසුවියක්.|Она читает книгу.|She is reading a book.|ඇය පොතක් කියවමින් සිටී.
мы|pronoun|my|we|අපි|Personal pronoun, first person plural.|Мы студенты.|We are students.|අපි සිසුන්.|Мы учим русский язык.|We are learning Russian.|අපි රුසියානු භාෂාව ඉගෙන ගනිමු.
они|pronoun|a-NEE|they|ඔවුන්|Personal pronoun, third person plural, for people and things.|Они дома.|They are at home.|ඔවුන් ගෙදර සිටී.|Они говорят по-русски.|They speak Russian.|ඔවුන් රුසියානු කතා කරයි.
это|pronoun|E-ta|this, it|මෙය / එය|Demonstrative word. Use it to point at something ("this") or to say "this is …". It does not change for gender.|Это моя книга.|This is my book.|මෙය මගේ පොතයි.|Что это?|What is this?|මෙය කුමක්ද?
мой|pronoun|moy|my|මගේ|Possessive pronoun "my". It agrees with the noun it describes: мой дом, моя книга, моё окно.|Это мой дом.|This is my house.|මෙය මගේ නිවසයි.|Мой друг живёт здесь.|My friend lives here.|මගේ මිතුරා මෙහි ජීවත් වේ.
наш|pronoun|nash|our|අපගේ|Possessive pronoun "our". Like all possessives it changes ending to agree with the noun.|Наш университет большой.|Our university is big.|අපගේ විශ්වවිද්‍යාලය විශාලයි.|Это наш преподаватель.|This is our teacher.|මෙය අපගේ ගුරුතුමායි.
кто|pronoun|kto|who|කවුද|Interrogative pronoun for people. It asks about a person, never about a thing.|Кто это?|Who is this?|මේ කවුද?|Кто говорит по-русски?|Who speaks Russian?|කවුද රුසියානු කතා කරන්නේ?
что|pronoun|shto|what; that|කුමක්ද / බව|Pronoun "what" in questions, and also the conjunction "that" in the middle of a sentence.|Что это?|What is this?|මෙය කුමක්ද?|Я знаю, что он студент.|I know that he is a student.|ඔහු සිසුවෙක් බව මම දනිමි.
# ------------------------------------------------------------- conjunctions
и|conjunction|i|and|සහ|Coordinating conjunction. It joins equal words or sentences: A и B.|Мама и папа дома.|Mum and dad are at home.|අම්මා සහ තාත්තා ගෙදර සිටී.|Я читаю и пишу.|I read and write.|මම කියවමි සහ ලියමි.
а|conjunction|a|and, but (mild contrast)|සහ / නමුත්|Coordinating conjunction that compares two facts. It is softer than "но".|Я студент, а он врач.|I am a student, and he is a doctor.|මම සිසුවෙක්, ඔහු වෛද්‍යවරයෙක්.|А ты?|And you?|ඔයා?
но|conjunction|no|but|නමුත්|Coordinating conjunction showing contrast: the second part is surprising.|Дом маленький, но уютный.|The house is small but cosy.|නිවස කුඩායි, නමුත් සුවපහසුයි.|Я устал, но работаю.|I am tired, but I am working.|මම මහන්සියි, නමුත් වැඩ කරමි.
или|conjunction|EE-lee|or|හෝ|Coordinating conjunction offering a choice.|Чай или кофе?|Tea or coffee?|තේද නැත්නම් කෝපිද?|Ты идёшь или нет?|Are you going or not?|ඔයා යනවාද නැද්ද?
потому что|conjunction|pa-ta-MOO shto|because|මොකද|Subordinating conjunction that gives a reason. Two words, always together.|Я дома, потому что я болен.|I am at home because I am ill.|මම අසනීප නිසා ගෙදර සිටිමි.|Он учит русский, потому что работает в России.|He learns Russian because he works in Russia.|ඔහු රුසියාවේ වැඩ කරන නිසා රුසියානු ඉගෙන ගනියි.
если|conjunction|YES-lee|if|නම්|Subordinating conjunction for a condition: "if …".|Если будет время, я приду.|If there is time, I will come.|වෙලාව තිබුණොත් මම එන්නම්.|Если ты хочешь, мы идём.|If you want, we are going.|ඔයාට ඕන නම් අපි යමු.
# ----------------------------------------------------------------- particles
не|particle|ne|not|නැත|Negative particle. Put it directly before the word you want to negate.|Я не понимаю.|I do not understand.|මට තේරෙන්නේ නැත.|Это не мой дом.|This is not my house.|මෙය මගේ නිවස නොවේ.
пожалуйста|particle|pa-ZHAL-sta|please; you're welcome|කරුණාකර|Politeness particle used in requests, and the standard answer to "спасибо".|Дайте, пожалуйста, чай.|Please give me tea.|කරුණාකර තේ දෙන්න.|— Спасибо! — Пожалуйста.|— Thank you! — You're welcome.|— ස්තුතියි! — ස්වාගතයි.
# -------------------------------------------------------------- prepositions
в|preposition|v|in, into, at|තුළ / ...|Preposition "in/into". It takes the prepositional case for a place (в Москве) and the accusative for a direction (в парк).|Я живу в Москве.|I live in Moscow.|මම මොස්කව්හි ජීවත් වෙමි.|Мы идём в парк.|We are going to the park.|අපි උද්‍යානයට යමු.
на|preposition|na|on, at, to|මත|Preposition "on/at". Used for surfaces and for events (на работе, на уроке).|Книга на столе.|The book is on the table.|පොත මේසය මත ඇත.|Я иду на работу.|I am going to work.|මම වැඩට යමි.
с|preposition|s|with; from|සමඟ / සිට|Preposition "with" (+ instrumental case) and "from/down from" (+ genitive).|Я иду с другом.|I am going with a friend.|මම මිතුරෙකු සමඟ යමි.|Он пришёл с работы.|He came from work.|ඔහු වැඩ සිට පැමිණියේය.
из|preposition|iz|from (out of)|සිට|Preposition "from/out of", always with the genitive case.|Я из Шри-Ланки.|I am from Sri Lanka.|මම ශ්‍රී ලංකාවෙන්.|Он вышел из дома.|He left the house.|ඔහු නිවසින් පිටවිය.
к|preposition|k|to (a person)|වෙත|Preposition "to/towards", mostly for people (к врачу).|Я иду к врачу.|I am going to the doctor.|මම දොස්තරට යමි.|Приходи к нам.|Come to us.|අපි ළඟට එන්න.
у|preposition|u|at, by; to have|ළඟ / සතුව|Preposition "at/by". The phrase у меня есть literally means "by me there is" = "I have".|У меня есть книга.|I have a book.|මට පොතක් ඇත.|У дома стоит машина.|A car is standing by the house.|නිවස ළඟ මෝටර් රථයක් ඇත.
для|preposition|dlya|for|සඳහා|Preposition "for", always with the genitive case.|Это подарок для тебя.|This is a present for you.|මෙය ඔයා සඳහා තෑග්ගකි.|Вода для чая.|Water for tea.|තේ සඳහා වතුර.
без|preposition|bez|without|නොමැතිව|Preposition "without", always with the genitive case.|Кофе без сахара.|Coffee without sugar.|සීනි නොමැතිව කෝපි.|Я не могу без музыки.|I cannot live without music.|සංගීතය නොමැතිව මට බැහැ.
о|preposition|o|about|ගැන|Preposition "about", used with the prepositional case (о работе).|Мы говорим о работе.|We talk about work.|අපි වැඩ ගැන කතා කරමු.|Книга о России.|A book about Russia.|රුසියාව ගැන පොතක්.
по|preposition|po|on, along, by|දිගේ / අනුව|Preposition "along/around" (+ dative) and "by/in the manner of" (по-русски).|Я говорю по-русски.|I speak Russian.|මම රුසියානු කතා කරමි.|Мы гуляем по городу.|We walk around the city.|අපි නගරය දිගේ ඇවිදිමු.
# --------------------------------------------------------------- greetings
привет|interjection|pree-VYET|hi, hello (informal)|හායි|Informal greeting for friends, classmates and people your own age.|Привет! Как дела?|Hi! How are you?|හායි! කොහොමද?|Привет, друг!|Hi, friend!|හායි, යාළුවා!
здравствуйте|interjection|ZDRAST-vuy-tye|hello (polite)|ආයුබෝවන්|Polite greeting for strangers, teachers, officials and older people.|Здравствуйте! Меня зовут Анна.|Hello! My name is Anna.|ආයුබෝවන්! මගේ නම ඇනා.|Здравствуйте, вы студент?|Hello, are you a student?|ආයුබෝවන්, ඔබ සිසුවෙක්ද?
спасибо|interjection|spa-SEE-ba|thank you|ස්තුතියි|The everyday word of thanks. Add "большое" for "thank you very much".|Спасибо за помощь!|Thank you for the help!|උදව්වට ස්තුතියි!|Большое спасибо!|Thank you very much!|බොහොම ස්තුතියි!
извините|verb|iz-vee-NEE-tye|excuse me, sorry|සමාවෙන්න|Polite imperative of извинить "to excuse", used as a fixed formula to get attention or apologise.|Извините, где метро?|Excuse me, where is the metro?|සමාවෙන්න, මෙට්‍රෝ කොහේද?|Извините за опоздание.|Sorry for being late.|ප්‍රමාද වීමට සමාවෙන්න.
до свидания|interjection|da svee-DA-nee-ya|goodbye|ගිහින් එන්න|Neutral or polite farewell. Literally "until a meeting".|До свидания! До завтра!|Goodbye! See you tomorrow!|ගිහින් එන්න! හෙට හමුවෙමු!|До свидания, профессор.|Goodbye, professor.|ගිහින් එන්න, මහාචාර්යතුමනි.
пока|interjection|pa-KA|bye; while|ගිහින් එන්නම්|Informal "bye" between friends. As an adverb it means "while, for now".|Пока! Увидимся.|Bye! See you.|ගිහින් එන්නම්! හමුවෙමු.|Пока я жду, я читаю.|While I wait, I read.|මම බලා සිටින අතරතුර කියවමි.
# ------------------------------------------------------------------- numbers
мир|noun|mir|world; peace|ලෝකය / සාමය|Masculine noun ending in a consonant (мир). It means both "world" and "peace"; the sentence decides which. Plural миры is used for "worlds".|Мир очень большой.|The world is very big.|ලෝකය ඉතා විශාලයි.|Мы хотим мира.|We want peace.|අපට සාමය අවශ්‍යයි.
один|numeral|a-DEEN|one|එක|Numeral "one". It behaves like an adjective and agrees: один дом, одна книга, одно окно.|У меня один брат.|I have one brother.|මට එක් සහෝදරයෙක් ඇත.|Я живу один.|I live alone.|මම තනිව ජීවත් වෙමි.
два|numeral|dva|two|දෙක|Numeral "two". With feminine nouns use "две" (две книги).|У нас два урока.|We have two lessons.|අපට පාඩම් දෙකක් ඇත.|Два чая, пожалуйста.|Two teas, please.|කරුණාකර තේ දෙකක්.
три|numeral|tree|three|තුන|Numeral "three". It does not change for gender.|Три студента ждут.|Three students are waiting.|සිසුන් තිදෙනෙක් බලා සිටිති.|Я знаю три слова.|I know three words.|මම වචන තුනක් දනිමි.
пять|numeral|pyat|five|පහ|Numeral "five". After five and above the noun is genitive plural: пять книг.|Пять минут, пожалуйста.|Five minutes, please.|කරුණාකර මිනිත්තු පහක්.|У меня пять книг.|I have five books.|මට පොත් පහක් ඇත.
десять|numeral|DYE-syat|ten|දහය|Numeral "ten". Like all numbers from five up it takes the genitive plural.|Десять студентов в классе.|Ten students are in the classroom.|පන්තියේ සිසුන් දස දෙනෙක් සිටිති.|Дайте десять рублей.|Give me ten roubles.|රුබල් දහයක් දෙන්න.
# --------------------------------------------------------------------- nouns
дом|noun|dom|house, home|නිවස|Masculine noun ending in a hard consonant (дом). Masculine because of the final consonant. Plural: дома; cases add endings (дома, дому, домом, доме).|Это мой дом.|This is my house.|මෙය මගේ නිවසයි.|Я иду домой.|I am going home.|මම ගෙදර යමි.
вода|noun|va-DA|water|වතුර|Feminine noun ending in -а (вода). Feminine because of the -а ending. Plural: воды; the stress stays on the last syllable.|Можно воду?|May I have water?|වතුර ටිකක් දෙන්නද?|Я пью воду.|I drink water.|මම වතුර බොමි.
хлеб|noun|khlyep|bread|පාන්|Masculine noun ending in a consonant (хлеб). Masculine because of the final consonant. It is uncountable, so it normally stays singular.|Купи хлеб, пожалуйста.|Buy bread, please.|කරුණාකර පාන් මිලදී ගන්න.|Я ем хлеб с маслом.|I eat bread with butter.|මම බටර් සමඟ පාන් කමි.
чай|noun|chay|tea|තේ|Masculine noun ending in -й (чай). Masculine because of the final -й.|Хочешь чай?|Do you want tea?|ඔයාට තේ ඕනද?|Я пью чай утром.|I drink tea in the morning.|මම උදෑසන තේ බොමි.
кофе|noun|KO-fye|coffee|කෝපි|Masculine borrowed noun (кофе). It is indeclinable: the form never changes.|Один кофе, пожалуйста.|One coffee, please.|කරුණාකර කෝපි එකක්.|Я люблю кофе без сахара.|I like coffee without sugar.|මම සීනි නැති කෝපි වලට කැමතියි.
еда|noun|ye-DA|food|ආහාර|Feminine noun ending in -а (еда). Feminine because of the -а ending. It is a mass noun, normally uncountable.|Русская еда вкусная.|Russian food is tasty.|රුසියානු ආහාර රසවත්ය.|Здесь есть еда?|Is there food here?|මෙහි ආහාර තිබේද?
книга|noun|KNEE-ga|book|පොත|Feminine noun ending in -а (книга). Feminine because of the -а ending. Plural: книги.|Это интересная книга.|This is an interesting book.|මෙය සිත් ඇදගන්නා පොතකි.|Я читаю книгу.|I am reading a book.|මම පොතක් කියවමි.
школа|noun|SHKO-la|school|පාසල|Feminine noun ending in -а (школа). Feminine because of the -а ending.|Моя школа здесь.|My school is here.|මගේ පාසල මෙහි ඇත.|Дети идут в школу.|The children are going to school.|ළමයි පාසලට යති.
университет|noun|oo-nee-veer-see-TYET|university|විශ්වවිද්‍යාලය|Masculine noun ending in a hard consonant (университет). Masculine because of the final consonant.|Я учусь в университете.|I study at the university.|මම විශ්වවිද්‍යාලයේ ඉගෙන ගනිමි.|Наш университет большой.|Our university is big.|අපගේ විශ්වවිද්‍යාලය විශාලයි.
студент|noun|stoo-DYENT|student (male)|සිසුවා|Masculine noun ending in a consonant (студент), for a male student. The feminine form is студентка.|Он студент.|He is a student.|ඔහු සිසුවෙක්.|Студент читает текст.|The student is reading the text.|සිසුවා පෙළ කියවයි.
студентка|noun|stoo-DYENT-ka|student (female)|සිසුවිය|Feminine noun ending in -а (студентка), for a female student. The masculine form is студент.|Она студентка.|She is a student.|ඇය සිසුවියක්.|Студентка пишет тест.|The student is writing a test.|සිසුවිය පරීක්ෂණයක් ලියයි.
друг|noun|droog|friend (male)|මිතුරා|Masculine noun ending in a consonant (друг). Irregular plural: друзья.|Он мой друг.|He is my friend.|ඔහු මගේ මිතුරාය.|У меня есть друг.|I have a friend.|මට මිතුරෙක් ඇත.
семья|noun|sye-MYA|family|පවුල|Feminine noun ending in -я (семья). Feminine because of the -я ending. Plural: семьи.|Моя семья большая.|My family is big.|මගේ පවුල විශාලයි.|Я люблю свою семью.|I love my family.|මම මගේ පවුලට ආදරෙයි.
мать|noun|mat|mother|අම්මා|Feminine noun ending in -ь (мать). Nouns in -ь can be masculine or feminine, and мать is feminine. Irregular cases: матери, матерью.|Это моя мать.|This is my mother.|මෙය මගේ අම්මායි.|Мать готовит еду.|The mother is cooking food.|අම්මා ආහාර පිසයි.
отец|noun|a-TYETS|father|තාත්තා|Masculine noun ending in a consonant (отец). Irregular: отца, отцу (the -е- disappears).|Мой отец работает.|My father works.|මගේ තාත්තා වැඩ කරයි.|Отец и мать дома.|Father and mother are at home.|තාත්තා සහ අම්මා ගෙදර සිටී.
брат|noun|brat|brother|සහෝදරයා|Masculine noun ending in a consonant (брат). Irregular plural: братья.|У меня два брата.|I have two brothers.|මට සහෝදරයන් දෙදෙනෙක් ඇත.|Мой брат студент.|My brother is a student.|මගේ සහෝදරයා සිසුවෙක්.
сестра|noun|sees-TRA|sister|සහෝදරිය|Feminine noun ending in -а (сестра). Feminine because of the -а ending. Plural: сёстры, with the stress moving.|Моя сестра живёт здесь.|My sister lives here.|මගේ සහෝදරිය මෙහි ජීවත් වේ.|Сестра читает книгу.|The sister is reading a book.|සහෝදරිය පොතක් කියවයි.
город|noun|GO-rat|city|නගරය|Masculine noun ending in a consonant (город). Plural: города, with the stress moving to the end.|Москва — большой город.|Moscow is a big city.|මොස්කව් විශාල නගරයකි.|Я люблю этот город.|I love this city.|මම මේ නගරයට කැමතියි.
улица|noun|OO-lee-tsa|street|වීදිය|Feminine noun ending in -а (улица). Feminine because of the -а ending.|Я живу на улице Ленина.|I live on Lenin Street.|මම ලෙනින් වීදියේ ජීවත් වෙමි.|Улица длинная.|The street is long.|වීදිය දිගයි.
метро|noun|mee-TRO|metro, subway|මෙට්‍රෝ|Neuter borrowed noun (метро). It is indeclinable, so the form never changes.|Где метро?|Where is the metro?|මෙට්‍රෝ දුම්රිය ස්ථානය කොහේද?|Я еду на метро.|I travel by metro.|මම මෙට්‍රෝවෙන් යමි.
работа|noun|ra-BO-ta|work, job|වැඩ / රැකියාව|Feminine noun ending in -а (работа). Feminine because of the -а ending.|Я иду на работу.|I am going to work.|මම වැඩට යමි.|У меня много работы.|I have a lot of work.|මට වැඩ ගොඩක් ඇත.
урок|noun|oo-ROK|lesson|පාඩම|Masculine noun ending in a consonant (урок). Plural: уроки.|Урок начинается утром.|The lesson begins in the morning.|පාඩම උදෑසන ආරම්භ වේ.|Сегодня три урока.|Today there are three lessons.|අද පාඩම් තුනක් ඇත.
слово|noun|SLO-va|word|වචනය|Neuter noun ending in -о (слово). Neuter because of the -о ending. Plural: слова.|Это новое слово.|This is a new word.|මෙය නව වචනයකි.|Я учу десять слов в день.|I learn ten words a day.|මම දිනකට වචන දහයක් ඉගෙන ගනිමි.
язык|noun|ya-ZYK|language; tongue|භාෂාව|Masculine noun ending in a consonant (язык). It means the language you speak, and also the tongue in your mouth.|Русский язык трудный.|The Russian language is difficult.|රුසියානු භාෂාව අමාරුයි.|Я учу язык каждый день.|I study the language every day.|මම දිනපතා භාෂාව ඉගෙන ගනිමි.
вопрос|noun|va-PROS|question|ප්‍රශ්නය|Masculine noun ending in a consonant (вопрос). Plural: вопросы.|У меня есть вопрос.|I have a question.|මට ප්‍රශ්නයක් ඇත.|Это трудный вопрос.|This is a difficult question.|මෙය අමාරු ප්‍රශ්නයකි.
ответ|noun|at-VYET|answer|පිළිතුර|Masculine noun ending in a consonant (ответ). Plural: ответы.|Я знаю ответ.|I know the answer.|මම පිළිතුර දනිමි.|Спасибо за ответ.|Thank you for the answer.|පිළිතුරට ස්තුතියි.
время|noun|VREE-mya|time|වේලාව|Neuter noun ending in -мя (время). Irregular cases: времени, время, временем. Neuter because of the -мя ending.|У меня нет времени.|I have no time.|මට වේලාවක් නැත.|Время идёт быстро.|Time goes quickly.|වේලාව ඉක්මනින් ගෙවෙයි.
день|noun|dyen|day|දවස|Masculine noun ending in -ь (день). Masculine because of the soft -ь after -е. Cases: дня, дню.|Добрый день!|Good afternoon!|සුබ සන්ධ්‍යාවක්!|Каждый день я учусь.|Every day I study.|දිනපතා මම ඉගෙන ගනිමි.
год|noun|got|year|අවුරුද්ද|Masculine noun ending in a consonant (год). In dates it takes a special form: в 2025 году.|Я живу здесь год.|I have lived here for a year.|මම මෙහි අවුරුද්දක් ජීවත් වී ඇත.|Новый год — мой любимый праздник.|New Year is my favourite holiday.|නව අවුරුද්ද මගේ ප්‍රියතම උත්සවයයි.
деньги|noun|DYEN-gee|money|මුදල්|Plural noun (деньги) with no singular in everyday use. Plural because of the -и ending; cases: денег, деньгам.|У меня нет денег.|I have no money.|මට මුදල් නැත.|Деньги в сумке.|The money is in the bag.|මුදල් බෑගයේ ඇත.
магазин|noun|ma-ga-ZEEN|shop, store|වෙළඳසැල|Masculine noun ending in a consonant (магазин).|Магазин рядом.|The shop is nearby.|වෙළඳසැල ළඟයි.|Я иду в магазин.|I am going to the shop.|මම වෙළඳසැලට යමි.
комната|noun|KOM-na-ta|room|කාමරය|Feminine noun ending in -а (комната). Feminine because of the -а ending.|Моя комната маленькая.|My room is small.|මගේ කාමරය කුඩායි.|В комнате есть окно.|There is a window in the room.|කාමරයේ ජනේලයක් ඇත.
окно|noun|ak-NO|window|ජනේලය|Neuter noun ending in -о (окно). Neuter because of the -о ending. Plural: окна.|Открой окно, пожалуйста.|Open the window, please.|කරුණාකර ජනේලය විවෘත කරන්න.|Окно большое.|The window is big.|ජනේලය විශාලයි.
дверь|noun|dvyer|door|දොර|Feminine noun ending in -ь (дверь). Feminine because of the soft sign. Cases: двери, дверью.|Закрой дверь.|Close the door.|දොර වසන්න.|Дверь открыта.|The door is open.|දොර විවෘතයි.
стол|noun|stol|table|මේසය|Masculine noun ending in a consonant (стол). Plural: столы.|Книга на столе.|The book is on the table.|පොත මේසය මත ඇත.|Это новый стол.|This is a new table.|මෙය නව මේසයකි.
телефон|noun|tee-lee-FON|telephone, phone|දුරකථනය|Masculine noun ending in a consonant (телефон).|Где мой телефон?|Where is my phone?|මගේ දුරකථනය කොහේද?|У неё новый телефон.|She has a new phone.|ඇයට නව දුරකථනයක් ඇත.
человек|noun|chee-la-VYEK|person, human|මිනිසා|Masculine noun ending in a consonant (человек). Irregular plural: люди (people).|Это добрый человек.|This is a kind person.|මෙය කරුණාවන්ත මිනිසෙකි.|В комнате три человека.|There are three people in the room.|කාමරයේ පුද්ගලයන් තිදෙනෙක් සිටිති.
ребёнок|noun|ree-BYO-nak|child|දරුවා|Masculine noun ending in a consonant (ребёнок). Irregular plural: дети (children).|Ребёнок спит.|The child is sleeping.|දරුවා නිදාගෙන සිටී.|У них два ребёнка.|They have two children.|ඔවුන්ට දරුවන් දෙදෙනෙක් ඇත.
имя|noun|EE-mya|name, first name|නම|Neuter noun ending in -мя (имя). Irregular cases: имени, именем.|Как твоё имя?|What is your name?|ඔයාගේ නම මොකක්ද?|Моё имя Анна.|My name is Anna.|මගේ නම ඇනා.
жизнь|noun|zheezn|life|ජීවිතය|Feminine noun ending in -ь (жизнь). Feminine because of the soft sign. Cases: жизни, жизнью.|Жизнь в городе быстрая.|Life in the city is fast.|නගරයේ ජීවිතය වේගවත්ය.|Я люблю эту жизнь.|I love this life.|මම මේ ජීවිතයට කැමතියි.
любовь|noun|lyu-BOF|love|ආදරය|Feminine noun ending in -ь (любовь). Feminine because of the soft sign. Cases: любви, любовью.|Любовь — это важно.|Love is important.|ආදරය වැදගත්ය.|Это история о любви.|This is a story about love.|මෙය ආදරය ගැන කතාවකි.
# ---------------------------------------------------------------- adjectives
хороший|adjective|ha-RO-shee|good|හොඳ|Adjective with the soft stem ending -ий. It describes a noun and agrees with it: хороший дом, хорошая книга, хорошее окно.|Это хороший фильм.|This is a good film.|මෙය හොඳ චිත්‍රපටයකි.|У тебя хорошая работа.|You have a good job.|ඔයාට හොඳ රැකියාවක් ඇත.
плохой|adjective|pla-KHOY|bad|නරක|Adjective with a stressed ending -ой. It agrees with the noun: плохой день, плохая идея.|Сегодня плохой день.|Today is a bad day.|අද නරක දවසක්.|Это плохая идея.|That is a bad idea.|එය නරක අදහසකි.
большой|adjective|bal-SHOY|big, large|විශාල|Adjective with a stressed ending -ой. Masculine большой, feminine большая, neuter большое.|У них большой дом.|They have a big house.|ඔවුන්ට විශාල නිවසක් ඇත.|Это большая проблема.|This is a big problem.|මෙය විශාල ගැටලුවකි.
маленький|adjective|MA-len-kee|small, little|කුඩා|Adjective with the soft stem ending -ий. Masculine маленький, feminine маленькая, neuter маленькое.|Маленький ребёнок спит.|The little child is sleeping.|කුඩා දරුවා නිදාගෙන සිටී.|У меня маленькая комната.|I have a small room.|මට කුඩා කාමරයක් ඇත.
новый|adjective|NO-vy|new|නව|Adjective with the hard ending -ый. It agrees with the noun: новый телефон, новая книга, новое слово.|У меня новый телефон.|I have a new phone.|මට නව දුරකථනයක් ඇත.|Это новая книга.|This is a new book.|මෙය නව පොතකි.
старый|adjective|STA-ry|old|පැරණි|Adjective with the hard ending -ый. It means "old" for things and for people.|Это старый дом.|This is an old house.|මෙය පැරණි නිවසකි.|Мой старый друг живёт здесь.|My old friend lives here.|මගේ පැරණි මිතුරා මෙහි ජීවත් වේ.
красивый|adjective|kra-SEE-vy|beautiful, handsome|ලස්සන / සුන්දර|Adjective with the hard ending -ый. It describes appearance and agrees with the noun: красивый дом, красивая девушка, красивое платье.|Это красивый дом.|This is a beautiful house.|මෙය ලස්සන නිවසකි.|У неё красивое платье.|She has a beautiful dress.|ඇයට ලස්සන ඇඳුමක් තිබේ.
трудный|adjective|TROOD-ny|difficult, hard|අමාරු|Adjective with the hard ending -ый. Use it for tasks, texts and exams.|Это трудный текст.|This is a difficult text.|මෙය අමාරු පෙළකි.|Русский язык трудный, но интересный.|Russian is difficult but interesting.|රුසියානු අමාරුයි, නමුත් සිත් ඇදගන්නා සුළුය.
лёгкий|adjective|LYOKH-kee|easy; light|පහසු / සැහැල්ලු|Adjective with the soft stem ending -ий. It means "easy" for tasks and "light" for weight.|Это лёгкий вопрос.|This is an easy question.|මෙය පහසු ප්‍රශ්නයකි.|Урок был лёгкий.|The lesson was easy.|පාඩම පහසු විය.
быстрый|adjective|BYST-ry|fast, quick|වේගවත්|Adjective with the hard ending -ый. It describes nouns; the matching adverb is быстро.|Это быстрый поезд.|This is a fast train.|මෙය වේගවත් දුම්රියකි.|У него быстрый интернет.|He has fast internet.|ඔහුට වේගවත් අන්තර්ජාලයක් ඇත.
медленный|adjective|MYED-len-ny|slow|මන්දගාමී|Adjective with the hard ending -ый. It describes nouns; the matching adverb is медленно.|Это медленный автобус.|This is a slow bus.|මෙය මන්දගාමී බස් රථයකි.|У нас медленный интернет.|We have slow internet.|අපට මන්දගාමී අන්තර්ජාලයක් ඇත.
важный|adjective|VAZH-ny|important|වැදගත්|Adjective with the hard ending -ый.|Это важный вопрос.|This is an important question.|මෙය වැදගත් ප්‍රශ්නයකි.|У меня важная встреча.|I have an important meeting.|මට වැදගත් හමුවීමක් ඇත.
русский|adjective|ROOS-kee|Russian|රුසියානු|Adjective with the soft stem ending -ий, made from the noun Россия. It is also used as a noun: русский = a Russian man.|Я учу русский язык.|I am learning the Russian language.|මම රුසියානු භාෂාව ඉගෙන ගනිමි.|Это русская книга.|This is a Russian book.|මෙය රුසියානු පොතකි.
интересный|adjective|in-tee-RYES-ny|interesting|සිත් ඇදගන්නා|Adjective with the hard ending -ый. The matching adverb is интересно.|Это интересный фильм.|This is an interesting film.|මෙය සිත් ඇදගන්නා චිත්‍රපටයකි.|У неё интересная работа.|She has an interesting job.|ඇයට සිත් ඇදගන්නා රැකියාවක් ඇත.
вкусный|adjective|VKOOS-ny|tasty, delicious|රසවත්|Adjective with the hard ending -ый. It describes food.|Это вкусный суп.|This is tasty soup.|මෙය රසවත් සුප් එකකි.|Русская еда очень вкусная.|Russian food is very tasty.|රුසියානු ආහාර ඉතා රසවත්ය.
холодный|adjective|ha-LOD-ny|cold|සීතල|Adjective with the hard ending -ый. It describes things and weather; the adverb is холодно.|Сегодня холодный день.|Today is a cold day.|අද සීතල දවසක්.|Дай мне холодную воду.|Give me cold water.|මට සීතල වතුර දෙන්න.
дорогой|adjective|da-ra-GOY|expensive; dear|මිල අධික / ආදරණීය|Adjective with a stressed ending -ой. It means "expensive" for things and "dear" when addressing someone.|Это дорогой телефон.|This is an expensive phone.|මෙය මිල අධික දුරකථනයකි.|Дорогая мама, здравствуй!|Dear mother, hello!|ආදරණීය අම්මේ, ආයුබෝවන්!
молодой|adjective|ma-la-DOY|young|තරුණ|Adjective with a stressed ending -ой. Masculine молодой, feminine молодая.|Он молодой учитель.|He is a young teacher.|ඔහු තරුණ ගුරුවරයෙකි.|У нас молодая команда.|We have a young team.|අපට තරුණ කණ්ඩායමක් ඇත.
# -------------------------------------------------------------------- adverbs
хорошо|adverb|ha-ra-SHO|well, fine|හොඳින්|Adverb formed from the adjective хороший with -о. It describes how an action is done, or a general state ("it is good").|Она хорошо говорит по-русски.|She speaks Russian well.|ඇය රුසියානු හොඳින් කතා කරයි.|Всё хорошо.|Everything is fine.|සියල්ල හොඳයි.
плохо|adverb|PLO-kha|badly, poorly|නරක ලෙස|Adverb formed from the adjective плохой with -о.|Я плохо понимаю.|I understand poorly.|මට හොඳින් තේරෙන්නේ නැත.|Он плохо спит.|He sleeps badly.|ඔහු නරක ලෙස නිදාගනී.
быстро|adverb|BYST-ra|quickly, fast|වේගයෙන්|Adverb formed from the adjective быстрый with -о. It describes a verb, not a noun.|Он быстро читает.|He reads quickly.|ඔහු ඉක්මනින් කියවයි.|Время идёт быстро.|Time goes quickly.|වේලාව ඉක්මනින් ගෙවෙයි.
медленно|adverb|MYED-len-na|slowly|සෙමින්|Adverb formed from the adjective медленный with -о.|Пожалуйста, говорите медленно.|Please speak slowly.|කරුණාකර සෙමින් කතා කරන්න.|Автобус едет медленно.|The bus goes slowly.|බස් රථය සෙමින් ධාවනය වේ.
много|adverb|MNO-ga|a lot, much, many|බොහෝ|Adverb of quantity. It is used with uncountable nouns and with plural nouns in the genitive case.|У меня много работы.|I have a lot of work.|මට වැඩ ගොඩක් ඇත.|Он читает много книг.|He reads many books.|ඔහු පොත් බොහෝ කියවයි.
мало|adverb|MA-la|little, few|අල්ප|Adverb of quantity, the opposite of много.|У нас мало времени.|We have little time.|අපට වේලාව අල්පය.|Он мало говорит.|He speaks little.|ඔහු අල්ප වශයෙන් කතා කරයි.
очень|adverb|O-chen|very|ඉතා|Adverb that makes an adjective or another adverb stronger.|Это очень важно.|This is very important.|මෙය ඉතා වැදගත්.|Она очень хорошо готовит.|She cooks very well.|ඇය ඉතා හොඳින් ආහාර පිසයි.
сейчас|adverb|see-CHAHS|now, right now|දැන්|Adverb of time for the present moment.|Я сейчас работаю.|I am working right now.|මම දැන් වැඩ කරමි.|Сейчас три часа.|It is three o'clock now.|දැන් වේලාව තුනයි.
здесь|adverb|zdyes|here|මෙහි|Adverb of place for "here".|Я здесь живу.|I live here.|මම මෙහි ජීවත් වෙමි.|Здесь нет метро.|There is no metro here.|මෙහි මෙට්‍රෝ නැත.
там|adverb|tam|there|එහි|Adverb of place for "there".|Магазин там.|The shop is there.|වෙළඳසැල එහි ඇත.|Я работаю там.|I work there.|මම එහි වැඩ කරමි.
# --------------------------------------------------------------------- verbs
быть|verb|byt|to be|වීම|Verb, imperfective. Infinitive: быть. Russian normally drops "to be" in the present tense ("Я студент" = I am a student) and uses был/была/было/были in the past.|Я хочу быть врачом.|I want to be a doctor.|මට වෛද්‍යවරයෙකු වීමට අවශ්‍යයි.|Вчера я был дома.|Yesterday I was at home.|ඊයේ මම ගෙදර සිටියෙමි.
хотеть|verb|ha-TYET|to want|අවශ්‍ය වීම|Verb, imperfective. Infinitive: хотеть. Present: я хочу, ты хочешь, он хочет, мы хотим, они хотят.|Я хочу чай.|I want tea.|මට තේ ඕනෑ.|Она хочет учиться в России.|She wants to study in Russia.|ඇය රුසියාවේ ඉගෙන ගැනීමට අවශ්‍යයි.
знать|verb|znat|to know|දැන සිටීම|Verb, imperfective. Infinitive: знать. Present: я знаю, ты знаешь, он знает.|Я знаю это слово.|I know this word.|මම මේ වචනය දනිමි.|Ты знаешь, где метро?|Do you know where the metro is?|මෙට්‍රෝ කොහේද කියා ඔයා දන්නවාද?
любить|verb|lyu-BEET|to love, to like|ආදරය කිරීම|Verb, imperfective. Infinitive: любить. Present: я люблю, ты любишь, он любит.|Я люблю русскую музыку.|I love Russian music.|මම රුසියානු සංගීතයට ආදරෙයි.|Она любит читать.|She loves to read.|ඇය කියවීමට කැමතියි.
идти|verb|eed-TEE|to go on foot|ගමන් කිරීම|Verb, imperfective and unidirectional. Infinitive: идти. Present: я иду, ты идёшь, он идёт. For vehicles use ехать.|Я иду в магазин.|I am going to the shop.|මම වෙළඳසැලට යමි.|Куда ты идёшь?|Where are you going?|ඔයා කොහේ යනවාද?
видеть|verb|VEE-dyet|to see|දැකීම|Verb, imperfective. Infinitive: видеть. Present: я вижу, ты видишь, он видит.|Я вижу дом.|I see the house.|මම නිවස දකිමි.|Ты видишь это слово?|Do you see this word?|ඔයා මේ වචනය දකිනවාද?
читать|verb|chee-TAT|to read|කියවීම|Verb, imperfective. Infinitive: читать. Present: я читаю, ты читаешь, он читает.|Я читаю книгу.|I am reading a book.|මම පොතක් කියවමි.|Он читает по-русски.|He reads in Russian.|ඔහු රුසියානු භාෂාවෙන් කියවයි.
писать|verb|pee-SAT|to write|ලිවීම|Verb, imperfective. Infinitive: писать. Present: я пишу, ты пишешь, он пишет.|Я пишу письмо.|I am writing a letter.|මම ලිපියක් ලියමි.|Она пишет тест.|She is writing a test.|ඇය පරීක්ෂණයක් ලියයි.
говорить|verb|ga-va-REET|to speak, to talk|කතා කිරීම|Verb, imperfective. Infinitive: говорить. Present: я говорю, ты говоришь, он говорит.|Я говорю по-русски.|I speak Russian.|මම රුසියානු කතා කරමි.|Мы говорим о работе.|We are talking about work.|අපි වැඩ ගැන කතා කරමු.
понимать|verb|pa-nee-MAT|to understand|තේරුම් ගැනීම|Verb, imperfective. Infinitive: понимать. Present: я понимаю, ты понимаешь.|Я понимаю вопрос.|I understand the question.|මම ප්‍රශ්නය තේරුම් ගනිමි.|Вы понимаете по-английски?|Do you understand English?|ඔබ ඉංග්‍රීසි තේරුම් ගන්නවාද?
учить|verb|oo-CHEET|to learn, to study something|ඉගෙන ගැනීම|Verb, imperfective. Infinitive: учить. It takes a direct object: учить слова = to learn words.|Я учу русские слова.|I am learning Russian words.|මම රුසියානු වචන ඉගෙන ගනිමි.|Он учит язык каждый день.|He studies the language every day.|ඔහු දිනපතා භාෂාව ඉගෙන ගනියි.
учиться|verb|oo-CHEET-sya|to study at a place|ඉගෙන ගැනීම|Verb, imperfective and reflexive (ends in -ся). Infinitive: учиться. Use it for studying at a school or university.|Я учусь в университете.|I study at the university.|මම විශ්වවිද්‍යාලයේ ඉගෙන ගනිමි.|Она учится хорошо.|She studies well.|ඇය හොඳින් ඉගෙන ගනියි.
работать|verb|ra-BO-tat|to work|වැඩ කිරීම|Verb, imperfective. Infinitive: работать. Present: я работаю, ты работаешь, он работает.|Я работаю в школе.|I work at a school.|මම පාසලක වැඩ කරමි.|Он работает много.|He works a lot.|ඔහු බොහෝ වැඩ කරයි.
жить|verb|zheet|to live|ජීවත් වීම|Verb, imperfective. Infinitive: жить. Present: я живу, ты живёшь, он живёт.|Я живу в Москве.|I live in Moscow.|මම මොස්කව්හි ජීවත් වෙමි.|Где ты живёшь?|Where do you live?|ඔයා ජීවත් වන්නේ කොහේද?
есть|verb|yest|to eat; there is|කෑම / ඇත|Verb, imperfective. Infinitive: есть (to eat). The same word also means "there is/are": Здесь есть еда.|Я хочу есть.|I want to eat.|මට කන්න ඕනෑ.|Здесь есть метро.|There is a metro here.|මෙහි මෙට්‍රෝ තිබේ.
пить|verb|peet|to drink|බීම|Verb, imperfective. Infinitive: пить. Present: я пью, ты пьёшь, он пьёт.|Я пью чай.|I drink tea.|මම තේ බොමි.|Что ты пьёшь?|What are you drinking?|ඔයා බොන්නේ මොකක්ද?
делать|verb|DYE-lat|to do, to make|කිරීම|Verb, imperfective. Infinitive: делать. Present: я делаю, ты делаешь, он делает.|Что ты делаешь?|What are you doing?|ඔයා මොකද කරන්නේ?|Я делаю домашнюю работу.|I am doing homework.|මම ගෙදර වැඩ කරමි.
дать|verb|dat|to give|දීම|Verb, perfective. Infinitive: дать. Future: я дам, ты дашь, он даст.|Дай мне воду, пожалуйста.|Give me water, please.|කරුණාකර මට වතුර දෙන්න.|Я дам тебе книгу.|I will give you the book.|මම ඔයාට පොත දෙන්නම්.
купить|verb|koo-PEET|to buy|මිලදී ගැනීම|Verb, perfective. Infinitive: купить. Past: купил, купила.|Я хочу купить хлеб.|I want to buy bread.|මට පාන් මිලදී ගන්න ඕනෑ.|Она купила новый телефон.|She bought a new phone.|ඇය නව දුරකථනයක් මිලදී ගත්තාය.
открыть|verb|at-KRYT|to open|විවෘත කිරීම|Verb, perfective. Infinitive: открыть.|Открой окно.|Open the window.|ජනේලය විවෘත කරන්න.|Магазин открыт.|The shop is open.|වෙළඳසැල විවෘතයි.
помочь|verb|pa-MOCH|to help|උදව් කිරීම|Verb, perfective. Infinitive: помочь. The imperfective partner is помогать.|Помоги мне, пожалуйста.|Help me, please.|කරුණාකර මට උදව් කරන්න.|Он помог мне с работой.|He helped me with the work.|ඔහු වැඩේට මට උදව් කළේය.
ждать|verb|zhdat|to wait|බලා සිටීම|Verb, imperfective. Infinitive: ждать. Present: я жду, ты ждёшь, он ждёт.|Я жду автобус.|I am waiting for the bus.|මම බස් රථය එනතුරු බලා සිටිමි.|Жди меня здесь.|Wait for me here.|මෙහි මා එනතුරු බලා සිටින්න.
думать|verb|DOO-mat|to think|සිතීම|Verb, imperfective. Infinitive: думать. Present: я думаю, ты думаешь, он думает.|Я думаю о тебе.|I am thinking about you.|මම ඔයා ගැන සිතමි.|Что ты думаешь?|What do you think?|ඔයා මොකද හිතන්නේ?
мочь|verb|moch|to be able to, can|හැකි වීම|Verb, imperfective. Infinitive: мочь. Present: я могу, ты можешь, он может.|Я могу помочь.|I can help.|මට උදව් කරන්න පුළුවන්.|Он может читать по-русски.|He can read Russian.|ඔහුට රුසියානු කියවිය හැකිය.
начинать|verb|na-chee-NAT|to begin, to start|ආරම්භ කිරීම|Verb, imperfective. Infinitive: начинать. The perfective partner is начать.|Мы начинаем урок.|We are starting the lesson.|අපි පාඩම ආරම්භ කරමු.|Я начинаю понимать.|I am beginning to understand.|මම තේරුම් ගැනීම ආරම්භ කරමි.
# END
"""


def _parse(block: str) -> Dict[str, dict]:
    entries: Dict[str, dict] = {}
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 12:
            continue
        word, pos, pron, english, sinhala, grammar = parts[:6]
        ex = parts[6:12]
        if not word or not english or not sinhala:
            continue
        entries[word.lower()] = {
            "word": word,
            "pos": pos,
            "pron": pron,
            "en": english,
            "si": sinhala,
            "grammar": grammar,
            "examples": [
                {"ru": ex[0], "en": ex[1], "si": ex[2]},
                {"ru": ex[3], "en": ex[4], "si": ex[5]},
            ],
        }
    return entries


LEXICON: Dict[str, dict] = _parse(_RAW)

# Longest first so "потому что" wins over "что" when matching phrases.
PHRASES: List[str] = sorted(
    (word for word in LEXICON if " " in word), key=len, reverse=True
)


# Irregular forms the ending rules cannot reduce correctly. Especially verbs,
# whose present tense often changes the stem (хотеть → хочу, мочь → могу).
FORM_MAP = {
    "хочу": "хотеть", "хочешь": "хотеть", "хочет": "хотеть", "хотим": "хотеть",
    "хотите": "хотеть", "хотят": "хотеть",
    "знаю": "знать", "знаешь": "знать", "знает": "знать", "знают": "знать",
    "люблю": "любить", "любишь": "любить", "любит": "любить", "любим": "любить",
    "любите": "любить", "любят": "любить",
    "иду": "идти", "идёшь": "идти", "идёт": "идти", "идём": "идти", "идёте": "идти",
    "идут": "идти", "шёл": "идти", "шла": "идти", "шли": "идти",
    "вижу": "видеть", "видишь": "видеть", "видит": "видеть", "видят": "видеть",
    "пишу": "писать", "пишешь": "писать", "пишет": "писать", "пишут": "писать",
    "говорю": "говорить", "говоришь": "говорить", "говорит": "говорить",
    "говорим": "говорить", "говорите": "говорить", "говорят": "говорить",
    "учу": "учить", "учишь": "учить", "учит": "учить", "учат": "учить",
    "учусь": "учиться", "учишься": "учиться", "учится": "учиться",
    "учатся": "учиться",
    "живу": "жить", "живёшь": "жить", "живёт": "жить", "живут": "жить",
    "ем": "есть", "ешь": "есть", "ест": "есть", "едим": "есть", "едят": "есть",
    "пью": "пить", "пьёшь": "пить", "пьёт": "пить", "пьют": "пить",
    "могу": "мочь", "можешь": "мочь", "может": "мочь", "можем": "мочь",
    "можете": "мочь", "могут": "мочь", "мог": "мочь", "могла": "мочь",
    "дам": "дать", "дашь": "дать", "даст": "дать", "дадут": "дать",
    "куплю": "купить", "купишь": "купить", "купит": "купить", "купил": "купить",
    "купила": "купить", "купили": "купить",
    "открою": "открыть", "откроешь": "открыть", "откроет": "открыть",
    "помогу": "помочь", "поможешь": "помочь", "поможет": "помочь",
    "помог": "помочь", "помогла": "помочь", "помогли": "помочь",
    "жду": "ждать", "ждёшь": "ждать", "ждёт": "ждать", "ждут": "ждать",
    "друзья": "друг", "друзей": "друг", "друзьям": "друг",
    "братья": "брат", "сёстры": "сестра", "матери": "мать", "матерью": "мать",
    "отца": "отец", "отцу": "отец", "отцом": "отец",
    "времени": "время", "временем": "время", "имени": "имя", "именем": "имя",
    "денег": "деньги", "деньгам": "деньги", "деньгами": "деньги",
    "люди": "человек", "людей": "человек", "людям": "человек",
    "дети": "ребёнок", "детей": "ребёнок", "детям": "ребёнок",
    "книги": "книга", "книгу": "книга", "книгой": "книга", "книг": "книга",
    "работы": "работа", "работу": "работа", "работой": "работа",
    "жизни": "жизнь", "жизнью": "жизнь", "любви": "любовь", "любовью": "любовь",
    "языка": "язык", "языку": "язык", "языком": "язык",
    "города": "город", "городе": "город", "городом": "город",
    "столы": "стол", "стола": "стол", "столом": "стол",
    "окна": "окно", "окну": "окно", "окном": "окно",
    "двери": "дверь", "дверью": "дверь",
    "магазина": "магазин", "магазине": "магазин",
    "телефона": "телефон", "телефоне": "телефон",
    "вопросы": "вопрос", "вопроса": "вопрос", "ответы": "ответ", "ответа": "ответ",
    "уроки": "урок", "урока": "урок", "уроке": "урок",
}


def lookup(word: str) -> dict | None:
    """Exact dictionary-form lookup (case-insensitive)."""
    return LEXICON.get((word or "").strip().lower())


def lookup_form(word: str) -> dict | None:
    """Lookup through the irregular-form table, then the dictionary."""
    key = (word or "").strip().lower()
    lemma = FORM_MAP.get(key)
    if lemma:
        entry = LEXICON.get(lemma)
        if entry:
            return entry
    return LEXICON.get(key)


def size() -> int:
    return len(LEXICON)
