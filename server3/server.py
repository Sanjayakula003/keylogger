import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, redirect, render_template_string, request, send_from_directory, url_for


APP = Flask(__name__)

DATA_DIR = Path(os.environ.get("MONITOR_DEMO_DATA_DIR", "data")).resolve()
KEYSTROKES_LOG = DATA_DIR / "keystrokes.log"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    if not KEYSTROKES_LOG.exists():
        KEYSTROKES_LOG.write_text("", encoding="utf-8")


@APP.get("/")
def index() -> Response:
    return redirect(url_for("dashboard"))


@APP.get("/dashboard")
def dashboard() -> str:
    ensure_dirs()

    tail = ""
    try:
        content = KEYSTROKES_LOG.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()[-200:]
        tail = "\n".join(lines)
    except FileNotFoundError:
        tail = ""

    shots = sorted(
        (p.name for p in SCREENSHOTS_DIR.glob("*.png")),
        reverse=True,
    )[:50]

    return render_template_string(
        """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Consent Monitoring Demo</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; }
      .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
      pre { background: #0b1020; color: #e6e8ef; padding: 12px; border-radius: 8px; overflow: auto; max-height: 70vh; }
      a { color: #2457ff; text-decoration: none; }
      .muted { color: #556; }
      .card { border: 1px solid #e7e7ef; border-radius: 12px; padding: 14px; }
      img { width: 100%; border-radius: 10px; border: 1px solid #e7e7ef; }
      code { background: #f4f6ff; padding: 2px 6px; border-radius: 6px; }
    </style>
  </head>
  <body>
    <h2>Consent-based Monitoring Demo</h2>
    <p class="muted">
      This server receives events from the demo client. It is not stealthy and is meant for visible, consent-based classroom demonstration.
    </p>
    <div class="grid">
      <div class="card">
        <h3>Recent typed text (from demo app input only)</h3>
        <pre>{{ tail }}</pre>
      </div>
      <div class="card">
        <h3>Latest screenshots</h3>
        {% if shots|length == 0 %}
          <p class="muted">No screenshots received yet.</p>
        {% else %}
          <p class="muted">Showing newest first. Stored under <code>{{ screenshots_dir }}</code>.</p>
          {% for name in shots %}
            <div style="margin-bottom: 14px;">
              <div class="muted" style="font-size: 12px; margin-bottom: 6px;">{{ name }}</div>
              <a href="{{ url_for('get_screenshot', filename=name) }}"><img src="{{ url_for('get_screenshot', filename=name) }}" /></a>
            </div>
          {% endfor %}
        {% endif %}
      </div>
    </div>
  </body>
</html>
        """,
        tail=tail,
        shots=shots,
        screenshots_dir=str(SCREENSHOTS_DIR),
    )


@APP.post("/api/keystrokes")
def api_keystrokes():
    ensure_dirs()
    payload = request.get_json(silent=True) or {}
    device = str(payload.get("device", "unknown"))
    text = str(payload.get("text", ""))
    ts = str(payload.get("ts", utc_now_iso()))

    if not text:
        return jsonify({"ok": False, "error": "empty text"}), 400

    KEYSTROKES_LOG.open("a", encoding="utf-8").write(f"{ts}\t{device}\t{text}\n")
    return jsonify({"ok": True})


@APP.post("/api/screenshot")
def api_screenshot():
    ensure_dirs()
    device = request.form.get("device", "unknown")
    ts = request.form.get("ts", utc_now_iso())
    f = request.files.get("file")
    if f is None:
        return jsonify({"ok": False, "error": "missing file"}), 400

    safe_device = "".join(ch for ch in device if ch.isalnum() or ch in ("-", "_"))[:50] or "unknown"
    safe_ts = "".join(ch for ch in ts if ch.isalnum() or ch in ("-", "_", ".", "T", "Z", "+"))[:80]
    name = f"{safe_ts}_{safe_device}.png".replace(":", "-")
    out = SCREENSHOTS_DIR / name
    f.save(out)
    return jsonify({"ok": True, "saved_as": name})


@APP.get("/screenshots/<path:filename>")
def get_screenshot(filename: str):
    ensure_dirs()
    return send_from_directory(SCREENSHOTS_DIR, filename)


def main() -> None:
    ensure_dirs()
    host = os.environ.get("MONITOR_DEMO_HOST", "0.0.0.0")
    # 8080 is sometimes reserved/blocked on Windows; default to 5000.
    port = int(os.environ.get("PORT", 5000))
    APP.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
