"""Uso:
    python main.py http://localhost:8000
    python main.py http://localhost:8000 https://seu-site.com --wait 8 --out relatorios
"""
import argparse
from datetime import datetime
from pathlib import Path

from auditor import capture_cookies
from classifier import load_db, classify_all, summarize
from report import write_json, write_html


def normalize_url(url: str) -> str:
    return url if url.startswith(("http://", "https://")) else "https://" + url


def main() -> None:
    ap = argparse.ArgumentParser(description="Auditor de consentimento de cookies")
    ap.add_argument("urls", nargs="+", help="URLs a auditar (use só sites seus ou de teste)")
    ap.add_argument("--wait", type=float, default=5, help="segundos extras de espera após carregar")
    ap.add_argument("--out", default="out", help="pasta de saída dos relatórios")
    ap.add_argument("--headed", action="store_true", help="abre o navegador visível (debug)")
    args = ap.parse_args()

    db = load_db()
    out_dir = Path(args.out)
    out_dir.mkdir(exist_ok=True)

    results = []
    for raw_url in args.urls:
        url = normalize_url(raw_url)
        print(f"[+] Auditando {url} ...")
        try:
            cookies = capture_cookies(url, wait_seconds=args.wait, headless=not args.headed)
        except Exception as e:
            print(f"    [!] falhou: {e}")
            continue
        classified = classify_all(cookies, db)
        summary = summarize(classified)
        print(f"    {summary['total']} cookies | {summary['violations']} violações | "
              f"{summary['review']} p/ revisar | {summary['ok']} ok")
        results.append({
            "url": url,
            "scanned_at": datetime.now().isoformat(timespec="seconds"),
            "summary": summary,
            "cookies": classified,
        })

    if results:
        write_json(results, out_dir / "report.json")
        write_html(results, out_dir / "report.html")
        print(f"[✓] Relatórios salvos em {out_dir}/report.json e {out_dir}/report.html")


if __name__ == "__main__":
    main()