import os, json, time, re, hashlib
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
STATE_PATH = ROOT / "state.json"

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
if not TOKEN or not CHAT_ID:
    raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; StockWatcher/1.0; contact admin)",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}
OUT_PATTERNS = [re.compile(p, re.I) for p in CONFIG.get("out_of_stock_patterns", [])]
IN_PATTERNS = [re.compile(p, re.I) for p in CONFIG.get("in_stock_patterns", [])]

def load_state():
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

def telegram_send(text):
    api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(api, data={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": False}, timeout=20)
    r.raise_for_status()

def fetch_page(url):
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Remove scripts/styles and reduce text noise
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)[:250000]

def detect_stock(text):
    # Out-of-stock signals take priority, since product pages often mention stock in unrelated areas.
    if any(p.search(text) for p in OUT_PATTERNS):
        return "out_of_stock"
    if any(p.search(text) for p in IN_PATTERNS):
        return "in_stock"
    return "unknown"

def fingerprint(text):
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]

def check_target(target, state):
    key = target["url"]
    try:
        text = fetch_page(key)
        status = detect_stock(text)
        old = state.get(key, {}).get("status", "unknown")
        state[key] = {"status": status, "checked_at": int(time.time()), "fingerprint": fingerprint(text)}
        if status == "in_stock" and old != "in_stock":
            msg = (
                "🟢 ¡STOCK DETECTADO!\n"
                f"{target.get('product', 'Producto Pokémon')}\n"
                f"Tienda: {target.get('store', urlparse(key).netloc)}\n"
                f"URL: {key}\n"
                "Confirma el stock en la web: los detectores automáticos pueden equivocarse."
            )
            telegram_send(msg)
        elif status == "out_of_stock" and old == "in_stock":
            telegram_send(f"🔴 Se agotó / ya no aparece disponible:\n{target.get('product', 'Producto Pokémon')}\n{key}")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {target.get('store')} | {status} (prev: {old})")
    except Exception as e:
        state.setdefault(key, {})["last_error"] = str(e)[:300]
        print(f"Error revisando {key}: {e}")

def main():
    state = load_state()
    targets = CONFIG.get("targets", [])
    delay = int(CONFIG.get("delay_between_targets_seconds", 8))

    if not targets:
        print("Añade tiendas/product URLs en config.json")
        return

    for i, target in enumerate(targets):
        check_target(target, state)
        save_state(state)

        if i < len(targets) - 1:
            time.sleep(delay)

    save_state(state)
    print("Revisión terminada.")


if __name__ == "__main__":
    main()
