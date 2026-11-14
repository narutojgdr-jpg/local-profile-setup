document.getElementById("login").onclick = async () => {
  const status = document.getElementById("status");
  const nid = document.getElementById("nid").value.trim();
  const snid = document.getElementById("snid").value.trim();

  if (!nid || !snid) {
    status.textContent = "Cola os dois cookies primeiro";
    return;
  }

  status.textContent = "Injetando...";

  const cookies = [
    {
      name: "NetflixId",
      value: nid,
      domain: ".netflix.com",
      path: "/",
      secure: true,
      httpOnly: true,
      expirationDate: Math.floor(Date.now() / 1000) + 60 * 60 * 24 * 180
    },
    {
      name: "SecureNetflixId",
      value: snid,
      domain: ".netflix.com",
      path: "/",
      secure: true,
      httpOnly: true,
      expirationDate: Math.floor(Date.now() / 1000) + 60 * 60 * 24 * 180
    }
  ];

  try {
    for (const c of cookies) {
      await chrome.cookies.set({
        url: "https://www.netflix.com",
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path,
        secure: c.secure,
        httpOnly: c.httpOnly,
        expirationDate: c.expirationDate
      });
    }
    status.textContent = "Ok. Abrindo Netflix...";
    chrome.tabs.create({ url: "https://www.netflix.com/browse" });
  } catch (e) {
    status.textContent = "Erro: " + e.message;
  }
};
