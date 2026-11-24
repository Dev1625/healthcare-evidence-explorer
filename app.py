"""Serve the demo frontend and one read-only endpoint."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from evidence import load_evidence, search

STATIC = Path(__file__).resolve().parent / "static"
PAGES = {
    "/": ("index.html", "text/html"),
    "/app.js": ("app.js", "text/javascript"),
    "/style.css": ("style.css", "text/css"),
}


def make_server(host, port, data_dir=None):
    evidence, summary = load_evidence() if data_dir is None else load_evidence(data_dir)
    topics = sorted(evidence["topic"].dropna().unique().tolist())
    summary.update(
        records=len(evidence),
        sources=int(evidence["source_ref"].nunique()),
        undated=int(evidence["published"].isna().sum()),
    )

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/api/evidence":
                params = parse_qs(url.query)
                result = {
                    "records": search(
                        evidence,
                        params.get("q", [""])[0],
                        params.get("topic", [""])[0],
                    ),
                    "topics": topics,
                    "summary": summary,
                }
                self.send_content(json.dumps(result).encode("utf-8"), "application/json")
                return
            if url.path in PAGES:
                name, media_type = PAGES[url.path]
                self.send_content((STATIC / name).read_bytes(), media_type)
                return
            self.send_error(404)

        def send_content(self, body, media_type):
            self.send_response(200)
            self.send_header("Content-Type", f"{media_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    with make_server("127.0.0.1", args.port) as server:
        print(f"Evidence explorer running at http://127.0.0.1:{server.server_port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
