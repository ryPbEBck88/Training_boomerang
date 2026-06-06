import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone


CHECK_URL = os.environ.get("CHECK_URL", "http://web:8000/").strip()
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", "30") or "30")
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "5") or "5")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
SERVICE_NAME = os.environ.get("MONITORED_SERVICE_NAME", "web").strip() or "web"


def is_up() -> tuple[bool, str]:
    try:
        req = urllib.request.Request(CHECK_URL, method="GET")
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            code = getattr(resp, "status", 200)
            if 200 <= code < 400:
                return True, f"HTTP {code}"
            return False, f"HTTP {code}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def send_telegram(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        print(f"[monitor] Telegram skipped (missing env): {text}")
        return

    endpoint = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode(
        {
            "chat_id": CHAT_ID,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")

    req = urllib.request.Request(endpoint, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        _ = resp.read()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def main() -> None:
    # Unknown initial state; notify only on state transitions.
    was_up: bool | None = None
    print(
        f"[monitor] started: url={CHECK_URL}, interval={CHECK_INTERVAL_SECONDS}s, service={SERVICE_NAME}"
    )

    while True:
        up, details = is_up()
        print(f"[monitor] check={up} details={details}")

        if was_up is None:
            was_up = up
        elif was_up and not up:
            send_telegram(
                f"🚨 Service DOWN: {SERVICE_NAME}\nURL: {CHECK_URL}\nReason: {details}\nTime: {now_utc()}"
            )
            was_up = False
        elif (not was_up) and up:
            send_telegram(
                f"✅ Service RECOVERED: {SERVICE_NAME}\nURL: {CHECK_URL}\nStatus: {details}\nTime: {now_utc()}"
            )
            was_up = True

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
