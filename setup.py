"""Configura l'avviso Telegram su GitHub in un colpo solo.

Prima: crea il bot con @BotFather e mandagli un messaggio qualsiasi.
Poi:   python setup.py   e incolla il token quando te lo chiede.
"""
import getpass
import subprocess

from curl_cffi import requests as cffi_requests

REPO = "Shailene1/aion2-daminu-alert"


def telegram(token, method, **params):
    resp = cffi_requests.post(f"https://api.telegram.org/bot{token}/{method}", json=params, timeout=30)
    data = resp.json()
    if not data.get("ok"):
        raise SystemExit(f"Telegram ha risposto: {data.get('description')}. Il token è giusto?")
    return data["result"]


def main():
    token = getpass.getpass("Incolla il token del bot (non verrà mostrato) e premi Invio: ").strip()
    bot = telegram(token, "getMe")
    print(f"Bot trovato: @{bot['username']}")

    chats = [u["message"]["chat"] for u in telegram(token, "getUpdates") if "message" in u]
    if not chats:
        raise SystemExit(f"Nessun messaggio ricevuto: scrivi qualcosa a @{bot['username']} su Telegram e rilancia.")
    chat_id = str(chats[-1]["id"])
    print(f"Chat trovata: {chats[-1].get('first_name') or chats[-1].get('title')}")

    for name, value in (("TELEGRAM_TOKEN", token), ("TELEGRAM_CHAT_ID", chat_id)):
        subprocess.run(["gh", "secret", "set", name, "--repo", REPO], input=value, text=True, check=True)
    print("Segreti salvati su GitHub.")

    telegram(token, "sendMessage", chat_id=chat_id, text="Tutto pronto: ti scrivo quando Daminu non è più bloccato.")
    print("Messaggio di prova inviato: controlla Telegram.")


if __name__ == "__main__":
    main()
