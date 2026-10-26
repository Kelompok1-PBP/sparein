# Mockup SVG

Mockup visual buat dibuka di Figma, dibikin dari spesifikasi di [`UI-Specs.md`](../UI-Specs.md) dan [`UI-Auth-Build.md`](../UI-Auth-Build.md). File di sini cuma referensi tampilan jadi, bukan sumber kebenaran. Kalau beda sama dokumen spesifikasi, dokumennya yang menang.

## Isi

| Folder | Isi |
|---|---|
| `auth/` | Semua 16 frame di `UI-Auth-Build.md`: Masuk (P01, termasuk state dari konten terkunci), Daftar (P02), Akses ditolak (P05), Mobile Menu Visitor, dan Toast. Desktop 1440 dan mobile 390 |
| `base/` | Kerangka halaman di `UI-Base-Build.md`: header per role (desktop), dropdown akun dan buat, mobile menu, footer terang, dan template halaman (desktop, desktop kosong, mobile). Total 15 file |

Penamaan file di `auth/`: `<kode halaman>-<nama>-<ukuran>-<state>.svg`, contoh `p01-masuk-desktop-default.svg`. Frame pendukung yang bukan halaman namanya `mobile-menu-visitor-mobile.svg` dan `toast-auth-desktop.svg`. Di `base/` namanya ngikutin isinya, contoh `header-desktop-member.svg` atau `template-halaman-mobile.svg`.

## Cara import ke Figma

1. Install font **Inter** dulu di komputermu, biar teks ngga ganti font.
2. Drag file `.svg` ke kanvas Figma. Hasilnya satu frame berisi vektor dan layer teks.
3. Nama layer udah dirapihin (`Panel Ilustrasi`, `Panel Form`, `Form Wrap`, `Heading Group`, dan seterusnya) supaya gampang disamain sama struktur di build sheet.

## Yang ngga ikut ke-import

Auto layout, komponen beserta variannya, Color Style, Text Style, dan sambungan prototype. SVG cuma bentuk statis. Bagian itu tetap dibangun manual di Figma ngikutin `UI-Auth-Build.md`, dengan SVG ini sebagai patokan visual.

## Catatan

- Efek **Background blur** di header (`base/`) ngga ikut ke SVG. Tambahin manual di Figma: fill `white` 80% plus efek Background blur 20.
- Teks di SVG ditulis per baris (ngga ada auto wrap), jadi kalau font berbeda, lebar teks bisa sedikit geser.
- Ilustrasi di dalam frame sama dengan `docs/brand/auth-illustration.svg` dan `auth-illustration-banner.svg`. Kalau ilustrasinya diganti, frame di sini perlu digenerate ulang.
- Ikon (mata, peringatan, panah) dari Lucide (lisensi ISC).
