"""Text normalisation for keyword search. Thai is written without spaces between words, so a keyword index
can't find a word inside a sentence unless we split it first."""
import re
import unicodedata
from functools import lru_cache

THAI = re.compile(r"[฀-๿]")
THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")


def has_thai(text: str) -> bool:
    return bool(THAI.search(text))


@lru_cache(maxsize=1)
def _segmenter():
    """PyThaiNLP's dictionary-based segmenter, with our own words added. Out of the box it splits brand
    transliterations it doesn't know (ไนกี้ -> ไน + กี้); adding domain words keeps them whole."""
    from pythainlp.corpus.common import thai_words
    from pythainlp.tokenize import word_tokenize
    from pythainlp.util import dict_trie

    from . import catalog

    domain = set(catalog.BRAND_TH.values()) | set(catalog.COLOR_TH.values()) | {c[2] for c in catalog.CATEGORIES}
    domain |= {w for v in catalog.BRAND_TH.values() for w in v.split()}
    trie = dict_trie(set(thai_words()) | domain)
    return lambda text: word_tokenize(text, custom_dict=trie, engine="newmm", keep_whitespace=False)


def normalise(text: str) -> str:
    """NFC Unicode form, Thai digits to Arabic digits, lowercase."""
    return unicodedata.normalize("NFC", text).translate(THAI_DIGITS).lower()


def segment(text: str) -> str:
    """Split Thai runs into words with spaces between them; leave other text as it is.

    'รองเท้าวิ่งสีน้ำเงิน' -> 'รองเท้าวิ่ง สีน้ำเงิน'
    """
    text = normalise(text)
    if not has_thai(text):
        return text
    return " ".join(w for w in _segmenter()(text) if w.strip())
