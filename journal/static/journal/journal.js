(function () {
  var root = document.querySelector("[data-journal]");
  if (!root) return;

  var csrf = root.dataset.csrf;
  var live = root.querySelector("[data-live]");
  var number = new Intl.NumberFormat("id-ID");
  var kg = new Intl.NumberFormat("id-ID", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  function announce(text) {
    live.textContent = text;
  }

  function updateStats(summary) {
    var scope = root.querySelector('[data-stats="me"]');
    if (!scope) return;
    scope.querySelector('[data-stat="repairs"]').textContent = summary.repairs;
    scope.querySelector('[data-stat="waste"]').textContent = kg.format(summary.waste_avoided_kg);
    scope.querySelector('[data-stat="cost"]').textContent = number.format(summary.cost_avoided);
  }

  function updateCard(card, data) {
    var badge = card.querySelector("[data-badge]");
    badge.textContent = data.status_label;
    badge.dataset.status = data.status;
    var impact = card.querySelector("[data-impact]");
    impact.textContent = data.impact
      ? "Menghindari " + kg.format(data.impact.waste_avoided_kg) + " kg limbah, menghemat Rp" + number.format(data.impact.cost_avoided)
      : "";
  }

  root.addEventListener("change", function (event) {
    var select = event.target.closest("[data-status-select]");
    if (!select) return;

    var card = select.closest("[data-log]");
    var previous = select.dataset.current;
    select.disabled = true;
    announce("Menyimpan status…");

    fetch(select.dataset.url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrf,
        "X-Requested-With": "XMLHttpRequest",
        Accept: "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ status: select.value }),
    })
      .then(function (response) {
        if (!response.ok) throw new Error("gagal");
        return response.json();
      })
      .then(function (data) {
        select.dataset.current = data.status;
        updateCard(card, data);
        updateStats(data.summary);
        announce("Status diubah menjadi " + data.status_label + ".");
      })
      .catch(function () {
        select.value = previous;
        announce("Status gagal diubah. Coba lagi.");
      })
      .finally(function () {
        select.disabled = false;
      });
  });
})();
