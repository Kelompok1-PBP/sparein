# M3 Repair Guide — Hanna

Modul panduan perbaikan: CRUD panduan, langkah, peringatan keselamatan, filter AJAX, API JSON, dan impor satu panduan iFixit sebagai draf.

**Dokumentasi lengkap:** [docs/GUIDES-GUIDE.md](../docs/GUIDES-GUIDE.md), berisi owner/dependencies, kontrak fungsi dan endpoint, model/DTO, hak akses, error, transaksi, konfigurasi, migrasi, dan changelog.

## Menjalankan lokal

Dari root proyek, aktifkan virtual environment dan instal requirements.txt. Gunakan konfigurasi lokal sesuai README proyek; jika membuat .env, jangan biarkan SECRET_KEY kosong.

```sh
python manage.py migrate
python manage.py loaddata seed_devices
python manage.py createsuperuser
python manage.py runserver
```

Buka `/guides/`, login di `/accounts/login/`. `seed_devices` hanya berisi perangkat; daftar panduan dapat kosong. Akun superuser dapat membuat data uji. Untuk Contributor, role akun harus ditetapkan melalui mekanisme pengelolaan akun tim.

## Fitur dan akses

- Pengunjung membaca panduan terbit, ringkasan, judul langkah, dan peringatan. Detail langkah hanya untuk pengguna login, termasuk di JSON dan query database.
- Contributor/Admin dapat membuat dan mengimpor. Edit untuk Contributor penulis atau Admin; hapus untuk penulis yang login atau Admin.
- Draf terlihat hanya oleh penulis atau Admin.
- Filter perangkat/kesulitan/durasi memakai AJAX dengan fallback form GET.
- `/api/guides/` mengembalikan maksimal 100 hasil. POST create/edit/delete mendukung JSON melalui `Accept: application/json`, dengan form-encoded body dan CSRF.

## Impor iFixit

Buka `/guides/import/`, atau jalankan:

```sh
python manage.py import_ifixit_guide GUIDE_ID --device DEVICE_ID --author USERNAME
```

Gunakan `--minutes 30` bila durasi sumber tidak tersedia. Impor membuat draf dan tidak menimpa ID sumber yang sudah ada. Cocokkan perangkat, langkah, gambar dan peringatan sebelum menerbitkan. Atribusi dan tautan sumber ditampilkan; teks tetap dalam bahasa sumber. Respons API di-cache satu jam dan pembacaan panduan tersimpan tidak memerlukan iFixit.

## Integrasi

Modul memakai core untuk role/login/layout dan devices untuk perangkat. Selector publik `get_guide_qs` / `get_guide_or_404` tidak menyaring draf; konsumen wajib menerapkan aturan akses. Journal dapat merujuk RepairGuide. Relasi opsional symptom yang direncanakan di MODULES.md belum diimplementasikan dalam model guides.

## Pemeriksaan

```sh
python manage.py test guides
python manage.py makemigrations --check --dry-run
```

Untuk lint, seluruh tes, coverage, dan alur PR ke dev, ikuti [CONTRIBUTING.md](../CONTRIBUTING.md). Perubahan core memerlukan review sesuai aturan tim.
