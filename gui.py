import json
import requests
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

CONFIG_FILE = "config.json"
PROXIES_FILE = "proxies.txt"

COUNTRIES = [
    ("br", "Brazil"),
    ("us", "United States"),
    ("gb", "United Kingdom"),
    ("de", "Germany"),
    ("fr", "France"),
    ("ca", "Canada"),
    ("au", "Australia"),
    ("nl", "Netherlands"),
    ("es", "Spain"),
    ("it", "Italy"),
    ("mx", "Mexico"),
    ("ar", "Argentina"),
]

def load_config():
    if not Path(CONFIG_FILE).exists():
        return {"token": ""}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def load_proxies():
    if not Path(PROXIES_FILE).exists():
        return ""
    with open(PROXIES_FILE, "r", encoding="utf-8") as f:
        return f.read()

def save_proxies(text):
    with open(PROXIES_FILE, "w", encoding="utf-8") as f:
        f.write(text)

def parse_proxy(line):
    line = line.strip()
    if line.startswith("http://") or line.startswith("https://"):
        line = line.split("//", 1)[1]
    parts = line.split(":")
    if len(parts) >= 4:
        return {
            "mode": "http",
            "host": parts[0],
            "port": int(parts[1]),
            "username": parts[2],
            "password": ":".join(parts[3:])
        }
    elif len(parts) == 2:
        return {
            "mode": "http",
            "host": parts[0],
            "port": int(parts[1]),
            "username": "",
            "password": ""
        }
    return None

def create_profile(token, name):
    url = "https://api.gologin.com/browser/quick"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "os": "win",
        "name": name
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=30)
        if r.ok:
            data = r.json()
            return True, data.get("id")
        else:
            return False, r.text[:200]
    except Exception as e:
        return False, str(e)

def set_custom_proxy(token, profile_id, proxy):
    url = "https://api.gologin.com/browser/proxy/many/v2"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "proxies": [
            {
                "profileId": profile_id,
                "proxy": proxy
            }
        ]
    }
    try:
        r = requests.patch(url, headers=headers, json=body, timeout=30)
        return r.ok, r.text[:150] if not r.ok else "proxy set"
    except Exception as e:
        return False, str(e)

def set_gologin_proxy(token, profile_id, country):
    url = "https://api.gologin.com/users-proxies/mobile-proxy"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "countryCode": country,
        "profileIdToLink": profile_id,
        "isMobile": True
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=30)
        return r.ok, r.text[:150] if not r.ok else "gologin proxy set"
    except Exception as e:
        return False, str(e)

class App:
    def __init__(self, root):
        self.root = root
        root.title("Profile Setup")
        root.geometry("520x680")

        cfg = load_config()

        tk.Label(root, text="API Token").pack(anchor="w", padx=10, pady=(10,0))
        self.token = tk.Entry(root, width=65)
        self.token.insert(0, cfg.get("token", ""))
        self.token.pack(padx=10, pady=5)

        self.use_gologin = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text="Usar proxies do GoLogin (em vez da lista)", variable=self.use_gologin).pack(anchor="w", padx=10, pady=5)

        country_frame = tk.Frame(root)
        country_frame.pack(anchor="w", padx=10)
        tk.Label(country_frame, text="País:").pack(side="left")
        self.country = ttk.Combobox(country_frame, width=20, state="readonly")
        self.country["values"] = [f"{code.upper()} - {name}" for code, name in COUNTRIES]
        self.country.current(0)
        self.country.pack(side="left", padx=5)

        tk.Label(root, text="Proxies custom (um por linha)").pack(anchor="w", padx=10, pady=(10,0))
        self.proxies = scrolledtext.ScrolledText(root, height=10)
        self.proxies.insert("1.0", load_proxies())
        self.proxies.pack(padx=10, pady=5, fill="both", expand=True)

        frame = tk.Frame(root)
        frame.pack(pady=10)
        tk.Label(frame, text="Quantidade:").grid(row=0, column=0, padx=5)
        self.qty = tk.Entry(frame, width=8)
        self.qty.insert(0, "5")
        self.qty.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Prefixo:").grid(row=0, column=2, padx=5)
        self.prefix = tk.Entry(frame, width=10)
        self.prefix.insert(0, "P")
        self.prefix.grid(row=0, column=3, padx=5)

        tk.Button(root, text="Salvar Proxies", command=self.save).pack(pady=5)
        tk.Button(root, text="Criar Perfis", command=self.create, bg="#238636", fg="white").pack(pady=5)

        self.status = tk.Label(root, text="")
        self.status.pack(pady=5)

    def save(self):
        save_proxies(self.proxies.get("1.0", "end"))
        cfg = load_config()
        cfg["token"] = self.token.get().strip()
        save_config(cfg)
        self.status.config(text="Salvo.")

    def create(self):
        self.save()
        token = self.token.get().strip()
        if not token:
            messagebox.showerror("Erro", "Token vazio")
            return

        use_gl = self.use_gologin.get()
        country_code = self.country.get().split(" - ")[0].lower()

        lines = [l.strip() for l in self.proxies.get("1.0", "end").splitlines() if l.strip()]
        if not use_gl and not lines:
            messagebox.showerror("Erro", "Nenhum proxy na lista")
            return

        try:
            qty = int(self.qty.get())
        except:
            qty = 5 if use_gl else len(lines)

        prefix = self.prefix.get().strip() or "P"

        self.status.config(text="Criando...")
        self.root.update()

        created = 0
        for i in range(qty):
            name = f"{prefix}{i+1}"

            ok, profile_id = create_profile(token, name)
            if not ok:
                self.status.config(text=f"{name}: FAIL criar - {str(profile_id)[:40]}")
                self.root.update()
                time.sleep(0.5)
                continue

            if use_gl:
                pok, pmsg = set_gologin_proxy(token, profile_id, country_code)
            else:
                proxy_line = lines[i % len(lines)]
                proxy = parse_proxy(proxy_line)
                if not proxy:
                    self.status.config(text=f"{name}: proxy inválido")
                    self.root.update()
                    continue
                pok, pmsg = set_custom_proxy(token, profile_id, proxy)

            if pok:
                created += 1
                self.status.config(text=f"{name}: OK")
            else:
                self.status.config(text=f"{name}: criado mas proxy FAIL - {pmsg[:40]}")
            self.root.update()
            time.sleep(0.6)

        tipo = "GoLogin" if use_gl else "custom"
        self.status.config(text=f"Concluído. {created}/{qty} com proxy {tipo}. Dê F5 no GoLogin.")
        messagebox.showinfo("Pronto", f"{created} de {qty} perfis criados.")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
