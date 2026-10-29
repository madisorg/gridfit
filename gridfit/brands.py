"""Brand and model-code normalisation shared by the build and the register import."""
import re
from pathlib import Path

import yaml

LEGAL = re.compile(
    r"\b(co\.?,?\s*ltd\.?|co\.?|ltd\.?|limited|gmbh|ag|s\.?p\.?a\.?|inc\.?|llc|b\.?v\.?|a/?s|s\.?a\.?|oy|ab|sp\.? z o\.?o\.?)\s*$",
    re.I,
)


def _clean(name: str) -> str:
    s = re.sub(r"\s+", " ", (name or "").strip().lower().rstrip(".,"))
    prev = None
    while prev != s:
        prev, s = s, LEGAL.sub("", s).strip(" ,.")
    return s


class Brands:
    def __init__(self, path: Path):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.canonical = list(data)
        self.lookup = {}
        for canon, spellings in data.items():
            self.lookup[_clean(canon)] = canon
            for s in spellings or []:
                self.lookup[_clean(s)] = canon
        self.unknown = set()

    def canon(self, raw: str, strict: bool = True):
        """Canonical brand for a spelling. Unknown spellings give None, or - with
        strict=False, for sources that name brands themselves (evcc) - the spelling as is."""
        c = _clean(raw)
        if c in self.lookup:
            return self.lookup[c]
        if strict or not c:
            self.unknown.add(raw)
            return None
        name = re.sub(r"\s+", " ", raw.strip())
        self.lookup[c] = name
        return name


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower().replace("&", " and ").replace("+", " plus "))
    return s.strip("-") or "x"


def norm_model(raw: str) -> str:
    """Same rule as the register parser: upper-case, separators removed."""
    return re.sub(r"[\s\-_./,()+]", "", (raw or "").upper())
