def load_cookies():
    if not Path(COOKIES_FILE).exists():
        return {}
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except:
        return {}