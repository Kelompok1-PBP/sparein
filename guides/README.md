# M3 Repair Guide — Hanna

Modul ini memakai `core` (login dan role) serta `devices` (perangkat dan selector) dari proyek tim. Tidak menyertakan login/demo pengganti. Template mewarisi `base.html`. Model, login, dan perangkat tim dipakai kembali. Layout bersama di `core` disesuaikan dengan referensi desain pengguna; file `devices/` tidak diubah.

## Menjalankan lokal

Dari folder proyek, aktifkan virtual environment dan instal `requirements.txt`, kemudian:

```sh
python manage.py migrate
python manage.py loaddata seed_devices
python manage.py createsuperuser
python manage.py runserver
```

Buka `/guides/`. Login di `/accounts/login/` dengan akun yang dibuat. Superuser dapat mencoba seluruh fungsi. Untuk akun contributor biasa, ubah `UserProfile.role` menjadi `CONTRIBUTOR` melalui admin yang sudah disediakan tim. Member tidak dapat menulis panduan.

## Fitur

- Daftar, filter perangkat/kesulitan/durasi dengan AJAX dan fallback form GET.
- Detail panduan dan peringatan yang selalu dapat dibaca pengunjung.
- Detail langkah hanya untuk pengguna login, termasuk di JSON.
- Tambah/edit panduan dengan beberapa langkah dan peringatan; hapus melalui POST dengan CSRF.
- Draf hanya terlihat oleh penulis dan admin.
- `/api/guides/` untuk JSON. POST create/edit/delete mendukung respons JSON dengan header `Accept: application/json`; kirim form-encoded data dan token CSRF (bukan JSON body).
- Impor melalui `/guides/import/`: ID panduan iFixit + perangkat yang sesuai. Hasil masuk sebagai draf, tidak menimpa panduan yang sudah ada. Teks tetap dalam bahasa sumber. Gambar memakai URL sumber, bukan disimpan lokal.
- Respons iFixit di-cache satu jam; panduan tersimpan di database sehingga pembacaan tidak membutuhkan API. Timeout/error ditampilkan di form.
- Atribusi penulis sumber dan tautan lisensi pada panduan impor.

Alternatif impor dari terminal:

```sh
python manage.py import_ifixit_guide ID_PANDUAN --device ID_PERANGKAT --author USERNAME
```

Gunakan `--minutes 30` bila sumber tidak menyediakan durasi. Cocokkan model perangkat dengan sumber, jangan memilih perangkat hanya karena kategori/brand sama. Periksa seluruh langkah, gambar, peringatan dan tautan sumber sebelum mencentang Terbitkan. Jangan gunakan gambar atau panduan untuk menjanjikan bahwa perbaikan pasti berhasil.

## Batas integrasi

App `diagnostics` belum ada dalam salinan proyek ini. FK opsional `symptom` sengaja belum ditambahkan: menambahkan FK ke model yang tidak ada akan membuat migrasi gagal. Saat M2 tersedia, tambahkan FK nullable melalui migrasi baru sesuai kontrak tim. Selector `get_guide_qs` dan `get_guide_or_404` tersedia untuk M5. Pemanggil selector tetap harus menerapkan aturan akses jika menampilkan draf kepada publik.

Navbar, menu akun, dan footer memiliki tautan Panduan menuju `/guides/`. Menu diagnosis, suku cadang, dan jurnal masih berupa teks karena modulnya belum tersedia. Perubahan layout `core` perlu review tim sesuai aturan kontribusi.

Perubahan di luar app: registrasi `guides` di `sparein/settings.py`, URL di `sparein/urls.py`, template base/header/footer, stylesheet bersama dan varian logo untuk latar terang. Jika versi tim telah berubah, gabungkan perubahan melalui Git; jangan menimpa file seluruhnya.

## Pemeriksaan

```sh
python manage.py test guides core devices
python manage.py makemigrations --check --dry-run
ruff check .
```

Branch kerja: `feat/guides-repair-module`, berbasis `dev`. Belum di-push atau di-deploy. Buat PR ke `dev` dan ikuti review perubahan `core` sebelum merge.
