(function () {
  var KEY = "auth-swap";

  // kalau barusan pindah dari login ke daftar (atau sebaliknya), jalanin efek geser
  try {
    if (sessionStorage.getItem(KEY)) {
      document.documentElement.classList.add("auth-swapping");
      sessionStorage.removeItem(KEY);
    }
  } catch (e) {}

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-auth-switch]").forEach(function (link) {
      link.addEventListener("click", function (e) {
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        try { sessionStorage.setItem(KEY, "1"); } catch (err) {}
      });
    });

    document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
      var input = btn.parentElement.querySelector("input");
      btn.hidden = false;
      btn.addEventListener("click", function () {
        var show = input.type === "password";
        input.type = show ? "text" : "password";
        btn.setAttribute("aria-pressed", String(show));
        btn.setAttribute("aria-label", show ? "Sembunyikan password" : "Tampilkan password");
      });
    });

    document.querySelectorAll("[data-auth-form]").forEach(function (form) {
      var submit = form.querySelector("[type=submit]");
      if (!submit) return;
      var label = submit.textContent;

      form.addEventListener("submit", function () {
        // ditunda biar form tetap terkirim dulu sebelum tombolnya dimatiin
        setTimeout(function () {
          submit.disabled = true;
          submit.setAttribute("aria-busy", "true");
          submit.textContent = "Memproses...";
        }, 0);
      });

      // tombol back dari browser bisa balik dalam keadaan "Memproses..."
      window.addEventListener("pageshow", function () {
        submit.disabled = false;
        submit.removeAttribute("aria-busy");
        submit.textContent = label;
      });
    });
  });
})();
