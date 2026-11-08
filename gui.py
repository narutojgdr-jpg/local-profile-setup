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
            return True, data.get("id", "created")
        else:
            return False, r.text[:200]
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

        tk.Label(root, text="Proxies (um por linha, host:port) - opcional por enquanto").pack(anchor="w", padx=10)
        self.proxies = scrolledtext.ScrolledText(root, height=12)
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

        try:
            qty = int(self.qty.get())
        except:
            qty = 5

        prefix = self.prefix.get().strip() or "P"

        self.status.config(text="Criando...")
        self.root.update()

        created = 0
        for i in range(qty):
            name = f"{prefix}{i+1}"
            ok, msg = create_profile(token, name)
            if ok:
                created += 1
                self.status.config(text=f"{name}: OK ({msg[:20]})")
            else:
                self.status.config(text=f"{name}: FAIL - {msg[:50]}")
            self.root.update()
            time.sleep(0.6)

        self.status.config(text=f"Concluído. {created}/{qty} criados. Dê F5 no GoLogin.")
        messagebox.showinfo("Pronto", f"{created} de {qty} perfis criados.")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
