"""Interface web LOCAL do auditor: digite o site e veja o relatório na tela.

Uso:
    python app.py
    (abra http://127.0.0.1:5000 no navegador)
"""
from datetime import datetime
from html import escape
from urllib.parse import urlparse

from flask import Flask, request, send_from_directory

from auditor import capture_cookies
from classifier import load_db, classify_all, summarize
from report import build_sections, CSS_SOURCE

app = Flask(__name__)
DB = load_db()
HISTORY: list[dict] = []   # resultados desta sessão (o mais recente primeiro)


def normalize_url(raw: str):
    """Valida o que foi digitado. Devolve (url, erro)."""
    raw = raw.strip()
    if not raw:
        return None, "Digite o endereço de um site."
    if "://" not in raw:
        local = raw.startswith(("localhost", "127.0.0.1"))
        raw = ("http://" if local else "https://") + raw
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return None, "Use um endereço http:// ou https:// válido."
    return raw, None


def render_page(url_value: str = "", error: str | None = None) -> str:
    error_html = f'<div class="error">{escape(error)}</div>' if error else ""
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cookie Consent Auditor</title>
<link rel="stylesheet" href="/report.css"></head><body>
<div class="wrap">
  <header>
    <h1>Cookie Consent <span>Auditor</span></h1>
    <p>Cookies gravados <b>antes</b> de qualquer interação com o banner de consentimento.</p>
  </header>
  <form method="post" class="search" id="scan-form">
    <input type="text" name="url" value="{escape(url_value)}" placeholder="http://localhost:8000" autofocus required>
    <button type="submit" id="scan-btn">Auditar</button>
  </form>
  <p class="hint" id="hint">Use só sites seus, de teste ou públicos, uma página por vez.</p>
  {error_html}
  {build_sections(HISTORY)}
</div>
<script>
  document.getElementById('scan-form').addEventListener('submit', function () {{
    var btn = document.getElementById('scan-btn');
    btn.disabled = true; btn.textContent = 'Auditando...';
    document.getElementById('hint').textContent = '... Isso leva alguns segundos. Aguarde.';
  }});
</script>
</body></html>"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_page()

    raw = request.form.get("url", "")
    url, error = normalize_url(raw)
    if error:
        return render_page(raw, error)

    try:
        cookies = capture_cookies(url)
    except Exception as e:
        return render_page(raw, f"Não consegui abrir {url}: {e}")

    classified = classify_all(cookies, DB)
    HISTORY.insert(0, {
        "url": url,
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summarize(classified),
        "cookies": classified,
    })
    del HISTORY[10:]   # guarda só os 10 últimos
    return render_page()


@app.route("/report.css")
def css():
    return send_from_directory(CSS_SOURCE.parent, CSS_SOURCE.name)


if __name__ == "__main__":
    # 127.0.0.1 = só ESTA máquina acessa. Nunca troque por 0.0.0.0: qualquer pessoa
    # na rede poderia usar o seu computador pra visitar sites.
    app.run(host="127.0.0.1", port=5000, debug=False)