import json
import requests
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, scrolledtext

CONFIG_FILE = "config.json"
PROXIES_FILE = "proxies.txt"

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

def create_profile(token, name, proxy):
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

class App:
    def __init__(self, root):
        self.root = root
        root.title("Profile Setup")
        root.geometry("500x600")

        cfg = load_config()

        tk.Label(root, text="API Token").pack(anchor="w", padx=10, pady=(10,0))
        self.token = tk.Entry(root, width=60)
        self.token.insert(0, cfg.get("token", ""))
        self.token.pack(padx=10, pady=5)

        tk.Label(root, text="Proxies (um por linha, host:port)").pack(anchor="w", padx=10)
        self.proxies = scrolledtext.ScrolledText(root, height=12)
        self.proxies.insert("1.0", load_proxies())
        self.proxies.pack(padx=10, pady=5, fill="both", expand=True)

        frame = tk.Frame(root)
        frame.pack(pady=10)
        tk.Label(frame, text="Quantidade:").grid(row=0, column=0, padx=5)
        self.qty = tk.Entry(frame, width=8)
        self.qty.insert(0, "10")
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

        lines = [l.strip() for l in self.proxies.get("1.0", "end").splitlines() if l.strip()]
        if not lines:
            messagebox.showerror("Erro", "Nenhum proxy")
            return

        try:
            qty = int(self.qty.get())
        except:
            qty = len(lines)

        prefix = self.prefix.get().strip() or "P"

        self.status.config(text="Criando...")
        self.root.update()

        for i in range(qty):
            name = f"{prefix}{i+1}"
            proxy = lines[i % len(lines)]
            ok, msg = create_profile(token, name, proxy)
            self.status.config(text=f"{name}: {'OK' if ok else 'FAIL'}")
            self.root.update()
            time.sleep(0.4)

        self.status.config(text="Concluído. Dê F5 no GoLogin.")
        messagebox.showinfo("Pronto", f"{qty} perfis processados.")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
