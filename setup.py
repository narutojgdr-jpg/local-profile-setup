import json
import requests
import time
from pathlib import Path

CONFIG_FILE = "config.json"
PROXIES_FILE = "proxies.txt"

def load_config():
    if not Path(CONFIG_FILE).exists():
        return {"token": "", "workspace": ""}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def load_proxies():
    if not Path(PROXIES_FILE).exists():
        return []
    with open(PROXIES_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def create_profile(token, name, proxy):
    # GoLogin profile creation endpoint
    url = "https://api.gologin.com/browser"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "name": name,
        "proxy": {
            "mode": "http",
            "host": proxy.split(":")[0] if ":" in proxy else proxy,
            "port": int(proxy.split(":")[1]) if ":" in proxy else 8080,
            "username": "",
            "password": ""
        } if proxy else {"mode": "none"}
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=30)
        return r.ok, r.text[:200] if not r.ok else "ok"
    except Exception as e:
        return False, str(e)

def main():
    cfg = load_config()
    token = cfg.get("token") or input("API token: ").strip()
    if not token:
        print("Token required.")
        return
    cfg["token"] = token
    save_config(cfg)

    proxies = load_proxies()
    if not proxies:
        print("No proxies in proxies.txt")
        return

    qty = int(input(f"How many profiles? (proxies available: {len(proxies)}): ") or len(proxies))
    prefix = input("Name prefix (default P): ").strip() or "P"

    print(f"Creating {qty} profiles...")
    for i in range(qty):
        name = f"{prefix}{i+1}"
        proxy = proxies[i % len(proxies)]
        ok, msg = create_profile(token, name, proxy)
        print(f"{name} -> {'OK' if ok else 'FAIL: ' + msg}")
        time.sleep(0.5)

if __name__ == "__main__":
    main()
