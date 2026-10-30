// Filter direktori tanpa reload: ambil /api/parts/ terus gambar ulang kartunya.
// Tanpa JS form-nya tetap jalan biasa lewat tombol "Terapkan filter".

const form = document.getElementById("part-filter");
const results = document.getElementById("part-results");
const count = document.getElementById("part-count");
let current;
let timer;

// textContent bukan innerHTML biar nama suku cadang ga ke-render jadi HTML
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function icon(src, size) {
  const img = el("img");
  img.src = src;
  img.alt = "";
  img.width = size;
  img.height = size;
  return img;
}

function rupiah(value) {
  return `Rp ${value.toLocaleString("id-ID")}`;
}

// isinya disamain sama _part_card.html
function card(part) {
  const article = el("article", "card part-card");
  const media = el("div", "part-card__media");
  if (part.image_url) {
    const img = el("img");
    img.src = part.image_url;
    img.alt = "";
    img.loading = "lazy";
    img.referrerPolicy = "no-referrer";
    media.append(img);
  } else {
    media.append(icon(results.dataset.placeholder, 40));
  }
  const title = el("h2", "part-card__title");
  const link = el("a", "", part.name);
  link.href = part.url;
  title.append(link);
  article.append(media, el("span", "badge part-badge", part.category_label), title);
  if (part.part_number) article.append(el("p", "part-card__number", part.part_number));

  const price = el("p", "part-card__price");
  if (!part.source_count) {
    price.textContent = "Harga belum tersedia";
  } else if ("lowest_price" in part) {
    price.append("Mulai ", el("strong", "", rupiah(part.lowest_price)), ` · ${part.source_count} toko`);
  } else {
    // visitor ga dapet kunci harga dari API
    const login = el("a", "link", "Masuk untuk lihat harga");
    login.href = `${results.dataset.login}?next=${encodeURIComponent(location.pathname + location.search)}`;
    price.append(login);
  }
  article.append(price);
  return article;
}

// pesannya sama kayak _empty_message di views.py
function emptyState(params, filtered) {
  const box = el("div", "empty-state");
  box.append(icon(results.dataset.emptyIcon, 48));
  const device = form.elements.device;
  const others = ["q", "category", "max_price"].some((key) => params.has(key));
  let message = "Belum ada suku cadang terdaftar.";
  if (device.value && !others) {
    message = `Belum ada suku cadang terdaftar buat ${device.selectedOptions[0].text}.`;
  } else if (filtered) {
    message = "Belum ada suku cadang yang cocok.";
  }
  box.append(el("p", "", message));
  if (filtered) {
    const reset = el("a", "btn btn--primary", "Reset filter");
    reset.href = location.pathname;
    box.append(reset);
  }
  return box;
}

async function search() {
  clearTimeout(timer);
  if (current) current.abort();
  current = new AbortController();
  // isian kosong ga usah ikut ke URL
  const params = new URLSearchParams();
  for (const [key, value] of new FormData(form)) {
    if (value.trim()) params.append(key, value.trim());
  }
  const query = params.toString();
  results.setAttribute("aria-busy", "true");
  try {
    const response = await fetch(`${form.dataset.api}?${query}`, { signal: current.signal });
    if (!response.ok) throw new Error(response.statusText);
    const data = await response.json();
    history.replaceState(null, "", query ? `?${query}` : location.pathname);
    if (data.results.length) {
      const grid = el("div", "part-grid");
      grid.append(...data.results.map(card));
      results.replaceChildren(grid);
    } else {
      results.replaceChildren(emptyState(params, Boolean(query)));
    }
    count.textContent = `${data.results.length} suku cadang`;
    results.removeAttribute("aria-busy");
  } catch (error) {
    if (error.name === "AbortError") return;  // udah diganti request yang lebih baru
    count.textContent = "Gagal memuat suku cadang. Coba lagi.";
    results.removeAttribute("aria-busy");
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  search();
});

// ketik, centang, atau pilih perangkat langsung nyari, ditunda dikit biar ga tiap huruf
form.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(search, 300);
});

const quick = form.querySelector("[data-quick-price]");
if (quick) {
  quick.hidden = false;
  quick.addEventListener("click", (event) => {
    const button = event.target.closest("[data-price]");
    if (!button) return;
    form.elements.max_price.value = button.dataset.price;
    search();
  });
}
