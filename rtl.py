"""Pure RTL rewrite for Arabic markdown. rtl_transform(text) -> text; idempotent."""
import re

RLM = "\u200f"
_AR = re.compile("[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_HR = re.compile(r"^\s*([-*_=])(\s*\1){2,}\s*$")
_SEP = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")
_MARK = re.compile(r"^(\s*(?:#{1,6} |(?:>\s?)+|[-*+] \[[ xX]\] ))")  # heading / quote / task item: keep marker
_ITEM = re.compile(r"^(\s*)(?:[-*+]|\d+[.)]) (.*)$")
_CELL = re.compile(r"(?<!\\)\|")


def _code_mask(lines):
    """True for lines inside ``` / ~~~ fences or $$ blocks (delimiters included)."""
    mask, fence, math = [], None, False
    for l in lines:
        if fence:
            mask.append(True)
            m = _FENCE.match(l)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not l.strip().strip(fence[0]):
                fence = None
        elif math:
            mask.append(True)
            math = "$$" not in l
        elif (m := _FENCE.match(l)):
            fence = m.group(1)
            mask.append(True)
        elif l.strip().startswith("$$"):
            mask.append(True)
            math = l.strip().count("$$") < 2  # single-line $$..$$ opens nothing
        else:
            mask.append(False)
    return mask


def _pre(s):
    """Prefix RLM unless already there."""
    return s if s.startswith(RLM) else RLM + s


def rtl_transform(text):
    if not text or not _AR.search(text):
        return text
    lines = text.split("\n")
    mask = _code_mask(lines)
    if not _AR.search("\n".join(l for l, c in zip(lines, mask) if not c)):
        return text
    out, counters = [], {}
    for l, code in zip(lines, mask):
        if code or not l.strip() or _HR.match(l) or ("|" not in l and _SEP.match(l)):
            if not l.strip():
                counters = {}  # a blank line ends the list, so the next list restarts at 1
            out.append(l)
            continue
        if l.lstrip().startswith("|"):
            if _SEP.match(l):
                out.append(l)
                continue
            cells = _CELL.split(l)
            out.append("|".join(c if not c.strip() or c.lstrip().startswith(RLM) else RLM + c for c in cells))
            counters = {}
            continue
        m = _MARK.match(l)
        if m:
            rest = l[m.end():]
            out.append(m.group(1) + _pre(rest) if rest else l)
            counters = {}
            continue
        m = _ITEM.match(l)
        if m:
            indent, body = m.groups()
            for k in [k for k in counters if k > len(indent)]:
                del counters[k]
            n = counters[len(indent)] = counters.get(len(indent), 0) + 1
            out.append(f"{RLM}{indent}{n}. {body}")
            continue
        counters = {}
        out.append(_pre(l))
    return "\n".join(out)
