import json
import requests
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, simpledialog

CONFIG_FILE = "config.json"
PROXIES_FILE = "proxies.txt"
COOKIES_FILE = "cookies.json"

# Tema preto + roxo
BG = "#0d0d12"
FG = "#e6e6f0"
ACCENT = "#a855f7"
CARD = "#1a1a24"
BORDER = "#2d2d3d"

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
        return {"token": "", "site_url": "https://tempmailsuko.shop", "site_token": ""}
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
        root.geometry("580x740")
        root.configure(bg=BG)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=CARD, foreground=FG, padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "white")])

        self.cfg = load_config()
        self.cookies_data = load_cookies()

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.tab_profiles = ttk.Frame(notebook)
        notebook.add(self.tab_profiles, text="Perfis")

        self.tab_cookies = ttk.Frame(notebook)
        notebook.add(self.tab_cookies, text="Cookies / Gmail")

        self.tab_site = ttk.Frame(notebook)
        notebook.add(self.tab_site, text="Site")

        self.build_profiles_tab()
        self.build_cookies_tab()
        self.build_site_tab()

    def build_profiles_tab(self):
        parent = self.tab_profiles
        parent.configure(style="TFrame")

        tk.Label(parent, text="API Token", bg=BG, fg=FG).pack(anchor="w", padx=10, pady=(10,0))
        self.token = tk.Entry(parent, width=65, bg=CARD, fg=FG, insertbackground=FG, relief="flat")
        self.token.insert(0, self.cfg.get("token", ""))
        self.token.pack(padx=10, pady=5)

        self.use_gologin = tk.BooleanVar(value=False)
        tk.Checkbutton(parent, text="Usar proxies do GoLogin", variable=self.use_gologin, bg=BG, fg=FG, selectcolor=CARD, activebackground=BG, activeforeground=FG).pack(anchor="w", padx=10, pady=5)

        country_frame = tk.Frame(parent, bg=BG)
        country_frame.pack(anchor="w", padx=10)
        tk.Label(country_frame, text="País:", bg=BG, fg=FG).pack(side="left")
        self.country = ttk.Combobox(country_frame, width=20, state="readonly")
        self.country["values"] = [f"{code.upper()} - {name}" for code, name in COUNTRIES]
        self.country.current(0)
        self.country.pack(side="left", padx=5)

        tk.Label(parent, text="Proxies custom (um por linha)", bg=BG, fg=FG).pack(anchor="w", padx=10, pady=(10,0))
        self.proxies = scrolledtext.ScrolledText(parent, height=8, bg=CARD, fg=FG, insertbackground=FG, relief="flat")
        self.proxies.insert("1.0", load_proxies())
        self.proxies.pack(padx=10, pady=5, fill="both", expand=True)

        frame = tk.Frame(parent, bg=BG)
        frame.pack(pady=10)
        tk.Label(frame, text="Quantidade:", bg=BG, fg=FG).grid(row=0, column=0, padx=5)
        self.qty = tk.Entry(frame, width=8, bg=CARD, fg=FG, insertbackground=FG, relief="flat")
        self.qty.insert(0, "5")
        self.qty.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Prefixo:", bg=BG, fg=FG).grid(row=0, column=2, padx=5)
        self.prefix = tk.Entry(frame, width=10, bg=CARD, fg=FG, insertbackground=FG, relief="flat")
        self.prefix.insert(0, "P")
        self.prefix.grid(row=0, column=3, padx=5)

        tk.Button(parent, text="Salvar Proxies", command=self.save, bg=CARD, fg=FG, relief="flat", activebackground=ACCENT).pack(pady=5)
        tk.Button(parent, text="Criar Perfis", command=self.create, bg=ACCENT, fg="white", relief="flat", activebackground="#9333ea").pack(pady=5)

        self.status = tk.Label(parent, text="", bg=BG, fg=FG)
        self.status.pack(pady=5)

    def build_cookies_tab(self):
        parent = self.tab_cookies

        tk.Label(parent, text="Nome / Email do Gmail:", bg=BG, fg=FG).pack(anchor="w", padx=10, pady=(10,0))
        self.cookie_name = tk.Entry(parent, width=50, bg=CARD, fg=FG, insertbackground=FG, relief="flat")
        self.cookie_name.pack(padx=10, pady=5)

        tk.Label(parent, text="Cole o JSON dos cookies aqui:", bg=BG, fg=FG).pack(anchor="w", padx=10)
        self.cookie_json = scrolledtext.ScrolledText(parent, height=12, bg=CARD, fg=FG, insertbackground=FG, relief="flat")
        self.cookie_json.pack(padx=10, pady=5, fill="both", expand=True)

        btn_frame = tk.Frame(parent, bg=BG)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Salvar Cookie", command=self.save_cookie, bg=CARD, fg=FG, relief="flat").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Excluir Selecionado", command=self.delete_cookie, bg=CARD, fg=FG, relief="flat").pack(side="left", padx=5)

        tk.Label(parent, text="Contas salvas:", bg=BG, fg=FG).pack(anchor="w", padx=10, pady=(10,0))
        self.cookie_list = tk.Listbox(parent, height=8, bg=CARD, fg=FG, selectbackground=ACCENT, relief="flat")
        self.cookie_list.pack(padx=10, pady=5, fill="x")
        self.refresh_cookie_list()

        create_frame = tk.Frame(parent, bg=BG)
        create_frame.pack(pady=10)
        tk.Button(create_frame, text="Criar Perfil com este Cookie", command=self.create_from_cookie, bg=ACCENT, fg="white", relief="flat").pack()

        self.cookie_status = tk.Label(parent, text="", bg=BG, fg=FG)
        self.cookie_status.pack(pady=5)

    def build_site_tab(self):
        parent = self.tab_site

        tk.Label(parent, text="URL do site (ex: https://tempmailsuko.shop)", bg=BG, fg=FG).pack(anchor="w", padx=10, pady=(10,0))
        self.site_url = tk.Entry(parent, width=60, bg=CARD, fg=FG, insertbackground=FG, relief="flat")
        self.site_url.insert(0, self.cfg.get("site_url", "https://tempmailsuko.shop"))
        self.site_url.pack(padx=10, pady=5)

        tk.Label(parent, text="Token / chave admin (se tiver)", bg=BG, fg=FG).pack(anchor="w", padx=10)
        self.site_token = tk.Entry(parent, width=60, bg=CARD, fg=FG, insertbackground=FG, relief="flat", show="*")
        self.site_token.insert(0, self.cfg.get("site_token", ""))
        self.site_token.pack(padx=10, pady=5)

        tk.Button(parent, text="Buscar Gmails do Site", command=self.fetch_from_site, bg=ACCENT, fg="white", relief="flat").pack(pady=10)

        self.site_list = tk.Listbox(parent, height=15, bg=CARD, fg=FG, selectbackground=ACCENT, relief="flat")
        self.site_list.pack(padx=10, pady=5, fill="both", expand=True)

        tk.Button(parent, text="Criar Perfil do Selecionado", command=self.create_from_site, bg=CARD, fg=FG, relief="flat").pack(pady=5)

        self.site_status = tk.Label(parent, text="", bg=BG, fg=FG)
        self.site_status.pack(pady=5)

    def refresh_cookie_list(self):
        self.cookie_list.delete(0, tk.END)
        for name in sorted(self.cookies_data.keys()):
            self.cookie_list.insert(tk.END, name)

    def save(self):
        save_proxies(self.proxies.get("1.0", "end"))
        self.cfg["token"] = self.token.get().strip()
        self.cfg["site_url"] = self.site_url.get().strip()
        self.cfg["site_token"] = self.site_token.get().strip()
        save_config(self.cfg)
        self.status.config(text="Salvo.")

    def fetch_from_site(self):
        self.save()
        url = self.site_url.get().strip().rstrip("/")
        token = self.site_token.get().strip()
        if not url:
            messagebox.showerror("Erro", "URL do site vazia")
            return
        # Placeholder - precisa de endpoint no site
        self.site_status.config(text="Buscando...")
        self.root.update()
        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            r = requests.get(f"{url}/api/admin/gologin-gmails", headers=headers, timeout=15)
            if r.ok:
                data = r.json()
                self.site_list.delete(0, tk.END)
                for item in data.get("items", []):
                    self.site_list.insert(tk.END, f"{item.get('email','')} | {item.get('pass','')}")
                self.site_status.config(text=f"{len(data.get('items',[]))} itens carregados")
            else:
                self.site_status.config(text=f"Erro {r.status_code}: endpoint ainda não existe no site")
        except Exception as e:
            self.site_status.config(text=f"Falha: {str(e)[:60]}")

    def create_from_site(self):
        sel = self.site_list.curselection()
        if not sel:
            messagebox.showerror("Erro", "Selecione um item")
            return
        line = self.site_list.get(sel[0])
        email = line.split(" |")[0]
        # TODO: pegar cookies do site se o endpoint retornar
        self.site_status.config(text=f"Criando perfil para {email}...")
        # Reusa a lógica de create_from_cookie se tiver cookies salvos com esse nome
        if email in self.cookies_data:
            self.cookie_list.selection_clear(0, tk.END)
            idx = list(sorted(self.cookies_data.keys())).index(email)
            self.cookie_list.selection_set(idx)
            self.create_from_cookie()
        else:
            messagebox.showinfo("Info", "Cookies não encontrados localmente. Salve na aba Cookies primeiro.")

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
