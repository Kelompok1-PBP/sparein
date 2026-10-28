(function () {
  var root = document.querySelector("[data-journal]");
  var api = window.SpareinJournal;
  if (!root || !api) return;

  var results = root.querySelector("[data-results]");
  var live = root.querySelector("[data-live]");

  // ---------- penjelasan dampak ----------
  var how = root.querySelector("[data-how]");
  var info = document.getElementById("impact-info");
  if (how && info) {
    how.addEventListener("click", function () {
      var open = info.hidden;
      info.hidden = !open;
      how.setAttribute("aria-expanded", String(open));
    });
  }

  // ---------- tab dan halaman ----------
  function currentStatus() {
    return new URL(window.location.href).searchParams.get("status") || "";
  }

  function markTabs() {
    var status = currentStatus();
    root.querySelectorAll("[data-tab]").forEach(function (tab) {
      if (tab.dataset.tab === status) tab.setAttribute("aria-current", "page");
      else tab.removeAttribute("aria-current");
    });
  }

  function showSkeleton() {
    results.replaceChildren();
    for (var i = 0; i < 3; i++) {
      var bar = document.createElement("div");
      bar.className = "skeleton";
      results.appendChild(bar);
    }
  }

  function load(url, push) {
    results.setAttribute("aria-busy", "true");
    showSkeleton();
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (response) {
        if (!response.ok) throw new Error("gagal");
        return response.text();
      })
      .then(function (html) {
        results.innerHTML = html; // fragmen dari server, sudah di-escape oleh template
        if (push) window.history.pushState({}, "", url);
        markTabs();
      })
      .catch(function () {
        window.location.href = url; // tanpa AJAX tetap bisa
      })
      .finally(function () {
        results.removeAttribute("aria-busy");
      });
  }

  function plainClick(event) {
    return !(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button);
  }

  root.addEventListener("click", function (event) {
    var link = event.target.closest("[data-tab], [data-page]");
    if (!link || !plainClick(event)) return;
    event.preventDefault();
    load(link.href, true);
  });

  window.addEventListener("popstate", function () {
    load(window.location.href, false);
  });

  // ---------- menu kartu ----------
  document.addEventListener("click", function (event) {
    document.querySelectorAll("details.log-menu[open]").forEach(function (menu) {
      if (!menu.contains(event.target)) menu.removeAttribute("open");
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    document.querySelectorAll("details.log-menu[open]").forEach(function (menu) {
      menu.removeAttribute("open");
      menu.querySelector("summary").focus();
    });
  });

  // ---------- ubah status ----------
  function updateTiles(tiles) {
    Object.keys(tiles).forEach(function (key) {
      var target = root.querySelector('[data-tile-value="' + key + '"]');
      if (target) target.textContent = tiles[key];
    });
  }

  function updateCounts(counts) {
    root.querySelectorAll("[data-tab]").forEach(function (tab) {
      var target = tab.querySelector("[data-tab-count]");
      var key = tab.dataset.countKey;
      if (target && key in counts) target.textContent = counts[key];
    });
  }

  function showEmptyTab() {
    var message = document.createElement("p");
    message.className = "j-empty-tab";
    message.textContent = "Belum ada catatan dengan status ini.";
    results.replaceChildren(message);
  }

  function applyStatus(card, data) {
    card.dataset.status = data.status;
    card.querySelector("[data-badge]").outerHTML = data.badge_html; // dirender server
    var impact = card.querySelector("[data-card-impact]");
    impact.hidden = !data.card_impact;
    impact.querySelector("[data-card-impact-text]").textContent = data.card_impact;
    card.querySelectorAll("[data-set-status]").forEach(function (option) {
      if (option.dataset.setStatus === data.status) option.setAttribute("aria-current", "true");
      else option.removeAttribute("aria-current");
    });
    updateTiles(data.tiles);
    updateCounts(data.counts);
    var menu = card.querySelector("details.log-menu");
    if (menu) menu.removeAttribute("open");
    var filter = currentStatus();
    if (filter && filter !== data.status) {
      card.remove(); // sudah tidak cocok dengan tab yang aktif
      if (!results.querySelector("[data-log]")) showEmptyTab();
    }
  }

  results.addEventListener("click", function (event) {
    var option = event.target.closest("[data-set-status]");
    if (!option) return;
    var card = option.closest("[data-log]");
    if (option.dataset.setStatus === card.dataset.status) {
      card.querySelector("details.log-menu").removeAttribute("open");
      return;
    }
    var options = card.querySelectorAll("[data-set-status]");
    options.forEach(function (o) {
      o.disabled = true;
    });
    live.textContent = "Menyimpan status…";
    api
      .postStatus(option.dataset.url, option.dataset.setStatus)
      .then(function (data) {
        applyStatus(card, data);
        var message = "Status diubah jadi " + data.status_label + ".";
        live.textContent = message;
        api.toast(message, "success");
      })
      .catch(function () {
        live.textContent = "Status gagal diubah. Coba lagi.";
        api.toast("Status gagal diubah. Coba lagi.", "error");
      })
      .finally(function () {
        options.forEach(function (o) {
          o.disabled = false;
        });
      });
  });
})();
