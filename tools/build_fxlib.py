"""Extract the battle animation engine of the old SELECTEAR build into selectear_gacha/fxlib.js + fxlib.css.

The old build (a bundled single-file app) contains the effect library `L` (every ability / skill /
buff / debuff / damage / money animation and their synthesised sounds) and the event dispatcher `Ia`
that the old battle used to play them. The new battle (battle.html) keeps its own rules engine and
feeds its events to these, so the animations are exactly the old ones.

  * card art p01..p17 -> img/f_<id>.webp, design sheets / logo dropped (not used by the effects)
  * the old app's boot (`Yo()`) is removed; nothing of the old UI is shown
  * `dt()` (stage setup from the old game state) -> window.__fxStage(L, fa) supplied by battle.html
  * exports window.OLDFX = { L, Ia, Ho, Or, mo, et, Jo, snd }
  * CSS: the old effect styles, scoped to the effect layer / fighters / overlays so they never touch the new UI

usage: python3 tools/build_fxlib.py <old selectear html> selectear_gacha
"""
import re
import sys

src, outdir = sys.argv[1], sys.argv[2]
html = open(src, encoding="utf-8").read()

CARD = {"p01": "kazano", "p02": "ushida", "p03": "sato", "p04": "yanai", "p05": "hirabayashi", "p06": "fujikura",
        "p07": "morooka", "p08": "nishida", "p09": "yamanaka", "p10": "ohashi", "p11": "kobukuda", "p12": "utsugi",
        "p13": "sakayori", "p14": "kashima", "p15": "ogawa", "p16": "endo", "p17": "chou"}

# ---------------- JS ----------------
a = html.index('<script type="module">') + len('<script type="module">')
b = html.rindex("</script>")
js = html[a:b]


def one(old, new):
    global js
    assert js.count(old) == 1, (js.count(old), old[:90])
    js = js.replace(old, new)


def swap_images(map_name, folder, to):
    global js
    m = re.search(map_name + r'=Object\.assign\(\{(.*?)\}\)', js)
    pairs = re.findall(r'"\.\./\.\./assets/' + folder + r'/(p\d\d)\.jpg":([A-Za-z_$][\w$]*)', m.group(1))
    assert len(pairs) == 17, (map_name, len(pairs))
    for pid, var in pairs:
        pat = re.compile(r'([,;\s]|const )' + re.escape(var) + r'="data:image/jpeg;base64,[A-Za-z0-9+/=]+"')
        assert len(pat.findall(js)) == 1, (pid, var)
        js = pat.sub(lambda mm: f'{mm.group(1)}{var}="{to(pid)}"', js)


swap_images("NV", "cards", lambda pid: f"img/f_{CARD[pid]}.webp")
swap_images("EV", "sheets", lambda pid: "")
# the old title logo (png) is not needed
js = re.sub(r'(const t0=\(\)=>it\(!1\),r0=)"data:image/png;base64,[A-Za-z0-9+/=]+"', r'\1""', js)

# no old app: drop the boot
one('document.addEventListener("keydown",At,{capture:!0});Yo();', 'document.addEventListener("keydown",At,{capture:!0});')

# stage setup comes from the new battle
i = js.index("function dt(A){us();const o=I")
depth, k = 0, js.index("{", i)
while True:
    if js[k] == "{": depth += 1
    elif js[k] == "}":
        depth -= 1
        if depth == 0: break
    k += 1
js = js[:i] + "function dt(A){us();window.__fxStage&&window.__fxStage(L,fa)}" + js[k + 1:]

# new rules: パキるみ = 我慢+1 (1/2 panic) instead of panic / 4 heal
one('await L.miniRoul("パキるみ",["錯乱","4回復"],B?0:1),B?(await L.confuse(p),await aA(400),L.bubble(p,"まじウケんだけど笑")):await L.heal((y==null?void 0:y.amount)??4,p,!0);break',
    'L.word(p,"我慢+1","#ff2f5b"),await aA(500),B&&(await L.confuse(p),await aA(400),L.bubble(p,"まじウケんだけど笑"));break')

# the played card settles at 1:1 so its text stays sharp (it was parked at scale 1.15 = blurry)
one('{transform:"translateY(0) rotateY(0) scale(1.15)",opacity:1}],{duration:i?1:450', '{transform:"none",opacity:1}],{duration:i?1:450')
one('await W.animate([{transform:"scale(1.15)",opacity:1},', 'await W.animate([{transform:"none",opacity:1},')

# 灰コンブ: only the player picks (for their own character); the new rules' third result is ダウン
one('Kl={poison:"☠️ 毒",restrain:"⛓️ 拘束状態",debt:"💸 借金+1"}', 'Kl={poison:"☠️ 毒",restrain:"⛓️ 拘束状態",debt:"💸 借金+1",weaken:"⬇️ ダウン"}')
one('const a=I?dA(I,A):void 0,t=!I||!!a&&a.team===AA,', 'const a=void 0,t=!!(window.__kombuHuman&&window.__kombuHuman(A)),')
one('`${a?v(ZA(a)):""}　どれを食べる？`', '`${v(window.__nameOf?window.__nameOf(A):"")}　どれを食べる？`')
one('const K=["poison","restrain","debt"].filter(M=>M!==o)', 'const K=["poison","restrain","weaken"].filter(M=>M!==o)')

# 泥酔: only the drinker's card wobbles (the whole field used to sway)
one('P(l.el,"drunk"),P(lA("field"),"sway"),', 'P(l.el,"drunk"),')

# new rules: 亀甲 has no ◆ cost
one('L.bankFlash(p.side,"loss"),L.floatTxt(L.pt(j),"◆-4（万円）",L.C.red),', '')

js += ';window.OLDFX={L,Ia,Ho,Or,mo,et,Jo,us,motion:p0,get fa(){return fa},snd:v=>{to=v}};window.dispatchEvent(new Event("oldfx"));'
js = js.replace("西田 こうき", "西田 晃季")
one("p09,山中 雅文,男,13,", "p09,山中 雅文,男,11,")
one("p10,大橋 央玲,男,9,", "p10,大橋 央玲,男,10,")
open(f"{outdir}/fxlib.js", "w", encoding="utf-8").write(js)
print("fxlib.js", len(js))

# ---------------- CSS ----------------
m = re.search(r"<style>(:root\{--green.*?)</style>", html, re.S)
css = m.group(1)
KEEP = (".xf", ".xlayer", ".xfield", ".overlay", ".xscope", ":root", "html", "body")


def split_top(sel):
    out, depth, cur = [], 0, ""
    for ch in sel:
        if ch in "([": depth += 1
        if ch in ")]": depth -= 1
        if ch == "," and depth == 0: out.append(cur); cur = ""; continue
        cur += ch
    out.append(cur)
    return out


def scope_sel(sel):
    s = sel.strip()
    if not s: return s
    if any(k in s for k in KEEP):
        if s.startswith(("html", "body", ":root")): return None   # never restyle the page itself
        return s
    return ":is(.xlayer,.xf,.xscope,.overlay) " + s


def scope(block):
    out, i, n = [], 0, len(block)
    while i < n:
        j = block.find("{", i)
        if j < 0: out.append(block[i:]); break
        head = block[i:j].strip()
        # find matching brace
        depth, k = 0, j
        while True:
            if block[k] == "{": depth += 1
            elif block[k] == "}":
                depth -= 1
                if depth == 0: break
            k += 1
        body = block[j + 1:k]
        if head.startswith("@keyframes") or head.startswith("@font-face"):
            out.append(f"{head}{{{body}}}")
        elif head.startswith("@media") or head.startswith("@supports"):
            out.append(f"{head}{{{scope(body)}}}")
        else:
            sels = [x for x in (scope_sel(p) for p in split_top(head)) if x]
            if sels: out.append(",".join(sels) + "{" + body + "}")
        i = k + 1
    return "".join(out)


# 暴食: the card keeps its shape and size (it became big and round)
css = css.replace(".xf.st-glutton{border-radius:24px;border-width:3px;scale:1.06;z-index:2;box-shadow:0 0 14px #ff7ac88c;transition:scale .4s,border-radius .4s}", ".xf.st-glutton{box-shadow:0 0 14px #ff7ac88c}")
css = css.replace(".xf.st-glutton .por{border-radius:21px 21px 0 0}", "")
css = css.replace("@keyframes xk-grow{50%{scale:1.14}}", "@keyframes xk-grow{50%{scale:1.05}}")
scoped = scope(css) + """
/* new battle: bigger played card (instead of scaling it up) */
.xlayer .castcard{width:168px;min-height:224px;margin:-112px 0 0 -84px;padding:32px 12px 12px;-webkit-font-smoothing:antialiased}
.xlayer .castcard .cname{font-size:22px}.xlayer .castcard .ctext{font-size:13px}
"""
open(f"{outdir}/fxlib.css", "w", encoding="utf-8").write(scoped)
print("fxlib.css", len(scoped))
