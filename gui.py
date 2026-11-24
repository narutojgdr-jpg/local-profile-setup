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
            try:
                created = 0
                total = len(emails)
                errors = []
                self.root.after(0, lambda: self.log(f"--- Iniciando {total} perfis ---"))
                for idx, email in enumerate(emails):
                    self.root.after(0, lambda e=email: self.log(f"[{idx+1}/{total}] Processando: {e}"))
                    cookies = self.cookies_data.get(email, [])
                    if not cookies:
                        raw = self.site_accounts.get(email, {}).get("cookies", "")
                        cookies = try_parse_cookies(raw)
                        if cookies:
                            self.cookies_data[email] = cookies
                    if not cookies:
                        errors.append(f"{email}: sem cookies")
                        self.root.after(0, lambda e=email: self.log(f"{e}: SEM COOKIES, pulando"))
                        continue

                    self.root.after(0, lambda i=idx, e=email: self.site_status.config(text=f"Criando {i+1}/{total}: {e}"))
                    self.root.after(0, lambda e=email: self.log(f"Criando perfil: {e}"))

                    ok, result = create_profile(profile_tok, email)
                    self.root.after(0, lambda o=ok, r=str(result)[:100]: self.log(f"  Criar perfil: ok={o} id={r}"))
                    if not ok:
                        errors.append(f"{email}: {result}")
                        self.root.after(0, lambda r=result: self.log(f"  ERRO criar: {r}"))
                        continue

                    profile_id = result

                    if use_gl:
                        self.root.after(0, lambda: self.log(f"  Criando proxy GoLogin..."))
                        okp, proxy_obj, msgp = create_proxy_only(proxy_tok, country_code, f"auto-{email[:12]}")
                        self.root.after(0, lambda o=okp, m=str(msgp)[:80]: self.log(f"  Proxy: ok={o} {m}"))
                        if okp and proxy_obj:
                            ok2, msg2 = set_custom_proxy(profile_tok, profile_id, proxy_obj)
                            self.root.after(0, lambda o=ok2, m=str(msg2)[:60]: self.log(f"  Atribuir proxy: ok={o} {m}"))
                    else:
                        proxy = parse_proxy(proxy_lines[idx % len(proxy_lines)])
                        if proxy:
                            ok2, msg2 = set_custom_proxy(profile_tok, profile_id, proxy)
                            self.root.after(0, lambda o=ok2, m=str(msg2)[:60]: self.log(f"  Proxy custom: ok={o} {m}"))

                    self.root.after(0, lambda: self.log(f"  Setando cookies..."))
                    ok_c, msg_c = set_cookies(profile_tok, profile_id, cookies)
                    self.root.after(0, lambda o=ok_c, m=str(msg_c)[:60]: self.log(f"  Cookies: ok={o} {m}"))

                    created += 1
                    self.root.after(0, lambda c=created, t=total: self.log(f"  OK {c}/{t}"))
                    time.sleep(0.3)

                msg = f"=== CONCLUIDO: {created}/{total} ==="
                if errors:
                    msg += "\nErros: " + " | ".join(errors[:3])
                self.root.after(0, lambda m=msg: self.site_status.config(text=m.replace("\n", " ")))
                self.root.after(0, lambda m=msg: self.log(m))
            except Exception as e:
                self.root.after(0, lambda err=str(e): self.log(f"ERRO GERAL: {err}"))
                self.root.after(0, lambda err=str(e): self.site_status.config(text=f"Erro: {err[:50]}"))

        self.site_status.config(text="Iniciando...")
        self.log("=== INICIANDO CRIACAO ===")
        threading.Thread(target=work, daemon=True).start()