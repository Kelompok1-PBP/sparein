document.querySelectorAll('.add-row').forEach(button => button.addEventListener('click', () => {
  const prefix = button.dataset.prefix;
  const total = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
  const maximum = Number(document.getElementById(`id_${prefix}-MAX_NUM_FORMS`).value);
  if (Number(total.value) >= maximum) return;
  const template = document.getElementById(`${prefix}-template`);
  const wrapper = document.createElement('div');
  wrapper.innerHTML = template.innerHTML.replaceAll('__prefix__', total.value);
  document.getElementById(`${prefix}-rows`).append(...wrapper.children);
  total.value = Number(total.value) + 1;
}));
