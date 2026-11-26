"""Build selectear_gacha/battle.html from the old SELECTEAR build (the bundled single-file app).

The old build already has the battle engine, the developer mode, every battle animation and the
synthesised sound effects. This script reuses it as the gacha page's battle / developer layer:
  * card art p01..p17 -> the new card images (img/f_<id>.webp, served next to battle.html)
  * boot: `#dev` opens the developer mode, `#battle=p01,p17,p08` starts a battle with that team
    (enemy = 3 other random members), anything else shows the old title screen
  * "タイトルへ" / "タイトル画面" go back to the gacha page (postMessage to the parent frame)
  * "もう一度" keeps the gacha team and draws a new enemy team

usage: python3 tools/build_battle.py <old selectear html> selectear_gacha/battle.html
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

# old card file -> new card id
CARD = {"p01": "kazano", "p02": "ushida", "p03": "sato", "p04": "yanai", "p05": "hirabayashi", "p06": "fujikura",
        "p07": "morooka", "p08": "nishida", "p09": "yamanaka", "p10": "ohashi", "p11": "kobukuda", "p12": "utsugi",
        "p13": "sakayori", "p14": "kashima", "p15": "ogawa", "p16": "endo", "p17": "chou"}


def one(old, new):
    global s
    assert s.count(old) == 1, old[:80]
    s = s.replace(old, new)


# 1. card art: find the variable bound to each "../../assets/cards/pNN.jpg" and swap its data URI for the new image
m = re.search(r'NV=Object\.assign\(\{(.*?)\}\)', s)
pairs = re.findall(r'"\.\./\.\./assets/cards/(p\d\d)\.jpg":([A-Za-z_$][\w$]*)', m.group(1))
assert len(pairs) == 17, pairs
for pid, var in pairs:
    pat = re.compile(r'([,;\s]|const )' + re.escape(var) + r'="data:image/jpeg;base64,[A-Za-z0-9+/=]+"')
    hits = pat.findall(s)
    assert len(hits) == 1, (pid, var, len(hits))
    s = pat.sub(lambda mm: f'{mm.group(1)}{var}="img/f_{CARD[pid]}.webp"', s)

# 2. title screen -> back to the gacha page when embedded
one('function Yo(){I=null,', 'function Yo(){if(window.parent!==window){I=null,NA=null,document.querySelectorAll(".overlay").forEach(A=>A.remove());parent.postMessage({selectear:"battleBack"},"*");return}I=null,')

# 3. "もう一度" in a gacha battle: same team, new random enemy
one('function Gl(A){', 'function Gl(A){if(window.__team){document.querySelectorAll(".overlay").forEach(t=>t.remove()),oi=!1,zA=null,AA=0,ro=1,A?oo={wins:[0,0],game:1,counted:!1,cpuTeam:[]}:(oo.game++,oo.counted=!1),io.dealMode="random";const T=window.__team,E=IA.map(t=>t.id).filter(t=>!T.includes(t)).sort(()=>Math.random()-.5).slice(0,3);Ot([...T],E);return}')

# 4. boot router
one('document.addEventListener("keydown",At,{capture:!0});Yo();',
    'document.addEventListener("keydown",At,{capture:!0});'
    '(function(){const h=location.hash.slice(1);if(h==="dev"){Jr();return}'
    'const b=h.match(/^battle=([\\w,]+)/);if(b){const T=b[1].split(",").filter(t=>IA.some(c=>c.id===t));'
    'if(T.length){window.__team=T;io.difficulty=(at().cpu)||"normal";Gl(!0);return}}Yo()})();')

# 5. v46 values from the spec: 西田's full name, 山中 HP11, 大橋 HP10
s = s.replace("西田 こうき", "西田 晃季")
one("p09,山中 雅文,男,13,", "p09,山中 雅文,男,11,")
one("p10,大橋 央玲,男,9,", "p10,大橋 央玲,男,10,")

# 6. page title
one('<title>selectear</title>', '<title>SELECTEAR Battle</title>')

open(dst, "w", encoding="utf-8").write(s)
print(dst, len(s))
