#!/usr/bin/env python3
"""Render the article Markdown into styled dark-theme HTML pages. Needs pandoc.
Run:  python3 build_html.py   (re-run whenever the .md changes)"""
import subprocess, os, html
HERE = os.path.dirname(os.path.abspath(__file__))
EN_TITLE = "The Grammar of Bitcoin's Extensibility"
# (source .md, output .html, page title, topbar label)
# A title of None means "use the first '# ' heading of the source file" (keeps
# the Chinese edition's title out of this script). The English page's topbar is
# English-only; the Chinese edition keeps its bilingual "EN · CN" topbar.
DOCS = [
    ("article-en.md", "article-en.html", EN_TITLE, EN_TITLE),
    ("article-cn.md", "article-cn.html", None, "bilingual"),
]
def first_h1(src):
    with open(os.path.join(HERE,src),encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "): return line[2:].strip()
    return EN_TITLE
CSS = """
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--fg:#e6edf3;--dim:#8b949e;--accent:#58a6ff;--op:#f0883e;--ok:#2ea043}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.75 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif}
.topbar{position:sticky;top:0;background:rgba(13,17,23,.9);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:11px 20px;font-size:14px}
.topbar a{color:var(--accent);text-decoration:none} .topbar a:hover{text-decoration:underline}
main{max-width:760px;margin:0 auto;padding:34px 22px 100px}
h1{font-size:30px;line-height:1.25;margin:8px 0 8px}
h2{font-size:22px;margin:44px 0 14px;padding-top:22px;border-top:1px solid var(--line)}
h3{font-size:17px;color:var(--dim);font-weight:600;margin:0 0 22px}
h1+*,h2+*{margin-top:0}
p,li{color:#c9d1d9} strong,b{color:var(--fg)}
a{color:var(--accent)} a:hover{text-decoration:underline}
blockquote{margin:18px 0;padding:6px 18px;border-left:3px solid var(--accent);background:#12182080;color:var(--dim);border-radius:0 6px 6px 0}
code{font-family:"SF Mono",ui-monospace,Menlo,Consolas,monospace;font-size:.88em;background:var(--panel);border:1px solid var(--line);border-radius:5px;padding:1px 5px}
pre{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:14px 16px;overflow:auto}
pre code{background:none;border:0;padding:0;font-size:13px;line-height:1.6;color:var(--op)}
table{border-collapse:collapse;margin:16px 0;font-size:14.5px;display:block;overflow:auto}
th,td{border:1px solid var(--line);padding:7px 11px;text-align:left;vertical-align:top}
th{background:var(--panel);color:var(--fg)}
hr{border:0;border-top:1px solid var(--line);margin:34px 0}
em{color:#c9d1d9} ul,ol{padding-left:24px}
.cta{display:inline-block;background:var(--op);color:#0d1117;font-weight:700;text-decoration:none;padding:9px 16px;border-radius:8px;margin:10px 0}
.foot{color:var(--dim);font-size:13px;margin-top:40px;border-top:1px solid var(--line);padding-top:16px}
"""
def render(src, out, title, topbar):
    if title is None: title = first_h1(src)
    if topbar == "bilingual": topbar = f"{EN_TITLE} · {title}"
    body = subprocess.run(["pandoc","-f","gfm","-t","html5","--no-highlight",os.path.join(HERE,src)],
                          capture_output=True, text=True, check=True).stdout
    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/><title>{html.escape(title)}</title>
<style>{CSS}</style><script>window.goatcounter={{path:function(p){{return location.host+p}}}}</script><script data-goatcounter="https://bitcoincoding.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script></head><body>
<div class="topbar">← <a href="./">{html.escape(topbar, quote=False)}</a></div>
<main>
{body}
<p><a class="cta" href="./explorer.html">▶ Open the interactive Upgrade-Slot Explorer</a></p>
<div class="foot">Part of <a href="./">The Grammar of Bitcoin's Extensibility</a>. Every byte from real signet transactions.</div>
</main></body></html>"""
    with open(os.path.join(HERE,out),"w",encoding="utf-8") as f: f.write(page)
    print(f"  {src} -> {out} ({len(page)} bytes)")
if __name__ == "__main__":
    print("rendering:")
    for a in DOCS: render(*a)
    print("done.")
