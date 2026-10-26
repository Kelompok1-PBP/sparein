# Panduan Modul Diagnosa (M2)

Dokumen ini buat belajar ulang dan presentasi modul `diagnostics`: gimana user memilih perangkat, mencentang gejala, lalu dapat daftar kemungkinan penyebab yang berurutan. Kontrak resminya ada di [`MODULES.md`](MODULES.md), tampilan acuannya di mockup `docs/design/pages/diagnostics/` (P20, P21, P22).

## Daftar isi

1. [Gambaran besar](#1-gambaran-besar)
2. [Model dan kenapa ada Cause](#2-model-dan-kenapa-ada-cause)
3. [Cara hasil diranking](#3-cara-hasil-diranking)
4. [Rute dan hak akses](#4-rute-dan-hak-akses)
5. [Alur AJAX](#5-alur-ajax)
6. [Struktur file](#6-struktur-file)
7. [Cara jalanin dan ngetes](#7-cara-jalanin-dan-ngetes)
8. [Yang sengaja ngga dibikin](#8-yang-sengaja-ngga-dibikin)

---

## 1. Gambaran besar

Alurnya: **pilih perangkat, centang gejala, lihat kemungkinan masalah**. Halaman `/diagnostics/` punya dua keadaan:

| Keadaan | URL | Isi |
|---|---|---|
| A, belum pilih perangkat | `/diagnostics/` | Kolom cari perangkat (AJAX ke `/api/devices/`) dan ubin kategori yang membuka `/devices/?category=` |
| B, perangkat sudah dipilih | `/diagnostics/?device=iphone-17` | Daftar gejala di kiri, hasil di kanan |

Modul ini cuma bergantung ke `core` dan `devices`. Perangkat diambil lewat `devices.selectors` (`get_device_or_404`, `get_device_qs`), tidak pernah query langsung ke tabel `devices`.

## 2. Model dan kenapa ada Cause

| Model | Fungsi |
|---|---|
| `Symptom` | Gejala milik satu perangkat. `severity`: `low` (Ringan), `medium` (Sedang), `high` (Parah) |
| `Cause` | Kemungkinan penyebab, nyambung ke banyak gejala (M2M) |
| `DiagnosisSession` | Satu kali diagnosa: siapa (boleh anonim), perangkat apa, gejala apa saja |
| `DiagnosisResult` | Isi hasil sebuah sesi: penyebab, tingkat kemungkinan, catatan |

Kontrak awal cuma punya `Symptom` dan `DiagnosisResult.symptom`. Padahal desain menampilkan **penyebab** ("Baterai sudah aus") yang berbeda dari gejala ("Baterai cepat habis"). Jadi ditambah model `Cause`, dan `DiagnosisResult` menunjuk ke `Cause`, bukan `Symptom`. Perubahan ini cuma di dalam app `diagnostics`, jadi modul lain tidak terdampak. `MODULES.md` sudah diperbarui.

`Cause` tidak punya form publik. Isinya dikelola admin lewat Django admin (`/admin/`).

## 3. Cara hasil diranking

Logikanya ada di satu fungsi murni, `diagnostics/services.py::rank_causes`.

Untuk tiap penyebab milik perangkat, hitung **berapa persen gejalanya yang dicentang**:

| Persentase gejala cocok | Tingkat |
|---|---|
| 2/3 atau lebih | Tinggi |
| 1/3 sampai kurang dari 2/3 | Sedang |
| Kurang dari 1/3 | Rendah |

Penyebab tanpa gejala yang cocok tidak ditampilkan. Urutan: persentase paling besar dulu, lalu jumlah gejala cocok terbanyak, lalu urut abjad judul.

Contoh: penyebab "Baterai aus" punya gejala A dan B. Kalau user mencentang A dan B hasilnya Tinggi. Kalau cuma A, hasilnya Sedang (1 dari 2 = 50%).

## 4. Rute dan hak akses

| Aksi | Rute | Siapa |
|---|---|---|
| Diagnosa | `GET /diagnostics/` | Semua |
| Detail gejala | `GET /diagnostics/<slug>/` | Semua |
| Tambah gejala | `/diagnostics/symptoms/create/` | Contributor ke atas |
| Ubah gejala | `/diagnostics/<slug>/edit/` | Contributor pembuat, atau Admin |
| Hapus gejala | `/diagnostics/<slug>/delete/` | Admin (lewat POST) |
| JSON gejala | `GET /api/symptoms/?device=&severity=` | Semua |
| JSON hasil | `GET /api/diagnose/?device=&symptom=` | Semua |
| Simpan hasil | `POST /api/diagnose/save/` | Semua |
| Riwayat diagnosa | `GET /diagnostics/my/sessions/` | Login, cuma milik sendiri |

Visitor yang buka form dilempar ke halaman login, Member kena 403. Pengecekan ada di view, memakai `core.permissions`.

## 5. Alur AJAX

```
User centang gejala
  -> JS tampilkan 3 skeleton di panel hasil
  -> GET /api/diagnose/?device=...&symptom=1&symptom=2
  -> server hitung rank_causes, balikin JSON (tidak menulis ke database)
  -> JS ganti skeleton dengan daftar hasil, update jumlah hasil
```

Dua hal yang sengaja dibikin begini:

- **Menghitung tidak menulis database.** Kalau tiap centang bikin sesi baru, visitor anonim bisa ngebanjirin tabel. Sesi baru disimpan waktu user menekan tombol **Simpan hasil** (`POST /api/diagnose/save/`).
- **Tetap jalan tanpa JavaScript.** Form gejala adalah form GET biasa. Server juga merender hasil dari `?symptom=` yang ada di URL. Tanpa JS, tombol "Lihat kemungkinan" muncul sebagai gantinya.

Di mobile, setelah ada hasil muncul bar biru menempel di bawah layar ("2 kemungkinan ditemukan · Lihat") yang membawa user ke panel hasil.

Panel hasil punya `aria-live="polite"` supaya pembaca layar menyebut hasil baru. Tingkat kemungkinan selalu ditulis dengan kata ("Kemungkinan tinggi"), bukan cuma bar atau warna.

## 6. Struktur file

```
diagnostics/
├─ models.py        Symptom, Cause, DiagnosisSession, DiagnosisResult
├─ selectors.py     get_symptoms_for_device (diekspor), get_symptom_qs, get_symptom_or_404
├─ services.py      rank_causes, save_session
├─ forms.py         SymptomForm, SeverityRadio (radio keparahan tampil sebagai kartu)
├─ views.py, urls.py
├─ admin.py
├─ fixtures/seed_diagnostics.json   data contoh iPhone 17 dan MacBook Air 13"
├─ static/diagnostics/              diagnostics.css, diagnostics.js
├─ templates/diagnostics/           diagnose, _results, history, symptom_detail, symptom_form, confirm_delete, widgets/
└─ tests.py
```

Markup hasil di `_results.html` harus sama dengan yang dibuat `diagnostics.js`. Kalau salah satu diubah, ubah dua-duanya (pola yang sama dengan kartu perangkat di `devices`).

## 7. Cara jalanin dan ngetes

```powershell
python manage.py migrate
python manage.py loaddata seed_devices seed_diagnostics
python manage.py runserver
```

Buka `http://127.0.0.1:8000/diagnostics/?device=iphone-17`. Buat nyoba tambah gejala, ubah `UserProfile.role` akunmu jadi `CONTRIBUTOR` lewat `/admin/`.

Sebelum bikin PR:

```powershell
ruff check .
python manage.py makemigrations --check --dry-run
python manage.py test
```

Kode ditulis test-first. `tests.py` mencakup model, selector, ranking, halaman, JSON, simpan sesi, dan keempat operasi CRUD beserta batas akses per role.

## 8. Yang sengaja ngga dibikin

- **Panduan terkait per gejala.** `RepairGuide` belum punya FK `symptom` (lihat `guides/README.md`, dan Q10 di UI Specs). Untuk sementara tombol "Lihat panduan terkait" membuka daftar panduan yang difilter ke perangkat.
- **Form untuk Cause.** Cukup lewat Django admin dulu.
- **Hapus riwayat diagnosa.** Halaman riwayat baru bisa melihat dan mengulang diagnosa.
