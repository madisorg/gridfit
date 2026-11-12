"""robots.txt read the way RFC 9309 and the search engines read it.

urllib.robotparser takes the first rule that matches and knows no wildcards, so "Allow: /" followed by
"Disallow: /upload/" (en.growatt.com) lets every upload through, the opposite of what the maker wrote. Here the most
specific (longest) matching rule wins, an Allow wins a tie, `*` matches any run of characters and `$` ends the path.
The groups for the crawler's product token come before the `*` groups; several matching groups are read as one.
What an unreachable robots.txt means (allow all, disallow all) is the caller's choice: this module only reads text."""
import re
import urllib.parse


def _rx(pattern: str):
    """A robots path pattern as a regex: `*` any run of characters, a final `$` the end of the path."""
    end = pattern.endswith("$")
    body = pattern[:-1] if end else pattern
    return re.compile("".join(".*" if ch == "*" else re.escape(ch) for ch in body) + ("$" if end else ""))


def _norm(path: str) -> str:
    # compare percent-encoded on both sides: "/a b" in a rule and "/a%20b" in a URL are the same path
    return urllib.parse.quote(urllib.parse.unquote(path), safe="/*$?=&;:@!,+~%")


class Robots:
    def __init__(self, text: str = ""):
        self.groups = []  # [(agents, [(allow, pattern, rx)], crawl_delay)]
        agents, rules, delay, in_rules = [], [], None, False
        for raw in (text or "").lstrip("﻿").splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, val = (x.strip() for x in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if in_rules:  # a user-agent line after rules starts a new group
                    self.groups.append((agents, rules, delay))
                    agents, rules, delay, in_rules = [], [], None, False
                agents.append(val.lower())
            elif key in ("allow", "disallow"):
                in_rules = True
                if val:  # an empty Disallow is no rule
                    p = _norm(val)
                    rules.append((key == "allow", p, _rx(p)))
            elif key == "crawl-delay":
                in_rules = True
                try:
                    delay = float(val)
                except ValueError:
                    pass
        if agents:
            self.groups.append((agents, rules, delay))

    def _rules(self, ua: str):
        token = (ua or "*").split("/")[0].strip().lower()
        specific = [g for g in self.groups if any(a != "*" and a and a in token for a in g[0])]
        chosen = specific or [g for g in self.groups if "*" in g[0]]
        return [r for g in chosen for r in g[1]], next((g[2] for g in chosen if g[2] is not None), None)

    def allowed(self, ua: str, url: str) -> bool:
        parts = urllib.parse.urlsplit(url)
        path = _norm(parts.path or "/") + ("?" + parts.query if parts.query else "")
        if path == "/robots.txt":
            return True
        rules, _ = self._rules(ua)
        best = None  # (length, allow)
        for allow, pattern, rx in rules:
            if rx.match(path):
                cand = (len(pattern), allow)
                if best is None or cand[0] > best[0] or (cand[0] == best[0] and allow):
                    best = cand
        return True if best is None else best[1]

    def crawl_delay(self, ua: str):
        return self._rules(ua)[1]
