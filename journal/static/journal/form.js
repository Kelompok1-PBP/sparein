(function () {
  var page = document.querySelector("[data-journal-form]");
  if (!page) return;

  var widgets = page.querySelectorAll("[data-autocomplete]");

  widgets.forEach(function (widget) {
    var input = widget.querySelector("[data-autocomplete-input]");
    var list = widget.querySelector("[data-autocomplete-list]");
    var source = widget.nextElementSibling;
    var select = source && source.querySelector("select");

    if (!input || !list || !select) return;

    list.tabIndex = -1;

    var items = []; 
    var active = -1; 

    function setActive(index) {
      if (items[active]) items[active].classList.remove("autocomplete__option--active");
      active = Math.max(0, Math.min(index, items.length - 1));
      if (items[active]) {
        items[active].classList.add("autocomplete__option--active");
        items[active].scrollIntoView({ block: "nearest" });
      }
    }

    function getOptions() {
      return Array.prototype.filter.call(select.options, function (option) {
        return option.value !== "";
      });
    }

    function syncInput() {
      var selected = select.options[select.selectedIndex];
      input.value = selected && selected.value ? selected.text : "";
    }

    function openList(filterByText) {
      var query = filterByText === true ? input.value.trim().toLowerCase() : "";
      var options = getOptions().filter(function (option) {
        return option.text.toLowerCase().indexOf(query) !== -1;
      });
      var selectedItem = null;

      items = [];
      active = -1;
      list.replaceChildren();

      options.forEach(function (option) {
        var item = document.createElement("button");
        item.type = "button";
        item.className = "autocomplete__option";
        item.textContent = option.text;
        item.setAttribute("role", "option");
        item.tabIndex = -1; 

        var isSelected = option.value === select.value;
        item.setAttribute("aria-selected", String(isSelected));
        if (isSelected) {
          item.classList.add("autocomplete__option--selected");
          selectedItem = item;
        }

        item.addEventListener("click", function () {
          select.value = option.value;
          syncInput();
          closeList();
          select.dispatchEvent(new Event("change", { bubbles: true }));
        });

        list.appendChild(item);
        items.push(item);
      });

      if (options.length === 0) {
        var empty = document.createElement("p");
        empty.className = "autocomplete__empty";
        empty.textContent = "Tidak ada pilihan yang cocok.";
        list.appendChild(empty);
      }

      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
      if (selectedItem) selectedItem.scrollIntoView({ block: "nearest" });
    }

    function closeList() {
      list.hidden = true;
      input.setAttribute("aria-expanded", "false");
      if (input.value.trim() === "" && select.value !== "") {
        select.value = ""; 
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
      syncInput();
    }

    widget.closeAutocomplete = closeList;

    input.addEventListener("input", function () {
      openList(true);
    });
    input.addEventListener("click", function () {
      if (list.hidden) openList(false);
    });

    list.addEventListener("mousedown", function (event) {
      event.preventDefault();
    });

    input.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        closeList();
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        if (list.hidden) openList(false);
        else setActive(active + 1);
      } else if (event.key === "ArrowUp" && !list.hidden) {
        event.preventDefault();
        setActive(active - 1);
      } else if (event.key === "Enter" && !list.hidden) {
        var target = items[active] || (items.length === 1 ? items[0] : null);
        if (target) {
          event.preventDefault();
          target.click();
        }
      }
    });

    widget.addEventListener("focusout", function (event) {
      if (!widget.contains(event.relatedTarget)) closeList();
    });

    select.addEventListener("change", syncInput);
    syncInput();
  });

  document.addEventListener(
    "pointerdown",
    function (event) {
      var inside = event.target.closest ? event.target.closest("[data-autocomplete]") : null;
      widgets.forEach(function (widget) {
        if (widget !== inside && widget.closeAutocomplete) widget.closeAutocomplete();
      });
    },
    true
  );

  // panduan mengisi perangkat 
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
      if (exists) {
        device.value = deviceId;
        device.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
  }

  // petunjuk untuk status Berhasil 
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
