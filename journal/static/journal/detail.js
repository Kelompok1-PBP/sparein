(function () {
  var root = document.querySelector("[data-journal]");
  var api = window.SpareinJournal;
  if (!root || !api) return;

  var live = root.querySelector("[data-live]");

  root.addEventListener("click", function (event) {
    var button = event.target.closest("[data-mark-succeeded]");
    if (!button) return;
    button.disabled = true;
    live.textContent = "Menyimpan status…";

    api
      .postStatus(button.dataset.url, "succeeded")
      .then(function (data) {
        root.querySelector("[data-impact-box]").innerHTML = data.impact_html; 
        root.querySelector("[data-badge]").outerHTML = data.badge_html;
        var date = root.querySelector("[data-detail-date]");
        if (date && data.repaired_at) date.textContent = data.repaired_at;
        var message = "Status diubah jadi " + data.status_label + ".";
        live.textContent = message;
        api.toast(message, "success");
      })
      .catch(function () {
        button.disabled = false;
        live.textContent = "Status gagal diubah. Coba lagi.";
        api.toast("Status gagal diubah. Coba lagi.", "error");
      });
  });
})();
