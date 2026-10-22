// Dua halaman: pilih perangkat (cari lewat /api/devices/) dan centang gejala (hasil lewat AJAX)

// Bikin elemen + isi teksnya. textContent bukan innerHTML biar teks dari database ga ke-render jadi HTML
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

/* ---------- pilih perangkat ---------- */
const picker = document.getElementById("device-picker");
if (picker) {
  const input = document.getElementById("picker-q");
  const out = document.getElementById("picker-results");

  const showDevices = (items) => {
    out.replaceChildren();
    if (!items.length) {
      out.append(el("p", "meta", "Perangkat tidak ditemukan."));
      return;
    }
    const list = el("ul", "picker__list");
    for (const d of items.slice(0, 8)) {
      const li = el("li");
      const a = el("a", "picker__item");
      a.href = `${picker.dataset.target}?device=${encodeURIComponent(d.slug)}`;
      a.append(el("span", "", d.name), el("span", "picker__brand", d.brand));
      li.append(a);
      list.append(li);
    }
    out.append(list);
  };

  const search = async () => {
    const q = input.value.trim();
    if (!q) {
      out.replaceChildren();
      return;
    }
    const resp = await fetch(`${picker.dataset.api}?q=${encodeURIComponent(q)}`);
    if (resp.ok) showDevices((await resp.json()).results);
  };

  input.addEventListener("input", debounce(search, 300));
}

/* ---------- centang gejala ---------- */
const form = document.getElementById("symptom-form");
if (form) {
  const panel = document.getElementById("diagnosis-results");
  const emptyIcon = panel.querySelector("img")?.src;
  const csrf = document.querySelector("#save-form [name=csrfmiddlewaretoken]")?.value;

  const ticked = () => new URLSearchParams(new FormData(form));

  // Markup ini harus sama dengan diagnostics/_results.html
  const makeResult = (r, rank, guidesUrl) => {
    const li = el("li", "result");
    const body = el("div", "result__body");
    const bar = el("span", `bar bar--${r.likelihood}`);
    bar.setAttribute("aria-hidden", "true");
    bar.append(el("span"));
    body.append(
      el("h3", "result__title", r.title),
      bar,
      el("p", "result__likelihood", `Kemungkinan ${r.likelihood_label.toLowerCase()}`),
    );
    if (r.note) body.append(el("p", "result__note", r.note));
    const link = el("a", "link", "Lihat panduan terkait");
    link.href = guidesUrl;
    body.append(link);
    li.append(el("span", "result__rank", String(rank)), body);
    return li;
  };

  const makeEmpty = (message, icon, guidesUrl) => {
    const box = el("div", "empty-state");
    if (icon) {
      const img = el("img");
      img.src = icon;
      img.alt = "";
      img.width = 48;
      img.height = 48;
      box.append(img);
    }
    box.append(el("p", "", message));
    if (guidesUrl) {
      const a = el("a", "link", "Lihat panduan");
      a.href = guidesUrl;
      box.append(a);
    }
    return box;
  };

  const showSkeleton = () => {
    panel.replaceChildren(...[1, 2, 3].map(() => el("div", "skeleton")));
  };

  const showResults = (data) => {
    panel.replaceChildren();
    if (!data.count) {
      panel.append(makeEmpty("Belum ada kemungkinan yang cocok buat kombinasi gejala ini.", null, data.guides_url));
      return;
    }
    const list = el("ol", "results");
    data.results.forEach((r, i) => list.append(makeResult(r, i + 1, data.guides_url)));
    panel.append(el("p", "result-count", `${data.count} kemungkinan ditemukan`), list);
  };

  const refresh = async () => {
    const params = ticked();
    if (!params.has("symptom")) {
      panel.replaceChildren(makeEmpty("Centang gejala di sebelah kiri buat lihat kemungkinan masalahnya.", emptyIcon));
      history.replaceState(null, "", `?${params}`);
      return;
    }
    showSkeleton();
    const resp = await fetch(`${form.dataset.api}?${params}`);
    if (!resp.ok) {
      panel.replaceChildren(makeEmpty("Hasil belum bisa dimuat. Coba lagi ya."));
      return;
    }
    showResults(await resp.json());
    history.replaceState(null, "", `?${params}`);
  };

  form.addEventListener("change", refresh);
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    refresh();
  });

  /* ---------- simpan hasil ---------- */
  const saveForm = document.getElementById("save-form");
  if (saveForm) {
    const note = document.getElementById("save-note");
    saveForm.hidden = false; // tanpa JS tombolnya ga ada gunanya
    saveForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const params = ticked();
      if (!params.has("symptom")) {
        note.textContent = "Pilih minimal satu gejala dulu.";
        return;
      }
      const resp = await fetch(saveForm.dataset.api, {
        method: "POST",
        headers: { "X-CSRFToken": csrf },
        body: params,
      });
      note.textContent = resp.ok ? "Hasil diagnosa tersimpan." : "Gagal menyimpan. Coba lagi ya.";
    });
  }
}

/* ---------- cari di Select perangkat (form gejala) ---------- */
const deviceFilter = document.querySelector("[data-filter-for]");
if (deviceFilter) {
  const select = document.getElementById(deviceFilter.dataset.filterFor);
  const options = [...select.options];
  deviceFilter.hidden = false; // tanpa JS Select biasa tetap bisa dipakai

  deviceFilter.addEventListener("input", () => {
    const q = deviceFilter.value.trim().toLowerCase();
    const chosen = select.value;
    // dibangun ulang karena <option hidden> tidak didukung semua browser
    select.replaceChildren(...options.filter((o) => !o.value || o.value === chosen || o.text.toLowerCase().includes(q)));
    select.value = chosen;
  });
}
