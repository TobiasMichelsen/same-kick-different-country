# Step 4: local server for the annotation tool
#
# Opens your sheet in the tool and "Save CSV" saves straight into
# annotations/sheets/annotator_N.csv. Works in every browser, no extra packages.
# annotate.command (Mac) and annotate.bat (Windows) start this for you.
#
# Run from the repo root: python src/02_annotation/04_serve_annotator.py 1
#
# To not break anything:
#   - only runs on your own computer (127.0.0.1)
#   - only saves into sheets that already exist
#   - doesn't save if the rows don't match the sheet (so no half/wrong sheet)
#   - keeps the old version as .csv.bak

import argparse
import csv
import io
import os
import re
import socket
import sys
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
ANNOTATIONS = ROOT / "annotations"
SHEETS = ANNOTATIONS / "sheets"
SHEET_NAME = re.compile(r"^annotator_\d+$")


# the unit_id column of a sheet, to check a save has the same rows
def unit_ids(text):
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    if not rows or "unit_id" not in rows[0]:
        raise ValueError("no unit_id column")
    i = rows[0].index("unit_id")
    return [r[i] for r in rows[1:] if r]


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")   # no caching, always the newest sheet
        super().end_headers()

    def log_message(self, fmt, *args):                 # don't print every request
        pass

    def _reply(self, code, text):
        body = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path == "/api/ping":
            return self._reply(200, "ok")
        return super().do_GET()

    # saving a sheet
    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/api/save":
            return self._reply(404, "not found")
        # only our tool sends this header, so other websites can't save here
        if self.headers.get("X-Annotator") != "1":
            return self._reply(403, "missing X-Annotator header")
        sheet = parse_qs(url.query).get("sheet", [""])[0]
        path = SHEETS / f"{sheet}.csv"
        if not SHEET_NAME.match(sheet) or not path.exists():
            return self._reply(400, f"unknown sheet {sheet!r}")

        text = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8")
        try:
            if unit_ids(text) != unit_ids(path.read_text(encoding="utf-8")):
                return self._reply(409, "the units in this save don't match the sheet on disk")
        except (ValueError, csv.Error) as e:
            return self._reply(400, f"not a valid sheet: {e}")

        # write to a tmp file first, then swap, old one becomes .bak
        tmp = path.with_suffix(".csv.tmp")
        tmp.write_text(text, encoding="utf-8", newline="")
        os.replace(path, path.with_suffix(".csv.bak"))
        os.replace(tmp, path)
        print(f"  saved {path.relative_to(ROOT)}")
        return self._reply(200, "saved")


# first port that isn't used yet
def free_port(start=8765, tries=20):
    for port in range(start, start + tries):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    sys.exit("No free port found between 8765 and 8784.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("annotator", help="1, 2, 3, annotator-2, annotator_3 ...")
    ap.add_argument("--port", type=int)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)   # print messages right away

    n = re.sub(r"\D", "", args.annotator)          # "annotator_2" -> "2"
    sheet = f"annotator_{n}"
    if not n or not (SHEETS / f"{sheet}.csv").exists():
        sys.exit(f"Can't find annotations/sheets/{sheet}.csv (use 1, 2 or 3).")

    port = args.port or free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port),
                                 partial(Handler, directory=str(ANNOTATIONS)))
    url = f"http://127.0.0.1:{port}/annotator.html?sheet={sheet}"
    print(f"\nAnnotating {sheet} at {url}")
    print("Your sheet opens automatically and 'Save CSV' writes straight into")
    print(f"annotations/sheets/{sheet}.csv.")
    print("\nKeep this window open while you annotate. Press Ctrl+C here when you're done.\n")
    if not args.no_browser:
        threading.Timer(0.5, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped. Remember to commit and push your sheet.")


if __name__ == "__main__":
    main()
