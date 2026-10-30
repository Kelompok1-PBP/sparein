// Nomor urut baris ("Langkah 1") dan nilai order tersembunyi ikut posisi baris yang masih dipakai
const renumber = (container) => {
  let position = 0;
  container.querySelectorAll("[data-row]").forEach((row) => {
    if (row.querySelector("input[name$='-DELETE']").checked) return;
    position += 1;
    row.querySelector("[data-number]").textContent = position;
    const order = row.querySelector("input[name$='-order']");
    if (order) order.value = position;
  });
};

const prepare = (container) => {
  // Tombol geser cuma berguna kalau JS jalan, jadi tersembunyi dari awal
  container.querySelectorAll("[data-move]").forEach((button) => (button.hidden = false));
  renumber(container);
};

document.querySelectorAll("[data-rows]").forEach((container) => {
  prepare(container);

  container.addEventListener("change", (event) => {
    if (!event.target.matches("input[name$='-DELETE']")) return;
    event.target.closest("[data-row]").classList.toggle("is-deleted", event.target.checked);
    renumber(container);
  });

  container.addEventListener("click", (event) => {
    const button = event.target.closest("[data-move]");
    if (!button) return;
    const row = button.closest("[data-row]");
    if (button.dataset.move === "up" && row.previousElementSibling) row.previousElementSibling.before(row);
    if (button.dataset.move === "down" && row.nextElementSibling) row.nextElementSibling.after(row);
    renumber(container);
  });
});

document.querySelectorAll(".add-row").forEach((button) =>
  button.addEventListener("click", () => {
    const prefix = button.dataset.prefix;
    const total = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
    const maximum = Number(document.getElementById(`id_${prefix}-MAX_NUM_FORMS`).value);
    if (Number(total.value) >= maximum) return;
    const template = document.getElementById(`${prefix}-template`);
    const wrapper = document.createElement("div");
    wrapper.innerHTML = template.innerHTML.replaceAll("__prefix__", total.value);
    const container = document.querySelector(`[data-rows=${prefix}]`);
    container.append(...wrapper.children);
    total.value = Number(total.value) + 1;
    prepare(container);
  })
);
