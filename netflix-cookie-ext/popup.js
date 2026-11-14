const cookies = [
  {
    name: "NetflixId",
    value: "ct%3DBgjHlOvcAxLYA7JJbgpRxjjCD3nVsDADE-evsLWpD8fX_7YtM0pTj5HQ2rs-G3GosVu099_L1n2vFcp3KqlnfWCNtTeEyw8u1sNQxmYKGmQAPT_u2XUghyNXJlMHfVu49dWWjCfjoP-LAEWrKNSfkxTOfIq-h6XsIA_u9sH5aaTHvDXvv-MT0D3Z9UPP2pf324kPw1foAuDlrYPePRUsRQj8jL2sXC8fgxugeB9yvUTxFh8GqIl-mkhFVGUIq1Mizfwq7_IZm14FKs5hrRjPN3mKNuaXMwb6TpERbReN5GeUuM7g60nWMxZwb4LqVUFe2N_nUiPPtLPIZxkqbQ66pHYDXbnZ8VAe8VyQxnak5xKRWxmvjthp_ue7Zp5B5QqQPElhWsmOBjFxl3yE1QAhaMKuCMlqF5ZzihsXRv1Asi-HuTJZpN46zohBzpec9nkyKXv-k9A_dQfInJBJwJZ0nzWh0fGDzjbSnD0jo-rNkhbFVZhO66Si1kgzNXlWkE2uiZlTC_dBWEbVZNzvipXIGL20Lgkh7Sbwa7bj378F5pzmSlCG5cODoF2YC9lx02PObARvQEKnnBzfDwofcP4NTXrhUX2NKj6T1h0gHtiVymm_ylGIEA28AZxYZWZFmfykRoAYBiIOCgzChA2QdJ_IObAxwF8.%26ch%3DAQEAEAABABRLdcRaJ8U1Vv5YNK5MZm9FQuyrpA3ZB4A.%26v%3D3%26pg%3DQST3BAXF45AE3JHCX4IGLIM22U",
    domain: ".netflix.com",
    path: "/",
    secure: true,
    httpOnly: true,
    expirationDate: 1812313745
  },
  {
    name: "SecureNetflixId",
    value: "v%3D3%26mac%3DAQEAEQABABRwUjiV7c6Gda66Z6JRnrWZmHyT26tthfU.%26dt%3D1780777742616",
    domain: ".netflix.com",
    path: "/",
    secure: true,
    httpOnly: true,
    expirationDate: 1812313745
  },
  {
    name: "nfvdid",
    value: "BQFmAAEBEFLcD47_7UKTSi2z-pGOXjZgeuCkaXd6zEtoXYUVqRCVOt_ToRMYa07jTIfazEv9mRtLRisty9eQGtLayf_ulv3Sn8uqTGK4bDWz_6acVsoRY1fo0X3f2kKTp2_5LoR6dPG88ZjqW1AFzA9o-aw9VGmp",
    domain: ".netflix.com",
    path: "/",
    secure: false,
    httpOnly: false,
    expirationDate: 1807051917
  }
];

document.getElementById("login").onclick = async () => {
  const status = document.getElementById("status");
  status.textContent = "Aplicando cookies...";

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
    status.textContent = "Cookies ok. Abrindo Netflix...";
    chrome.tabs.create({ url: "https://www.netflix.com/browse" });
  } catch (e) {
    status.textContent = "Erro: " + e.message;
  }
};
