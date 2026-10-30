// JS buat kerangka komponen halaman.

// 1. header dapet garis bawah setelah halaman di-scroll
var header = document.querySelector("[data-site-header]");
function updateHeader() {
  header.classList.toggle("is-scrolled", window.scrollY > 4);
}
updateHeader();
window.addEventListener("scroll", updateHeader, { passive: true });

// 2. dropdown akun dan buat (<details>) nutup kalau klik di luar atau tekan Esc
var menus = document.querySelectorAll("details[data-menu]");
document.addEventListener("click", function (e) {
  menus.forEach(function (menu) {
    if (!menu.contains(e.target)) menu.removeAttribute("open");
  });
});
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") {
    menus.forEach(function (menu) { menu.removeAttribute("open"); });
  }
});

// 3. toast hilang sendiri setelah 5 detik atau kalau tombol tutupnya diklik
document.querySelectorAll("[data-toast]").forEach(function (toast) {
  toast.querySelector("[data-toast-close]").addEventListener("click", function () {
    toast.remove();
  });
  setTimeout(function () { toast.remove(); }, 5000);
});
