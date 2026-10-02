// JS buat kerangka halaman: bayangan header waktu scroll, dropdown, menu mobile, dan toast.
// Tanpa JS, dropdown akun dan buat tetap bisa dibuka (pakai <details>), tapi menu mobile butuh JS.
(function () {
  var header = document.querySelector("[data-site-header]");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 4);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // dropdown akun dan buat: tutup kalau klik di luar, tekan Esc, atau buka yang lain
  var menus = document.querySelectorAll("details[data-menu]");
  document.addEventListener("click", function (e) {
    menus.forEach(function (m) {
      if (!m.contains(e.target)) m.removeAttribute("open");
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    menus.forEach(function (m) {
      if (!m.open) return;
      m.removeAttribute("open");
      m.querySelector("summary").focus();
    });
  });
  menus.forEach(function (m) {
    m.addEventListener("toggle", function () {
      if (!m.open) return;
      menus.forEach(function (other) {
        if (other !== m) other.removeAttribute("open");
      });
    });
  });

  // menu mobile
  var burger = document.querySelector("[data-menu-open]");
  var panel = document.getElementById("menu-mobile");
  if (burger && panel) {
    var closeBtn = panel.querySelector("[data-menu-close]");
    var setOpen = function (open) {
      panel.hidden = !open;
      burger.setAttribute("aria-expanded", String(open));
      document.body.classList.toggle("is-menu-open", open);
      (open ? closeBtn : burger).focus();
    };
    burger.addEventListener("click", function () { setOpen(true); });
    closeBtn.addEventListener("click", function () { setOpen(false); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !panel.hidden) setOpen(false);
    });
    // kalau layar dilebarin sampai tampilan desktop, tutup panelnya
    window.matchMedia("(min-width: 1024px)").addEventListener("change", function (e) {
      if (e.matches && !panel.hidden) {
        panel.hidden = true;
        burger.setAttribute("aria-expanded", "false");
        document.body.classList.remove("is-menu-open");
      }
    });
  }

  // toast: hilang sendiri setelah 5 detik atau kalau ditutup
  document.querySelectorAll("[data-toast]").forEach(function (toast) {
    var remove = function () { toast.remove(); };
    toast.querySelector("[data-toast-close]").addEventListener("click", remove);
    setTimeout(remove, 5000);
  });
})();
