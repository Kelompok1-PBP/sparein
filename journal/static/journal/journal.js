(function () {
  var root = document.querySelector("[data-journal]");
  if (!root) return;

  function toast(message, kind) {
    var container = document.querySelector(".toasts");
    if (!container) {
      container = document.createElement("div");
      container.className = "toasts";
      container.setAttribute("role", "status");
      container.setAttribute("aria-live", "polite");
      document.body.appendChild(container);
    }
    var item = document.createElement("div");
    item.className = "toast";
    var icon = document.createElement("img");
    icon.src = kind === "error" ? root.dataset.iconError : root.dataset.iconSuccess;
    icon.alt = "";
    icon.width = 20;
    icon.height = 20;
    var text = document.createElement("p");
    text.textContent = message;
    item.appendChild(icon);
    item.appendChild(text);
    container.appendChild(item);
    setTimeout(function () {
      item.remove();
    }, 5000);
  }

  function postStatus(url, status) {
    return fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": root.dataset.csrf,
        "X-Requested-With": "XMLHttpRequest",
        Accept: "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ status: status }),
    }).then(function (response) {
      if (!response.ok) throw new Error("gagal");
      return response.json();
    });
  }

  window.SpareinJournal = { toast: toast, postStatus: postStatus };
})();
