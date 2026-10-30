# M1 Devices

## Identitas

| | |
|---|---|
| **Purpose** | Katalog perangkat elektronik dan kategorinya; acuan `device` untuk semua modul lain. |
| **Owner** | Muhammad Sultan Zidan (`zidanristek`) |
| **Versi** | 1.0, 30 Oktober 2026, berdasarkan `dev` `a347c8f` |
| **Dependencies** | Django, `core.permissions` (`is_contributor`, `is_admin`), `requests` (seed iFixit) |
| **Konsumen** | `guides`, `parts`, `diagnostics`, `journal` |

## Can and cannot

- **Can:** cari dan filter perangkat (nama, kategori, merek), detail, CRUD sesuai role, JSON `/api/devices/`, seed dari iFixit atau fixture.
- **Cannot:** pagination, lebih dari 60 hasil, error envelope JSON, menghapus perangkat yang masih dirujuk `guides`, `parts`, atau `diagnostics`, dan mengubah slug.
- **Prerequisites:** role dari `core`; jalankan `migrate` lalu `seed_devices`.

## Publik dan internal

| Publik | Internal |
|---|---|
| Model `Device`, `DeviceCategory` | `unique_slug`, `_filters`, `_can_edit` |
| `get_device_qs`, `get_device_or_404` | `ifixit.fetch_family`, `ifixit.upsert_family` |
| Endpoint HTML, `GET /api/devices/` | `DeviceForm` |

Modul lain cukup memakai selector, tanpa query langsung ke model.

## Kontrak selector

| Signature | Pre → post | Error | Side effect, idempotency |
|---|---|---|---|
| `get_device_qs(*, q=None, category=None, brand=None) -> QuerySet[Device]` | Argumen berupa string atau `None`, filter kosong dilewati → `q` dicocokkan `name__icontains`, `category` dengan slug kategori, `brand` dengan `iexact`; terurut `name`, `select_related("category")` | Tidak ada; filter tidak cocok menghasilkan QuerySet kosong | Hanya baca, lazy, idempotent; tanpa transaksi dan cache |
| `get_device_or_404(slug: str) -> Device` | Slug exist → satu `Device` dengan `category` | `Http404`, tidak retryable | Hanya baca, idempotent |

Semua perangkat bersifat publik, jadi selector tidak menyaring berdasarkan hak akses.

## Kontrak endpoint

| Route | Akses | Sukses | Error | Side effect |
|---|---|---|---|---|
| GET `/devices/?q=&category=&brand=` | Semua | HTML 200, maksimal 60 | Tidak ada | Tidak ada |
| GET `/devices/<slug>/` | Semua | HTML 200 | 404 | Tidak ada |
| GET/POST `/devices/create/` | Contributor/Admin | 302 ke detail | 302 ke login, 403, form tidak valid 200 | Insert; `created_by` = user |
| GET/POST `/devices/<slug>/edit/` | Admin, atau Contributor pembuatnya | 302 ke detail | 302 ke login, 403, 404, form tidak valid 200 | Update; slug tetap |
| GET/POST `/devices/<slug>/delete/` | Admin | GET konfirmasi; POST 302 ke daftar | 403, 404; masih dirujuk: 200 dengan pesan `blocked` | Delete |
| GET `/api/devices/?q=&category=&brand=` | Semua | JSON 200 | Tidak ada | Tidak ada |

- **Idempotency:** GET selalu idempotent. POST create tidak idempotent, karena submit ulang membuat perangkat baru dengan slug `-2`. Edit dengan data yang sama hasilnya sama. Delete yang diulang menghasilkan 404.
- **Transaksi:** autocommit Django per `save()` dan `delete()`.
- **Cache dan event:** tidak ada.
- **Retry:** tidak ada error yang retryable. 403, 404, dan error validasi harus diperbaiki di sisi input atau akun dulu.

## Data contract

**`DeviceCategory`**

| Field | Type | Constraint |
|---|---|---|
| name | string(100) | required |
| slug | slug(210) | unique, auto |
| parent | FK DeviceCategory | null, blank, `SET_NULL` |

**`Device`**

| Field | Type | Constraint |
|---|---|---|
| name | string(200) | required |
| slug | slug(210) | unique, auto, immutable |
| category | FK DeviceCategory | required, `PROTECT` |
| brand | string(100) | blank |
| release_year | small int | null, blank, 1970 s.d. next year (form) |
| image_url | URL | blank |
| summary | text | blank |
| ifixit_wikiid | int | null, blank, unique |
| repairability_score | small int | null, blank, 0 s.d. 10 |
| created_by | FK User | null, blank, `SET_NULL` |
| created_at | datetime | auto |

**DTO `GET /api/devices/`**

```json
{"results": [{"name": "iPhone 13", "slug": "iphone-13", "brand": "Apple",
  "category": "iphone", "image_url": "https://...", "url": "/devices/iphone-13/"}]}
```

Semua field yang tipenya string; `brand` dan `image_url` boleh string kosong. Tidak ada `id`, pagination, atau total; batasnya 60 hasil.

**Format error:** belum ada error envelope JSON. Error 403 dan 404 memakai halaman HTML dari `core`, dan error validasi ditampilkan di form.

**Dampak hapus ke modul lain:**

- `guides`, `parts`, `diagnostics`: `PROTECT`, jadi perangkat yang masih dirujuk tidak bisa dihapus.
- `journal.RepairLog.device`: `SET_NULL`.
- Menghapus kategori ikut menghapus `journal.CategoryImpactProfile` (`CASCADE`).

## Seed dan konfigurasi

- `python manage.py seed_devices [--families "Judul:Merek,..."]` melakukan upsert berdasarkan `ifixit_wikiid` dalam satu transaksi. Idempotent: dijalankan ulang tidak membuat duplikat.
- Kalau iFixit gagal (`OSError` atau `ValueError`), transaksi di-rollback lalu `loaddata seed_devices` dijalankan.
- Timeout iFixit 15 detik, tanpa API key dan tanpa environment variable khusus.

## Migrasi

| Migrasi | Isi |
|---|---|
| `0001_initial` | `DeviceCategory` |
| `0002_device` | `Device`; bergantung pada `0001` dan `AUTH_USER_MODEL` |

## Batasan yang diketahui

- `unique_slug` ngecheck lalu menyimpan tanpa lock. Dua create dengan nama sama di waktu bersamaan bisa kena constraint unik dan berakhir 500.
- Daftar perangkat dan API dibatasi 60 item, tanpa pagination.

## Changelog

- **1.0, 30 Oktober 2026:** kontrak pertama berdasarkan #9, #12 s.d. #14, #23, dan #27.
