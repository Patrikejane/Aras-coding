"""
serve.py  -  Local reviewer UI server (stdlib only, no npm)
Usage:  python ui/serve.py
        python ui/serve.py --port 9090
"""
import http.server, socketserver, webbrowser, argparse
from pathlib import Path

UI_DIR = Path(__file__).parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(UI_DIR), **kw)
    def log_message(self, *_): pass   # suppress request noise

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    url = f"http://localhost:{args.port}"
    print(f"\n  Aras Reviewer UI  ->  {url}  (Ctrl+C to stop)\n")
    with socketserver.TCPServer(("", args.port), Handler) as s:
        s.allow_reuse_address = True
        if not args.no_browser: webbrowser.open(url)
        try:    s.serve_forever()
        except KeyboardInterrupt: print("\n  Stopped.")

if __name__ == "__main__":
    main()
