"""Build one self-contained HTML file of SELECTEAR (images + BGM embedded).

Usage: python3 tools/build_standalone.py
Output: dist/selectear.html — open it directly in any browser (double-click on Windows,
or via the Files app / AirDrop on iPhone).
"""
import base64, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "selectear"
OUT = ROOT / "dist" / "selectear.html"
MIME = {".webp": "image/webp", ".mp3": "audio/mpeg"}

page = (SRC / "index.html").read_text(encoding="utf-8")
paths = sorted(set(re.findall(r"img/[a-z0-9_]+\.webp|miyu_bgm\.mp3", page)))
assets = {}
for rel in paths:
    f = SRC / rel
    assets[rel] = f"data:{MIME[f.suffix]};base64," + base64.b64encode(f.read_bytes()).decode()

# The published artifact gets its <html>/<head> from the host; the standalone file needs its own.
doc = (
    "<!doctype html>\n<html lang=\"ja\">\n<head>\n"
    + "<script>window.__ASSETS=" + json.dumps(assets) + ";</script>\n"
    + page.replace("<style>", "<style>\n:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}", 1)
    + "\n</html>\n"
)
# Keep the original paths out of src/style until the script swaps them in, so file:// shows no broken images.
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(doc, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.1f} MB, {len(assets)} assets)")
