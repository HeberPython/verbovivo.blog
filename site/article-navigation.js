(() => {
  const navigation = document.querySelector("[data-article-pagination]");
  if (!navigation) return;

  const previous = navigation.querySelector("[data-article-previous]");
  const next = navigation.querySelector("[data-article-next]");
  const previousTitle = navigation.querySelector("[data-article-previous-title]");
  const nextTitle = navigation.querySelector("[data-article-next-title]");
  const current = new URL(window.location.href).pathname.replace(/\/+$/, "");

  const disable = (link, title, message) => {
    link.removeAttribute("href");
    link.setAttribute("aria-disabled", "true");
    title.textContent = message;
  };

  const enable = (link, title, article) => {
    link.href = article.url;
    link.removeAttribute("aria-disabled");
    title.textContent = article.title;
  };

  fetch("../feed.xml", { cache: "no-cache" })
    .then((response) => {
      if (!response.ok) throw new Error("Feed indisponível");
      return response.text();
    })
    .then((xml) => {
      const documentXml = new DOMParser().parseFromString(xml, "application/xml");
      const articles = [...documentXml.querySelectorAll("item")].map((item) => ({
        title: item.querySelector("title")?.textContent?.trim() || "Artigo",
        url: item.querySelector("link")?.textContent?.trim() || "",
      }));
      const position = articles.findIndex((article) => {
        try {
          return new URL(article.url).pathname.replace(/\/+$/, "") === current;
        } catch {
          return false;
        }
      });
      if (position < 0) throw new Error("Artigo ausente do feed");

      const older = articles[position + 1];
      const newer = articles[position - 1];
      older
        ? enable(previous, previousTitle, older)
        : disable(previous, previousTitle, "Este é o primeiro artigo");
      newer
        ? enable(next, nextTitle, newer)
        : disable(next, nextTitle, "Este é o artigo mais recente");
      navigation.classList.add("is-ready");
    })
    .catch(() => {
      disable(previous, previousTitle, "Navegação indisponível");
      disable(next, nextTitle, "Navegação indisponível");
      navigation.classList.add("is-ready");
    });
})();
