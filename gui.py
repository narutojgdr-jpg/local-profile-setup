import json
import requests
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, simpledialog

CONFIG_FILE = "config.json"
PROXIES_FILE = "proxies.txt"
COOKIES_FILE = "cookies.json"

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

def load_cookies():
    if not Path(COOKIES_FILE).exists():
        return {}
    with open(COOKIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cookies(data):
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

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

def set_cookies(token, profile_id, cookies):
    url = f"https://api.gologin.com/browser/{profile_id}/cookies?fromUser=true&cleanCookies=true"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Normalize cookies for API (add url if missing)
    normalized = []
    for c in cookies:
        item = dict(c)
        if "url" not in item:
            domain = item.get("domain", "").lstrip(".")
            item["url"] = f"https://{domain}" if domain else "https://google.com"
        if "value" in item and not isinstance(item["value"], str):
            item["value"] = str(item["value"])
        normalized.append(item)
    try:
        r = requests.post(url, headers=headers, json=normalized, timeout=30)
        return r.ok, r.text[:150] if not r.ok else "cookies set"
    except Exception as e:
        return False, str(e)

class App:
    def __init__(self, root):
        self.root = root
        root.title("Profile Setup")
        root.geometry("560x720")

        self.cfg = load_config()
        self.cookies_data = load_cookies()

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab Perfis
        self.tab_profiles = ttk.Frame(notebook)
        notebook.add(self.tab_profiles, text="Perfis")

        # Tab Cookies
        self.tab_cookies = ttk.Frame(notebook)
        notebook.add(self.tab_cookies, text="Cookies / Gmail")

        self.build_profiles_tab()
        self.build_cookies_tab()

    def build_profiles_tab(self):
        parent = self.tab_profiles

        tk.Label(parent, text="API Token").pack(anchor="w", padx=10, pady=(10,0))
        self.token = tk.Entry(parent, width=65)
        self.token.insert(0, self.cfg.get("token", ""))
        self.token.pack(padx=10, pady=5)

        self.use_gologin = tk.BooleanVar(value=False)
        tk.Checkbutton(parent, text="Usar proxies do GoLogin (em vez da lista)", variable=self.use_gologin).pack(anchor="w", padx=10, pady=5)

        country_frame = tk.Frame(parent)
        country_frame.pack(anchor="w", padx=10)
        tk.Label(country_frame, text="País:").pack(side="left")
        self.country = ttk.Combobox(country_frame, width=20, state="readonly")
        self.country["values"] = [f"{code.upper()} - {name}" for code, name in COUNTRIES]
        self.country.current(0)
        self.country.pack(side="left", padx=5)

        tk.Label(parent, text="Proxies custom (um por linha)").pack(anchor="w", padx=10, pady=(10,0))
        self.proxies = scrolledtext.ScrolledText(parent, height=8)
        self.proxies.insert("1.0", load_proxies())
        self.proxies.pack(padx=10, pady=5, fill="both", expand=True)

        frame = tk.Frame(parent)
        frame.pack(pady=10)
        tk.Label(frame, text="Quantidade:").grid(row=0, column=0, padx=5)
        self.qty = tk.Entry(frame, width=8)
        self.qty.insert(0, "5")
        self.qty.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Prefixo:").grid(row=0, column=2, padx=5)
        self.prefix = tk.Entry(frame, width=10)
        self.prefix.insert(0, "P")
        self.prefix.grid(row=0, column=3, padx=5)

        tk.Button(parent, text="Salvar Proxies", command=self.save).pack(pady=5)
        tk.Button(parent, text="Criar Perfis", command=self.create, bg="#238636", fg="white").pack(pady=5)

        self.status = tk.Label(parent, text="")
        self.status.pack(pady=5)

    def build_cookies_tab(self):
        parent = self.tab_cookies

        tk.Label(parent, text="Nome / Email do Gmail:").pack(anchor="w", padx=10, pady=(10,0))
        self.cookie_name = tk.Entry(parent, width=50)
        self.cookie_name.pack(padx=10, pady=5)

        tk.Label(parent, text="Cole o JSON dos cookies aqui:").pack(anchor="w", padx=10)
        self.cookie_json = scrolledtext.ScrolledText(parent, height=12)
        self.cookie_json.pack(padx=10, pady=5, fill="both", expand=True)

        btn_frame = tk.Frame(parent)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Salvar Cookie", command=self.save_cookie).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Excluir Selecionado", command=self.delete_cookie).pack(side="left", padx=5)

        tk.Label(parent, text="Contas salvas:").pack(anchor="w", padx=10, pady=(10,0))
        self.cookie_list = tk.Listbox(parent, height=8)
        self.cookie_list.pack(padx=10, pady=5, fill="x")
        self.refresh_cookie_list()

        create_frame = tk.Frame(parent)
        create_frame.pack(pady=10)
        tk.Button(create_frame, text="Criar Perfil com este Cookie", command=self.create_from_cookie, bg="#238636", fg="white").pack()

        self.cookie_status = tk.Label(parent, text="")
        self.cookie_status.pack(pady=5)

    def refresh_cookie_list(self):
        self.cookie_list.delete(0, tk.END)
        for name in sorted(self.cookies_data.keys()):
            self.cookie_list.insert(tk.END, name)

    def save(self):
        save_proxies(self.proxies.get("1.0", "end"))
        self.cfg["token"] = self.token.get().strip()
        save_config(self.cfg)
        self.status.config(text="Salvo.")

    def save_cookie(self):
        name = self.cookie_name.get().strip()
        raw = self.cookie_json.get("1.0", "end").strip()
        if not name or not raw:
            messagebox.showerror("Erro", "Nome e cookies obrigatórios")
            return
        try:
            cookies = json.loads(raw)
            if not isinstance(cookies, list):
                raise ValueError("Deve ser uma lista")
            self.cookies_data[name] = cookies
            save_cookies(self.cookies_data)
            self.refresh_cookie_list()
            self.cookie_status.config(text=f"Salvo: {name}")
            self.cookie_name.delete(0, tk.END)
            self.cookie_json.delete("1.0", tk.END)
        except Exception as e:
            messagebox.showerror("Erro", f"JSON inválido: {e}")

    def delete_cookie(self):
        sel = self.cookie_list.curselection()
        if not sel:
            return
        name = self.cookie_list.get(sel[0])
        if messagebox.askyesno("Excluir", f"Excluir {name}?"):
            self.cookies_data.pop(name, None)
            save_cookies(self.cookies_data)
            self.refresh_cookie_list()

    def create_from_cookie(self):
        sel = self.cookie_list.curselection()
        if not sel:
            messagebox.showerror("Erro", "Selecione uma conta")
            return
        name = self.cookie_list.get(sel[0])
        cookies = self.cookies_data.get(name, [])

        token = self.token.get().strip()
        if not token:
            messagebox.showerror("Erro", "Token vazio (aba Perfis)")
            return

        use_gl = self.use_gologin.get()
        country_code = self.country.get().split(" - ")[0].lower()

        lines = [l.strip() for l in self.proxies.get("1.0", "end").splitlines() if l.strip()]
        if not use_gl and not lines:
            messagebox.showerror("Erro", "Nenhum proxy na lista")
            return

        self.cookie_status.config(text="Criando...")
        self.root.update()

        ok, profile_id = create_profile(token, name)
        if not ok:
            self.cookie_status.config(text=f"FAIL criar: {profile_id[:50]}")
            return

        if use_gl:
            pok, pmsg = set_gologin_proxy(token, profile_id, country_code)
        else:
            proxy_line = lines[0]
            proxy = parse_proxy(proxy_line)
            if not proxy:
                self.cookie_status.config(text="Proxy inválido")
                return
            pok, pmsg = set_custom_proxy(token, profile_id, proxy)

        cok, cmsg = set_cookies(token, profile_id, cookies)

        if pok and cok:
            self.cookie_status.config(text=f"OK: {name} criado com proxy + cookies. Dê F5 no GoLogin.")
            messagebox.showinfo("Pronto", f"Perfil '{name}' criado.")
        else:
            self.cookie_status.config(text=f"Criado mas falhou proxy/cookies: {pmsg} / {cmsg}")

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
