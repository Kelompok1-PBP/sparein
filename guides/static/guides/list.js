const form = document.getElementById('filters');
let current;
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (current) current.abort();
  current = new AbortController();
  const status = document.getElementById('result-status');
  status.textContent = 'Mencari panduan…';
  const query = new URLSearchParams(new FormData(form));
  try {
    const response = await fetch(`/api/guides/?${query}`, {signal: current.signal});
    if (!response.ok) throw new Error('Filter tidak valid atau server tidak tersedia.');
    const data = await response.json();
    const grid = document.getElementById('guide-grid');
    grid.replaceChildren();
    for (const guide of data.results) {
      const card = document.createElement('article'); card.className = 'card';
      const device = document.createElement('p'); device.className = 'eyebrow'; device.textContent = guide.device_name;
      const heading = document.createElement('h2');
      const link = document.createElement('a'); link.href = guide.url; link.textContent = guide.title; heading.append(link);
      const summary = document.createElement('p'); summary.textContent = guide.summary;
      const meta = document.createElement('p'); meta.className = 'meta'; meta.textContent = `${guide.difficulty} · ${guide.time_required_minutes} menit`;
      card.append(device, heading, summary, meta); grid.append(card);
    }
    if (!data.results.length) { const empty = document.createElement('p'); empty.className = 'empty'; empty.textContent = 'Belum ada panduan yang cocok. Coba ubah filter.'; grid.append(empty); }
    history.replaceState(null, '', `?${query}`);
    status.textContent = `${data.results.length} panduan ditampilkan (maks. 100)`;
  } catch (error) { if (error.name !== 'AbortError') status.textContent = 'Gagal memuat panduan. Cek filter dan coba lagi.'; }
});
