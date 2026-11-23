"""本地票册服务：提供 HTML 页面 + 补充写回 SQLite 的 API。"""
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from album_db import all_tickets, apply_supplements

PORT = 8765


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE, **kwargs)

    def log_message(self, fmt, *args):
        pass  # 静默

    def do_GET(self):
        self.path = self.path.split("?", 1)[0]
        if self.path == "/api/tickets":
            data = json.dumps(all_tickets(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path in ("/", "/index.html"):
            self.path = "/%E9%97%A8%E7%A5%A8%E6%94%B6%E8%97%8F%E5%86%8C.html"
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/supplement":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n) or b"{}")
                apply_supplements(body)
                resp = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
            except Exception as e:
                resp = json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False).encode("utf-8")
                self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_error(404)


if __name__ == "__main__":
    # 绑定 0.0.0.0，手机等同一局域网设备可访问
    print(f"ticket album serving on http://127.0.0.1:{PORT} (LAN: http://<本机局域网IP>:{PORT})")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
