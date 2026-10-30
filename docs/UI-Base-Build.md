# UI Base Template Build Sheet

Lembar kerja buat ngegambar kerangka yang dipakai semua halaman Sparein di Figma: **header**, **footer**, dan **body template** (area isi halaman). Di kode ini bakal jadi `base.html` plus partial `header.html` dan `footer.html`. Gaya yang dituju: clean, modern, profesional, dengan sentuhan kreatif yang halus. Ukuran dan warna ngikutin [`UI-Specs.md`](UI-Specs.md) dan [`DESIGN-SYSTEM.md`](DESIGN-SYSTEM.md), kecuali di bagian [Yang beda dari spec lama](#8-yang-beda-dari-spec-lama).

Contoh jadinya ada di [`design/base/`](design/README.md), tinggal drag ke Figma buat jadi patokan visual. Komponen dan auto layout-nya tetap dibangun manual.

## Daftar isi

1. [Arah desain](#1-arah-desain)
2. [Yang bakal digambar](#2-yang-bakal-digambar)
3. [Token tambahan](#3-token-tambahan)
4. [Komponen](#4-komponen)
5. [Frame dan struktur layer](#5-frame-dan-struktur-layer)
6. [Sambungan prototype](#6-sambungan-prototype)
7. [Catatan buat base.html](#7-catatan-buat-basehtml)
8. [Yang beda dari spec lama](#8-yang-beda-dari-spec-lama)
9. [Hal yang masih perlu dibahas](#9-hal-yang-masih-perlu-dibahas)
10. [Checklist sebelum selesai](#10-checklist-sebelum-selesai)

---

## 1. Arah desain

Tiga keputusan yang udah disepakati:

| Topik | Keputusan | Artinya |
|---|---|---|
| Corner dan bayangan | **Tetap flat** | Ikut `DESIGN-SYSTEM.md`: tanpa drop shadow, kartu radius 14, tombol dan input radius 10, cuma garis tipis `blue/200`. Elemen yang melayang (dropdown, toast) dipisahin dari latar pakai garis, bukan bayangan |
| Header | **Sticky kaca blur** | Putih semi transparan dengan blur latar, garis bawah tipis cuma muncul setelah halaman di-scroll |
| Footer | **Terang ala Apple** | Latar `surface`, teks kecil abu, garis pemisah tipis. Konten di atasnya yang jadi bintang |

Kesan clean modern dibangun dari hal-hal ini, bukan dari efek berat:

- **Ruang kosong lega.** Jarak antar section 32 sampai 64, bukan padat.
- **Satu warna aksen.** Biru `blue/500` dipakai hemat: tombol utama, menu aktif, link. Sisanya netral (`ink`, `muted`, `surface`).
- **Menu aktif berupa pil lembut** (`blue/50` dengan teks `blue/700`), bukan garis bawah tebal.
- **Tipografi tegas.** Judul besar dan tebal (`Heading/H1` 32/40 bold), teks isi tenang. Kontras ukuran yang bikin kesan profesional.
- **Sentuhan kreatif** disimpen buat area tertentu, misalnya panel ilustrasi di halaman login dan nanti section dampak gelap di beranda. Base template sendiri tetap kalem.

---

## 2. Yang bakal digambar

Total **15 frame**. Penamaan ngikutin aturan `UI-Specs.md` bagian 2.3.

| # | Nama frame | Isi | Ukuran |
|---|---|---|---|
| 1 | `Header / Visitor / Desktop` | Header buat yang belum login | 1440 x 64 |
| 2 | `Header / Member / Desktop` | Header buat Member (ada Jurnal dan avatar) | 1440 x 64 |
| 3 | `Header / Contributor / Desktop` | Sama kayak Member plus tombol "+ Buat". Admin tampilannya sama | 1440 x 64 |
| 4 | `Header / Member / Desktop / Top` | State saat halaman masih di paling atas (tanpa garis bawah) | 1440 x 64 |
| 5 | `Menu / Akun / Member` | Dropdown akun kebuka | 1440 x 360 |
| 6 | `Menu / Akun / Admin` | Dropdown akun, ada "Panel admin" | 1440 x 400 |
| 7 | `Menu / Buat / Contributor` | Dropdown "+ Buat" kebuka | 1440 x 300 |
| 8 | `Mobile Menu / Visitor` | Panel menu mobile buat Visitor | 390 x 844 |
| 9 | `Mobile Menu / Member` | Panel menu mobile buat Member | 390 x 844 |
| 10 | `Mobile Menu / Contributor` | Panel menu mobile, ada grup "Buat baru". Admin ada tambahan "Panel admin" | 390 x 844 |
| 11 | `Footer / Desktop` | Footer terang | 1440 x 345 |
| 12 | `Footer / Mobile` | Footer terang, kolom bertumpuk | 390 x tinggi ngikutin isi |
| 13 | `Template / Halaman / Desktop` | Contoh halaman: header, page header, area isi, footer | 1440 x tinggi ngikutin isi |
| 14 | `Template / Halaman / Desktop / Kosong` | Sama, tapi isinya Empty State dan ada Toast | 1440 x tinggi ngikutin isi |
| 15 | `Template / Halaman / Mobile` | Contoh halaman mobile | 390 x tinggi ngikutin isi |

---

## 3. Token tambahan

Warna dan text style lainnya ngikutin `UI-Specs.md` bagian 3. Yang baru buat base template (ditandai **baru**, nanti masuk `DESIGN-SYSTEM.md` kalau disetujui):

| Nama | Nilai | Dipakai di |
|---|---|---|
| `glass` (baru) | `white` opacity 80% plus efek **Background blur 20** | Header sticky |
| `line/glass` (baru) | `blue/200` opacity 60% | Garis bawah header waktu di-scroll |
| `Text/Nav` (baru) | 15/26, 400. Versi aktif 600 | Label menu navigasi |

Text style yang kepake: `Heading/H1` (32/40, mobile 26/34), `Body` (16/26), `Body/Strong`, `Small` (14/20), `Small/Strong`, `Text/Nav`. Footer juga pakai ukuran 13/18 buat catatan paling bawah, cukup override ukuran di layer tanpa bikin style baru.

Jarak tetap dari skala `4, 8, 12, 16, 24, 32, 48, 64`. Pengecualian cuma buat tinggi baris yang udah ada di spec (36, 40, 44, 56).

---

## 4. Komponen

Semua pakai **auto layout** dan dinamain `Kategori / Nama`.

### 4.1 Header

Nama: `Header`. Property: `role` = visitor, member, contributor, admin. `device` = desktop, mobile. `scrolled` = true, false. `active` = perangkat, diagnosa, panduan, suku-cadang, jurnal, none.

**Desktop (tinggi 64):**

| Bagian | Nilai |
|---|---|
| Latar | `glass`: isi `white` 80%, efek Background blur 20 |
| Garis bawah | 1 `line/glass`. Cuma ada kalau `scrolled = true` |
| Isi | Auto layout horizontal, rata tengah vertikal, lebar 1120 di tengah frame (margin 160) |
| Kiri | `Logo` lockup terang tinggi 28, lalu jarak 40, lalu `Nav` |
| `Nav` | Deretan `Nav / Link`, gap 4. Isi: Perangkat, Diagnosa, Panduan, Suku Cadang. Kalau `role` bukan visitor, tambah Jurnal |
| Kanan | Beda per role, lihat tabel di bawah. Didorong ke ujung kanan (spacer Fill) |

| Role | Isi bagian kanan |
|---|---|
| visitor | `Button / Ghost` sm "Masuk" (teks `blue/700`), gap 8, `Button / Primary` sm "Daftar" |
| member | `Akun Button` (lihat 4.3) |
| contributor, admin | `Button / Primary` sm "Buat" dengan ikon `plus` 20 di kiri, gap 12, lalu `Akun Button` |

**Mobile (tinggi 56):** logo lockup tinggi 28 di kiri (margin 16), Icon Button `menu` 44 x 44 di kanan (ikon 24, `ink`). Latar dan garis sama kayak desktop.

### 4.2 Nav / Link

| Bagian | Nilai |
|---|---|
| Property | `state` = default, hover, active, focus |
| Tinggi | 36 |
| Padding kiri kanan | 12 |
| Radius | 10 |
| Teks | `Text/Nav` |

| State | Tampilan |
|---|---|
| default | Tanpa isi, teks `ink` |
| hover | Isi `blue/50`, teks `ink` |
| active | Isi `blue/50`, teks `blue/700`, tebal 600 |
| focus | Garis luar 2 `blue/400`, jarak 2 |

Menu yang aktif ditandai juga lewat `aria-current="page"` di kode, jadi bukan cuma warna.

### 4.3 Akun Button dan Avatar

`Akun Button` isinya `Avatar` 32 plus ikon `chevron-down` 16 (`muted`), gap 8, bungkus pil tinggi 40 padding 4 kiri 8 kanan. Hover: isi `blue/50`. Focus: garis luar 2 `blue/400`.

`Avatar`: lingkaran, isi `blue/100`, huruf pertama username (`Small/Strong`, `blue/700`). Ukuran 32 (header) dan 40 (menu mobile).

`Badge / Role`: pil tinggi 24, padding 10 kiri kanan, teks `Small/Strong`.

| Role | Isi | Teks |
|---|---|---|
| Member | `blue/100` | `blue/700` |
| Contributor | `success` 10% | `success` |
| Admin | `blue/900` | `white` |

### 4.4 Menu dropdown (Akun dan Buat)

Nama: `Menu`. Dipakai dua kali: menu akun dan menu "+ Buat".

| Bagian | Nilai |
|---|---|
| Lebar | 240 |
| Isi dan garis | `white`, garis 1 `blue/200`, radius 14, **tanpa bayangan** |
| Padding | 8 |
| Posisi | 8 di bawah header, rata kanan sama tepi konten (x = 1280) |
| `Item` | Tinggi 40, padding kiri kanan 12, radius 10, gap 12, ikon 20 (`muted`), teks `Body` `ink` |
| `Item` hover | Isi `blue/50` |
| `Item` bahaya | Teks dan ikon `danger` (cuma "Keluar") |
| `Item` link luar | Ikon `external-link` 16 (`muted`) di kanan |
| Pemisah | Garis 1 `blue/100`, margin 4 atas bawah |

**Menu akun** dari atas ke bawah:

1. Blok identitas (tinggi 76): username (`Small/Strong`) dan `Badge / Role` di bawahnya. Bukan tombol.
2. Pemisah.
3. Profil Saya (`user`), Jurnal Saya (`notebook-pen`), Panduan Tersimpan (`bookmark`).
4. Khusus Admin: Panel admin (`shield`, link luar ke `/admin/`).
5. Pemisah.
6. Keluar (`log-out`, bahaya). Di kode ini harus tombol form POST, bukan link biasa.

**Menu buat** (Contributor dan Admin): Perangkat baru (`smartphone`), Gejala baru (`stethoscope`), Panduan baru (`book-open`), Suku cadang baru (`package`).

### 4.5 Mobile Menu

Panel penuh layar yang muncul dari kanan. Latar `white`, tanpa bayangan.

```
Panel 390 x 844 (atau lebih panjang kalau isinya banyak)
├─ Baris Atas              tinggi 56, garis bawah 1 blue/200
│   ├─ Logo lockup tinggi 28 (x 16)
│   └─ Icon Button x 44 x 44
├─ Akun                    cuma kalau login: Avatar 40, username (Body/Strong), Badge / Role
│                          padding 16, garis bawah 1 blue/100
├─ Menu Utama              baris tinggi 48: Perangkat, Diagnosa, Panduan, Suku Cadang, (Jurnal)
│                          ikon 20, teks Body. Baris aktif: isi blue/50, teks dan ikon blue/700, tebal 600
├─ Grup Akun               (login) Profil Saya, Panduan Tersimpan
├─ Grup Buat Baru          (contributor dan admin) judul "Buat baru" (Small/Strong, muted) lalu 4 item
├─ Panel admin             (admin) link luar
├─ Keluar                  (login) warna danger
└─ Aksi                    (visitor) Button / Primary md fullWidth "Daftar", lalu Button / Secondary md fullWidth "Masuk"
```

Antar grup dipisah garis 1 `blue/100` dengan margin 8. Tinggi panel ngikutin isi, minimal 844.

### 4.6 Footer

Nama: `Footer`. Property: `device` = desktop, mobile.

| Bagian | Desktop | Mobile |
|---|---|---|
| Latar | `surface`, garis atas 1 `blue/200` | sama |
| Padding | 48 atas, 32 bawah, margin kiri kanan ngikutin konten (160) | 32 atas, margin 24 |
| Blok merek | Logo lockup terang tinggi 28 plus tagline "Repair first, discard last." (`Small`, `muted`) | sama, di paling atas |
| Kolom link | Tiga kolom (Jelajahi, Akun, Tentang) mulai x = 620, lebar 200 per kolom. Judul `Small/Strong` `ink`, link `Small` `muted`, jarak antar link 12 | Bertumpuk satu kolom, jarak antar kolom 24 |
| Pemisah | Garis 1 `blue/200`, lebar penuh konten | sama |
| Catatan data | "Sebagian data perangkat dan panduan berasal dari iFixit, dipakai di bawah lisensi CC BY-NC-SA." ukuran 13/18, `muted` | dua baris |
| Catatan tim | "Kelompok 1 · Pemrograman Berbasis Platform · Fasilkom UI · 2026" ukuran 13/18, `muted` | dua baris |

Link footer: hover jadi `ink`, focus garis luar 2 `blue/400`.

| Kolom | Isi link |
|---|---|
| Jelajahi | Perangkat, Diagnosa, Panduan, Suku Cadang |
| Akun | Masuk, Daftar, Jurnal (buat yang udah login, "Masuk" dan "Daftar" diganti "Profil Saya" dan "Keluar") |
| Tentang | Tentang Sparein, GitHub |

### 4.7 Page Container, Page Header, dan Breadcrumb

Ini bagian `body` template yang dipakai semua halaman modul.

| Bagian | Nilai |
|---|---|
| Latar halaman | `surface` |
| Lebar isi | Maks 1120, di tengah. Di bawah 1200 jadi margin 32 kiri kanan, di mobile 16 |
| Jarak dari header | 32 (desktop), 24 (mobile) |
| Jarak ke footer | 64 (desktop), 48 (mobile) |

`Breadcrumb`: teks `Small`. Item terakhir `Small/Strong` `ink`, sisanya `muted`. Pemisah ikon `chevron-right` 16, margin 6 kiri kanan. Di mobile cuma satu tingkat ke atas: ikon `chevron-right` diputar 180 derajat plus nama induk.

`Page Header` dari atas ke bawah:

1. Breadcrumb (kalau ada), tinggi 20, jarak 8 ke bawah.
2. Baris judul: `Heading/H1` di kiri, grup tombol aksi di kanan (rata atas sama judul). Di mobile tombol turun ke bawah deskripsi dan jadi fullWidth.
3. Deskripsi satu baris, `Body` `muted`, jarak 8 dari judul (opsional).
4. Jarak 32 ke area isi.

### 4.8 Toast area

Toast ngikutin komponen `Toast` di `UI-Auth-Build.md`. Posisi di base template: pojok kanan atas, 16 di bawah header, 16 dari tepi kanan (lebar 360). Di mobile: tengah atas, 8 di bawah header, lebar Fill dikurangi margin 16.

Di kode, toast diisi dari Django `messages`, jadi tiap level (`success`, `error`, `info`) punya varian.

### 4.9 Empty State

`blue/50`, radius 14, tanpa garis, padding 40 atas bawah. Isi rata tengah: ikon `inbox` 48 (`blue/400`), jarak 16, satu kalimat `Body` `ink`, jarak 16, satu `Button / Primary` md. Sesuai komponen C39 di `UI-Specs.md`, cuma paddingnya dilonggarin.

---

## 5. Frame dan struktur layer

### 5.1 Frame template halaman (desktop)

`Template / Halaman / Desktop`. Lebar 1440, tinggi ngikutin isi (minimal 900 biar footer tetap di bawah).

```
Frame 1440, isi surface, vertikal, gap 0
├─ Header                       sticky, tinggi 64
├─ Main                         vertikal, padding 32 atas, 64 bawah, isi di tengah lebar 1120
│   ├─ Page Header              (lihat 4.7)
│   └─ Block Content            kotak putus-putus penanda area {% block content %}
│       └─ (isi contoh: tiga kartu placeholder)
└─ Footer
```

`Block Content` itu cuma penanda di Figma (garis putus-putus `blue/300`), bukan elemen yang dikoding. Isi contohnya tiga kartu placeholder: kartu putih, garis `blue/200`, radius 14, gambar `blue/50`, dua baris skeleton `blue/100`.

Frame `... / Kosong` ngeganti isi `Block Content` jadi satu `Empty State` selebar 1120 (tinggi 260), dan nambah satu `Toast` success di pojok kanan atas.

### 5.2 Frame template halaman (mobile)

Sama, tapi lebar 390, header 56, margin 16 kiri kanan, kartu satu kolom, dan Page Header ngikutin aturan mobile di 4.7. Footer versi mobile.

### 5.3 Frame dropdown

`Menu / Akun / Member` dan kawan-kawannya: taruh `Header` role yang sesuai di atas, lalu `Menu` kebuka di bawahnya, rata kanan sama tepi konten. Latar frame `surface`. Frame ini buat dokumentasi, jadi nggak perlu isi halaman di belakangnya.

---

## 6. Sambungan prototype

| Dari | Elemen | Ke | Animasi |
|---|---|---|---|
| `Header / Member` | `Akun Button` | `Menu / Akun / Member` | Instant (Open overlay kalau mau) |
| `Header / Contributor` | Tombol "+ Buat" | `Menu / Buat / Contributor` | Instant |
| Frame menu kebuka | Klik di luar menu | Frame header tanpa menu | Instant |
| Header mobile (semua) | Icon Button `menu` | `Mobile Menu` sesuai role | Move in dari kanan, 300 ms, ease out |
| `Mobile Menu` (semua) | Icon Button `x` | Frame sebelumnya (Back) | Move out ke kanan, 300 ms |
| `Header / Visitor` | "Masuk" dan "Daftar" | Frame P01 dan P02 di `UI-Auth-Build.md` | Instant |

---

## 7. Catatan buat base.html

Ini bahan buat pas nanti dikoding (jangan dikerjain sekarang, dikoding setelah desainnya kelar). Nyentuh `core/`, jadi butuh dua approval.

**Struktur yang diusulin:**

```
core/templates/
├─ base.html               kerangka: skip link, header, area toast, main, footer
└─ partials/
    ├─ header.html         header desktop dan mobile, isinya beda per role
    └─ footer.html
```

Block yang udah ada di `base.html`: `title`, `content`, `extra_js`. Usulan tambahan: `page_header` (buat breadcrumb dan judul) dan `extra_css`. Modul lain tetap cuma ngisi block, bukan ngedit `base.html`.

**Ikon dipanggil dari file, bukan SVG inline.** Jangan nulis `<svg>` langsung di HTML. Simpen ikon sebagai file `.svg` di `core/static/core/icons/`, terus panggil lewat `<img src="{% static 'core/icons/nama.svg' %}" alt="" width="20" height="20">`. Aturannya:

- Warna ikon udah ada di dalam file, jadi namanya ditambah warna: `eye-muted.svg`, `circle-alert-danger.svg`, `info-blue.svg`. Butuh warna lain, bikin file baru.
- Ikon yang cuma hiasan dikasih `alt=""`. Ikon yang jadi satu-satunya isi tombol, kasih `aria-label` di tombolnya.
- Ikon yang udah kepake di halaman auth ada di folder yang sama, tinggal dipakai ulang. Sisanya (misal `user`, `bookmark`, `log-out`) bisa diambil dari mockup di `design/base/` atau dari Lucide, lalu disimpen sebagai file.

**Header sticky kaca blur (CSS):**

```css
.site-header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: rgb(255 255 255 / 0.8);
  border-bottom: 1px solid transparent;
  transition: border-color 150ms ease;
}
@supports (backdrop-filter: blur(1px)) {
  .site-header { backdrop-filter: saturate(180%) blur(20px); }
}
.site-header.is-scrolled { border-bottom-color: rgb(176 215 251 / 0.6); }
```

Kalau browser nggak dukung `backdrop-filter`, header tetap kebaca karena fallback-nya putih 80%. Buat ngasih class `is-scrolled`, cukup pakai `IntersectionObserver` di sentinel kecil di atas halaman, atau event `scroll` sederhana.

**Beda isi header per role:**

| Kondisi | Template |
|---|---|
| Belum login | `{% if not user.is_authenticated %}` tombol Masuk dan Daftar |
| Login | `{% if user.is_authenticated %}` avatar, menu akun, link Jurnal |
| Contributor atau Admin | Perlu penanda di template. Fungsi `is_contributor` di `core/permissions.py` belum bisa dipanggil dari template, jadi butuh context processor kecil atau akses `user.profile.role`. Ini bagian backend, dibahas terpisah |

**Menu aktif:** butuh tahu halaman sekarang. Cara paling gampang pakai `request.resolver_match.namespace` (misal `devices`), asal `django.template.context_processors.request` aktif di settings.

**Aksesibilitas:**

- Link "Lewati ke konten utama" di paling atas, muncul pas di-Tab.
- `<header>`, `<nav aria-label="Utama">`, `<main id="konten">`, `<footer>`.
- Menu aktif pakai `aria-current="page"`.
- Tombol akun pakai `aria-expanded` dan `aria-haspopup="menu"`.
- Area toast pakai `role="status"` dengan `aria-live="polite"`.
- Semua yang bisa diklik punya focus ring 2 `blue/400`.

---

## 8. Yang beda dari spec lama

| Komponen | Di `UI-Specs.md` | Di lembar ini |
|---|---|---|
| C28 Header | Putih solid, menu aktif teks `blue/500` plus garis bawah 2 | Kaca blur 80%, menu aktif berupa pil `blue/50` dengan teks `blue/700` |
| C34 Footer | `blue/950` gelap | `surface` terang |
| C30 Account Menu | Item 40, tanpa pengaturan hover jelas | Hover `blue/50`, blok identitas tinggi 76 |
| C28 tombol kanan | Tombol "+ Buat" `Primary` md | `Primary` sm dengan ikon `plus` |

Kalau disetujui, tiga komponen itu perlu diupdate di `UI-Specs.md`. Frame P05 di `design/auth/` juga masih pakai header solid dan footer gelap, nanti di-generate ulang biar sama.

---

## 9. Hal yang masih perlu dibahas

| # | Pertanyaan | Tebakan sementara |
|---|---|---|
| B1 | Perlu kolom pencarian di header? (Apple punya ikon cari) | Belum, pencarian ada di halaman Katalog dan Beranda |
| B2 | Link "Tentang Sparein" di footer mau ke mana? | Arahin ke README di GitHub dulu |
| B3 | Menu Jurnal buat Visitor ditampilin atau disembunyiin? | Disembunyiin, cuma muncul buat yang login |
| B4 | Perlu mode gelap? | Nggak, di luar cakupan versi ini |
| B5 | Nama tombol di header buat Contributor: "Buat" atau "+ Buat"? | "Buat" dengan ikon plus |

---

## 10. Checklist sebelum selesai

- [ ] 15 frame ada dengan nama sesuai aturan.
- [ ] Header pakai fill `white` 80% dan efek Background blur 20, bukan warna solid.
- [ ] State `scrolled` true dan false sama-sama ada.
- [ ] Menu dropdown **nggak** punya bayangan, cuma garis 1 `blue/200`.
- [ ] Semua warna pakai Color Style, semua teks pakai Text Style.
- [ ] Semua jarak dari skala `4, 8, 12, 16, 24, 32, 48, 64` (kecuali tinggi baris yang udah di spec).
- [ ] Menu aktif nggak cuma ngandelin warna (ada tebal 600 dan di kode `aria-current`).
- [ ] Item "Keluar" warna `danger`, ada ikon dan teks.
- [ ] Kontras teks lolos 4.5:1, terutama `muted` di atas `surface` dan `blue/700` di atas `blue/50`.
- [ ] Layer dinamain jelas (`Header`, `Nav`, `Akun Button`, `Menu`, `Footer`, `Page Header`, `Block Content`).
- [ ] Ukuran target sentuh di mobile minimal 44.
- [ ] Sudah di-review satu anggota lain lewat komentar Figma.
