import json
import requests
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, simpledialog

CONFIG_FILE = "config.json"
PROXIES_FILE = "proxies.txt"
COOKIES_FILE = "cookies.json"

SITE_URL = "https://tempmailsuko.shop"
SYNC_KEY = "suko-gl-sync-2026"

BG = "#0a0a0f"
FG = "#f0f0f5"
MUTED = "#9ca3af"
ACCENT = "#a855f7"
ACCENT_HOVER = "#9333ea"
CARD = "#15151f"
INPUT = "#1e1e2a"
BORDER = "#2a2a3a"

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

def try_parse_cookies(raw):
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    s = str(raw).strip()
    if not s:
        return []
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return parsed
    except:
        pass
    start = s.find("[")
    end = s.rfind("]")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(s[start:end+1])
            if isinstance(parsed, list):
                return parsed
        except:
            pass
    return []

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
        root.geometry("660x840")
        root.configure(bg=BG)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=CARD, foreground=MUTED, padding=[14, 7], font=("Segoe UI", 9))
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

        self.cfg = load_config()
        self.cookies_data = load_cookies()
        self.site_accounts = {}

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_profiles = ttk.Frame(notebook, style="TFrame")
        notebook.add(self.tab_profiles, text="Perfis")

        self.tab_cookies = ttk.Frame(notebook, style="TFrame")
        notebook.add(self.tab_cookies, text="Cookies / Gmail")

        self.tab_site = ttk.Frame(notebook, style="TFrame")
        notebook.add(self.tab_site, text="Site / Import")

        self.build_profiles_tab()
        self.build_cookies_tab()
        self.build_site_tab()

    def build_profiles_tab(self):
        parent = self.tab_profiles

        tk.Label(parent, text="API Token", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(12,2))
        self.token = tk.Entry(parent, width=72, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 9))
        self.token.insert(0, self.cfg.get("token", ""))
        self.token.pack(padx=12, pady=(0,8))

        self.use_gologin = tk.BooleanVar(value=False)
        tk.Checkbutton(parent, text="Usar proxies do GoLogin", variable=self.use_gologin,
                       bg=BG, fg=FG, selectcolor=INPUT, activebackground=BG, activeforeground=FG,
                       font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=4)

        country_frame = tk.Frame(parent, bg=BG)
        country_frame.pack(anchor="w", padx=12, pady=4)
        tk.Label(country_frame, text="País:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
        self.country = ttk.Combobox(country_frame, width=22, state="readonly")
        self.country["values"] = [f"{code.upper()} - {name}" for code, name in COUNTRIES]
        self.country.current(0)
        self.country.pack(side="left", padx=6)

        tk.Label(parent, text="Proxies custom (um por linha)", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(8,2))
        self.proxies = scrolledtext.ScrolledText(parent, height=9, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 9))
        self.proxies.insert("1.0", load_proxies())
        self.proxies.pack(padx=12, pady=(0,8), fill="both", expand=True)

        frame = tk.Frame(parent, bg=BG)
        frame.pack(pady=8)
        tk.Label(frame, text="Quantidade:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).grid(row=0, column=0, padx=6)
        self.qty = tk.Entry(frame, width=8, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Segoe UI", 10), justify="center")
        self.qty.insert(0, "5")
        self.qty.grid(row=0, column=1, padx=6)

        tk.Label(frame, text="Prefixo:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).grid(row=0, column=2, padx=6)
        self.prefix = tk.Entry(frame, width=10, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Segoe UI", 10))
        self.prefix.insert(0, "P")
        self.prefix.grid(row=0, column=3, padx=6)

        tk.Button(parent, text="Salvar Proxies", command=self.save, bg=CARD, fg=FG, relief="flat",
                  activebackground=BORDER, font=("Segoe UI", 9), padx=12, pady=6).pack(pady=4)
        tk.Button(parent, text="Criar Perfis", command=self.create, bg=ACCENT, fg="white", relief="flat",
                  activebackground=ACCENT_HOVER, font=("Segoe UI", 9, "bold"), padx=16, pady=7).pack(pady=4)

        self.status = tk.Label(parent, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.status.pack(pady=6)

    def build_cookies_tab(self):
        parent = self.tab_cookies

        tk.Label(parent, text="Nome / Email do Gmail:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(12,2))
        self.cookie_name = tk.Entry(parent, width=52, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Segoe UI", 10))
        self.cookie_name.pack(padx=12, pady=(0,8))

        tk.Label(parent, text="Cole o JSON dos cookies aqui:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12)
        self.cookie_json = scrolledtext.ScrolledText(parent, height=13, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 9))
        self.cookie_json.pack(padx=12, pady=5, fill="both", expand=True)

        btn_frame = tk.Frame(parent, bg=BG)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="Salvar Cookie", command=self.save_cookie, bg=CARD, fg=FG, relief="flat", font=("Segoe UI", 9), padx=10, pady=5).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Excluir Selecionado", command=self.delete_cookie, bg=CARD, fg=FG, relief="flat", font=("Segoe UI", 9), padx=10, pady=5).pack(side="left", padx=4)

        tk.Label(parent, text="Contas salvas:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(8,2))
        self.cookie_list = tk.Listbox(parent, height=8, bg=INPUT, fg=FG, selectbackground=ACCENT, relief="flat", font=("Segoe UI", 9), activestyle="none", selectmode="extended")
        self.cookie_list.pack(padx=12, pady=5, fill="x")
        self.refresh_cookie_list()

        create_frame = tk.Frame(parent, bg=BG)
        create_frame.pack(pady=8)
        tk.Button(create_frame, text="Criar Perfil com este Cookie", command=self.create_from_cookie, bg=ACCENT, fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=14, pady=6).pack()

        self.cookie_status = tk.Label(parent, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.cookie_status.pack(pady=6)

    def build_site_tab(self):
        parent = self.tab_site

        top_btns = tk.Frame(parent, bg=BG)
        top_btns.pack(pady=8)
        tk.Button(top_btns, text="Buscar do Site", command=self.fetch_from_site, bg=ACCENT, fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=14, pady=6).pack(side="left", padx=4)
        tk.Button(top_btns, text="Importar Texto Colado", command=self.import_pasted, bg=CARD, fg=FG, relief="flat", font=("Segoe UI", 9), padx=14, pady=6).pack(side="left", padx=4)

        tk.Label(parent, text="Cole o export do HTML aqui (=== email | senha === + JSON)", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(6,2))
        self.paste_area = scrolledtext.ScrolledText(parent, height=9, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 8))
        self.paste_area.pack(padx=12, pady=(0,6), fill="x")

        tk.Label(parent, text="Contas (local + site) — Ctrl+clique pra selecionar vários", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12)
        self.site_list = tk.Listbox(parent, height=13, bg=INPUT, fg=FG, selectbackground=ACCENT, relief="flat", font=("Segoe UI", 9), activestyle="none", selectmode="extended")
        self.site_list.pack(padx=12, pady=5, fill="both", expand=True)

        btn_row = tk.Frame(parent, bg=BG)
        btn_row.pack(pady=6)
        tk.Button(btn_row, text="Criar Perfis Selecionados", command=self.create_from_site, bg=ACCENT, fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=12, pady=6).pack(side="left", padx=4)
        tk.Button(btn_row, text="Enviar Local pro Site", command=self.push_to_site, bg=CARD, fg=FG, relief="flat", font=("Segoe UI", 9), padx=12, pady=6).pack(side="left", padx=4)

        self.site_status = tk.Label(parent, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.site_status.pack(pady=4)

    def refresh_cookie_list(self):
        self.cookie_list.delete(0, tk.END)
        for name in sorted(self.cookies_data.keys()):
            self.cookie_list.insert(tk.END, name)

    def refresh_site_list(self):
        self.site_list.delete(0, tk.END)
        all_emails = set(self.cookies_data.keys()) | set(self.site_accounts.keys())
        for email in sorted(all_emails):
            src = []
            if email in self.cookies_data:
                src.append("local")
            if email in self.site_accounts:
                src.append("site")
            self.site_list.insert(tk.END, f"{email}  ({', '.join(src)})")

    def save(self):
        save_proxies(self.proxies.get("1.0", "end"))
        self.cfg["token"] = self.token.get().strip()
        save_config(self.cfg)
        self.status.config(text="Salvo.")

    def import_pasted(self):
        raw = self.paste_area.get("1.0", "end").strip()
        if not raw:
            messagebox.showerror("Erro", "Cole o texto primeiro")
            return
        blocks = [b.strip() for b in raw.split("===") if b.strip()]
        added = 0
        with_cookies = 0
        for block in blocks:
            lines = block.splitlines()
            header = lines[0].replace("===", "").strip()
            if "@" not in header:
                continue
            if "|" in header:
                parts = [p.strip() for p in header.split("|")]
                email = parts[0].lower()
                password = parts[1] if len(parts) > 1 else ""
            else:
                email = header.lower()
                password = ""
            cookies = try_parse_cookies(block)
            self.cookies_data[email] = cookies
            self.site_accounts[email] = {"pass": password, "cookies": json.dumps(cookies) if cookies else ""}
            added += 1
            if cookies:
                with_cookies += 1
        save_cookies(self.cookies_data)
        self.refresh_cookie_list()
        self.refresh_site_list()
        self.paste_area.delete("1.0", "end")
        self.site_status.config(text=f"Importados {added}, {with_cookies} com cookies")

    def fetch_from_site(self):
        self.site_status.config(text="Buscando...")
        self.root.update()
        try:
            r = requests.get(f"{SITE_URL}/api/gologin-sync?key={SYNC_KEY}", timeout=15)
            if r.ok:
                data = r.json()
                self.site_accounts.clear()
                loaded = 0
                for item in data.get("items", []):
                    email = item.get("email", "")
                    if not email:
                        continue
                    raw_cookies = item.get("cookies", "")
                    self.site_accounts[email] = {
                        "pass": item.get("pass", ""),
                        "cookies": raw_cookies
                    }
                    parsed = try_parse_cookies(raw_cookies)
                    if parsed:
                        self.cookies_data[email] = parsed
                        loaded += 1
                save_cookies(self.cookies_data)
                self.refresh_cookie_list()
                self.refresh_site_list()
                self.site_status.config(text=f"{len(data.get('items',[]))} do site, {loaded} com cookies")
            else:
                self.site_status.config(text=f"Erro {r.status_code}")
        except Exception as e:
            self.site_status.config(text=f"Falha: {str(e)[:60]}")

    def push_to_site(self):
        sel = self.site_list.curselection()
        if not sel:
            messagebox.showerror("Erro", "Selecione uma conta na lista")
            return
        line = self.site_list.get(sel[0])
        email = line.split()[0]
        cookies = self.cookies_data.get(email, [])

        self.site_status.config(text="Enviando...")
        self.root.update()
        try:
            payload = {
                "email": email,
                "pass": self.site_accounts.get(email, {}).get("pass", ""),
                "cookies": json.dumps(cookies) if isinstance(cookies, list) else str(cookies)
            }
            r = requests.post(f"{SITE_URL}/api/gologin-sync?key={SYNC_KEY}", json=payload, timeout=15)
            if r.ok:
                self.site_status.config(text=f"Enviado: {email}")
                self.fetch_from_site()
            else:
                self.site_status.config(text=f"Erro {r.status_code} ao enviar")
        except Exception as e:
            self.site_status.config(text=f"Falha: {str(e)[:60]}")

    def create_from_site(self):
        sels = self.site_list.curselection()
        if not sels:
            messagebox.showerror("Erro", "Selecione um ou mais itens (Ctrl+clique)")
            return

        token = self.token.get().strip()
        if not token:
            messagebox.showerror("Erro", "Token GoLogin vazio (aba Perfis)")
            return

        use_gl = self.use_gologin.get()
        country_code = self.country.get().split(" - ")[0].lower()

        proxy_lines = [l.strip() for l in self.proxies.get("1.0", "end").splitlines() if l.strip()]
        if not use_gl and not proxy_lines:
            messagebox.showerror("Erro", "Nenhum proxy na lista")
            return

        created = 0
        total = len(sels)
        errors = []
        for idx, sel in enumerate(sels):
            line = self.site_list.get(sel)
            email = line.split()[0]
            cookies = self.cookies_data.get(email, [])
            if not cookies:
                raw = self.site_accounts.get(email, {}).get("cookies", "")
                cookies = try_parse_cookies(raw)
                if cookies:
                    self.cookies_data[email] = cookies
            if not cookies:
                errors.append(f"{email}: sem cookies")
                self.site_status.config(text=f"{email}: sem cookies, pulando")
                self.root.update()
                continue

            self.site_status.config(text=f"Criando {idx+1}/{total}: {email}")
            self.root.update()

            ok, result = create_profile(token, email)
            if not ok:
                errors.append(f"{email}: {result}")
                self.site_status.config(text=f"Erro criar: {result[:80]}")
                self.root.update()
                continue

            profile_id = result
            if use_gl:
                set_gologin_proxy(token, profile_id, country_code)
            else:
                proxy = parse_proxy(proxy_lines[idx % len(proxy_lines)])
                if proxy:
                    set_custom_proxy(token, profile_id, proxy)

            ok_c, msg_c = set_cookies(token, profile_id, cookies)
            if not ok_c:
                errors.append(f"{email}: cookies {msg_c}")

            created += 1
            time.sleep(0.3)

        msg = f"Concluído. {created}/{total} perfis criados."
        if errors:
            msg += " Erros: " + " | ".join(errors[:3])
        self.site_status.config(text=msg)

    def save_cookie(self):
        name = self.cookie_name.get().strip().lower()
        raw = self.cookie_json.get("1.0", "end").strip()
        if not name or not raw:
            messagebox.showerror("Erro", "Preencha nome e JSON")
            return
        cookies = try_parse_cookies(raw)
        if not cookies:
            messagebox.showerror("Erro", "JSON invalido ou vazio")
            return
        self.cookies_data[name] = cookies
        save_cookies(self.cookies_data)
        self.refresh_cookie_list()
        self.refresh_site_list()
        self.cookie_status.config(text=f"Salvo: {name}")

    def delete_cookie(self):
        sel = self.cookie_list.curselection()
        if not sel:
            return
        name = self.cookie_list.get(sel[0])
        if name in self.cookies_data:
            del self.cookies_data[name]
            save_cookies(self.cookies_data)
            self.refresh_cookie_list()
            self.refresh_site_list()
            self.cookie_status.config(text=f"Excluido: {name}")

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
        self.cookie_status.config(text="Criando...")
        self.root.update()
        ok, result = create_profile(token, name)
        if not ok:
            self.cookie_status.config(text=f"Erro: {result[:100]}")
            return
        set_cookies(token, result, cookies)
        self.cookie_status.config(text=f"Criado: {name}")

    def create(self):
        token = self.token.get().strip()
        if not token:
            messagebox.showerror("Erro", "Token vazio")
            return
        qty = int(self.qty.get() or 1)
        prefix = self.prefix.get().strip() or "P"
        use_gl = self.use_gologin.get()
        country_code = self.country.get().split(" - ")[0].lower()
        proxy_lines = [l.strip() for l in self.proxies.get("1.0", "end").splitlines() if l.strip()]
        if not use_gl and not proxy_lines:
            messagebox.showerror("Erro", "Nenhum proxy")
            return
        created = 0
        for i in range(1, qty + 1):
            name = f"{prefix}{i}"
            self.status.config(text=f"Criando {i}/{qty}...")
            self.root.update()
            ok, result = create_profile(token, name)
            if not ok:
                self.status.config(text=f"Erro: {result[:80]}")
                break
            if use_gl:
                set_gologin_proxy(token, result, country_code)
            else:
                proxy = parse_proxy(proxy_lines[(i-1) % len(proxy_lines)])
                if proxy:
                    set_custom_proxy(token, result, proxy)
            created += 1
            time.sleep(0.3)
        self.status.config(text=f"{created}/{qty} criados")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
