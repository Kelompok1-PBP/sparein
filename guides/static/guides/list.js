const form = document.getElementById("filters");
const grid = document.getElementById("guide-grid");
const status = document.getElementById("result-status");
const chips = document.getElementById("filter-chips");
let current;

// Bikin elemen + isi teksnya. textContent bukan innerHTML biar teks dari database ga ke-render jadi HTML
const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

const icon = (src, size) => {
  const img = el("img");
  img.src = src;
  img.alt = "";
  img.width = size;
  img.height = size;
  return img;
};

// Markup kartu harus sama dengan guides/_card.html
const makeCard = (guide) => {
  const cover = el("span", "guide-card__cover");
  if (guide.device_image_url) {
    const photo = icon(guide.device_image_url, 120);
    photo.className = "guide-card__photo";
    photo.removeAttribute("width");
    photo.removeAttribute("height");
    photo.loading = "lazy";
    cover.append(photo);
  } else {
    cover.append(icon(grid.dataset.coverIcon, 40));
  }
  cover.append(el("span", `difficulty difficulty--${guide.difficulty_tone}`, guide.difficulty_label));
  if (!guide.published) cover.append(el("span", "guide-card__draft", "Draf"));

  const meta = el("span", "guide-meta");
  const time = el("span");
  time.append(icon(grid.dataset.clockIcon, 16), guide.duration_label);
  const steps = el("span");
  steps.append(icon(grid.dataset.stepsIcon, 16), `${guide.step_total} langkah`);
  meta.append(time, steps);

  const link = el("a", "guide-card");
  link.href = guide.url;
  link.append(cover, el("span", "guide-card__title", guide.title), el("span", "guide-card__device", guide.device_name), meta);
  const item = el("li");
  item.append(link);
  return item;
};

// Markup state kosong harus sama dengan partials/empty_state.html
const makeEmpty = () => {
  const box = el("div", "empty-state");
  box.append(icon(grid.dataset.emptyIcon, 48), el("p", "", "Belum ada panduan yang cocok. Coba ubah filter perangkat atau durasinya."));
  const item = el("li", "guide-grid__empty");
  item.append(box);
  return item;
};

// Chip filter aktif, sama dengan chips dari server. Linknya mencabut satu filter
const renderChips = (query) => {
  const active = [];
  const device = form.elements.device.selectedOptions[0];
  if (query.get("device")) active.push(["device", `Perangkat: ${device.textContent}`]);
  const difficulty = form.querySelector("[name=difficulty]:checked");
  if (query.get("difficulty")) active.push(["difficulty", `Kesulitan: ${difficulty.parentElement.textContent.trim()}`]);
  const maxTime = form.querySelector("[name=max_time]:checked");
  if (query.get("max_time")) active.push(["max_time", `Waktu: ≤ ${maxTime.parentElement.textContent.trim()}`]);

  chips.replaceChildren(...active.map(([name, text]) => {
    const rest = new URLSearchParams(query);
    rest.delete(name);
    const link = el("a", "filter-chip", `${text} `);
    link.href = rest.toString() ? `?${rest}` : location.pathname;
    const remove = icon(grid.dataset.removeIcon, 14);
    remove.alt = "Hapus filter";
    link.append(remove);
    const item = el("li");
    item.append(link);
    return item;
  }));
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (current) current.abort();
  current = new AbortController();
  status.textContent = "Mencari panduan…";
  const query = new URLSearchParams(new FormData(form));
  for (const [name, value] of [...query]) if (!value) query.delete(name);
  try {
    const response = await fetch(`/api/guides/?${query}`, { signal: current.signal });
    if (!response.ok) throw new Error("Filter tidak valid atau server tidak tersedia.");
    const data = await response.json();
    grid.replaceChildren(...(data.results.length ? data.results.map(makeCard) : [makeEmpty()]));
    renderChips(query);
    history.replaceState(null, "", query.toString() ? `?${query}` : location.pathname);
    status.textContent = `Menampilkan ${data.results.length} panduan`;
  } catch (error) {
    if (error.name !== "AbortError") status.textContent = "Gagal memuat panduan. Cek filter dan coba lagi.";
  }
});
