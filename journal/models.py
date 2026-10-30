from django.conf import settings
from django.db import models


class CategoryImpactProfile(models.Model):
    # data acuan untuk menghitung estimasi dampak bds kategori perangkat (berat perangkat & biaya pengganti)
    category = models.OneToOneField( # satu kategori hanya dapat memiliki satu data acuan
        "devices.DeviceCategory", # misalnya: Phone, Tablet, Headphone, dsb
        on_delete=models.CASCADE,
        related_name="impact_profile",
    )
    avg_mass_kg = models.DecimalField(max_digits=6, decimal_places=2) # akan selalu dalam format 2 angka di belakang koma
    replacement_cost = models.PositiveBigIntegerField( # field type yang cocok untuk menyimpan nilai uang dalam rupiah
        help_text="Total biaya yang diperlukan untuk mengganti perangkat dengan yang baru (Rp)"
    )

    class Meta:
        ordering = ["category__name"]

    def __str__(self):
        return f"{self.category} ({self.avg_mass_kg} kg)"

    
class RepairLog(models.Model):
    # catatan perbaikan yang dilakukan atau direncanakan pengguna. Intinya berisi aktivitas pengguna
    class Status(models.TextChoices): # models.TextChoices menyediakan pilihan status yang konsisten, sehingga tidak diisi dengan sembarang teks
        # format: database | tampilan
        PLANNED = "planned", "Direncanakan"
        IN_PROGRESS = "in_progress", "Sedang dikerjakan"
        SUCCEEDED = "succeeded", "Berhasil"
        FAILED = "failed", "Gagal"

    user = models.ForeignKey( # since RepairLog tidak bisa berdiri sendiri, oleh karena itu dia terhubung dengan pengguna
        # pengguna pemilik catatan
        settings.AUTH_USER_MODEL,  # merujuk kepada model pengguna yang dipakai di proyek Django
        on_delete=models.CASCADE,  # jika pengguna terkait dihapus, maka seluruh catatan perbaikan miliknya ikut terhapus
        related_name="repair_logs" # pintasan untuk mengakses kumpulan catatan perbaikan milik pengguna
    )

    # ! sebuah catatan tetap bisa disimpan walaupun tidak terhubung ke panduan atau perangkat tertentu

    guide = models.ForeignKey( # terhubung dengan panduan perbaikan
        # panduan perbaikan yang terkait
        "guides.RepairGuide",
        null=True,  # memperbolehkan nilai kosong di dalam database
        blank=True, # memperbolehkan nilai kosong di dalam form
        on_delete=models.SET_NULL, # jika panduan terkait dihapus, maka seluruh catatan perbaikan nya tetap ada, hanya mengosongkan referensinya saja
        related_name="repair_logs",
    )

    device = models.ForeignKey( # terhubung dengan perangkat yang ingin diperbaiki
        # perangkat yang diperbaiki
        "devices.Device",
        null=True,  # memperbolehkan nilai kosong di dalam database
        blank=True, # memperbolehkan nilai kosong di dalam form
        on_delete=models.SET_NULL, # jika perangkat terkait dihapus, maka seluruh catatan perbaikan nya tetap ada, hanya mengosongkan referensinya saja
        related_name="repair_logs",
    )

    title = models.CharField(max_length=200) 
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLANNED) 
    cost_spent = models.PositiveBigIntegerField(default=0, help_text="Total biaya yang dikeluarkan selama perbaikan (Rp)") # biaya perbaikan yang dikeluarkan (membeli komponen suku cadang, dsb)
    notes = models.TextField(blank=True)
    repaired_at = models.DateField(null=True, blank=True) # tanggal perbaikan

    class Meta:
        ordering = ["-repaired_at", "-pk"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs): # overridden untuk keperluan menyimpan objek model sesuai dengan kondisi yang terjadi di dalam app (khusus), yaitu mendefinisikan ulang perilakunya agar ada proses tambahan setelah catatan disimpan
            super().save(*args, **kwargs) # selalu disimpan ke database terlebih dahulu sebelum sinkronasi estimasi dijalankan, karena sync_impact() perlu mengetahui data terbaru dari catatan tertentu
            from .impact import sync_impact
    
            sync_impact(self) # self di sini merujuk pada objek RepairLog yang sedang disimpan


class ImpactEstimate(models.Model):
    # hasil perhitungan estimasi dampak dari catatan perbaikan yang berhasil. Intinya berisi hasil perhitungan yang berkaitan dengan aktivitas di RepairLog, dampaknya berupa:
    # 1. limbah elektronik yang dihindari
    # 2. biaya penggantian yang dihemat
    log = models.OneToOneField(RepairLog, on_delete=models.CASCADE, related_name="impact") # satu catatan perbaikan hanya memiliki maksimal satu hasil estimasi dampak
    waste_avoided_kg = models.DecimalField(max_digits=8, decimal_places=2) # berat perangkat yang tidak menjadi limbah
    cost_avoided = models.PositiveBigIntegerField()   # biaya penggantian yang dapat dihindari, dan dihitung dengan menggunakan rumus max(replacement_cost  - cost_spent, 0)
    computed_at = models.DateTimeField(auto_now=True) # waktu terakhir kali hasil estimasi DIPERBAHARUI

    def __str__(self):
        return f"{self.log}: {self.waste_avoided_kg} kg"
