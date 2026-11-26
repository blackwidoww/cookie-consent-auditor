"""Geração de relatórios (JSON + HTML)."""
import json
import shutil
from html import escape
from pathlib import Path

STATUS_LABEL = {"violation": "🚩 Violação", "review": "🔎 Revisar", "ok": "✅ OK"}

# O visual fica em report.css (edite lá, sem mexer no Python)
CSS_SOURCE = Path(__file__).parent / "report.css"


def write_json(results: list[dict], path: Path) -> None:
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


def build_sections(results: list[dict]) -> str:
    """Monta o HTML dos cards de resultado (usado pelo relatório e pela interface web)."""
    sections = []
    for r in results:
        s = r["summary"]
        rows = ""
        for c in sorted(r["cookies"], key=lambda x: x["status"] != "violation"):
            life = "sessão" if c["lifetime_days"] is None else f'{c["lifetime_days"]} dias'
            origin = "terceiros" if c["third_party"] else "própria"
            rows += (
                f'<tr class="{c["status"]}">'
                f'<td><span class="badge {c["status"]}">{STATUS_LABEL[c["status"]]}</span></td>'
                f'<td><code>{escape(c["name"])}</code></td>'
                f'<td>{escape(c["domain"])}</td>'
                f'<td>{origin}</td>'
                f'<td>{escape(c["category"])}</td>'
                f'<td>{escape(c["vendor"] or "-")}</td>'
                f'<td>{life}</td></tr>'
            )
        sections.append(f"""
        <section class="site">
          <h2>{escape(r["url"])}</h2>
          <small>escaneado em {escape(r["scanned_at"])}</small>
          <div class="chips">
            <span class="chip">{s["total"]} cookies</span>
            <span class="chip violation">{s["violations"]} violações</span>
            <span class="chip review">{s["review"]} para revisar</span>
            <span class="chip ok">{s["ok"]} ok</span>
          </div>
          <div class="table-wrap"><table>
            <thead><tr><th>Status</th><th>Nome</th><th>Domínio</th><th>Origem</th>
            <th>Categoria</th><th>Fornecedor</th><th>Duração</th></tr></thead>
            <tbody>{rows}</tbody>
          </table></div>
        </section>""")
    return "".join(sections)


def write_html(results: list[dict], path: Path) -> None:
    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cookie Consent Auditor</title>
<link rel="stylesheet" href="report.css"></head><body>
<div class="wrap">
  <header>
    <h1>Cookie Consent <span>Auditor</span></h1>
    <p>Cookies gravados <b>antes</b> de qualquer interação com o banner de consentimento.</p>
  </header>
  {build_sections(results)}
</div>
</body></html>"""
    path.write_text(html, encoding="utf-8")
    shutil.copyfile(CSS_SOURCE, path.parent / "report.css")  # o HTML usa este arquivo