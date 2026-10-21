import re, sys, collections

SRC = "static/css/style.css"
DST = "static/css/style.organized.css"
HEADERS = "--headers" in sys.argv   # off by default so the line count stays identical

GROUPS = [  # first match wins, so order matters
 ("01 Base & variables", r"^@import|^:root|^\*$|^html|^body$|^main$|^h1|^a$|^p$|:focus-visible|^@keyframes glow"),
 ("02 Shared section styles & scroll animations", r"^\.section(?![-\w])|^\.section-label|\.road-sign|\.scroll-progress|\.js-anim|\.yellow$|\.ink$|\.eyebrow|^::-webkit-scrollbar|^html"),
 ("03 Header / navigation", r"\.route-|\.brand-mark"),
 ("04 Hero / cover scene", r"\.hero|\.cloud|\.grass|\.road-surface|\.road-edge|\.road-studs|\.crosswalk$|\.curb-light|\.pole|\.signal(?![-\w])|\.island(?![-\w])|\.city-|\.facade|\.utility|\.street-(trees|life|lamp|sign)|\.system-card|\.crossing-state|\.signal-bars|\.detection|\.hazard|\.building|#road"),
 ("05 About", r"\.about|\.meaning|\.sign-pole|\.floating-sign|\.asphalt-stamp|\.chips"),
 ("06 Project foundation (cards & pop-ups)", r"\.objective|\.line-icon|\.card-arrow|\.info-|\.section-heading"),
 ("07 Process & demo pop-ups", r"\.process|\.signal-dot|\.demo-|\.street-|\.pedestrian|\.vehicle|\.crossing-|\.waiting|\.road-signal|\.road-top|\.road-bottom|\.island-|\.ped-|\.person|\.signal-|\.car-|\.sensor|body\.modal-open"),
 ("08 Components / hardware gallery", r"\.panel|\.hardware|\.component|\.feature|\.carousel"),
 ("09 Team", r"\.team|\.avatar"),
 ("10 Footer & back-to-top", r"footer|\.footer|\.foot-|\.back-to-top"),
]
KEYFRAME_HINTS = {"hero":4,"cloud":4,"cover":4,"status":4,"signalBars":4,"stud":4,"detection":4,
                  "footer":10,"nudge":10,"sensor":7,"drive":7,"vehicle":7,"person":7,"crossing":7,
                  "topView":7,"verify":7,"car":7,"integrated":7,"sign":5,"hazard":4,"badge":7,
                  "lightPulse":7,"lineDown":7,"fx":2,"line":2,"overlay":6,"modal":6,"icon":6,"stamp":5}

def split_blocks(css):
    blocks, buf, depth, i, n = [], [], 0, 0, len(css)
    start = 0
    while i < n:
        c = css[i]
        if css.startswith("/*", i):
            j = css.find("*/", i) + 2
            if depth == 0 and not css[start:i].strip():
                # standalone comment: glue it to the next block
                i = j
                continue
            i = j
            continue
        if c in "\"'":
            q = c; i += 1
            while i < n and css[i] != q:
                i += 2 if css[i] == "\\" else 1
            i += 1
            continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                i += 1
                # include trailing newline(s) up to the next content
                m = re.match(r"[ \t]*\n?", css[i:]); i += m.end()
                blocks.append(css[start:i]); start = i; continue
        elif c == ";" and depth == 0:
            i += 1
            m = re.match(r"[ \t]*\n?", css[i:]); i += m.end()
            blocks.append(css[start:i]); start = i; continue
        i += 1
    if css[start:].strip(): blocks.append(css[start:])
    return blocks

def selector_of(block):
    s = re.sub(r"/\*.*?\*/", "", block, flags=re.S).strip()
    return s.split("{")[0].strip()

def classify_selector(sel, inner_hint=None):
    for idx, (name, rx) in enumerate(GROUPS):
        if re.search(rx, sel):
            return idx
    return None

def classify(block):
    sel = selector_of(block)
    if sel.startswith("@import"): return 0
    if sel.startswith("@keyframes"):
        name = sel.split()[1]
        for k, g in KEYFRAME_HINTS.items():
            if name.lower().startswith(k.lower()):
                return g - 1
        return 1
    if sel.startswith("@media"):
        inner = block[block.find("{")+1: block.rfind("}")]
        votes = collections.Counter()
        for m in re.finditer(r"([^{}]+)\{", inner):
            s = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S).strip()
            g = classify_selector(s)
            if g is not None: votes[g] += 1
        return votes.most_common(1)[0][0] if votes else 1
    first = sel.split(",")[0].strip()
    g = classify_selector(first)
    if g is None: g = classify_selector(sel)
    return g if g is not None else 1

css = open(SRC, encoding="utf-8").read()
blocks = split_blocks(css)
buckets = collections.defaultdict(list)
for b in blocks:
    buckets[classify(b)].append(b)

out = []
for idx, (name, _) in enumerate(GROUPS):
    if not buckets[idx]: continue
    if HEADERS: out.append(f"\n/* ================= {name} ================= */\n")
    out.extend(buckets[idx])
result = "".join(out)
open(DST, "w", encoding="utf-8").write(result)

# --- checks ---
a, b = css.count("\n"), result.count("\n")
print(f"blocks: {len(blocks)}  lines before: {a}  after: {b}  {'OK' if a==b else 'MISMATCH'}")
for idx, (name, _) in enumerate(GROUPS):
    print(f"{len(buckets[idx]):4d} blocks  {name}")

# warn where the same selector lives in different groups (cascade-sensitive)
seen = collections.defaultdict(set)
for idx, bl in buckets.items():
    for b in bl:
        if not selector_of(b).startswith("@"): seen[selector_of(b)].add(idx)
risky = [s for s, g in seen.items() if len(g) > 1]
print(f"\nSelectors split across groups (check these visually): {len(risky)}")
for s in risky[:30]: print("  ", s[:90])