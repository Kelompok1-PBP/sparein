const form = document.getElementById("device-filter");
const results = document.getElementById("device-results");

// textContent bukan innerHTML biar nama device ga ke-render jadi HTML
function render(items) {
  results.replaceChildren();
  if (!items.length) {
    const p = document.createElement("p");
    p.textContent = "Perangkat tidak ditemukan.";
    results.append(p);
    return;
  }
  for (const d of items) {
    const article = document.createElement("article");
    const h3 = document.createElement("h3");
    const a = document.createElement("a");
    a.href = d.url;
    a.textContent = d.name;
    h3.append(a);
    const p = document.createElement("p");
    p.textContent = d.brand;
    article.append(h3, p);
    results.append(article);
  }
}

async function search() {
  const params = new URLSearchParams(new FormData(form));
  const resp = await fetch(`${form.dataset.api}?${params}`);
  if (resp.ok) render((await resp.json()).results);
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  search();
});

let timer;
form.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(search, 300);
});
