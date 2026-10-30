# M3 — Repair Guide

## Identitas dan cakupan

- **Purpose:** mengelola panduan perbaikan, langkah, peringatan keselamatan, filter, dan impor panduan iFixit.
- **Owner:** Hanna Zerlina Razaq Putri Wicaksono (`hannazerlina`).
- **Versi dokumen:** 1.0, 30 Oktober 2026; berdasarkan kode lokal pada commit `2db1221`. Ini versi dokumentasi, bukan versi rilis aplikasi.
- **Dependencies:** Django, `core` untuk autentikasi/role/layout, `devices` untuk perangkat dan selector, `requests` untuk HTTP, Django cache untuk respons iFixit.
- **Konsumen:** `journal` merujuk `RepairGuide` melalui foreign key.
- **Batas implementasi:** field `symptom` yang direncanakan dalam `MODULES.md` belum ada pada model/migrasi guides. Keberadaan app diagnostics tidak otomatis mengaktifkan relasi tersebut.

Dokumen ini menjelaskan perilaku yang sudah diimplementasikan. Rencana umum antarmodul berada di [MODULES.md](../MODULES.md).

## Publik dan internal

Kontrak Python lintas modul adalah model `RepairGuide` dan selector `get_guide_qs` / `get_guide_or_404`. Endpoint HTTP di bawah dapat dikonsumsi sesuai hak akses. Helper `visible_guides`, permission, form, editor, dan importer merupakan implementasi internal M3; jangan jadikan helper internal sebagai dependency modul lain tanpa koordinasi.

**Penting:** dua selector publik tidak memfilter draf atau pengguna. Pemanggil wajib menerapkan aturan akses sebelum menampilkan hasil ke publik. View bawaan memakai `visible_guides(user)` untuk itu.

## Hak akses

| Operasi | Pengunjung | Member | Contributor | Admin/superuser |
|---|---|---|---|---|
| Membaca panduan terbit | Ringkasan, metadata, judul langkah, peringatan | Termasuk detail langkah | Termasuk detail langkah | Termasuk detail langkah |
| Membaca draf | Tidak | Draf sendiri | Draf sendiri | Semua |
| Membuat / impor | Tidak | Tidak | Ya | Ya |
| Mengedit | Tidak | Tidak | Panduan sendiri | Semua |
| Menghapus | Tidak | Panduan sendiri jika menjadi penulis | Panduan sendiri | Semua |

Peringatan selalu ditampilkan pada panduan yang boleh dibaca pengguna; draf tetap mengikuti aturan visibilitas. Kolom `GuideStep.detail` tidak diambil oleh query langkah untuk pengunjung di halaman detail dan API. Semua POST memakai perlindungan CSRF Django.

## Kontrak data model

Semua model memiliki `id: BigAutoField` sebagai primary key otomatis. Selain field yang ditandai nullable, kolom tidak menerima NULL. `blank=True` berarti input boleh kosong, berbeda dari NULL. Validator/choices dijalankan melalui form atau validasi model; `save()` biasa tidak otomatis menjalankan `full_clean()`.

### RepairGuide

| Field | Tipe | Nullable / constraint |
|---|---|---|
| device | FK Device | Tidak; PROTECT, related name `repair_guides` |
| author | FK AUTH_USER_MODEL | Tidak; PROTECT, related name `repair_guides` |
| title | string | Maks. 200, wajib pada form |
| slug | slug string | Maks. 220, unik; dibuat otomatis saat create |
| summary | text | Wajib pada form |
| difficulty | string | Maks. 20; `Very easy`, `Easy`, `Moderate`, `Difficult`, `Very difficult` |
| time_required_minutes | positive integer | Validator minimal 1 |
| tools | text | Boleh kosong; satu alat per baris |
| ifixit_guideid | positive integer | Nullable, unik jika terisi; impor memerlukan integer > 0 |
| source_author | string | Maks. 200, boleh kosong |
| published | boolean | Default false |

Urutan default: `title`, lalu primary key. Slug menggunakan judul dan suffix UUID; edit judul tidak mengganti slug.

### GuideStep

| Field | Tipe | Nullable / constraint |
|---|---|---|
| guide | FK RepairGuide | Tidak; CASCADE, related name `steps` |
| order | positive integer | Validator minimal 1; pasangan `(guide, order)` unik di database |
| title | string | Maks. 200, wajib |
| detail | text | Wajib; hanya dikirim ke pengguna login |
| image_url | URL string | Maks. 200, boleh kosong |

Urutan default: `order`, lalu primary key. Form editor memerlukan 1–100 langkah aktif. ID baris langkah tidak stabil saat edit karena baris dibuat ulang.

### SafetyWarning

| Field | Tipe | Nullable / constraint |
|---|---|---|
| guide | FK RepairGuide | Tidak; CASCADE, related name `warnings` |
| level | string | Maks. 10; `info`, `caution`, `danger` |
| message | text | Wajib |

Form editor mengizinkan 0–50 peringatan. Batas 50 merupakan batas form, bukan constraint database/importer. ID baris peringatan juga dibuat ulang saat edit.

## Kontrak selector dan permission

| Signature | Parameter / return | Precondition → postcondition | Error / side effect |
|---|---|---|---|
| `get_guide_qs(*, device=None, difficulty=None, max_time=None)` | ID perangkat, string difficulty, batas menit; return `QuerySet[RepairGuide]` lazy | Nilai sudah divalidasi pemanggil → filter yang bernilai truthy diterapkan; device/author memakai select_related | Tidak menulis; input salah dapat menimbulkan error ORM, bukan error form; tidak melakukan HTTP/cache |
| `get_guide_or_404(slug: str)` | Slug; return `RepairGuide` | Slug valid → satu objek termasuk kemungkinan draf | `Http404` jika tidak ada; read database, tanpa write |
| `visible_guides(user)` (internal) | User/AnonymousUser; return QuerySet | Role tersedia dari core → admin semua, login published atau milik sendiri, pengunjung published | Tidak menulis; bukan pemeriksa akses untuk data yang sudah diambil lewat selector lain |
| `can_create(user)` (internal) | User → bool | Role core valid → true untuk Contributor/Admin | Tanpa write |
| `can_edit(user, guide)` (internal) | User, RepairGuide → bool | Objek ada → admin atau contributor penulis | Tanpa write |
| `can_delete(user, guide)` (internal) | User, RepairGuide → bool | Objek ada → admin atau penulis yang login | Tanpa write |

Read selector idempotent selama data tidak berubah. QuerySet dieksekusi ketika dievaluasi; tidak ada transaksi eksplisit pada selector.

## Kontrak endpoint dan view

Semua path HTML menggunakan prefix `/guides/`; API dipasang terpisah di `sparein/urls.py`. Parameter `slug` merujuk slug panduan. Method selain yang tercantum menghasilkan 405.

| View / route | Input dan precondition | Return / postcondition | Error dan side effect |
|---|---|---|---|
| `guide_list(request)` — GET `/guides/` | Opsional `device`, `difficulty`, `max_time` | HTML daftar maksimal 100 panduan yang terlihat, terurut title/pk | Filter invalid: HTML 200 dengan hasil kosong; tidak write |
| `guide_api(request)` — GET `/api/guides/` | Filter sama dengan daftar | JSON 200, DTO di bawah | Filter invalid 400; tidak write |
| `guide_detail(request, slug)` — GET `/guides/<slug>/` | Panduan ada dan terlihat pengguna | HTML 200; langkah sesuai autentikasi | Tidak ada/tidak terlihat: 404; tidak write |
| `guide_create(request)` — GET/POST `/guides/create/` | Contributor/Admin; POST form dan formset valid | GET form 200; POST sukses JSON 201 atau redirect 302 ke detail | 403 tanpa izin; 400 validasi; write guide, steps, warnings secara atomic |
| `guide_edit(request, slug)` — GET/POST `/guides/<slug>/edit/` | Panduan terlihat; admin atau contributor penulis | GET form 200; POST sukses JSON 200 atau redirect 302 | 404 tidak terlihat; 403 tanpa izin; 400 validasi; update parent, buat ulang children secara atomic |
| `guide_delete(request, slug)` — GET/POST `/guides/<slug>/delete/` | Panduan terlihat; admin atau penulis login | GET konfirmasi 200 tanpa hapus; POST JSON 200 atau redirect 302 ke daftar | 404/403; POST menghapus guide dan children; relasi jurnal saat ini SET_NULL |
| `guide_import(request)` — GET/POST `/guides/import/` | Contributor/Admin; POST `guide_id` integer >0, `device` valid, `minutes` opsional >0 | GET form 200; POST sukses redirect 302 ke edit draf | 403 tanpa izin; 400 form/import error; HTTP/cache iFixit dan write atomic |

Filter HTTP: `device` dan `max_time` integer minimal 1, `difficulty` salah satu pilihan model. ID perangkat yang valid secara angka tetapi tidak ada menghasilkan hasil kosong. API tidak menyediakan offset/pagination; `limit: 100` adalah batas hasil, bukan total jumlah panduan.

### Input create/edit dan negosiasi respons

Kirim form-encoded POST, bukan JSON body. Field guide: `device`, `title`, `summary`, `difficulty`, `time_required_minutes`, `tools`, `published`. Sertakan management form dengan prefix `steps` dan `warnings` (`TOTAL_FORMS`, `INITIAL_FORMS`), lalu field baris seperti `steps-0-order`, `steps-0-title`, `steps-0-detail`, `steps-0-image_url`, `warnings-0-level`, `warnings-0-message`. Saat edit, kirim ID baris existing dan initial count yang benar; gunakan `DELETE` bila menghapus baris.

Header `Accept: application/json` memilih JSON untuk sukses/error editor dan delete serta penolakan izin. Endpoint impor tetap memberikan HTML/redirect untuk sukses dan kesalahan form/import. CSRF wajib untuk POST, termasuk saat meminta JSON.

### DTO respons API

```json
{
  "results": [{
    "id": 1,
    "title": "Panduan contoh",
    "slug": "panduan-contoh-abc123",
    "summary": "Ringkasan",
    "device": 1,
    "device_name": "Perangkat contoh",
    "difficulty": "Easy",
    "time_required_minutes": 10,
    "url": "/guides/panduan-contoh-abc123/",
    "warnings": [{"level": "caution", "message": "Peringatan contoh"}],
    "steps": [{"order": 1, "title": "Langkah contoh", "image_url": ""}]
  }],
  "limit": 100
}
```

`id`, `device`, `order`, durasi dan limit adalah integer; field teks adalah string; warnings/steps/results adalah array yang dapat kosong sesuai data. Untuk pengguna login setiap step juga berisi `detail: string`; untuk pengunjung key tersebut tidak ada, bukan null. DTO list tidak mengekspor source_author, tools, published, atau author.

Sukses create/edit: `{"id": 1, "url": "/guides/<slug>/"}`. Sukses delete: `{"deleted": true}`.

### Format error yang benar-benar tersedia

Belum ada satu error envelope global yang seragam untuk semua route.

| Kondisi | Bentuk respons | Retry |
|---|---|---|
| Filter API invalid | 400 `{"errors": {"field": [{"message": "...", "code": "..."}]}}` | Perbaiki input dahulu |
| Editor invalid, Accept JSON | 400 `{"errors": {"guide": {}, "steps": [], "step_errors": [], "warnings": [], "warning_errors": []}}`; isi field berupa pesan validasi | Perbaiki input/formset dahulu |
| Permission ditolak, Accept JSON | 403 `{"error": "Akses ditolak."}` | Memerlukan perubahan akun/izin |
| Permission ditolak, HTML | 403 teks `Akses ditolak.` | Memerlukan perubahan akun/izin |
| Panduan tidak ada/tidak terlihat | 404 dari Django, tidak dijamin JSON walaupun Accept JSON | Verifikasi URL/akses dahulu |
| CSRF / method salah | 403 / 405 dari Django; tidak memakai envelope editor | Perbaiki token/method |
| Impor invalid/gagal | 400 HTML dengan error form | Sesuai penyebab impor di bawah |

## Kontrak impor iFixit

### `fetch_guide(guide_id) -> dict` (internal)

Precondition: ID bisa dikonversi menjadi integer; entry point form memvalidasi >0. Membaca cache `ifixit-guide-{guide_id}` dahulu. Cache miss melakukan GET `/api/2.0/guides/{id}` dengan timeout 20 detik, lalu memeriksa response dict dan kesesuaian guideid. Sukses menyimpan respons di cache selama 3600 detik; tidak menulis database.

`ImportFailure` untuk request/HTTP/JSON error dan respons tidak valid. Timeout/gangguan sementara dapat dicoba ulang secara manual; HTTP permanen seperti ID salah harus diperbaiki dulu. Pesan wrapper tidak menyediakan kode retry terstruktur dan tidak ada retry otomatis. Respons cache yang ada digunakan langsung.

### `import_guide(data, *, device, author, minutes=None) -> RepairGuide` (internal)

Precondition: data dict terstruktur seperti respons iFixit; device dan author tersimpan. Pemanggil bertanggung jawab atas role penulis dan validasi parameter. Form memvalidasi minutes >0; command CLI hanya mem-parsing integer, sehingga pemanggil tidak boleh mengandalkan service untuk seluruh validasi form.

Postcondition: satu panduan **draf**, langkah berurutan mulai 1, peringatan umum sumber dan peringatan dari bullet caution/warning/note; source_author tersimpan. Durasi memakai minutes jika diberikan, atau pembulatan ke atas detik sumber menjadi menit. Teks dibersihkan dari tag HTML, judul/atribusi dibatasi 200 karakter; gambar pertama diterima hanya jika URL HTTPS valid dan panjang <=200. Gambar tidak diunduh.

Error `ImportFailure`: ID salah/duplikat, difficulty tidak didukung, durasi tidak tersedia, judul/langkah kosong, jumlah langkah >100, atau teks langkah kosong. Perbaiki input dahulu; impor ID duplikat harus membuka data existing. Struktur nested sumber yang tidak sesuai asumsi dapat menimbulkan exception Python; tidak semua bentuk sumber rusak dibungkus sebagai ImportFailure. Constraint database tetap dapat memunculkan error database, termasuk race antarimpor.

Transaksi `transaction.atomic` membatalkan seluruh penulisan jika gagal. Cache/network berada pada fetch terpisah dan tidak ikut rollback. Tidak ada event domain atau antrean pekerjaan khusus.

### Command

```sh
python manage.py import_ifixit_guide GUIDE_ID --device DEVICE_ID --author USERNAME
# Opsional ketika durasi sumber tidak tersedia:
python manage.py import_ifixit_guide GUIDE_ID --device DEVICE_ID --author USERNAME --minutes 30
```

`Command.handle(guide_id, device, author, minutes=None, **options)` memvalidasi user Contributor/Admin dan perangkat; mengembalikan tanpa nilai serta mencetak URL edit draf saat sukses. User/perangkat salah atau ImportFailure menjadi `CommandError`. Exception lain tidak dinormalisasi. Tidak mengimpor daftar katalog sekaligus; pemanggil memilih satu ID panduan.

## Idempotency, transaksi, side effect

- GET daftar/detail/API hanya membaca database. Hasil dapat berubah setelah perubahan data.
- POST create tidak idempotent: pengulangan dapat menghasilkan panduan lain dengan slug baru; tidak ada idempotency key.
- POST edit mengganti parent dan membuat ulang children dalam satu transaksi. Isi yang sama dapat menghasilkan isi akhir sama tetapi ID children berbeda; jangan mengandalkan idempotency identitas child.
- POST delete menghapus parent beserta langkah/peringatan menggunakan mekanisme penghapusan Django; pengulangan URL yang sama menghasilkan 404. Tidak ada atomic block khusus di view delete.
- Impor tidak menimpa data existing: pengulangan ID menghasilkan error duplikat, bukan sukses idempotent. Constraint unik ifixit_guideid tetap menjadi pelindung database.
- Create/edit/import atomic. Validasi form gagal tidak menyimpan sebagian data. Respons HTML sukses memakai Django messages; delete juga menampilkan pesan sukses.
- Tidak ada cache untuk daftar panduan atau invalidasi cache khusus saat CRUD. Cache hanya dipakai fetch iFixit.

## Konfigurasi dan migrasi

`guides` terdaftar di INSTALLED_APPS. Gunakan autentikasi, database, cache dan static settings milik proyek. Tidak ada API key iFixit atau environment variable khusus M3. Timeout/TTL ditetapkan dalam `guides/ifixit.py`. Jika CACHES tidak diatur, backend default Django adalah cache memori lokal proses; jangan menganggap cache dibagikan antarworker. Proyek memakai TIME_ZONE Asia/Jakarta.

| Migrasi | Perubahan / dependency |
|---|---|
| `0001_initial` | Membuat tiga model dan constraint urutan langkah; bergantung pada `devices.0002_device` dan AUTH_USER_MODEL |
| `0002_repairguide_source_author` | Menambahkan source_author; bergantung pada guides.0001_initial |

Jalankan `python manage.py migrate`. Jangan mengedit migrasi app lain. Field symptom memerlukan perubahan model dan migrasi baru jika nanti disepakati; belum termasuk versi ini.

## Menjalankan dan memverifikasi

Ikuti [setup ringkas](../../guides/README.md). Data `seed_devices` hanya mengisi perangkat, bukan panduan. Buat panduan melalui contributor/admin atau impor satu panduan, periksa sumber dan peringatannya sebelum menerbitkan.

```sh
python manage.py test guides
python manage.py makemigrations --check --dry-run
```

Sebelum PR ikuti checks dalam [CONTRIBUTING.md](../../CONTRIBUTING.md). Tes guides mencakup CRUD, permission, draf/filter, CSRF, import rollback/duplikat/cache/timeout, serta larangan pengambilan kolom detail untuk pengunjung. Periksa manual warning tetap terlihat, AJAX filter, dan alur login sesuai kebutuhan; dokumentasi ini tidak menyatakan semua pengujian manual tersebut sudah dilakukan.

## Changelog dokumentasi

- **1.0 — 30 Oktober 2026:** kontrak M3 berdasarkan implementasi; merinci data, endpoint, selector, importer, error, transaksi, konfigurasi/migrasi; menandai symptom sebagai rencana dan memperbarui README lama.
