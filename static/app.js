document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy-steam-id]");
  if (!button) return;
  try {
    await navigator.clipboard.writeText(button.dataset.copySteamId);
    button.textContent = "คัดลอกแล้ว";
    window.setTimeout(() => { button.textContent = "คัดลอก"; }, 2000);
  } catch {
    button.textContent = "คัดลอกไม่สำเร็จ";
  }
});
