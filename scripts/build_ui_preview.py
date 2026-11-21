"""Static UI QA snapshot only. Does not alter the actual application files."""

from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.api import Application
from services.core import canonical

if __name__ == "__main__":
    dest = ROOT / "dist"
    dest.mkdir(exist_ok=True)
    for file in (ROOT / "apps/dashboard").iterdir():
        shutil.copy2(file, dest / file.name)
    with tempfile.TemporaryDirectory() as temp:
        app = Application(Path(temp) / "preview.sqlite")
        (dest / "fixture-state.json").write_text(canonical(app.state()))
    html = (
        (dest / "index.html")
        .read_text()
        .replace(
            '<script src="/app.js" defer>',
            '<script src="/preview-adapter.js" defer></script><script src="/app.js" defer>',
        )
    )
    html = html.replace(
        "<body>",
        '<body><div class="offline-banner">STATIC UI REVIEW · Backend actions are tested separately and unavailable in this preview.</div>',
    )
    (dest / "index.html").write_text(html)
    (dest / "mobile-preview.html").write_text(
        '<!doctype html><html><head><title>GTC mobile QA · 390px</title></head><body style="margin:0;background:#27313b;color:white;font-family:system-ui"><p style="margin:12px">Mobile layout QA · iframe viewport 390 × 844</p><iframe title="GTC mobile dashboard" src="/" width="390" height="844" style="border:0;display:block;margin:0 auto"></iframe></body></html>'
    )
    (dest / "preview-adapter.js").write_text("""
const realFetch=window.fetch.bind(window);
window.fetch=async (url,options={})=>{
 if(url==='/api/session')return new Response(JSON.stringify({token:'static-preview',mode:'DEMO'}));
 if(url==='/api/state')return realFetch('/fixture-state.json');
 if(String(url).startsWith('/api/'))return new Response(JSON.stringify({error:'STATIC_PREVIEW_ONLY',detail:'Run the local Python application to use backend actions.'}),{status:400});
 return realFetch(url,options);
};
""")
    print("Static snapshot ready; backend mutation testing remains separate.")
