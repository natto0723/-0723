"""Build SELECTEAR as ONE game: the home page with the map and the hideout as layers inside it.

Usage: python3 tools/build_standalone.py
Output:
  combined/            the publishable folder (index.html = home, map.html, hideout.html, images, sounds)
  dist/selectear.html  one self-contained file with everything embedded; open it directly in a browser
"""
import base64, json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
MIME = {".webp": "image/webp", ".mp3": "audio/mpeg"}
PAGES = {"index.html": "selectear", "map.html": "selectear_map", "hideout.html": "selectear_hideout"}
ASSET_RE = r"img/[a-z0-9_]+\.webp|[a-z_]+\.mp3"

# every image and sound in a page's folder (some names are built in code, e.g. light layers and effects)
def all_assets(folder):
    base = ROOT / folder
    return sorted([*base.glob("*.mp3"), *(base / "img").glob("*.webp")])

# 1. combined/ : the three pages side by side with all their files
OUT = ROOT / "combined"
shutil.rmtree(OUT, ignore_errors=True); (OUT / "img").mkdir(parents=True)
for name, folder in PAGES.items():
    page = (ROOT / folder / "index.html").read_text(encoding="utf-8")
    # map.html / hideout.html are served as plain pages: they need their own doctype
    (OUT / name).write_text(page if name == "index.html" else "<!doctype html>\n" + page, encoding="utf-8")
    for src in all_assets(folder):
        rel = src.relative_to(ROOT / folder).as_posix()
        shutil.copyfile(src, OUT / rel)
print("wrote combined/ (" + ", ".join(sorted(p.name for p in OUT.iterdir())) [:120] + "...)")

# 2. dist/selectear.html : one file.
# The map's old background (map.webp) and unused images are skipped to keep the file small Each page gets its own assets embedded; the map and hideout ride along as srcdoc.
def standalone(folder, extra_head=""):
    page = (ROOT / folder / "index.html").read_text(encoding="utf-8")
    assets = {}
    for f in all_assets(folder):
        assets[f.relative_to(ROOT / folder).as_posix()] = f"data:{MIME[f.suffix]};base64," + base64.b64encode(f.read_bytes()).decode()
    return ("<!doctype html>\n<html lang=\"ja\">\n<head>\n" + extra_head
            + "<script>window.__ASSETS=" + json.dumps(assets) + ";</script>\n"
            + page.replace("<style>", "<style>\n:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}", 1)
            + "\n</html>\n")

layers = {
    "map": standalone("selectear_map", "<script>window.__EMBEDDED=true;</script>\n"),
    "hideout": standalone("selectear_hideout", "<script>window.__EMBEDDED=true;</script>\n"),
}
home = standalone("selectear", "<script>window.__LAYERS=" + json.dumps(layers).replace("</", "<\\/") + ";</script>\n")
(ROOT / "dist").mkdir(exist_ok=True)
for old in ("selectear_map.html", "selectear_hideout.html"):
    (ROOT / "dist" / old).unlink(missing_ok=True)
out = ROOT / "dist" / "selectear.html"
out.write_text(home, encoding="utf-8")
print(f"wrote dist/selectear.html ({out.stat().st_size / 1e6:.1f} MB)")
