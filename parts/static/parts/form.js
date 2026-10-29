// Tambah baris formset (perangkat dan toko) dari <template>, polanya sama kayak guides/form.js.
// Tombol tambah disembunyiin di HTML, tanpa JS tombolnya ga bisa ngapa-ngapain.

document.querySelectorAll("[data-add-row]").forEach((button) => {
  const prefix = button.dataset.addRow;
  const total = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
  const max = Number(document.getElementById(`id_${prefix}-MAX_NUM_FORMS`).value);
  const template = document.getElementById(`${prefix}-template`);
  const rows = document.getElementById(`${prefix}-rows`);

  button.hidden = Number(total.value) >= max;
  button.addEventListener("click", () => {
    const index = Number(total.value);
    if (index >= max) return;
    // isi template dari Django, __prefix__ diganti nomor baris
    const wrapper = document.createElement("div");
    wrapper.innerHTML = template.innerHTML.replaceAll("__prefix__", index);
    const row = wrapper.firstElementChild;
    row.querySelector("[data-row-number]").textContent = index + 1;
    rows.append(row);
    total.value = index + 1;
    row.querySelector("select, input:not([type=hidden], [type=checkbox])").focus();
    button.hidden = index + 1 >= max;
  });
});
