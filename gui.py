import json
import requests
import time
import threading
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
        return {"profile_token": "", "proxy_token": "", "use_gologin": False, "country": "br"}
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
        return r.ok, r.text[:300] if not r.ok else "ok"
    except Exception as e:
        return False, str(e)

def create_proxy_only(token, country, custom_name):
    url = "https://api.gologin.com/users-proxies/mobile-proxy"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "countryCode": country.lower(),
        "city": "",
        "browserId": "",
        "isMobile": False,
        "isDC": False,
        "customName": custom_name
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=30)
        if r.ok:
            data = r.json()
            proxy_obj = {
                "mode": data.get("mode", "http"),
                "host": data.get("host"),
                "port": int(data.get("port", 10080)),
                "username": data.get("username", ""),
                "password": data.get("password", "")
            }
            return True, proxy_obj, r.text[:180]
        return False, None, f"STATUS {r.status_code}\n{r.text[:280]}"
    except Exception as e:
        return False, None, str(e)

def list_profiles(token):
    url = "https://api.gologin.com/browser/v2"
    headers = {"Authorization": f"Bearer {token}"}
    all_profiles = []
    page = 1
    try:
        while True:
            r = requests.get(url, headers=headers, params={"page": page}, timeout=30)
            if not r.ok:
                return False, r.text[:200]
            data = r.json()
            profiles = data.get("profiles", [])
            all_profiles.extend(profiles)
            if not profiles or len(profiles) < 30:
                break
            page += 1
            if page > 20:
                break
        return True, all_profiles
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
        root.geometry("660x980")
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
        self.selected_emails = set()
        self.profiles_data = []
        self.use_gologin = tk.BooleanVar(value=self.cfg.get("use_gologin", False))
        self.use_gologin.trace_add("write", lambda *a: self.save_gologin_state())

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

        self.root.after(500, self.fetch_from_site)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        try:
            self.cfg["profile_token"] = self.profile_token.get().strip()
            self.cfg["proxy_token"] = self.proxy_token.get().strip()
            self.cfg["use_gologin"] = self.use_gologin.get()
            if hasattr(self, "country"):
                self.cfg["country"] = self.country.get().split(" - ")[0].lower()
            save_config(self.cfg)
            if hasattr(self, "proxies"):
                save_proxies(self.proxies.get("1.0", "end"))
            save_cookies(self.cookies_data)
        except:
            pass
        self.root.destroy()

    def log(self, msg):
        if hasattr(self, "logbox"):
            self.logbox.insert(tk.END, msg + "\n")
            self.logbox.see(tk.END)

    def save_gologin_state(self):
        self.cfg["use_gologin"] = self.use_gologin.get()
        if hasattr(self, "country"):
            self.cfg["country"] = self.country.get().split(" - ")[0].lower()
        save_config(self.cfg)

    def get_profile_token(self):
        return self.profile_token.get().strip()

    def get_proxy_token(self):
        return self.proxy_token.get().strip() or self.get_profile_token()

    def build_profiles_tab(self):
        parent = self.tab_profiles

        tk.Label(parent, text="Token Perfil (cria perfil)", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(12,2))
        self.profile_token = tk.Entry(parent, width=72, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 9))
        self.profile_token.insert(0, self.cfg.get("profile_token", self.cfg.get("token", "")))
        self.profile_token.pack(padx=12, pady=(0,4))

        tk.Label(parent, text="Token Proxy (gera/atribui proxy)", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(4,2))
        self.proxy_token = tk.Entry(parent, width=72, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 9))
        self.proxy_token.insert(0, self.cfg.get("proxy_token", ""))
        self.proxy_token.pack(padx=12, pady=(0,8))

        tk.Checkbutton(parent, text="Usar proxies do GoLogin", variable=self.use_gologin,
                       bg=BG, fg=FG, selectcolor=INPUT, activebackground=BG, activeforeground=FG,
                       font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=4)

        country_frame = tk.Frame(parent, bg=BG)
        country_frame.pack(anchor="w", padx=12, pady=4)
        tk.Label(country_frame, text="País:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
        self.country = ttk.Combobox(country_frame, width=22, state="readonly")
        self.country["values"] = [f"{code.upper()} - {name}" for code, name in COUNTRIES]
        saved_country = self.cfg.get("country", "br")
        for i, (code, name) in enumerate(COUNTRIES):
            if code == saved_country:
                self.country.current(i)
                break
        else:
            self.country.current(0)
        self.country.bind("<<ComboboxSelected>>", lambda e: self.save_gologin_state())
        self.country.pack(side="left", padx=6)

        tk.Label(parent, text="Proxies custom (um por linha)", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(8,2))
        self.proxies = scrolledtext.ScrolledText(parent, height=5, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 9))
        self.proxies.insert("1.0", load_proxies())
        self.proxies.pack(padx=12, pady=(0,6), fill="x")

        frame = tk.Frame(parent, bg=BG)
        frame.pack(pady=6)
        tk.Label(frame, text="Quantidade:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).grid(row=0, column=0, padx=6)
        self.qty = tk.Entry(frame, width=8, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Segoe UI", 10), justify="center")
        self.qty.insert(0, "5")
        self.qty.grid(row=0, column=1, padx=6)

        tk.Label(frame, text="Prefixo:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).grid(row=0, column=2, padx=6)
        self.prefix = tk.Entry(frame, width=10, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Segoe UI", 10))
        self.prefix.insert(0, "P")
        self.prefix.grid(row=0, column=3, padx=6)

        tk.Button(parent, text="Salvar", command=self.save, bg=CARD, fg=FG, relief="flat",
                  activebackground=BORDER, font=("Segoe UI", 9), padx=12, pady=6).pack(pady=3)
        tk.Button(parent, text="Criar Perfis", command=self.create, bg=ACCENT, fg="white", relief="flat",
                  activebackground=ACCENT_HOVER, font=("Segoe UI", 9, "bold"), padx=16, pady=7).pack(pady=3)

        tk.Label(parent, text="Criar Proxy Novo e Aplicar nos Perfis", bg=BG, fg=ACCENT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(12,4))

        apply_frame = tk.Frame(parent, bg=BG)
        apply_frame.pack(anchor="w", padx=12, pady=2)
        tk.Label(apply_frame, text="País:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
        self.apply_country = ttk.Combobox(apply_frame, width=18, state="readonly")
        self.apply_country["values"] = [f"{code.upper()} - {name}" for code, name in COUNTRIES]
        self.apply_country.current(0)
        self.apply_country.pack(side="left", padx=6)

        btn_apply_frame = tk.Frame(parent, bg=BG)
        btn_apply_frame.pack(pady=4)
        tk.Button(btn_apply_frame, text="Carregar Perfis", command=self.load_profiles, bg=CARD, fg=FG, relief="flat", font=("Segoe UI", 9), padx=10, pady=5).pack(side="left", padx=3)
        tk.Button(btn_apply_frame, text="Criar Proxy Novo nos Marcados", command=self.create_fresh_proxy_on_selected, bg=ACCENT, fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=10, pady=5).pack(side="left", padx=3)

        self.profile_listbox = tk.Listbox(parent, height=6, bg=INPUT, fg=FG, selectbackground=ACCENT, relief="flat", font=("Segoe UI", 9), selectmode="extended")
        self.profile_listbox.pack(padx=12, pady=4, fill="x")

        tk.Label(parent, text="Log da API:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(6,2))
        self.logbox = scrolledtext.ScrolledText(parent, height=7, bg=INPUT, fg="#00ffaa", insertbackground=FG, relief="flat", font=("Consolas", 8))
        self.logbox.pack(padx=12, pady=(0,6), fill="x")

        self.status = tk.Label(parent, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.status.pack(pady=4)

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

        proxy_frame = tk.Frame(parent, bg=BG)
        proxy_frame.pack(anchor="w", padx=12, pady=4)
        tk.Checkbutton(proxy_frame, text="Usar proxies do GoLogin", variable=self.use_gologin,
                       bg=BG, fg=FG, selectcolor=INPUT, activebackground=BG, activeforeground=FG,
                       font=("Segoe UI", 9)).pack(side="left")

        tk.Label(parent, text="Cole o export do HTML aqui (=== email | senha === + JSON)", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(6,2))
        self.paste_area = scrolledtext.ScrolledText(parent, height=7, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 8))
        self.paste_area.pack(padx=12, pady=(0,6), fill="x")

        search_frame = tk.Frame(parent, bg=BG)
        search_frame.pack(anchor="w", padx=12, pady=(4,2), fill="x")
        tk.Label(search_frame, text="Buscar:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh_site_list())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=40, bg=INPUT, fg=FG, insertbackground=FG, relief="flat", font=("Segoe UI", 9))
        search_entry.pack(side="left", padx=6, fill="x", expand=True)

        select_btns = tk.Frame(parent, bg=BG)
        select_btns.pack(anchor="w", padx=12, pady=2)
        tk.Button(select_btns, text="Marcar todos visíveis", command=self.select_all_visible, bg=CARD, fg=FG, relief="flat", font=("Segoe UI", 8), padx=8, pady=3).pack(side="left", padx=2)
        tk.Button(select_btns, text="Desmarcar todos", command=self.deselect_all, bg=CARD, fg=FG, relief="flat", font=("Segoe UI", 8), padx=8, pady=3).pack(side="left", padx=2)

        tk.Label(parent, text="Contas (marque as caixinhas) — seleção fica salva na busca", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12)

        list_container = tk.Frame(parent, bg=BG)
        list_container.pack(padx=12, pady=5, fill="both", expand=True)

        self.site_canvas = tk.Canvas(list_container, bg=INPUT, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.site_canvas.yview)
        self.site_inner = tk.Frame(self.site_canvas, bg=INPUT)

        self.site_inner.bind("<Configure>", lambda e: self.site_canvas.configure(scrollregion=self.site_canvas.bbox("all")))
        self.site_canvas.create_window((0, 0), window=self.site_inner, anchor="nw")
        self.site_canvas.configure(yscrollcommand=scrollbar.set)

        self.site_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.site_canvas.bind_all("<MouseWheel>", lambda e: self.site_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        btn_row = tk.Frame(parent, bg=BG)
        btn_row.pack(pady=6)
        tk.Button(btn_row, text="Criar Perfis Marcados", command=self.create_from_site, bg=ACCENT, fg="white", relief="flat", font=("Segoe UI", 9, "bold"), padx=12, pady=6).pack(side="left", padx=4)
        tk.Button(btn_row, text="Enviar Todas pro Site", command=self.push_all_to_site, bg=CARD, fg=FG, relief="flat", font=("Segoe UI", 9), padx=12, pady=6).pack(side="left", padx=4)
        tk.Button(btn_row, text="Apagar Marcados do Local", command=self.delete_local, bg=CARD, fg="#ff6666", relief="flat", font=("Segoe UI", 9), padx=12, pady=6).pack(side="left", padx=4)

        self.site_status = tk.Label(parent, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.site_status.pack(pady=4)

    def refresh_cookie_list(self):
        self.cookie_list.delete(0, tk.END)
        for name in sorted(self.cookies_data.keys()):
            self.cookie_list.insert(tk.END, name)

    def refresh_site_list(self):
        for widget in self.site_inner.winfo_children():
            widget.destroy()

        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        all_emails = sorted(set(self.cookies_data.keys()) | set(self.site_accounts.keys()))

        self.check_vars = {}
        for email in all_emails:
            if query and query not in email.lower():
                continue
            src = []
            if email in self.cookies_data:
                src.append("local")
            if email in self.site_accounts:
                src.append("site")
            label = f"{email}  ({', '.join(src)})"

            var = tk.BooleanVar(value=email in self.selected_emails)
            self.check_vars[email] = var

            def make_cmd(em, v):
                def cmd():
                    if v.get():
                        self.selected_emails.add(em)
                    else:
                        self.selected_emails.discard(em)
                return cmd

            cb = tk.Checkbutton(
                self.site_inner,
                text=label,
                variable=var,
                command=make_cmd(email, var),
                bg=INPUT, fg=FG, selectcolor=CARD,
                activebackground=INPUT, activeforeground=FG,
                font=("Segoe UI", 9), anchor="w"
            )
            cb.pack(fill="x", padx=4, pady=1)

        self.site_canvas.update_idletasks()
        self.site_canvas.configure(scrollregion=self.site_canvas.bbox("all"))

    def select_all_visible(self):
        query = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        all_emails = set(self.cookies_data.keys()) | set(self.site_accounts.keys())
        for email in all_emails:
            if not query or query in email.lower():
                self.selected_emails.add(email)
        self.refresh_site_list()

    def deselect_all(self):
        self.selected_emails.clear()
        self.refresh_site_list()

    def save(self):
        save_proxies(self.proxies.get("1.0", "end"))
        self.cfg["profile_token"] = self.profile_token.get().strip()
        self.cfg["proxy_token"] = self.proxy_token.get().strip()
        self.cfg["use_gologin"] = self.use_gologin.get()
        self.cfg["country"] = self.country.get().split(" - ")[0].lower()
        save_config(self.cfg)
        self.status.config(text="Salvo.")

    def load_profiles(self):
        token = self.get_profile_token()
        if not token:
            messagebox.showerror("Erro", "Token Perfil vazio")
            return

        def work():
            ok, data = list_profiles(token)
            if ok:
                self.profiles_data = data
                self.root.after(0, self._refresh_profile_list)
                self.root.after(0, lambda: self.status.config(text=f"{len(data)} perfis carregados"))
                self.root.after(0, lambda: self.log(f"Carregados {len(data)} perfis"))
            else:
                self.root.after(0, lambda: self.log(f"Erro lista: {data}"))

        threading.Thread(target=work, daemon=True).start()

    def _refresh_profile_list(self):
        self.profile_listbox.delete(0, tk.END)
        for p in self.profiles_data:
            name = p.get("name", "sem nome")
            pid = p.get("id", "")[:8]
            self.profile_listbox.insert(tk.END, f"{name}  ({pid})")

    def create_fresh_proxy_on_selected(self):
        sels = self.profile_listbox.curselection()
        if not sels:
            messagebox.showerror("Erro", "Selecione um ou mais perfis")
            return

        proxy_tok = self.get_proxy_token()
        profile_tok = self.get_profile_token()
        if not proxy_tok or not profile_tok:
            messagebox.showerror("Erro", "Tokens vazios")
            return

        country = self.apply_country.get().split(" - ")[0].lower()

        def work():
            success = 0
            total = len(sels)
            self.root.after(0, lambda: self.log(f"--- Criando proxy {country.upper()} e atribuindo em {total} perfis ---"))
            for i, idx in enumerate(sels):
                profile = self.profiles_data[idx]
                pid = profile.get("id")
                name = profile.get("name", "")
                proxy_name = f"auto-{name[:12]}-{int(time.time())}"
                self.root.after(0, lambda n=name, ii=i: self.status.config(text=f"{ii+1}/{total}: {n}"))

                ok, proxy_obj, msg = create_proxy_only(proxy_tok, country, proxy_name)
                self.root.after(0, lambda m=msg, n=name: self.log(f"Criar {n}:\n{m}\n"))
                if not ok or not proxy_obj:
                    continue

                ok2, msg2 = set_custom_proxy(profile_tok, pid, proxy_obj)
                self.root.after(0, lambda m=msg2, n=name: self.log(f"Atribuir {n}:\n{m}\n"))
                if ok2:
                    success += 1
                time.sleep(0.6)
            self.root.after(0, lambda: self.status.config(text=f"Sucesso {success}/{total}"))
            self.root.after(0, lambda: self.log(f"=== Final: {success}/{total} ===\n"))

        self.status.config(text="Processando...")
        threading.Thread(target=work, daemon=True).start()

    def delete_local(self):
        if not self.selected_emails:
            messagebox.showerror("Erro", "Marque uma ou mais contas")
            return
        if not messagebox.askyesno("Confirmar", f"Apagar {len(self.selected_emails)} do local?"):
            return
        for email in list(self.selected_emails):
            self.cookies_data.pop(email, None)
            self.site_accounts.pop(email, None)
        self.selected_emails.clear()
        save_cookies(self.cookies_data)
        self.refresh_cookie_list()
        self.refresh_site_list()
        self.site_status.config(text=f"Apagados do local")

    def import_pasted(self):
        raw = self.paste_area.get("1.0", "end").strip()
        if not raw:
            messagebox.showerror("Erro", "Cole o texto primeiro")
            return
        parts = [p.strip() for p in raw.split("===") if p.strip()]
        added = 0
        with_cookies = 0
        i = 0
        while i < len(parts):
            part = parts[i]
            if "@" in part and "|" in part and "[" not in part:
                header = part.replace("===", "").strip()
                if "|" in header:
                    hp = [x.strip() for x in header.split("|")]
                    email = hp[0].lower()
                    password = hp[1] if len(hp) > 1 else ""
                else:
                    email = header.lower()
                    password = ""
                cookies = []
                if i + 1 < len(parts):
                    cookies = try_parse_cookies(parts[i + 1])
                    if cookies:
                        i += 1
                self.cookies_data[email] = cookies
                self.site_accounts[email] = {"pass": password, "cookies": json.dumps(cookies) if cookies else ""}
                added += 1
                if cookies:
                    with_cookies += 1
            i += 1
        save_cookies(self.cookies_data)
        self.refresh_cookie_list()
        self.refresh_site_list()
        self.paste_area.delete("1.0", "end")
        self.site_status.config(text=f"Importados {added}, {with_cookies} com cookies")

    def fetch_from_site(self):
        def work():
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
                    self.root.after(0, lambda: self._after_fetch(len(data.get("items", [])), loaded))
                else:
                    self.root.after(0, lambda: self.site_status.config(text=f"Erro {r.status_code}"))
            except Exception as e:
                self.root.after(0, lambda: self.site_status.config(text=f"Falha: {str(e)[:60]}"))

        self.site_status.config(text="Buscando...")
        threading.Thread(target=work, daemon=True).start()

    def _after_fetch(self, total, loaded):
        self.refresh_cookie_list()
        self.refresh_site_list()
        self.site_status.config(text=f"{total} do site, {loaded} com cookies")

    def push_all_to_site(self):
        if not self.cookies_data:
            messagebox.showerror("Erro", "Nenhuma conta local")
            return

        def work():
            sent = 0
            failed = 0
            for email, cookies in list(self.cookies_data.items()):
                try:
                    payload = {
                        "email": email,
                        "pass": self.site_accounts.get(email, {}).get("pass", ""),
                        "cookies": json.dumps(cookies) if isinstance(cookies, list) else str(cookies)
                    }
                    r = requests.post(f"{SITE_URL}/api/gologin-sync?key={SYNC_KEY}", json=payload, timeout=15)
                    if r.ok:
                        sent += 1
                    else:
                        failed += 1
                except:
                    failed += 1
            self.root.after(0, lambda: self.site_status.config(text=f"Enviadas {sent}, falharam {failed}"))
            self.root.after(100, self.fetch_from_site)

        self.site_status.config(text="Enviando todas...")
        threading.Thread(target=work, daemon=True).start()

    def create_from_site(self):
        if not self.selected_emails:
            messagebox.showerror("Erro", "Marque um ou mais gmails")
            return

        profile_tok = self.get_profile_token()
        if not profile_tok:
            messagebox.showerror("Erro", "Token Perfil vazio")
            return

        use_gl = self.use_gologin.get()
        country_code = self.country.get().split(" - ")[0].lower()
        proxy_lines = [l.strip() for l in self.proxies.get("1.0", "end").splitlines() if l.strip()]
        if not use_gl and not proxy_lines:
            messagebox.showerror("Erro", "Nenhum proxy na lista")
            return

        emails = list(self.selected_emails)
        proxy_tok = self.get_proxy_token()

        def work():
            created = 0
            total = len(emails)
            errors = []
            for idx, email in enumerate(emails):
                cookies = self.cookies_data.get(email, [])
                if not cookies:
                    raw = self.site_accounts.get(email, {}).get("cookies", "")
                    cookies = try_parse_cookies(raw)
                    if cookies:
                        self.cookies_data[email] = cookies
                if not cookies:
                    errors.append(f"{email}: sem cookies")
                    self.root.after(0, lambda e=email: self.site_status.config(text=f"{e}: sem cookies, pulando"))
                    continue

                self.root.after(0, lambda i=idx, e=email: self.site_status.config(text=f"Criando {i+1}/{total}: {e}"))

                ok, result = create_profile(profile_tok, email)
                if not ok:
                    errors.append(f"{email}: {result}")
                    self.root.after(0, lambda r=result: self.site_status.config(text=f"Erro criar: {r[:80]}"))
                    continue

                profile_id = result
                if use_gl:
                    okp, proxy_obj, msgp = create_proxy_only(proxy_tok, country_code, f"auto-{email[:12]}")
                    if okp and proxy_obj:
                        set_custom_proxy(profile_tok, profile_id, proxy_obj)
                else:
                    proxy = parse_proxy(proxy_lines[idx % len(proxy_lines)])
                    if proxy:
                        set_custom_proxy(profile_tok, profile_id, proxy)

                ok_c, msg_c = set_cookies(profile_tok, profile_id, cookies)
                if not ok_c:
                    errors.append(f"{email}: cookies {msg_c}")

                created += 1
                time.sleep(0.3)

            msg = f"Concluído. {created}/{total} perfis criados."
            if errors:
                msg += " Erros: " + " | ".join(errors[:3])
            self.root.after(0, lambda m=msg: self.site_status.config(text=m))

        self.site_status.config(text="Iniciando...")
        threading.Thread(target=work, daemon=True).start()

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
        token = self.get_profile_token()
        if not token:
            messagebox.showerror("Erro", "Token Perfil vazio")
            return

        def work():
            ok, result = create_profile(token, name)
            if not ok:
                self.root.after(0, lambda: self.cookie_status.config(text=f"Erro: {result[:100]}"))
                return
            set_cookies(token, result, cookies)
            self.root.after(0, lambda: self.cookie_status.config(text=f"Criado: {name}"))

        self.cookie_status.config(text="Criando...")
        threading.Thread(target=work, daemon=True).start()

    def create(self):
        profile_tok = self.get_profile_token()
        if not profile_tok:
            messagebox.showerror("Erro", "Token Perfil vazio")
            return
        qty = int(self.qty.get() or 1)
        prefix = self.prefix.get().strip() or "P"
        use_gl = self.use_gologin.get()
        country_code = self.country.get().split(" - ")[0].lower()
        proxy_lines = [l.strip() for l in self.proxies.get("1.0", "end").splitlines() if l.strip()]
        if not use_gl and not proxy_lines:
            messagebox.showerror("Erro", "Nenhum proxy")
            return

        proxy_tok = self.get_proxy_token()

        def work():
            created = 0
            for i in range(1, qty + 1):
                name = f"{prefix}{i}"
                self.root.after(0, lambda n=i: self.status.config(text=f"Criando {n}/{qty}..."))
                ok, result = create_profile(profile_tok, name)
                if not ok:
                    self.root.after(0, lambda r=result: self.status.config(text=f"Erro: {r[:80]}"))
                    break
                if use_gl:
                    okp, proxy_obj, _ = create_proxy_only(proxy_tok, country_code, f"auto-{name}")
                    if okp and proxy_obj:
                        set_custom_proxy(profile_tok, result, proxy_obj)
                else:
                    proxy = parse_proxy(proxy_lines[(i-1) % len(proxy_lines)])
                    if proxy:
                        set_custom_proxy(profile_tok, result, proxy)
                created += 1
                time.sleep(0.3)
            self.root.after(0, lambda: self.status.config(text=f"{created}/{qty} criados"))

        self.status.config(text="Iniciando...")
        threading.Thread(target=work, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
