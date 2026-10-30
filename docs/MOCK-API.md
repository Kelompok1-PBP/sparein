# Sparein Mock API

Belum ada Public API untuk harga suku cadang di Indonesia, jadi kelompok menerbitkan Mock API sendiri. Datanya ada di repo terpisah, [`Kelompok1-PBP/sparein-mock-api`](https://github.com/Kelompok1-PBP/sparein-mock-api), dan disajikan GitHub Pages. Modul `parts` (M4) mengonsumsinya lewat HTTP seperti API pihak ketiga.

Semua data di Mock API fiktif. Nama toko, harga, dan nomor kontak dibuat untuk tugas ini, dan link toko hanya mengarah ke halaman pencarian marketplace.

## Endpoint

```
GET https://kelompok1-pbp.github.io/sparein-mock-api/v1/parts.json
```

Tanpa API key. URL-nya dibaca dari setting `PARTS_API_URL`, jadi bisa diganti lewat `.env`.

## Skema

```json
{
  "version": "1.0",
  "generated_at": "2026-10-30T09:00:00+07:00",
  "parts": [
    {
      "id": "part-0001",
      "name": "Baterai iPhone 11",
      "part_number": "BAT-IP11",
      "category": "battery",
      "description": "Baterai pengganti kapasitas standar 3110 mAh.",
      "image_url": "",
      "compatible_devices": [
        { "slug": "iphone-11", "note": "" }
      ],
      "sources": [
        {
          "id": "src-0001",
          "vendor_name": "Sinar Ponsel",
          "city": "Depok",
          "price": 185000,
          "currency": "IDR",
          "url": "https://www.tokopedia.com/search?st=product&q=baterai+iphone+11",
          "contact": "0812-0000-0001",
          "last_checked": "2026-10-27"
        }
      ]
    }
  ]
}
```

| Kunci | Masuk ke | Aturan |
|---|---|---|
| `parts[].id` | `SparePart.external_id` | Wajib, tetap, maksimal 50 karakter |
| `parts[].name`, `part_number`, `description`, `image_url` | `SparePart` | `name` wajib, sisanya boleh kosong |
| `parts[].category` | `SparePart.category` | `battery`, `screen`, `charger`, `cable`, `motor`, atau `other` |
| `compatible_devices[].slug` | `PartCompatibility.device` | Slug perangkat Sparein |
| `compatible_devices[].note` | `PartCompatibility.note` | Boleh kosong, maksimal 200 karakter |
| `sources[].id` | `PartSource.external_id` | Wajib, tetap, maksimal 50 karakter |
| `sources[].vendor_name`, `city` | `PartSource` | Wajib |
| `sources[].price` | `PartSource.price` | Bilangan bulat rupiah, minimal 1 |
| `sources[].currency` | `PartSource.currency` | Kode tiga huruf, misalnya `IDR` |
| `sources[].url` | `PartSource.url` | Wajib `https://` |
| `sources[].contact` | `PartSource.contact` | Boleh kosong |
| `sources[].last_checked` | `PartSource.last_checked` | Format `YYYY-MM-DD` |

## Cara sinkronisasi

Halaman Sparein tidak pernah memanggil Mock API. API hanya dibaca saat sinkronisasi, lalu datanya disimpan ke database.

| Cara | Untuk | Kalau API gagal |
|---|---|---|
| `python manage.py sync_parts` | Setup lokal | Memakai `parts/data/parts_snapshot.json` |
| `python manage.py sync_parts --fresh` | Melihat perubahan terbaru tanpa menunggu cache | Sama |
| Tombol **Sinkronkan data** di `/parts/` (`POST /parts/sync/`, Admin) | PWS, karena tidak ada shell | Muncul pesan error, data lama tetap dipakai |

Respons API di-cache 1 jam. Jadi perubahan di Mock API bisa baru terlihat setelah cache habis, kecuali memakai `--fresh`. GitHub Pages sendiri juga butuh beberapa menit untuk memperbarui file.

## Aturan sync

- Baris dicocokkan lewat `external_id`, jadi sync berulang tidak membuat data ganda.
- Isi tiap baris divalidasi dengan form yang sama seperti input manual. Baris yang tidak valid dilewati dan dihitung, misalnya link `http://` atau harga 0.
- Slug perangkat yang tidak dikenal juga dilewati dan dihitung, tapi suku cadangnya tetap disimpan.
- Kalau struktur JSON rusak, seluruh sync dibatalkan dan data lama tetap utuh.
- Data manual (tanpa `external_id`) tidak pernah disentuh.
- Baris hasil sync ditimpa setiap sync, jadi editan manual pada baris itu akan hilang.
- Tidak ada yang dihapus. Toko yang hilang dari API tetap ada, tapi `last_checked`-nya berhenti diperbarui sehingga halaman detail menandainya sebagai data lama.

## Mengubah data

1. Edit `v1/parts.json` di repo `sparein-mock-api`, lalu push ke `main`.
2. Salin file yang sama ke `parts/data/parts_snapshot.json` di repo ini.
3. Jalankan `python manage.py sync_parts --fresh`.
