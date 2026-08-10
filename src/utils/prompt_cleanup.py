import re

# Asking the model not to use these words only half works - it reaches for them
# anyway - so they get stripped here instead. None of them describe anything
# that can actually appear in an image.
CLICHE_WORDS = [
    "photorealistic", "hyperrealistic", "hyper-realistic", "ultra-realistic",
    "photo-realistic", "stunning", "breathtaking", "majestic", "vibrant",
    "bustling", "nestled", "serene", "tranquil", "pristine", "placid",
    "nostalgic", "otherworldly", "ethereal", "timeless", "idyllic",
    "picturesque", "quaint", "mesmerizing", "mesmerising", "captivating",
    "enchanting", "evocative", "awe-inspiring", "magical", "dreamlike",
    "cinematic", "masterpiece", "exquisite", "immaculate", "breath-taking",
    "sublime", "iconic", "lush",
]

# Sentences that editorialise rather than describe. The model likes to close on
# one of these, which spends the image model's limited prompt budget on words
# that produce no pixels.
COMMENTARY_MARKERS = [
    "portrayal", "glimpse", "testament", "speaks of", "speak of", "evoking",
    "evokes", "conveying", "conveys", "sense of", "essence", "reminder",
    "reminding", "reminds", "symboliz", "symbolis", "narrative", "story of",
    "tapestry", "hallmark", "underscor", "reflects the", "reflecting the",
    "spirit of", "not through the lens", "completing the", "serving as",
    "rather than its", "as if waiting",
]

MAX_WORDS = 200
MIN_SENTENCES = 3
MAX_DROPPED_FRACTION = 0.5

# Adverbs get absorbed with the adjective they qualify, otherwise removing
# "otherworldly" from "an almost otherworldly appearance" strands the "almost".
_ADVERBS = (r"almost|quite|rather|very|somewhat|slightly|truly|utterly|"
            r"remarkably|strikingly|absolutely|incredibly|deeply|oddly|so")

# A cliche followed by one of these is not modifying a noun, so deleting it in
# place would leave the sentence dangling.
_FUNCTION_WORDS = (r"if|and|or|but|of|in|on|at|to|with|that|which|when|while|"
                   r"as|for|from|by|though|although|yet|nor|because")

_CLICHE = "|".join(
    re.escape(word) for word in sorted(CLICHE_WORDS, key=len, reverse=True))

# Left behind when a removal breaks the grammar - the sentence gets dropped
# whole rather than sent to the image model in pieces.
# Nouns that carry no meaning once their modifier is gone - "an almost
# otherworldly appearance" becomes "an appearance", which is grammatical but
# describes nothing.
_HOLLOW_NOUNS = (r"appearance|quality|feel|atmosphere|aesthetic|mood|"
                 r"ambiance|ambience|character|air")

_COPULA = (r"is|are|was|were|be|been|being|isn't|aren't|wasn't|weren't|"
           r"looks?|seems?|appears?|feels?|felt|remains?")

_BROKEN_PATTERNS = [
    rf"\b(?:an?|the)\s+(?:{_FUNCTION_WORDS})\b",
    r"\b(?:an?|the)\s*[.,;:]",
    rf"\b(?:{_COPULA})\s*[.,;:]",
    rf"\b(?:{_ADVERBS})\s*[.,;:]",
    r"^\s*[.,;:]",
    r"\b(?:an?|the)\s+(?:an?|the)\b",
    # a negated copula running straight into a preposition is what's left when
    # "isn't pristine, with ..." loses its adjective
    rf"\b(?:isn't|aren't|wasn't|weren't|is not|are not|was not|were not)\s+"
    rf"(?:{_FUNCTION_WORDS})\b",
    rf"\ban?\s+(?:{_HOLLOW_NOUNS})\b",
]

_REMOVAL_PATTERNS = [
    # adjective list: "a vibrant, bustling market" -> "a market", but only when
    # what follows is another describing word rather than a conjunction. The
    # lookahead sits directly after the comma and spans the spaces itself -
    # letting \s* consume them first lets it backtrack and match at a space,
    # where no word can match and the guard silently passes.
    rf"\b(?:(?:{_ADVERBS})\s+)?(?:{_CLICHE})\b\s*,(?!\s*(?:{_FUNCTION_WORDS})\b)\s*",
    # trailing item in a list: "..., serene"
    rf"\s*,\s*(?:(?:{_ADVERBS})\s+)?(?:{_CLICHE})\b",
    # plain modifier, with any adverb qualifying it
    rf"\b(?:(?:{_ADVERBS})\s+)?(?:{_CLICHE})\b\s*",
]


def _fix_articles(text):
    """After a word is removed, 'an ethereal glow' becomes 'an glow'."""
    def repl(match):
        article, following = match.group(1), match.group(2)
        correct = "an" if following[0].lower() in "aeiou" else "a"
        if article[0].isupper():
            correct = correct.capitalize()
        return f"{correct} {following}"

    return re.sub(r'\b([Aa]|[Aa]n)\s+([A-Za-z]\w*)', repl, text)


def _tidy(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([,.;:!?])', r'\1', text)
    text = re.sub(r'([,;:])\1+', r'\1', text)
    text = re.sub(r',\s*\.', '.', text)
    text = re.sub(r'\(\s*\)', '', text)
    return _fix_articles(text).strip()


def looks_broken(sentence):
    return any(re.search(pattern, sentence, re.IGNORECASE)
               for pattern in _BROKEN_PATTERNS)


def has_cliche(text):
    return bool(re.search(rf"\b(?:{_CLICHE})\b", text, re.IGNORECASE))


def split_sentences(text):
    return [s for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s]


def strip_cliches(text):
    """Remove filler adjectives sentence by sentence.

    Where a word can't be lifted out cleanly - it was the whole predicate, or
    removing it strands an article - the sentence is dropped instead. A
    mangled sentence confuses the image model more than the cliche would, so
    it's never worth leaving one behind.
    """
    sentences = split_sentences(text)
    floor = max(MIN_SENTENCES, int(len(sentences) * (1 - MAX_DROPPED_FRACTION)))

    kept = []
    for index, sentence in enumerate(sentences):
        cleaned = sentence
        for pattern in _REMOVAL_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        cleaned = _tidy(cleaned)

        if not looks_broken(cleaned) and cleaned.strip(' .,;:'):
            kept.append(cleaned)
            continue

        # Dropping this one would cut too deep - keep the original intact
        remaining = len(sentences) - index - 1
        if len(kept) + remaining < floor:
            kept.append(_tidy(sentence))

    return " ".join(kept) if kept else _tidy(text)


def drop_commentary_tail(text):
    """Drop trailing sentences that comment on the scene instead of describing
    it, so the prompt ends on something physically in the frame."""
    sentences = split_sentences(text)

    while len(sentences) > MIN_SENTENCES:
        last = sentences[-1].lower()
        if any(marker in last for marker in COMMENTARY_MARKERS):
            sentences.pop()
        else:
            break

    return " ".join(sentences)


def cap_length(text, max_words=MAX_WORDS):
    """Trim to a whole number of sentences under the word cap - Flux's text
    encoder truncates long prompts, so the tail is wasted anyway."""
    sentences = split_sentences(text)

    kept, total = [], 0
    for sentence in sentences:
        words = len(sentence.split())
        if kept and total + words > max_words:
            break
        kept.append(sentence)
        total += words

    return " ".join(kept)


def clean_image_prompt(text):
    cleaned = cap_length(drop_commentary_tail(strip_cliches(text)))

    if not cleaned.endswith(('.', '!', '?')):
        cleaned += '.'

    return cleaned
