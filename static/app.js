(() => {
  const apiBase = document.body.dataset.leetifyApiBase;
  const keyInput = document.querySelector("#leetify-api-key");
  const storageKey = "cs2ttracker:leetify-api-key";
  const timeoutMs = 12_000;

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);

  const csrfToken = () => document.cookie.split("; ").find((item) => item.startsWith("csrftoken="))?.split("=")[1] || "";

  if (keyInput) {
    keyInput.value = sessionStorage.getItem(storageKey) || "";
    keyInput.addEventListener("input", () => {
      if (keyInput.value.trim()) sessionStorage.setItem(storageKey, keyInput.value.trim());
      else sessionStorage.removeItem(storageKey);
    });
  }

  function apiKey() {
    return keyInput?.value.trim() || "";
  }

  async function localPost(path, values) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken() },
      body: new URLSearchParams(values),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "ดำเนินการไม่สำเร็จ");
    return payload;
  }

  async function getSteamId(query) {
    return (await localPost("/api/resolve-steam/", { query })).steam64_id;
  }

  async function leetifyGet(path, steam64Id) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    const url = new URL(`${apiBase}${path}`);
    url.searchParams.set("steam64_id", steam64Id);

    try {
      const response = await fetch(url, {
        headers: { Accept: "application/json", _leetify_key: apiKey() },
        signal: controller.signal,
      });
      const payload = await response.json().catch(() => null);
      if (response.status === 404) return null;
      if (response.status === 429) throw new Error("Leetify จำกัดคำขอชั่วคราว กรุณาลองใหม่ภายหลัง");
      if (response.status === 401 || response.status === 403) throw new Error("Leetify ปฏิเสธ API key หรือโปรไฟล์นี้");
      if (!response.ok || !payload) throw new Error(`เชื่อมต่อ Leetify ไม่สำเร็จ (${response.status || "network"})`);
      return payload;
    } catch (error) {
      if (error.name === "AbortError") throw new Error("Leetify ใช้เวลาตอบกลับนานเกินไป");
      throw error;
    } finally {
      window.clearTimeout(timer);
    }
  }

  function player(data, steam64Id) {
    const ranks = data.ranks || {};
    const ratings = data.rating || data.ratings || {};
    const rawWinRate = Number(data.winrate || 0);
    return {
      name: data.name || "N/A", steam64Id,
      totalMatches: data.total_matches ?? data.totalMatches ?? 0,
      winRate: Math.round((rawWinRate <= 1 ? rawWinRate * 100 : rawWinRate) * 100) / 100,
      premier: ranks.premier ?? "N/A", faceit: ranks.faceit ?? "N/A",
      aim: Number(ratings.aim || 0).toFixed(2), positioning: Number(ratings.positioning || 0).toFixed(2),
      utility: Number(ratings.utility || 0).toFixed(2), clutch: Number(ratings.clutch || 0).toFixed(2),
    };
  }

  function profileHtml(item) {
    const stat = (label, value, colour = "text-amber-400") => `<div class="rounded-xl bg-slate-900 p-4"><dt class="text-slate-400">${label}</dt><dd class="mt-1 font-bold ${colour}">${escapeHtml(value)}</dd></div>`;
    return `<article class="rounded-2xl border border-white/10 bg-white/5 p-6 sm:p-8"><p class="text-sm font-semibold uppercase tracking-wider text-amber-400">Player profile</p><h2 class="mt-1 text-3xl font-bold">${escapeHtml(item.name)}</h2><p class="mt-1 text-sm text-slate-400">Steam64: ${escapeHtml(item.steam64Id)}</p><a href="https://leetify.com/app/profile/${encodeURIComponent(item.steam64Id)}" target="_blank" rel="noopener noreferrer" class="mt-2 inline-block text-sm font-semibold text-pink-400 underline">View on Leetify</a><dl class="mt-6 grid gap-4 sm:grid-cols-2">${stat("จำนวนแมตช์", item.totalMatches)}${stat("อัตราชนะ", `${item.winRate}%`, "text-emerald-400")}${stat("Premier", item.premier)}${stat("FACEIT", item.faceit)}${stat("Aim", item.aim)}${stat("Positioning", item.positioning)}${stat("Utility", item.utility)}${stat("Clutch", item.clutch)}</dl></article>`;
  }

  function resultTarget(form) {
    let target = form.closest(".mx-auto").querySelector("#browser-leetify-result");
    if (!target) {
      target = document.createElement("div");
      target.id = "browser-leetify-result";
      target.className = "space-y-6";
      form.closest(".mx-auto").append(target);
    }
    return target;
  }

  function error(target, message) {
    target.innerHTML = `<div class="rounded-xl border border-rose-400/30 bg-rose-500/10 p-4 text-rose-200" role="alert">${escapeHtml(message)}</div>`;
  }

  async function searchProfile(form) {
    const query = form.elements.query.value.trim();
    const steam64Id = await getSteamId(query);
    const data = await leetifyGet("/v3/profile", steam64Id);
    if (!data?.name) throw new Error("ไม่พบข้อมูลผู้เล่นหรือโปรไฟล์ถูกตั้งเป็นส่วนตัว");
    document.querySelector("#profile-result").innerHTML = profileHtml(player(data, steam64Id));
    localPost("/api/search-history/", { query }).catch(() => {});
  }

  async function searchMatches(form) {
    const query = form.elements.query.value.trim();
    const steam64Id = await getSteamId(query);
    const data = await leetifyGet("/v3/profile/matches", steam64Id);
    const matches = (Array.isArray(data) ? data : data?.matches || []).slice(0, Number(form.elements.limit.value || 5));
    if (!matches.length) throw new Error("ไม่พบประวัติแมตช์ของผู้เล่นนี้");
    const rows = matches.map((match) => {
      const score = (match.team_scores || []).slice(0, 2).map((item) => item?.score ?? item).join(" - ") || "N/A";
      const won = String(match.outcome || "").toLowerCase() === "win";
      return `<tr class="border-b border-white/5"><td class="py-3 font-medium">${escapeHtml(match.map_name || "Unknown")}</td><td class="${won ? "text-emerald-400" : "text-rose-400"}">${won ? "ชนะ" : "แพ้"}</td><td>${escapeHtml(score)}</td><td class="text-slate-400">${escapeHtml(String(match.finished_at || match.started_at || "N/A").slice(0, 16))}</td></tr>`;
    }).join("");
    resultTarget(form).innerHTML = `<section class="overflow-x-auto rounded-2xl border border-white/10 bg-white/5 p-6"><h2 class="mb-4 text-xl font-bold">${escapeHtml(query)} · ${matches.length} แมตช์</h2><table class="w-full min-w-[36rem] text-left text-sm"><thead class="border-b border-white/10 text-slate-400"><tr><th class="py-3">แผนที่</th><th>ผล</th><th>สกอร์</th><th>วันที่</th></tr></thead><tbody>${rows}</tbody></table></section>`;
  }

  async function comparePlayers(form) {
    const [steam1, steam2] = await Promise.all([getSteamId(form.elements.player1.value.trim()), getSteamId(form.elements.player2.value.trim())]);
    const [data1, data2] = await Promise.all([leetifyGet("/v3/profile", steam1), leetifyGet("/v3/profile", steam2)]);
    if (!data1?.name || !data2?.name) throw new Error("ไม่พบข้อมูลผู้เล่นหนึ่งคนหรือทั้งสองคน");
    const first = player(data1, steam1); const second = player(data2, steam2);
    const rows = [["แมตช์", "totalMatches"], ["อัตราชนะ", "winRate"], ["Premier", "premier"], ["FACEIT", "faceit"], ["Aim", "aim"], ["Positioning", "positioning"], ["Utility", "utility"], ["Clutch", "clutch"]].map(([label, key]) => `<tr class="border-b border-white/5"><th class="py-3 font-normal text-slate-400">${label}</th><td>${escapeHtml(first[key])}${key === "winRate" ? "%" : ""}</td><td>${escapeHtml(second[key])}${key === "winRate" ? "%" : ""}</td></tr>`).join("");
    resultTarget(form).innerHTML = `<section class="overflow-x-auto rounded-2xl border border-white/10 bg-white/5 p-6"><table class="w-full min-w-[30rem] text-left"><thead><tr class="border-b border-white/10"><th class="py-3 text-slate-400">สถิติ</th><th class="text-amber-400">${escapeHtml(first.name)}</th><th class="text-amber-400">${escapeHtml(second.name)}</th></tr></thead><tbody>${rows}</tbody></table></section>`;
  }

  document.addEventListener("submit", async (event) => {
    const form = event.target.closest("[data-leetify-browser-form]");
    if (!form || !apiKey()) return;
    event.preventDefault(); event.stopImmediatePropagation();
    const button = form.querySelector('button[type="submit"], button:not([type])');
    if (button) button.disabled = true;
    try {
      if (form.dataset.leetifyBrowserForm === "profile") await searchProfile(form);
      if (form.dataset.leetifyBrowserForm === "matches") await searchMatches(form);
      if (form.dataset.leetifyBrowserForm === "compare") await comparePlayers(form);
    } catch (exception) {
      error(form.dataset.leetifyBrowserForm === "profile" ? document.querySelector("#profile-result") : resultTarget(form), exception.message || "ค้นหาข้อมูลจาก Leetify ไม่สำเร็จ");
    } finally {
      if (button) button.disabled = false;
    }
  }, true);

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-steam-id]");
    if (!button) return;
    try {
      await navigator.clipboard.writeText(button.dataset.copySteamId);
      button.textContent = "คัดลอกแล้ว";
      window.setTimeout(() => { button.textContent = "คัดลอก"; }, 2000);
    } catch { button.textContent = "คัดลอกไม่สำเร็จ"; }
  });
})();