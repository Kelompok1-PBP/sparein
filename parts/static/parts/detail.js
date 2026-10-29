// Salin nomor part ke clipboard terus kasih toast kecil.
// Tombolnya disembunyiin di HTML, baru dimunculin kalau browser punya clipboard API.

function showToast(message, icon) {
  let box = document.querySelector(".toasts");
  if (!box) {
    box = document.createElement("div");
    box.className = "toasts";
    box.setAttribute("role", "status");
    box.setAttribute("aria-live", "polite");
    document.body.append(box);
  }
  // markup sama kayak partials/toasts.html
  const toast = document.createElement("div");
  toast.className = "toast toast--success";
  const img = document.createElement("img");
  img.src = icon;
  img.alt = "";
  img.width = 20;
  img.height = 20;
  const p = document.createElement("p");
  p.textContent = message;
  toast.append(img, p);
  // ditunda dikit biar region aria-live yang baru dibuat sempat kebaca pembaca layar
  requestAnimationFrame(() => box.append(toast));
  setTimeout(() => toast.remove(), 3000);
}

const copyButton = document.querySelector("[data-copy]");
if (copyButton && navigator.clipboard) {
  copyButton.hidden = false;
  copyButton.addEventListener("click", async () => {
    const text = document.querySelector(copyButton.dataset.copy).textContent.trim();
    try {
      await navigator.clipboard.writeText(text);
      showToast("Nomor part disalin.", copyButton.dataset.icon);
    } catch {
      copyButton.hidden = true;  // izin clipboard ditolak, nomornya masih bisa diblok manual
    }
  });
}
