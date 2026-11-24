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
            self.root.after(0, lambda: self.log(f"--- Iniciando criação de {total} perfis ---"))
            for idx, email in enumerate(emails):
                self.root.after(0, lambda e=email: self.log(f"Processando: {e}"))
                cookies = self.cookies_data.get(email, [])
                if not cookies:
                    raw = self.site_accounts.get(email, {}).get("cookies", "")
                    cookies = try_parse_cookies(raw)
                    if cookies:
                        self.cookies_data[email] = cookies
                if not cookies:
                    errors.append(f"{email}: sem cookies")
                    self.root.after(0, lambda e=email: self.log(f"{e}: sem cookies, pulando"))
                    self.root.after(0, lambda e=email: self.site_status.config(text=f"{e}: sem cookies"))
                    continue

                self.root.after(0, lambda i=idx, e=email: self.site_status.config(text=f"Criando {i+1}/{total}: {e}"))
                self.root.after(0, lambda e=email: self.log(f"Criando perfil: {e}"))

                ok, result = create_profile(profile_tok, email)
                self.root.after(0, lambda o=ok, r=result, e=email: self.log(f"Criar {e}: ok={o}, result={str(r)[:100]}"))
                if not ok:
                    errors.append(f"{email}: {result}")
                    self.root.after(0, lambda r=result: self.site_status.config(text=f"Erro criar: {r[:80]}"))
                    continue

                profile_id = result
                self.root.after(0, lambda p=profile_id: self.log(f"Perfil criado: {p}"))

                if use_gl:
                    self.root.after(0, lambda: self.log(f"Criando proxy GoLogin..."))
                    okp, proxy_obj, msgp = create_proxy_only(proxy_tok, country_code, f"auto-{email[:12]}")
                    self.root.after(0, lambda o=okp, m=msgp: self.log(f"Proxy: ok={o}, msg={str(m)[:100]}"))
                    if okp and proxy_obj:
                        ok2, msg2 = set_custom_proxy(profile_tok, profile_id, proxy_obj)
                        self.root.after(0, lambda o=ok2, m=msg2: self.log(f"Atribuir proxy: ok={o}, msg={str(m)[:80]}"))
                else:
                    proxy = parse_proxy(proxy_lines[idx % len(proxy_lines)])
                    if proxy:
                        ok2, msg2 = set_custom_proxy(profile_tok, profile_id, proxy)
                        self.root.after(0, lambda o=ok2, m=msg2: self.log(f"Proxy custom: ok={o}, msg={str(m)[:80]}"))

                self.root.after(0, lambda: self.log(f"Setando cookies..."))
                ok_c, msg_c = set_cookies(profile_tok, profile_id, cookies)
                self.root.after(0, lambda o=ok_c, m=msg_c: self.log(f"Cookies: ok={o}, msg={str(m)[:80]}"))
                if not ok_c:
                    errors.append(f"{email}: cookies {msg_c}")

                created += 1
                time.sleep(0.3)

            msg = f"Concluído. {created}/{total} perfis criados."
            if errors:
                msg += " Erros: " + " | ".join(errors[:3])
            self.root.after(0, lambda m=msg: self.site_status.config(text=m))
            self.root.after(0, lambda m=msg: self.log(m))

        self.site_status.config(text="Iniciando...")
        self.log("Iniciando criação...")
        threading.Thread(target=work, daemon=True).start()