(function () {
  var page = document.querySelector("[data-journal-form]");
  if (!page) return;

  // ---------- cari di select panduan dan perangkat ----------
  page.querySelectorAll("[data-filter-for]").forEach(function (box) {
    var select = document.getElementById(box.dataset.filterFor);
    if (!select) return;
    var options = Array.prototype.slice.call(select.options);
    box.hidden = false; // tanpa JavaScript, select biasa tetap bisa dipakai
    box.addEventListener("input", function () {
      var query = box.value.trim().toLowerCase();
      var chosen = select.value;
      // dibangun ulang karena <option hidden> tidak didukung semua browser
      var shown = options.filter(function (option) {
        return !option.value || option.value === chosen || option.text.toLowerCase().indexOf(query) !== -1;
      });
      select.replaceChildren.apply(select, shown);
      select.value = chosen;
    });
  });

  // ---------- panduan mengisi perangkat ----------
  var guide = document.getElementById("id_guide");
  var device = document.getElementById("id_device");
  if (guide && device) {
    guide.addEventListener("change", function () {
      var picked = guide.options[guide.selectedIndex];
      var deviceId = picked && picked.dataset.device;
      if (!deviceId) return;
      var exists = Array.prototype.some.call(device.options, function (option) {
        return option.value === deviceId;
      });
      if (exists) device.value = deviceId;
    });
  }

  // ---------- petunjuk untuk status Berhasil ----------
  var hint = page.querySelector("[data-succeeded-hint]");
  var statuses = page.querySelectorAll('input[name="status"]');
  function syncHint() {
    if (!hint) return;
    var checked = page.querySelector('input[name="status"]:checked');
    hint.hidden = !(checked && checked.value === "succeeded");
  }
  statuses.forEach(function (radio) {
    radio.addEventListener("change", syncHint);
  });
  syncHint();
})();
