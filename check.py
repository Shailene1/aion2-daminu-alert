"""Manda un messaggio Telegram quando Daminu (EU) non blocca più la creazione di personaggi.

Serve un bot Telegram: il token e il chat id si leggono dalle variabili
d'ambiente TELEGRAM_TOKEN e TELEGRAM_CHAT_ID.

Uso:
  python aion2_daminu_alert.py chatid      stampa il tuo chat id (scrivi prima al bot)
  python aion2_daminu_alert.py test        manda un messaggio di prova
  python aion2_daminu_alert.py [minuti]    controlla ogni N minuti (default 5)
"""
import os
import sys
import time
from datetime import datetime

from curl_cffi import requests as cffi_requests

URL = "https://aion2.gaming.tools/server-status?region=EU"
SERVER = "Daminu"
BLOCKED_MARK = "Character creation blocked"


def creation_blocked():
    """True se bloccato, False se aperto. Solleva se la riga del server manca."""
    resp = cffi_requests.get(URL, impersonate="chrome124", timeout=30)
    resp.raise_for_status()
    html = resp.text
    start = html.find(f">{SERVER}</span>")
    if start == -1:
        raise RuntimeError(f"riga di {SERVER} non trovata nella pagina")
    end = html.find("</tr>", start)
    return BLOCKED_MARK in html[start:end]


def telegram(method, **params):
    token = os.environ["TELEGRAM_TOKEN"]
    resp = cffi_requests.post(f"https://api.telegram.org/bot{token}/{method}", json=params, timeout=30)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram: {data.get('description')}")
    return data["result"]


def notify(text):
    telegram("sendMessage", chat_id=os.environ["TELEGRAM_CHAT_ID"], text=text)


def print_chat_id():
    updates = telegram("getUpdates")
    if not updates:
        print("Nessun messaggio trovato: scrivi qualcosa al bot su Telegram e rilancia.")
    for u in updates:
        chat = (u.get("message") or {}).get("chat")
        if chat:
            print(f"chat id: {chat['id']}  ({chat.get('first_name') or chat.get('title')})")


def check_once():
    """Un solo controllo, per GitHub Actions. Se il server è aperto manda il
    messaggio e scrive open=true negli output del passo, così il workflow si spegne."""
    try:
        blocked = creation_blocked()
    except Exception as e:
        print(f"errore: {e}")
        return
    if blocked:
        print(f"{SERVER}: ancora bloccato")
        return
    print(f"{SERVER}: creazione APERTA, mando il messaggio")
    notify(f"{SERVER} non è più bloccato: puoi creare un personaggio.\n{URL}")
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write("open=true\n")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "5"
    if arg == "chatid":
        return print_chat_id()
    if arg == "test":
        return notify("Prova: l'avviso per Daminu funziona.")
    if arg == "once":
        return check_once()

    minutes = float(arg)
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        try:
            if not creation_blocked():
                print(f"{now}  {SERVER}: creazione APERTA, mando il messaggio")
                notify(f"{SERVER} non è più bloccato: puoi creare un personaggio.\n{URL}")
                return
            print(f"{now}  {SERVER}: ancora bloccato")
        except Exception as e:
            print(f"{now}  errore: {e}")
        time.sleep(minutes * 60)


if __name__ == "__main__":
    main()
