# Panduan Frontend core

Dokumen ini buat belajar ulang dan presentasi. Isinya ngejelasin gimana tampilan Sparein disusun di folder `core/`: halaman login, daftar, dan kerangka (header, footer) yang dipakai semua halaman. Semua pakai HTML, CSS, dan JavaScript biasa, tanpa framework tambahan.

Yang dibahas cuma **tampilan**. View, URL, dan model ngga disentuh sama sekali.

## Daftar isi

1. [Gambaran besar](#1-gambaran-besar)
2. [Gimana satu halaman dirender](#2-gimana-satu-halaman-dirender)
3. [Dua kerangka halaman](#3-dua-kerangka-halaman)
4. [Komponen yang bisa dipakai ulang](#4-komponen-yang-bisa-dipakai-ulang)
5. [CSS](#5-css)
6. [JavaScript](#6-javascript)
7. [Ikon](#7-ikon)
8. [Header beda per role](#8-header-beda-per-role)
9. [Cara bikin halaman baru](#9-cara-bikin-halaman-baru)
10. [Cara jalanin dan ngetes](#10-cara-jalanin-dan-ngetes)
11. [Bahan presentasi](#11-bahan-presentasi)
12. [Yang sengaja ngga dibikin](#12-yang-sengaja-ngga-dibikin)

---

## 1. Gambaran besar

```
core/
├─ templates/
│   ├─ base.html              kerangka biasa: header, isi, footer
│   ├─ auth_base.html         kerangka khusus login dan daftar (dua panel)
│   ├─ 403.html, 404.html     halaman akses ditolak dan tidak ditemukan
│   ├─ registration/login.html
│   ├─ core/register.html
│   └─ partials/              potongan kecil yang dipanggil di banyak tempat
└─ static/core/
    ├─ base.css, base.js      gaya dan JS buat semua halaman
    ├─ auth/                  CSS, JS, dan ilustrasi khusus login dan daftar
    ├─ icons/                 ikon, satu ikon satu file .svg
    └─ brand/                 logo
```

Kalau mau nyari sesuatu: **tampilannya** ada di `templates/`, **warna dan ukuran** ada di `static/core/*.css`.

---

## 2. Gimana satu halaman dirender

1. Browser minta alamat, misalnya `/devices/`.
2. Django jalanin view (ini kode backend, ngga kita ubah) dan nentuin template mana yang dipakai.
3. Template itu diawali `{% extends "base.html" %}`. Artinya "pakai kerangka `base.html`, aku cuma ngisi bagian-bagian yang kosong".
4. Django nyambungin kerangka dan isi halaman jadi satu HTML, terus dikirim ke browser.
5. Browser ngambil `base.css` dan `base.js` yang ditulis di `<head>`, lalu nampilin halamannya.

Bagian kosong di `base.html` namanya **block**:

| Block | Buat apa |
|---|---|
| `title` | Judul tab browser |
| `content` | Isi halaman (di dalam `<main>`) |
| `extra_css` | CSS tambahan khusus satu halaman |
| `extra_js` | JS tambahan khusus satu halaman |

Halaman modul lain cukup ngisi block ini, tanpa ngedit `base.html`.

---

## 3. Dua kerangka halaman

| Kerangka | Dipakai oleh | Isinya |
|---|---|---|
| `base.html` | Hampir semua halaman (beranda, perangkat, 403, 404) | Link lewati konten, header, area toast, `<main>`, footer |
| `auth_base.html` | Cuma login dan daftar | Dua panel: ilustrasi dan form. Tanpa header dan footer |

Login dan daftar dibikin terpisah karena tampilannya layar penuh dua panel, jadi ngga cocok kalau ditaruh di dalam `base.html`.

---

## 4. Komponen yang bisa dipakai ulang

Komponen disimpan di `templates/partials/`. Dipanggil pakai `{% include %}` dan dikasih parameter lewat kata `with`.

| File | Fungsi | Parameter | Contoh pemakaian |
|---|---|---|---|
| `form_field.html` | Satu isian form: label, input, hint, pesan error | `field`, `label`, `kind` (`text` atau `password`), `autocomplete`, `hint` | `{% include "partials/form_field.html" with field=form.username label="Username" kind="text" autocomplete="username" %}` |
| `alert.html` | Kotak info atau error | `kind` (`info` atau `error`), `message` | `{% include "partials/alert.html" with kind="info" message="Masuk dulu ya." %}` |
| `empty_state.html` | Tampilan "belum ada data" | `message`, opsional `action_url` dan `action_label` | `{% include "partials/empty_state.html" with message="Belum ada panduan." %}` |
| `card.html` | Kartu sederhana | `title`, `url`, `text` | `{% include "partials/card.html" with title=d.name url=link %}` |
| `toasts.html` | Notifikasi kecil dari Django `messages` | (otomatis) | Sudah dipanggil di `base.html` |
| `role_badge.html` | Lencana Member, Contributor, atau Admin | (otomatis, baca `user`) | Dipakai di header |
| `create_items.html` | Daftar menu "Buat" | `cls` | Dipakai di header |
| `header.html`, `footer.html` | Header dan footer | (otomatis) | Dipanggil di `base.html` |

Kalau butuh bikin tampilan yang sama di dua tempat, jadiin satu partial. Jangan disalin-tempel.

---

## 5. CSS

**Dua file, dua tugas:**

| File | Isinya |
|---|---|
| `base.css` | Warna, tombol, form, header, footer, toast, kartu. Dipakai semua halaman |
| `auth/auth.css` | Cuma layout dua panel login dan daftar |

**Warna ada di satu tempat:** bagian paling atas `base.css`, di blok `:root`.

```css
:root {
  --blue-500: #1581EE;
  --danger: #DC2626;
  ...
}
```

Nama dan nilainya sama dengan `docs/DESIGN-SYSTEM.md`. Mau ganti warna utama? Ubah satu baris `--blue-500`, semua tombol dan link ikut berubah. Di bagian lain CSS, warna selalu dipanggil pakai `var(--blue-500)`, jangan nulis kode hex lagi.

**Cara nama class:** pola `blok__bagian--varian`.

- `btn` adalah komponen tombol. `btn--primary` varian utamanya. `btn--sm` varian kecil.
- `field__label` adalah bagian label di dalam komponen `field`.
- `site-nav__link` adalah satu link di dalam `site-nav`.

Dengan pola ini, dari nama class aja udah kebaca itu bagian dari apa.

**Responsif (HP ke desktop).** CSS ditulis buat layar HP dulu, lalu ditambah aturan layar lebar:

```css
.container { width: min(100% - 32px, 1120px); }    /* HP */

@media (min-width: 768px) {
  .container { width: min(100% - 64px, 1120px); }  /* layar >= 768 */
}
```

Dua titik patahnya: **768px** buat layout login dan daftar, **1024px** buat header (di bawah itu muncul menu mobile).

**Aturan desain yang dipegang:** tanpa bayangan, radius kartu 14, radius tombol dan input 10, garis tipis `blue-200`.

---

## 6. JavaScript

JS dipakai seminim mungkin.

**`base.js` (30 baris), tiga hal:**

1. Header dapet garis bawah setelah halaman di-scroll (nambah class `is-scrolled`).
2. Dropdown akun dan "Buat" nutup kalau klik di luar atau tekan Esc.
3. Toast hilang sendiri setelah 5 detik.

**`auth/auth.js`, tiga hal:**

1. Tombol lihat atau sembunyiin password.
2. Teks tombol berubah jadi "Memproses..." setelah form dikirim.
3. Penanda `sessionStorage` buat efek geser lama. **Bagian ini sekarang ngga dipakai CSS lagi**, karena efek geser udah diurus `auth.css` (lihat di bawah). Aman dihapus kalau mau lebih ringkas.

**Efek geser login dan daftar tanpa JS.** Di `auth.css` kedua panel dikasih nama yang sama di dua halaman:

```css
@view-transition { navigation: auto; }
.auth__art   { view-transition-name: auth-art; }
.auth__panel { view-transition-name: auth-panel; }
```

Browser yang dukung (Chrome, Edge, Safari baru) otomatis ngegeser panel dari posisi lama ke posisi baru waktu pindah halaman. Browser lain tetap pindah halaman biasa, nggak ada yang rusak.

**Menu mobile pakai `<details>`.** Elemen HTML bawaan yang bisa buka dan tutup sendiri, jadi ngga butuh JS. Tombol burger-nya adalah `<summary>`, isinya panel menu.

---

## 7. Ikon

**Aturan:** ikon ditulis sebagai file `.svg` di `static/core/icons/`, dipanggil pakai `<img>`. Jangan nulis `<svg>` langsung di HTML.

```html
{% load static %}
<img src="{% static 'core/icons/user-muted.svg' %}" alt="" width="20" height="20">
```

- Warna ikon ada **di dalam file**, makanya namanya ditambah warna: `eye-muted.svg`, `circle-alert-danger.svg`, `info-blue.svg`.
- Butuh ikon yang sama dengan warna lain? Salin filenya, ganti nilai `stroke`, simpan dengan nama baru.
- Ikon hiasan dikasih `alt=""`. Ikon yang jadi satu-satunya isi tombol, kasih `aria-label` di tombolnya.
- Sumber bentuk ikon: Lucide (gratis, lisensi ISC).

---

## 8. Header beda per role

Header ada di `partials/header.html`. Tampilannya beda sesuai siapa yang login. Pengecekannya langsung di template:

| Siapa | Kondisi di template | Yang muncul |
|---|---|---|
| Belum login | `{% if not user.is_authenticated %}` | Tombol Masuk dan Daftar |
| Member | `{% if user.is_authenticated %}` | Menu Jurnal, avatar, dan menu akun |
| Contributor | `user.profile.role == "CONTRIBUTOR"` | Ditambah tombol "Buat" |
| Admin | `user.is_superuser` atau `user.profile.role == "ADMIN"` | Ditambah tombol "Buat" dan link "Panel admin" |

`user` tersedia otomatis di semua template. "Keluar" itu **form dengan method POST**, bukan link, karena Django nolak logout lewat GET.

Menu yang lagi dibuka ditandai pakai `aria-current="page"`, ditentukan dari `request.resolver_match.namespace` (nama app dari URL, misalnya `devices`).

---

## 9. Cara bikin halaman baru

Contoh halaman sederhana di modul kamu:

```html
{% extends "base.html" %}
{% block title %}Judul Halaman · Sparein{% endblock %}

{% block content %}
  <h1>Judul Halaman</h1>

  {% for item in items %}
    {% include "partials/card.html" with title=item.name %}
  {% empty %}
    {% include "partials/empty_state.html" with message="Belum ada data." %}
  {% endfor %}
{% endblock %}
```

Header, footer, lebar isi, dan gaya dasar langsung ikut. Elemen polos (`h1`, `p`, `input`, `button`) di dalam `<main>` sudah dikasih gaya dasar, jadi halaman yang belum didesain tetap rapi.

Ngomong-ngomong soal form: pakai `partials/form_field.html` biar tampilan label, input, dan pesan error-nya konsisten.

---

## 10. Cara jalanin dan ngetes

```powershell
python manage.py migrate
python manage.py runserver
```

Buka `http://127.0.0.1:8000/accounts/login/` dan `http://127.0.0.1:8000/register/`.

Kalau muncul error `SECRET_KEY setting must not be empty`: isi `SECRET_KEY=` di file `.env` pakai teks acak (jangan dikosongin, jangan di-commit).

**Sebelum bikin PR**, jalanin tiga perintah ini (sama dengan yang dicek CI):

```powershell
ruff check .
python manage.py makemigrations --check --dry-run
python manage.py test
```

---

## 11. Bahan presentasi

Kalau disuruh jelasin dalam 3 sampai 5 menit, urutannya begini:

1. **Masalahnya:** tiap halaman butuh header dan footer yang sama. Kalau ditulis ulang di tiap halaman, ngubah satu hal berarti ngubah banyak file.
2. **Solusinya:** satu kerangka `base.html`, halaman lain cuma `extends` dan ngisi block `content`.
3. **Komponen:** potongan yang sering dipakai (form, kotak info, state kosong) dijadiin partial, dipanggil pakai `include`.
4. **Desain konsisten:** semua warna ada di satu blok `:root`, jadi ganti warna cukup di satu tempat.
5. **Beda tampilan per role:** header ngecek `user` langsung di template.
6. **JS seminim mungkin:** menu mobile dan dropdown pakai `<details>` bawaan HTML, efek geser pakai CSS.

**Pertanyaan yang mungkin muncul:**

| Pertanyaan | Jawaban singkat |
|---|---|
| Kenapa CSS ditulis manual, bukan Tailwind? | Repo belum punya setup Tailwind dan PWS ngga jalanin proses build. Nama token-nya sama dengan `DESIGN-SYSTEM.md`, jadi gampang dipindah nanti |
| Kenapa ikon dipisah jadi file? | Biar HTML ngga penuh kode SVG panjang dan ikon gampang diganti |
| Kenapa logout pakai form? | Django cuma nerima logout lewat POST biar ngga bisa kepancing lewat link |
| Apa yang terjadi kalau JS mati? | Login, daftar, dropdown, dan menu mobile tetap jalan. Yang hilang cuma tombol lihat password dan toast hilang sendiri |
| Kenapa ada dua kerangka? | Login dan daftar tampilannya layar penuh dua panel, ngga cocok di dalam kerangka biasa |

---

## 12. Yang sengaja ngga dibikin

Biar kodenya tetap bisa dipelajari, hal-hal ini sengaja ditunda:

- **Halaman Profil** (`/profile/`). Butuh view dan URL baru, jadi masuk backend dan perlu keputusan tim dulu.
- **Toast di alur nyata.** Komponennya udah ada, tapi belum ada view yang ngirim `messages.success(...)`.
- **Tailwind.** Belum ada setup build.
- **Mode gelap.**
- **Link ke halaman modul lain** (`/diagnostics/`, `/guides/`, `/parts/`, `/journal/`) ditulis langsung sesuai `docs/MODULES.md`. Sebelum modulnya jadi, klik link itu bakal ke halaman 404. Kalau modulnya udah ada, ganti ke `{% url %}`.
- **Pesan error daftar** masih bawaan Django. Mau diganti ke teks desain butuh ngubah form, yaitu backend.
