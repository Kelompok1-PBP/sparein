from core.permissions import is_member


def can_use_journal(user): # membatasi siapa yang boleh masuk modul jurnal. di setiap baris pertama setiap fungsi di views.py akan memanggil fungsi ini
    return is_member(user) # visitor yang belum login hasilnya False
