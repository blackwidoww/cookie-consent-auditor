"""Captura de cookies gravados ANTES de qualquer interação com o banner de consentimento."""
import time
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


def _is_third_party(cookie_domain: str, site_host: str) -> bool:
    """Cookie é de terceiro se o domínio dele não bate com o host do site visitado."""
    cd = cookie_domain.lstrip(".").lower()
    host = site_host.lower()
    return not (host == cd or host.endswith("." + cd) or cd.endswith("." + host))


def capture_cookies(url: str, wait_seconds: float = 5, timeout_ms: int = 30000,
                    headless: bool = True) -> list[dict]:
    """Abre a página num contexto NOVO (sem cookies prévios), NÃO clica em nada
    e devolve todos os cookies que o navegador gravou até ali."""
    host = urlparse(url).hostname or ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(locale="pt-BR")  # contexto limpo = sem histórico de consentimento
        page = context.new_page()
        try:
            page.goto(url, wait_until="load", timeout=timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PWTimeout:
                pass  # alguns sites nunca ficam "idle"; seguimos mesmo assim
            page.wait_for_timeout(wait_seconds * 1000)  # dá tempo pra scripts atrasados
            raw = context.cookies()  # inclui cookies de terceiros
        finally:
            browser.close()

    now = time.time()
    cookies = []
    for c in raw:
        expires = c.get("expires", -1)
        cookies.append({
            "name": c["name"],
            "domain": c["domain"],
            "path": c["path"],
            "secure": c["secure"],
            "http_only": c["httpOnly"],
            "same_site": c.get("sameSite"),
            "lifetime_days": None if expires == -1 else round((expires - now) / 86400, 1),
            "third_party": _is_third_party(c["domain"], host),
        })
    return cookies