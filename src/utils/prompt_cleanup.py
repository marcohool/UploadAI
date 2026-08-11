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


# --- Captions ---------------------------------------------------------------

DEFAULT_HASHTAG_COUNT = 20
MAX_HOOK_CHARS = 95

# These survive being banned in the prompt often enough to be worth checking
# for. Unlike a stray adjective they can't be lifted out of the sentence - the
# sentence is built around them - so a caption containing one is rewritten
# rather than repaired.
_BANNED_CONSTRUCTIONS = [
    (r"\b(?:is|are|was|were|isn't|aren't|it's|its)\s+not\s+just\b", "\"is not just X, it's Y\""),
    (r"\b(?:isn't|aren't)\s+just\b", "\"isn't just X, it's Y\""),
    (r"\bmore than just\b", "\"more than just\""),
    (r"\bhere's the thing\b", "\"here's the thing\""),
    (r"\blet that sink in\b", "\"let that sink in\""),
    (r"\bin a world where\b", "\"in a world where\""),
    # the adjective slot is optional - "a silent testament to" is the same tic
    (r"\b(?:a|the)\s+(?:\w+\s+)?(?:testament|testimony)\s+to\b", "\"a testament/testimony to\""),
    (r"\bblend of (?:the )?old and (?:the )?new\b", "\"a blend of old and new\""),
    (r"\bwhere (?:tradition|the past|history|time)\s+\w+s\b", "a \"where tradition meets ...\" construction"),
    (r"\b(?:I|we|my|our|I'm|we're|I've|we've)\b", "first person - the account never claims to have been there"),
]

_TRAILING_HASHTAGS = re.compile(r'(?:\s*#[^\s#]+)+\s*$')
_NUMBER = re.compile(r'\b\d[\d,.]*\b')

_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️⬀-⯿]")


def caption_hook(text):
    """The part of the caption Instagram shows before it collapses the rest.

    Normally the first line, but a caption whose shape is one unbroken
    paragraph has no first line to speak of, so the first sentence stands in.
    """
    first_line = text.strip().splitlines()[0].strip()

    if len(first_line) <= MAX_HOOK_CHARS:
        return first_line

    sentences = split_sentences(first_line)

    return sentences[0] if sentences else first_line


def split_trailing_hashtags(text):
    """Pull a trailing run of hashtags back out of the caption body.

    The model puts them there instead of - or as well as - in the hashtags
    array often enough that they'd otherwise either go missing from the post or
    appear in it twice."""
    match = _TRAILING_HASHTAGS.search(text)

    if not match:
        return text.strip(), []

    return text[:match.start()].strip(), re.findall(r'#([^\s#]+)', match.group(0))


def _number_key(number):
    return number.replace(',', '').rstrip('.')


def unsupported_numbers(text, facts):
    """Numbers in the caption that the researcher never supplied.

    A reader takes a number at face value, and it is the thing the model is
    most willing to invent - it will happily open on a population figure it
    made up to fill a shape asking for a bare number. Every digit therefore has
    to trace back to the researched material."""
    sourced = {_number_key(number) for fact in facts
               for number in _NUMBER.findall(fact["fact"])}

    return [number for number in _NUMBER.findall(text)
            if _number_key(number) not in sourced]


def caption_issues(text, facts=()):
    """Problems worth spending another API call to fix, phrased so they can be
    handed straight back to the model."""
    issues = []

    unsupported = unsupported_numbers(text, facts)
    if unsupported:
        issues.append(
            "it states numbers that are not in the researched material - "
            + ", ".join(unsupported)
            + " - and inventing a figure is worse than having none, so take "
              "them out and write it without numbers")

    hook = caption_hook(text)
    if len(hook) > MAX_HOOK_CHARS:
        issues.append(
            f"the opening is {len(hook)} characters, over the {MAX_HOOK_CHARS} "
            "character limit - Instagram will cut it mid-thought")

    for pattern, description in _BANNED_CONSTRUCTIONS:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(f"it uses {description}, which is not allowed")

    if _EMOJI.search(text):
        issues.append("it contains an emoji")

    return issues


def _clean_caption_line(line):
    """strip_cliches() rejoins on spaces, which would flatten the line breaks a
    caption's shape depends on, so captions are cleaned a line at a time.

    A caption is short enough that dropping a sentence can take half of it, so
    nothing is dropped here - if lifting the word out breaks the line, the line
    is left as written."""
    if not line.strip() or not has_cliche(line):
        return line

    cleaned = line
    for pattern in _REMOVAL_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    cleaned = _tidy(cleaned)

    if looks_broken(cleaned) or not cleaned.strip(' .,;:'):
        return line

    return cleaned


def clean_caption(text):
    """Strip the filler adjectives the model reaches for despite being told not
    to. Unlike an image prompt, a caption is read by people, so a caption left
    slightly clichéd beats one left with a hole in it."""
    text = text.strip()

    if not has_cliche(text):
        return text

    cleaned = "\n".join(_clean_caption_line(line) for line in text.split("\n"))

    original_words = len(text.split())
    if original_words and len(cleaned.split()) < original_words * (1 - MAX_DROPPED_FRACTION):
        print("Caption cleanup would have cut too much - keeping it as written.")
        return text

    if has_cliche(cleaned):
        print("Caption still contains filler wording -> ", cleaned)

    return cleaned


def normalise_hashtags(tags, count=DEFAULT_HASHTAG_COUNT):
    """Hashtag output is inconsistent whatever the prompt says - a stray '#',
    mixed case, punctuation inside a tag, the odd duplicate - so it's fixed
    here rather than by asking the model again to be careful."""
    seen, cleaned = set(), []

    for tag in tags:
        tag = re.sub(r'\W+', '', tag.lower()).strip('_')

        if not tag or tag in seen:
            continue

        seen.add(tag)
        cleaned.append(f"#{tag}")

        if len(cleaned) == count:
            break

    return " ".join(cleaned)
