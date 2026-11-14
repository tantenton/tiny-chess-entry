"""tiny-chess-01: Positional & Tactical engine in <4KB Python for make.fun."""
import json, os, sys, urllib.error, urllib.request

ENV = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL not set")
VAL = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 20000}

# Compact Center-Manhattan Distance table for positional bonus
CENTER = [
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 1, 1, 1, 1, 1, 1, 0,
    0, 1, 3, 4, 4, 3, 1, 0,
    0, 2, 4, 6, 6, 4, 2, 0,
    0, 2, 4, 6, 6, 4, 2, 0,
    0, 1, 3, 4, 4, 3, 1, 0,
    0, 1, 1, 1, 1, 1, 1, 0,
    0, 0, 0, 0, 0, 0, 0, 0
]

def post(path, body):
    req = urllib.request.Request(ENV + path, data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: HTTP {e.code}")

def parse(fen):
    b, p = {}, fen.split()[0].split("/")
    for r, row in enumerate(p):
        f = 0
        for c in row:
            if c.isdigit(): f += int(c)
            else:
                b["abcdefgh"[f] + str(8 - r)] = c
                f += 1
    return b

def choose(fen, legal):
    b = parse(fen)
    def score(mv):
        src, dst = mv[:2], mv[2:4]
        m, v = b.get(src, ""), b.get(dst, "")
        if not v and m.lower() == "p" and src[0] != dst[0]:
            v = "p"
        vt = VAL.get(v.lower(), 0) if v else 0
        mt = VAL.get(m.lower(), 0) if m else 0
        pr = VAL.get(mv[4].lower(), 0) if len(mv) == 5 else 0
        f, r = ord(dst[0]) - 97, 8 - int(dst[1])
        c_bonus = CENTER[r * 8 + f] * (3 if m.lower() in "pn" else 1)
        # Advance pawns forward
        adv = (int(dst[1]) - int(src[1])) if m.isupper() else (int(src[1]) - int(dst[1]))
        adv_bonus = adv * 4 if m.lower() == "p" else 0
        tactical = vt * 16 - mt + pr * 10
        return (-tactical, -c_bonus - adv_bonus, mv)
    return min(legal, key=score)

while True:
    g = post("/game", {})
    if g["status"] == "done":
        break
    while g["status"] == "your_move":
        g = post("/move", {"game": g["game"], "move": choose(g["fen"], g["legal_moves"])})
    print(f"game {g['game']}: {g['outcome']} by {g['reason']}", file=sys.stderr)
print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost", file=sys.stderr)
