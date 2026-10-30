const form = document.getElementById("device-filter");
const results = document.getElementById("device-results");

// Bikin elemen + isi teksnya. Pakai textContent bukan innerHTML biar nama device ga ke-render jadi HTML
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

// Markup kartu ini harus sama dengan devices/_card.html
function makeCard(d) {
  const article = el("article", "device-card");
  const link = el("a", "device-card__link");
  link.href = d.url;

  const box = el("div", "device-card__img");
  const img = el("img");
  img.alt = "";
  img.loading = "lazy";
  if (d.image_url) {
    img.src = d.image_url;
  } else {
    img.src = results.dataset.placeholder;
    img.className = "is-placeholder";
    img.width = 40;
    img.height = 40;
  }
  box.append(img);

  link.append(box, el("h3", "device-card__name", d.name));
  if (d.brand) link.append(el("p", "device-card__brand", d.brand));
  article.append(link);
  return article;
}

// Markup ini sama dengan partials/empty_state.html
function makeEmpty() {
  const box = el("div", "empty-state");
  const img = el("img");
  img.src = results.dataset.emptyIcon;
  img.alt = "";
  img.width = 48;
  img.height = 48;
  box.append(img, el("p", "", "Perangkat tidak ditemukan."));
  return box;
}

function render(items) {
  results.replaceChildren();
  if (!items.length) {
    results.append(makeEmpty());
    return;
  }
  for (const d of items) results.append(makeCard(d));
}

async function search() {
  const params = new URLSearchParams(new FormData(form));
  const resp = await fetch(`${form.dataset.api}?${params}`);
  if (!resp.ok) return;
  render((await resp.json()).results);
  history.replaceState(null, "", `?${params}`);
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
