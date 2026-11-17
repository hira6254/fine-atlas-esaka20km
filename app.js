/* ==========================================================================
   FINE ATLAS — 江坂20km圏内 お魚カスタム定期便 営業図鑑 & 仕入・配送戦略 (app.js)
   Interactive Logic: 60-Store Atlas, JST Call Radar, CRM, AI Procurement & P&L Sim
   ========================================================================== */

(function () {
  "use strict";

  const STORAGE_KEY = "fine_atlas_esaka20km_crm_v1";
  const THEME_KEY = "fine_atlas_esaka20km_theme";

  const STORES = window.FINE_ATLAS_STORES || [];
  const FISH_CATALOG = window.FINE_ATLAS_FISH_CATALOG || [];
  const PLAYBOOK = window.FINE_ATLAS_PLAYBOOK || [];
  const PROCUREMENT = window.FINE_ATLAS_PROCUREMENT || { items: [], freezingComparison: [], sources: [] };
  const DELIVERY = window.FINE_ATLAS_DELIVERY_MODELS || { models: [], weekdayClusters: [] };

  const state = {
    mode: "sales",
    fish: "ALL",
    search: "",
    segment: "ALL",
    area: "ALL",
    sort: "priority",
    activeTags: new Set(),
    procTier: "ALL",
    sim: {
      stores: 39,
      order: 28000,
      drops: 4,
      gm: 40
    },
    crm: loadCrmState()
  };

  function loadCrmState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (_e) {
      return {};
    }
  }

  function saveCrmState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state.crm));
    } catch (_e) {
      // Ignore storage quota errors in restricted contexts
    }
  }

  function getStoreStatus(id) {
    return (state.crm[id] && state.crm[id].status) || "未架電";
  }

  function getStoreMemo(id) {
    return (state.crm[id] && state.crm[id].memo) || "";
  }

  function setStoreCrm(id, patch) {
    state.crm[id] = Object.assign({ status: "未架電", memo: "" }, state.crm[id] || {}, patch);
    saveCrmState();
    updateSummaryMetrics();
  }

  // Get current JST hours & minutes
  function getJstNowMinutes() {
    const now = new Date();
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Tokyo",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false
    }).formatToParts(now);
    let h = 0;
    let m = 0;
    for (const p of parts) {
      if (p.type === "hour") h = parseInt(p.value, 10) % 24;
      if (p.type === "minute") m = parseInt(p.value, 10);
    }
    return { h, m, total: h * 60 + m };
  }

  function isWithinCallWindow(windowStr, totalMinutes) {
    if (!windowStr) return false;
    const ranges = windowStr.split(/[\n/・,]+/);
    for (const r of ranges) {
      const match = r.match(/(\d{1,2}):(\d{2})\s*[〜~\-]\s*(\d{1,2}):(\d{2})/);
      if (match) {
        const start = parseInt(match[1], 10) * 60 + parseInt(match[2], 10);
        const end = parseInt(match[3], 10) * 60 + parseInt(match[4], 10);
        if (totalMinutes >= start && totalMinutes <= end) {
          return true;
        }
      }
    }
    return false;
  }

  function formatYen(num) {
    const rounded = Math.round(Number(num || 0));
    if (rounded < 0) {
      return "-¥" + Math.abs(rounded).toLocaleString("ja-JP");
    }
    return "¥" + rounded.toLocaleString("ja-JP");
  }

  function formatSignedYen(num) {
    const rounded = Math.round(Number(num || 0));
    if (rounded > 0) return "+¥" + rounded.toLocaleString("ja-JP");
    if (rounded < 0) return "-¥" + Math.abs(rounded).toLocaleString("ja-JP");
    return "¥0";
  }

  function showToast(msg) {
    const el = document.getElementById("toast-banner");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("is-visible");
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => {
      el.classList.remove("is-visible");
    }, 2400);
  }

  function copyText(text, label) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showToast("📋 " + label + " をコピーしました");
      }).catch(() => fallbackCopy(text, label));
    } else {
      fallbackCopy(text, label);
    }
  }

  function fallbackCopy(text, label) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
      showToast("📋 " + label + " をコピーしました");
    } catch (_e) {
      showToast("コピーに失敗しました");
    }
    document.body.removeChild(ta);
  }

  // Primary Workspace Mode Activation
  function activateMode(mode) {
    state.mode = mode === "procurement" ? "procurement" : "sales";
    const salesBtn = document.getElementById("mode-sales");
    const procBtn = document.getElementById("mode-procurement");
    const salesWs = document.getElementById("workspace-sales");
    const procWs = document.getElementById("workspace-procurement");

    const isSales = state.mode === "sales";
    if (salesBtn) {
      salesBtn.classList.toggle("is-active", isSales);
      salesBtn.setAttribute("aria-selected", isSales ? "true" : "false");
    }
    if (procBtn) {
      procBtn.classList.toggle("is-active", !isSales);
      procBtn.setAttribute("aria-selected", !isSales ? "true" : "false");
    }
    if (salesWs) salesWs.hidden = !isSales;
    if (procWs) procWs.hidden = isSales;
  }

  // Update Top Summary KPIs & Clock
  function updateSummaryMetrics() {
    const jst = getJstNowMinutes();
    const pad = (n) => String(n).padStart(2, "0");
    const clockEl = document.getElementById("live-jst-clock");
    if (clockEl) {
      clockEl.textContent = "日本時間 " + pad(jst.h) + ":" + pad(jst.m) + " 現在";
    }

    const total = STORES.length;
    const sCount = STORES.filter((s) => s.rank === "S").length;
    const aCount = STORES.filter((s) => s.rank === "A").length;
    const entryMrr = total * 10000;
    const expandMrr = STORES.reduce((acc, s) => acc + (s.monthlySales || 0), 0);
    const callReady = STORES.filter((s) => isWithinCallWindow(s.callWindow, jst.total)).length;
    const progressed = STORES.filter((s) => getStoreStatus(s.id) !== "未架電").length;

    const setTxt = (id, val) => {
      const node = document.getElementById(id);
      if (node) node.textContent = val;
    };

    setTxt("kpi-total-stores", total + " 店舗");
    setTxt("kpi-rank-breakdown", "Sランク " + sCount + "店 ／ Aランク " + aCount + "店");
    setTxt("kpi-entry-mrr", formatYen(entryMrr));
    setTxt("kpi-expand-mrr", formatYen(expandMrr));
    setTxt("kpi-call-ready", callReady + " 店舗");
    setTxt("kpi-progress-count", progressed + " / " + total + " 店");
  }

  // Render 5-Fish Selector Bar & Fish Lore
  function renderFishBar() {
    const grid = document.getElementById("fish-selector-grid");
    const drawer = document.getElementById("fish-lore-drawer");
    if (!grid || !drawer) return;

    grid.textContent = "";

    FISH_CATALOG.forEach((item) => {
      const count = item.key === "ALL"
        ? STORES.length
        : STORES.filter((s) => (s.fishTags || []).includes(item.key)).length;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "fish-chip-btn" + (state.fish === item.key ? " is-active" : "");
      btn.addEventListener("click", () => {
        state.fish = item.key;
        renderFishBar();
        renderStores();
      });

      const top = document.createElement("div");
      top.className = "fish-chip-top";
      const nameSpan = document.createElement("span");
      nameSpan.textContent = item.icon + " " + item.label;
      const countSpan = document.createElement("span");
      countSpan.className = "fish-chip-count";
      countSpan.textContent = count + "店";
      top.appendChild(nameSpan);
      top.appendChild(countSpan);

      const sub = document.createElement("div");
      sub.className = "fish-chip-prep";
      sub.textContent = item.prepForms;

      btn.appendChild(top);
      btn.appendChild(sub);
      grid.appendChild(btn);
    });

    const activeFish = FISH_CATALOG.find((f) => f.key === state.fish) || FISH_CATALOG[0];
    drawer.textContent = "";
    if (activeFish) {
      const title = document.createElement("span");
      title.className = "fish-lore-title";
      title.textContent = "♓ 魚好き目利きメモ｜" + activeFish.label + "：";

      const desc = document.createElement("span");
      desc.textContent = activeFish.lore;

      drawer.appendChild(title);
      drawer.appendChild(desc);
    }
  }

  // Filter & Sort Stores
  function getFilteredStores() {
    const jst = getJstNowMinutes();
    const q = state.search.trim().toLowerCase();

    const filtered = STORES.filter((s) => {
      if (state.fish !== "ALL" && !(s.fishTags || []).includes(state.fish)) {
        return false;
      }
      if (state.segment !== "ALL" && s.segmentCode !== state.segment) {
        return false;
      }
      if (state.area !== "ALL" && s.areaGroup !== state.area) {
        return false;
      }
      if (state.activeTags.has("ワンオペ・少人数") && !(s.painTags || []).includes("ワンオペ・少人数")) {
        return false;
      }
      if (state.activeTags.has("SNS発信活発") && !(s.painTags || []).includes("SNS発信活発")) {
        return false;
      }
      if (state.activeTags.has("市場遠方メリット") && !(s.painTags || []).includes("市場遠方メリット")) {
        return false;
      }
      if (state.activeTags.has("CALL_NOW") && !isWithinCallWindow(s.callWindow, jst.total)) {
        return false;
      }
      if (state.activeTags.has("UNCALLED") && getStoreStatus(s.id) !== "未架電") {
        return false;
      }
      if (q) {
        const hay = [
          s.name,
          s.kana,
          s.station,
          s.address,
          s.genre,
          s.hookProduct,
          s.customPlan10k,
          s.snsEvidence,
          s.whySell,
          s.pitchSample,
          s.pitchSub10k,
          (s.fishTags || []).join(" "),
          (s.painTags || []).join(" ")
        ].join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    filtered.sort((a, b) => {
      if (state.sort === "distance") {
        return a.distanceKm - b.distanceKm;
      }
      if (state.sort === "potential") {
        return (b.monthlySales || 0) - (a.monthlySales || 0);
      }
      if (a.rank !== b.rank) {
        return a.rank === "S" ? -1 : 1;
      }
      return a.id - b.id;
    });

    return filtered;
  }

  // Render Store Cards
  function renderStores() {
    const grid = document.getElementById("store-grid");
    const counter = document.getElementById("result-counter");
    if (!grid) return;

    const list = getFilteredStores();
    const jst = getJstNowMinutes();

    if (counter) {
      counter.textContent = "表示中: " + list.length + " / " + STORES.length + " 店舗";
    }

    grid.textContent = "";

    if (list.length === 0) {
      const empty = document.createElement("div");
      empty.style.gridColumn = "1 / -1";
      empty.style.padding = "36px 20px";
      empty.style.textAlign = "center";
      empty.style.backgroundColor = "var(--bg-elevated)";
      empty.style.borderRadius = "var(--radius-lg)";
      empty.textContent = "該当する店舗がありません。検索ワードや絞り込み条件をリセットしてみてください。";
      grid.appendChild(empty);
      return;
    }

    list.forEach((store) => {
      const card = document.createElement("article");
      card.className = "store-card";
      card.id = "store-card-" + store.id;

      // 1. Header
      const head = document.createElement("div");
      head.className = "store-card-head";

      const titleWrap = document.createElement("div");
      titleWrap.className = "store-title-wrap";

      const badges = document.createElement("div");
      badges.className = "store-badges-top";

      const rankBadge = document.createElement("span");
      rankBadge.className = "rank-badge rank-" + store.rank;
      rankBadge.textContent = store.rank + "ランク";
      badges.appendChild(rankBadge);

      const distChip = document.createElement("span");
      distChip.className = "distance-chip";
      distChip.textContent = "江坂から " + store.distanceKm.toFixed(1) + "km｜" + store.station;
      badges.appendChild(distChip);

      const segChip = document.createElement("span");
      segChip.className = "segment-chip";
      segChip.textContent = store.segmentLabel;
      badges.appendChild(segChip);

      if (isWithinCallWindow(store.callWindow, jst.total)) {
        const callChip = document.createElement("span");
        callChip.className = "call-now-chip";
        callChip.textContent = "🟢 今が架電時！";
        badges.appendChild(callChip);
      }

      const h2 = document.createElement("h2");
      h2.className = "store-name";
      h2.textContent = "No." + store.id + " " + store.name;

      const metaSub = document.createElement("div");
      metaSub.className = "store-meta-sub";
      metaSub.textContent = store.genre + "（" + store.priceRange + "）｜📍 " + store.address;

      titleWrap.appendChild(badges);
      titleWrap.appendChild(h2);
      titleWrap.appendChild(metaSub);
      head.appendChild(titleWrap);
      card.appendChild(head);

      // 2. Custom ¥10,000 Subscription Plan Box
      const prepBox = document.createElement("div");
      prepBox.className = "prep-recipe-box";

      const prepHead = document.createElement("div");
      prepHead.className = "prep-recipe-header";
      const prepTitle = document.createElement("span");
      prepTitle.textContent = "🐟 最優先フック：" + store.hookProduct + "（" + store.fitSummary + "）";
      const potSpan = document.createElement("span");
      potSpan.style.fontFamily = "var(--font-mono)";
      potSpan.textContent = "入口 ¥10,000 → 育成後 " + formatYen(store.monthlySales) + "/月";
      prepHead.appendChild(prepTitle);
      prepHead.appendChild(potSpan);

      const prepBody = document.createElement("div");
      prepBody.className = "prep-recipe-body";
      prepBody.textContent = "📦 月1万円カスタム定期便レシピ案：" + store.customPlan10k;

      prepBox.appendChild(prepHead);
      prepBox.appendChild(prepBody);
      card.appendChild(prepBox);

      // 3. SNS & Review Evidence + Labor Pain Analysis
      const evSec = document.createElement("div");
      evSec.className = "evidence-section";

      const snsBlock = document.createElement("div");
      snsBlock.className = "evidence-block";
      const snsLbl = document.createElement("div");
      snsLbl.className = "evidence-label";
      snsLbl.textContent = "📱 SNS・口コミ精査ファクト（" + (store.snsSourceLabel || "Instagram / Googleマップ / 食べログ") + "）";
      const snsP = document.createElement("p");
      snsP.className = "evidence-text";
      snsP.textContent = store.snsEvidence;
      snsBlock.appendChild(snsLbl);
      snsBlock.appendChild(snsP);

      const painBlock = document.createElement("div");
      painBlock.className = "evidence-block";
      const painLbl = document.createElement("div");
      painLbl.className = "evidence-label pain-label";
      painLbl.textContent = "💡 なぜ刺さるか（調理人不足・仕込み負荷・発注シグナル推論）";
      const painP = document.createElement("p");
      painP.className = "evidence-text";
      painP.textContent = store.whySell;
      painBlock.appendChild(painLbl);
      painBlock.appendChild(painP);

      evSec.appendChild(snsBlock);
      evSec.appendChild(painBlock);
      card.appendChild(evSec);

      // 4. Two-Stage Killer Talk Script
      const details = document.createElement("details");
      details.className = "pitch-details";
      if (store.rank === "S" && list.length <= 6) {
        details.open = true;
      }

      const summary = document.createElement("summary");
      summary.className = "pitch-summary";
      const sumLeft = document.createElement("span");
      sumLeft.textContent = "📞 二段構え営業トークを開く（サンプル打診 → 月1万円カスタム定期便）";
      const sumRight = document.createElement("span");
      sumRight.className = "pitch-time-hint";
      sumRight.textContent = "推奨架電：" + store.callWindow.replace(/\n/g, " / ");
      summary.appendChild(sumLeft);
      summary.appendChild(sumRight);

      const pitchBody = document.createElement("div");
      pitchBody.className = "pitch-body";

      const step1 = document.createElement("div");
      step1.className = "pitch-step";
      const s1Tag = document.createElement("span");
      s1Tag.className = "pitch-step-tag";
      s1Tag.textContent = "第一声｜無料サンプル・お試しセット打診";
      const s1Quote = document.createElement("p");
      s1Quote.className = "pitch-quote";
      s1Quote.textContent = store.pitchSample;
      step1.appendChild(s1Tag);
      step1.appendChild(s1Quote);

      const step2 = document.createElement("div");
      step2.className = "pitch-step";
      const s2Tag = document.createElement("span");
      s2Tag.className = "pitch-step-tag";
      s2Tag.textContent = "第二声｜手応え後の「月額1万円・加工度カスタム定期便」提案";
      const s2Quote = document.createElement("p");
      s2Quote.className = "pitch-quote";
      s2Quote.textContent = store.pitchSub10k;
      step2.appendChild(s2Tag);
      step2.appendChild(s2Quote);

      pitchBody.appendChild(step1);
      pitchBody.appendChild(step2);
      details.appendChild(summary);
      details.appendChild(pitchBody);
      card.appendChild(details);

      // 5. CRM Status, Memo & Action Links
      const footer = document.createElement("div");
      footer.className = "card-footer-crm";

      const crmRow = document.createElement("div");
      crmRow.className = "crm-controls-row";

      const statusSelect = document.createElement("select");
      statusSelect.className = "status-select";
      statusSelect.setAttribute("aria-label", store.name + " の架電ステータス");
      const currentStatus = getStoreStatus(store.id);
      statusSelect.dataset.status = currentStatus;

      ["未架電", "不在・再架電", "サンプル送付OK", "試食評価中", "定期便成約", "見送り"].forEach((optVal) => {
        const opt = document.createElement("option");
        opt.value = optVal;
        opt.textContent = optVal;
        if (optVal === currentStatus) opt.selected = true;
        statusSelect.appendChild(opt);
      });

      statusSelect.addEventListener("change", () => {
        statusSelect.dataset.status = statusSelect.value;
        setStoreCrm(store.id, { status: statusSelect.value });
        showToast("✅ " + store.name + " を「" + statusSelect.value + "」に更新しました");
      });

      const memoInput = document.createElement("input");
      memoInput.type = "text";
      memoInput.className = "memo-input";
      memoInput.placeholder = "富田君メモ（例：水曜15時に大将再架電、甘鯛フィレ興味あり）";
      memoInput.value = getStoreMemo(store.id);
      memoInput.addEventListener("change", () => {
        setStoreCrm(store.id, { memo: memoInput.value });
        showToast("💾 メモを保存しました");
      });

      crmRow.appendChild(statusSelect);
      crmRow.appendChild(memoInput);

      const linksRow = document.createElement("div");
      linksRow.className = "external-links-row";

      const mapUrl = "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(store.name + " " + store.address);
      const mapLink = document.createElement("a");
      mapLink.href = mapUrl;
      mapLink.target = "_blank";
      mapLink.rel = "noopener noreferrer";
      mapLink.className = "mini-link-btn";
      mapLink.textContent = "📍 Googleマップ・口コミ";

      const snsUrl = store.instagramUrl || ("https://www.google.com/search?q=" + encodeURIComponent(store.name + " Instagram " + store.station));
      const snsLink = document.createElement("a");
      snsLink.href = snsUrl;
      snsLink.target = "_blank";
      snsLink.rel = "noopener noreferrer";
      snsLink.className = "mini-link-btn";
      snsLink.textContent = store.instagramHandle ? ("📸 Insta (" + store.instagramHandle + ")") : "📸 公式・SNS確認";

      const copyBtn1 = document.createElement("button");
      copyBtn1.type = "button";
      copyBtn1.className = "mini-link-btn";
      copyBtn1.textContent = "📋 第一声コピー";
      copyBtn1.addEventListener("click", () => copyText(store.pitchSample, store.name + " 第一声トーク"));

      const copyBtn2 = document.createElement("button");
      copyBtn2.type = "button";
      copyBtn2.className = "mini-link-btn";
      copyBtn2.textContent = "📋 月1万定期便トーク";
      copyBtn2.addEventListener("click", () => copyText(store.pitchSub10k, store.name + " 定期便トーク"));

      linksRow.appendChild(mapLink);
      linksRow.appendChild(snsLink);
      linksRow.appendChild(copyBtn1);
      linksRow.appendChild(copyBtn2);

      footer.appendChild(crmRow);
      footer.appendChild(linksRow);
      card.appendChild(footer);

      grid.appendChild(card);
    });
  }

  // Render 20km Esaka SVG Radar Map (60 Stores)
  function renderRadarMap() {
    const container = document.getElementById("esaka-radar-container");
    if (!container) return;

    const esakaLat = 34.7588;
    const esakaLng = 135.4969;
    const size = 420;
    const cx = size / 2;
    const cy = size / 2;
    const maxKm = 20;
    const scale = (size / 2 - 34) / maxKm;

    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 " + size + " " + size);
    svg.style.width = "100%";
    svg.style.height = "auto";

    [20, 15, 10, 5].forEach((km) => {
      const circle = document.createElementNS(ns, "circle");
      circle.setAttribute("cx", cx);
      circle.setAttribute("cy", cy);
      circle.setAttribute("r", km * scale);
      circle.setAttribute("fill", km === 20 ? "hsla(198, 45%, 50%, 0.06)" : "none");
      circle.setAttribute("stroke", "hsla(198, 35%, 45%, 0.28)");
      circle.setAttribute("stroke-dasharray", km === 20 ? "none" : "4 4");
      svg.appendChild(circle);

      const lbl = document.createElementNS(ns, "text");
      lbl.setAttribute("x", cx + 4);
      lbl.setAttribute("y", cy - km * scale + 12);
      lbl.setAttribute("font-size", "10");
      lbl.setAttribute("fill", "currentColor");
      lbl.setAttribute("opacity", "0.55");
      lbl.textContent = km + "km";
      svg.appendChild(lbl);
    });

    const hLine = document.createElementNS(ns, "line");
    hLine.setAttribute("x1", 20);
    hLine.setAttribute("y1", cy);
    hLine.setAttribute("x2", size - 20);
    hLine.setAttribute("y2", cy);
    hLine.setAttribute("stroke", "hsla(198, 35%, 45%, 0.2)");
    svg.appendChild(hLine);

    const vLine = document.createElementNS(ns, "line");
    vLine.setAttribute("x1", cx);
    vLine.setAttribute("y1", 20);
    vLine.setAttribute("x2", cx);
    vLine.setAttribute("y2", size - 20);
    vLine.setAttribute("stroke", "hsla(198, 35%, 45%, 0.2)");
    svg.appendChild(vLine);

    const dirLabels = [
      { x: cx, y: 14, text: "北（千里中央・箕面・高槻）", anchor: "middle" },
      { x: cx, y: size - 6, text: "南（福島・北新地・本町・南船場）", anchor: "middle" },
      { x: 10, y: cy - 6, text: "西（伊丹・苦楽園・芦屋）", anchor: "start" },
      { x: size - 10, y: cy - 6, text: "東（吹田・高槻）", anchor: "end" }
    ];
    dirLabels.forEach((d) => {
      const t = document.createElementNS(ns, "text");
      t.setAttribute("x", d.x);
      t.setAttribute("y", d.y);
      t.setAttribute("text-anchor", d.anchor);
      t.setAttribute("font-size", "10.5");
      t.setAttribute("fill", "currentColor");
      t.setAttribute("opacity", "0.7");
      t.textContent = d.text;
      svg.appendChild(t);
    });

    STORES.forEach((s) => {
      if (typeof s.lat !== "number" || typeof s.lng !== "number") return;
      const dyKm = (s.lat - esakaLat) * 111.0;
      const dxKm = (s.lng - esakaLng) * 91.2;
      const px = cx + dxKm * scale;
      const py = cy - dyKm * scale;

      const g = document.createElementNS(ns, "g");
      g.style.cursor = "pointer";

      const dot = document.createElementNS(ns, "circle");
      dot.setAttribute("cx", px);
      dot.setAttribute("cy", py);
      dot.setAttribute("r", s.rank === "S" ? 5.6 : 4.6);
      dot.setAttribute("fill", s.rank === "S" ? "hsl(11, 72%, 50%)" : "hsl(196, 72%, 38%)");
      dot.setAttribute("stroke", "#ffffff");
      dot.setAttribute("stroke-width", "1.4");

      const title = document.createElementNS(ns, "title");
      title.textContent = "No." + s.id + " " + s.name + "（" + s.station + "・江坂から" + s.distanceKm.toFixed(1) + "km）";
      g.appendChild(title);
      g.appendChild(dot);

      g.addEventListener("click", () => {
        activateMode("sales");
        activateTab("tab-stores");
        state.fish = "ALL";
        state.segment = "ALL";
        state.area = "ALL";
        state.search = s.name;
        const searchInput = document.getElementById("search-input");
        if (searchInput) searchInput.value = s.name;
        renderFishBar();
        renderStores();
      });

      svg.appendChild(g);
    });

    const hub = document.createElementNS(ns, "circle");
    hub.setAttribute("cx", cx);
    hub.setAttribute("cy", cy);
    hub.setAttribute("r", 5.8);
    hub.setAttribute("fill", "hsl(41, 88%, 52%)");
    hub.setAttribute("stroke", "#0d1e2d");
    hub.setAttribute("stroke-width", "2");
    svg.appendChild(hub);

    const hubText = document.createElementNS(ns, "text");
    hubText.setAttribute("x", cx + 8);
    hubText.setAttribute("y", cy + 4);
    hubText.setAttribute("font-size", "11");
    hubText.setAttribute("font-weight", "700");
    hubText.setAttribute("fill", "currentColor");
    hubText.textContent = "江坂拠点";
    svg.appendChild(hubText);

    container.textContent = "";
    container.appendChild(svg);
  }

  // Render Objection Handling Playbook
  function renderPlaybook() {
    const wrap = document.getElementById("playbook-list");
    if (!wrap) return;
    wrap.textContent = "";

    PLAYBOOK.forEach((item) => {
      const card = document.createElement("article");
      card.className = "playbook-card";

      const col1 = document.createElement("div");
      col1.className = "playbook-fish-col";
      const h3 = document.createElement("h3");
      h3.textContent = item.category;
      const targetP = document.createElement("div");
      targetP.style.fontSize = "0.82rem";
      targetP.style.color = "var(--ink-muted)";
      targetP.textContent = "主な対象：" + item.targetGenre;
      const sampleBadge = document.createElement("div");
      sampleBadge.style.marginTop = "8px";
      sampleBadge.style.fontSize = "0.78rem";
      sampleBadge.style.fontWeight = "700";
      sampleBadge.style.color = "var(--accent-amber)";
      sampleBadge.textContent = "🎁 推奨サンプル：" + item.sampleSet;
      col1.appendChild(h3);
      col1.appendChild(targetP);
      col1.appendChild(sampleBadge);

      const col2 = document.createElement("div");
      col2.className = "playbook-objection-box";
      const objTitle = document.createElement("div");
      objTitle.style.fontSize = "0.76rem";
      objTitle.style.fontWeight = "700";
      objTitle.style.color = "var(--accent-vermilion)";
      objTitle.style.marginBottom = "4px";
      objTitle.textContent = "🗣️ 関西の料理長・店主から出る典型的な断り文句";
      const objQuote = document.createElement("p");
      objQuote.style.margin = "0 0 8px";
      objQuote.style.fontWeight = "700";
      objQuote.style.fontSize = "0.88rem";
      objQuote.textContent = item.objection;
      const truthP = document.createElement("p");
      truthP.style.margin = "0";
      truthP.style.fontSize = "0.82rem";
      truthP.style.color = "var(--ink-secondary)";
      truthP.textContent = "【裏の本音・ペイン】" + item.realPain;
      col2.appendChild(objTitle);
      col2.appendChild(objQuote);
      col2.appendChild(truthP);

      const col3 = document.createElement("div");
      col3.className = "playbook-counter-box";
      const cntTitle = document.createElement("div");
      cntTitle.style.fontSize = "0.76rem";
      cntTitle.style.fontWeight = "700";
      cntTitle.style.color = "var(--accent-tide)";
      cntTitle.style.marginBottom = "4px";
      cntTitle.textContent = "⚡ 一撃でサンプル送付＆月1万定期便に変える切り返しトーク";
      const cntP = document.createElement("p");
      cntP.style.margin = "0 0 10px";
      cntP.style.fontSize = "0.86rem";
      cntP.style.lineHeight = "1.65";
      cntP.textContent = item.counterTalk;
      const copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.className = "mini-link-btn";
      copyBtn.textContent = "📋 切り返しトークをコピー";
      copyBtn.addEventListener("click", () => copyText(item.counterTalk, item.category + " 切り返しトーク"));
      col3.appendChild(cntTitle);
      col3.appendChild(cntP);
      col3.appendChild(copyBtn);

      card.appendChild(col1);
      card.appendChild(col2);
      card.appendChild(col3);
      wrap.appendChild(card);
    });
  }

  // =========================================================================
  // WORKSPACE B: 全国冷凍魚 仕入AI調査 ＆ 江坂配送モデル試算
  // =========================================================================
  function renderProcurementStaticMeta() {
    const execEl = document.getElementById("proc-exec-conclusion");
    if (execEl && DELIVERY.executiveConclusion) {
      execEl.textContent = DELIVERY.executiveConclusion;
    }
    const depotEl = document.getElementById("delivery-depot-label");
    if (depotEl && DELIVERY.depotName) {
      depotEl.textContent = "拠点前提：" + DELIVERY.depotName;
    }
    const hlEl = document.getElementById("proc-headline");
    if (hlEl && PROCUREMENT.headline) {
      hlEl.textContent = "🐟 " + PROCUREMENT.headline;
    }
    const leadEl = document.getElementById("proc-summary-lead");
    if (leadEl && PROCUREMENT.summaryLead) {
      leadEl.textContent = PROCUREMENT.summaryLead;
    }

    // Freezing comparison cards
    const freezeGrid = document.getElementById("freezing-cards-grid");
    if (freezeGrid) {
      freezeGrid.textContent = "";
      (PROCUREMENT.freezingComparison || []).forEach((fc, idx) => {
        const card = document.createElement("article");
        card.className = "freezing-card" + (idx === 2 ? " is-best" : "");

        const topBadge = document.createElement("span");
        topBadge.className = "rank-badge " + (idx === 0 ? "rank-S" : "rank-A");
        topBadge.style.alignSelf = "flex-start";
        topBadge.textContent = "氷結晶通過：" + fc.passTime;

        const title = document.createElement("h3");
        title.className = "delivery-model-title";
        title.textContent = fc.method;

        const drip = document.createElement("div");
        drip.className = "freezing-drip-stat " + (idx === 0 ? "profit-negative" : "profit-positive");
        drip.textContent = "解凍ドリップ率：" + fc.dripRate;

        const cellP = document.createElement("p");
        cellP.className = "delivery-meta-note";
        cellP.textContent = fc.cellState;

        const fitP = document.createElement("div");
        fitP.style.fontSize = "0.82rem";
        fitP.style.fontWeight = "700";
        fitP.style.marginTop = "auto";
        fitP.textContent = fc.culinaryFit;

        card.appendChild(topBadge);
        card.appendChild(title);
        card.appendChild(drip);
        card.appendChild(cellP);
        card.appendChild(fitP);
        freezeGrid.appendChild(card);
      });
    }

    // Sources list
    const srcList = document.getElementById("proc-sources-list");
    if (srcList) {
      srcList.textContent = "";
      (PROCUREMENT.sources || []).forEach((src) => {
        const li = document.createElement("li");
        li.textContent = src;
        srcList.appendChild(li);
      });
    }

    // Weekday 4-Cluster Schedule
    const clTbody = document.getElementById("cluster-schedule-tbody");
    if (clTbody) {
      clTbody.textContent = "";
      let sumStores = 0;
      (DELIVERY.weekdayClusters || []).forEach((cl) => {
        sumStores += Number(cl.targetStoresCount || 0);
        const tr = document.createElement("tr");
        const tdDay = document.createElement("td");
        tdDay.style.fontWeight = "700";
        tdDay.textContent = cl.day;

        const tdName = document.createElement("td");
        tdName.style.fontWeight = "700";
        tdName.textContent = cl.clusterName;

        const tdArea = document.createElement("td");
        tdArea.textContent = cl.areas;

        const tdRoute = document.createElement("td");
        tdRoute.textContent = cl.routeNote;

        const tdCnt = document.createElement("td");
        tdCnt.className = "num-col";
        tdCnt.style.fontWeight = "700";
        tdCnt.textContent = cl.targetStoresCount + " 店舗";

        tr.appendChild(tdDay);
        tr.appendChild(tdName);
        tr.appendChild(tdArea);
        tr.appendChild(tdRoute);
        tr.appendChild(tdCnt);
        clTbody.appendChild(tr);
      });

      const totTr = document.createElement("tr");
      totTr.style.backgroundColor = "var(--bg-subtle)";
      const totLabel = document.createElement("td");
      totLabel.colSpan = 4;
      totLabel.style.fontWeight = "700";
      totLabel.textContent = "合計（月曜日は江坂デポ入荷検品・ピッキング＆富田君の新規サンプル持参訪問日）";
      const totVal = document.createElement("td");
      totVal.className = "num-col";
      totVal.style.fontWeight = "700";
      totVal.textContent = sumStores + " 店舗";
      totTr.appendChild(totLabel);
      totTr.appendChild(totVal);
      clTbody.appendChild(totTr);
    }
  }

  function renderProcurementTable() {
    const tbody = document.getElementById("proc-items-tbody");
    if (!tbody) return;
    tbody.textContent = "";

    const items = (PROCUREMENT.items || []).filter((it) => {
      if (state.procTier === "ALL") return true;
      return it.tier === state.procTier;
    });

    items.forEach((it) => {
      const tr = document.createElement("tr");

      const faMarginRate = ((it.atlasSellKg - it.wholesaleMid) / it.atlasSellKg) * 100;
      const dishCost = (it.atlasSellKg * (it.servingG / 1000)) / it.yieldRate;
      const flRatio = (dishCost / it.menuPriceStd) * 100;

      // Col 1: No
      const tdNo = document.createElement("td");
      tdNo.className = "num-col";
      tdNo.textContent = String(it.no);

      // Col 2: Tier badge
      const tdTier = document.createElement("td");
      const badge = document.createElement("span");
      badge.className = "rank-badge " + (it.tier === "主力5品目" ? "rank-S" : "rank-A");
      badge.textContent = it.tier;
      tdTier.appendChild(badge);

      // Col 3: Name & Origin Spec
      const tdName = document.createElement("td");
      const strongName = document.createElement("div");
      strongName.style.fontWeight = "700";
      strongName.style.fontSize = "0.9rem";
      strongName.textContent = it.name;
      const specDiv = document.createElement("div");
      specDiv.style.fontSize = "0.76rem";
      specDiv.style.color = "var(--ink-secondary)";
      specDiv.style.marginTop = "3px";
      specDiv.textContent = it.originSpec;
      tdName.appendChild(strongName);
      tdName.appendChild(specDiv);

      // Col 4: Wholesale Range
      const tdWh = document.createElement("td");
      tdWh.className = "num-col";
      const whMain = document.createElement("div");
      whMain.style.fontWeight = "700";
      whMain.textContent = formatYen(it.wholesaleLow) + "〜" + formatYen(it.wholesaleHigh);
      const whSub = document.createElement("div");
      whSub.style.fontSize = "0.74rem";
      whSub.style.color = "var(--ink-muted)";
      whSub.textContent = "標準仕入 " + formatYen(it.wholesaleMid) + "/kg";
      tdWh.appendChild(whMain);
      tdWh.appendChild(whSub);

      // Col 5: FA Wholesale Sell Price & Margin
      const tdFa = document.createElement("td");
      tdFa.className = "num-col";
      const faMain = document.createElement("div");
      faMain.style.fontWeight = "700";
      faMain.style.color = "var(--accent-amber)";
      faMain.textContent = formatYen(it.atlasSellKg) + "/kg";
      const faSub = document.createElement("div");
      faSub.style.fontSize = "0.74rem";
      faSub.style.color = "var(--accent-kelp)";
      faSub.textContent = "FA粗利率 " + faMarginRate.toFixed(1) + "%";
      tdFa.appendChild(faMain);
      tdFa.appendChild(faSub);

      // Col 6: Yield Rate
      const tdYield = document.createElement("td");
      const yMain = document.createElement("div");
      yMain.style.fontFamily = "var(--font-mono)";
      yMain.style.fontWeight = "700";
      yMain.textContent = Math.round(it.yieldRate * 100) + "%";
      const ySub = document.createElement("div");
      ySub.style.fontSize = "0.74rem";
      ySub.style.color = "var(--ink-secondary)";
      ySub.textContent = it.rawFishYieldNote;
      tdYield.appendChild(yMain);
      tdYield.appendChild(ySub);

      // Col 7: Per-Dish Cost & Restaurant Menu Price
      const tdFl = document.createElement("td");
      tdFl.className = "num-col";
      const flCost = document.createElement("div");
      flCost.style.fontWeight = "700";
      flCost.textContent = formatYen(dishCost) + " /皿 (" + it.servingG + "g)";
      const flMenu = document.createElement("div");
      flMenu.style.fontSize = "0.74rem";
      flMenu.style.color = "var(--ink-secondary)";
      flMenu.textContent = "売価 " + formatYen(it.menuPriceStd) + " ";
      const flPill = document.createElement("span");
      flPill.className = "fl-pill";
      flPill.textContent = "原価率 " + flRatio.toFixed(1) + "%";
      flMenu.appendChild(flPill);
      tdFl.appendChild(flCost);
      tdFl.appendChild(flMenu);

      // Col 8: Freezing Edge & Upsell Pitch
      const tdEdge = document.createElement("td");
      const edgeP = document.createElement("div");
      edgeP.style.fontSize = "0.79rem";
      edgeP.textContent = "❄️ " + it.freezingEdge;
      const pitchP = document.createElement("div");
      pitchP.style.fontSize = "0.79rem";
      pitchP.style.fontWeight = "600";
      pitchP.style.color = "var(--accent-tide)";
      pitchP.style.marginTop = "4px";
      pitchP.textContent = "🎯 " + it.upsellPitch;
      tdEdge.appendChild(edgeP);
      tdEdge.appendChild(pitchP);

      tr.appendChild(tdNo);
      tr.appendChild(tdTier);
      tr.appendChild(tdName);
      tr.appendChild(tdWh);
      tr.appendChild(tdFa);
      tr.appendChild(tdYield);
      tr.appendChild(tdFl);
      tr.appendChild(tdEdge);
      tbody.appendChild(tr);
    });
  }

  function renderDeliverySimulator() {
    const grid = document.getElementById("delivery-models-grid");
    const alertBanner = document.getElementById("sim-alert-banner");
    if (!grid) return;

    const stores = state.sim.stores;
    const order = state.sim.order;
    const drops = state.sim.drops;
    const gmRate = state.sim.gm / 100;

    // Update control value labels
    const setTxt = (id, txt) => {
      const el = document.getElementById(id);
      if (el) el.textContent = txt;
    };
    const dropLabels = {
      1: "月 1 回（まとめ便）",
      2: "月 2 回（隔週）",
      3: "月 3 回",
      4: "月 4 回（毎週）"
    };
    setTxt("sim-stores-val", stores + " 店舗");
    setTxt("sim-order-val", formatYen(order) + " /月");
    setTxt("sim-drops-val", dropLabels[drops] || ("月 " + drops + " 回"));
    setTxt("sim-gm-val", state.sim.gm + "%");

    // Alert check for entry ¥10,000 + weekly Cool shipping
    const perStoreCoolLossCheck = order * gmRate - drops * 1220;
    if (alertBanner) {
      if (perStoreCoolLossCheck < 0) {
        alertBanner.hidden = false;
        alertBanner.textContent =
          "⚠️ 赤字注意：平均発注 " + formatYen(order) + " × 月" + drops + "回クール便だと、1店舗あたり食材粗利 " +
          formatYen(order * gmRate) + " に対し配送費が " + formatYen(drops * 1220) +
          " かかり、1店ごとに毎月 " + formatSignedYen(perStoreCoolLossCheck) +
          " の赤字になります！月1万円台の入口プランは必ず『隔週（月2回以下）』に設定してください。";
      } else {
        alertBanner.hidden = true;
      }
    }

    const baseSales = stores * order;
    const baseGross = baseSales * gmRate;

    // Model 1: Yamato Cool Only
    const m1Ship = stores * drops * 1220;
    const m1Profit = baseGross - m1Ship;
    const m1PerDrop = 1220;

    // Model 2: Own Freezer Light Van Only
    const vanFixed = 235000;
    const vanVar = 140;
    const m2Ship = vanFixed + stores * drops * vanVar;
    const m2Profit = baseGross - m2Ship;
    const m2PerDrop = Math.round(m2Ship / Math.max(1, stores * drops));

    // Model 3: Hybrid Phase Model
    // Phase 1 (<39 stores): Cool shipping, enforcing max 2 drops/mo when order <= 12,000
    // Phase 2 (>=39 stores): 85% Own Van (¥140) + 15% Cool (¥1,220) = ¥302/drop + ¥235,000 fixed, plus +¥6,000/mo face-to-face upsell lift (or +¥3,000 if entry)
    let m3Sales = baseSales;
    let m3Gross = baseGross;
    let m3Ship = 0;
    let m3PhaseLabel = "";
    if (stores < 39) {
      const safeDrops = order <= 12000 ? Math.min(drops, 2) : drops;
      m3Ship = stores * safeDrops * 1220;
      m3PhaseLabel = "現在 Phase 1 適用中（1〜38店：固定費0円クール便＋近隣のみ富田君訪問、1万円枠は隔週2回上限ルール適用）";
    } else {
      const upsellLift = order >= 18000 ? 6000 : 3000;
      m3Sales = stores * (order + upsellLift);
      m3Gross = m3Sales * gmRate;
      const weightedDrop = Math.round(140 * 0.85 + 1220 * 0.15); // 302 yen
      m3Ship = vanFixed + stores * drops * weightedDrop;
      m3PhaseLabel = "現在 Phase 2 適用中（39店〜：火〜金自社冷凍バン85%＋遠方クール便15%併用、対面納品による単価+" + formatYen(upsellLift) + "効果反映）";
    }
    const m3Profit = m3Gross - m3Ship;
    const m3PerDrop = Math.round(m3Ship / Math.max(1, stores * drops));

    const calcResults = [
      {
        meta: DELIVERY.models[0] || { name: "① ヤマトクール宅急便単独", badge: "初期向き", breakevenStoresNote: "", pros: "" },
        sales: baseSales,
        gross: baseGross,
        ship: m1Ship,
        perDrop: m1PerDrop,
        profit: m1Profit,
        subNote: "固定費 ¥0 ／ 変動費 ¥1,220/回（運賃+保冷箱）"
      },
      {
        meta: DELIVERY.models[1] || { name: "② 自社軽バン冷凍車単独", badge: "拡大期向き", breakevenStoresNote: "", pros: "" },
        sales: baseSales,
        gross: baseGross,
        ship: m2Ship,
        perDrop: m2PerDrop,
        profit: m2Profit,
        subNote: "固定費 ¥235,000/月（車両・燃料・週4パート）＋ 通い箱 ¥140/回"
      },
      {
        meta: DELIVERY.models[2] || { name: "③ ハイブリッド段階移行（推奨）", badge: "推奨ベスト", breakevenStoresNote: "", pros: "" },
        sales: m3Sales,
        gross: m3Gross,
        ship: m3Ship,
        perDrop: m3PerDrop,
        profit: m3Profit,
        subNote: m3PhaseLabel
      }
    ];

    const maxProfit = Math.max(...calcResults.map((r) => r.profit));

    grid.textContent = "";
    calcResults.forEach((res) => {
      const isWinner = res.profit === maxProfit;
      const card = document.createElement("article");
      card.className = "delivery-model-card" + (isWinner ? " is-winner" : "");

      const badges = document.createElement("div");
      badges.className = "store-badges-top";
      const b1 = document.createElement("span");
      b1.className = "rank-badge " + (isWinner ? "rank-S" : "rank-A");
      b1.textContent = isWinner ? "🏆 この条件で最高利益" : res.meta.badge;
      badges.appendChild(b1);

      const title = document.createElement("h3");
      title.className = "delivery-model-title";
      title.textContent = res.meta.name;

      const plBox = document.createElement("div");
      plBox.className = "delivery-pl-box";

      const addRow = (lbl, valTxt, extraCls) => {
        const row = document.createElement("div");
        row.className = "delivery-pl-row" + (extraCls ? " " + extraCls : "");
        const s1 = document.createElement("span");
        s1.textContent = lbl;
        const s2 = document.createElement("span");
        s2.style.fontFamily = "var(--font-mono)";
        s2.textContent = valTxt;
        row.appendChild(s1);
        row.appendChild(s2);
        plBox.appendChild(row);
      };

      addRow("月間売上高合計", formatYen(res.sales));
      addRow("食材粗利額 (" + state.sim.gm + "%)", formatYen(res.gross));
      addRow("月間配送コスト計", "-" + formatYen(res.ship) + " (@" + formatYen(res.perDrop) + "/回)");

      const profitRow = document.createElement("div");
      profitRow.className = "delivery-pl-row delivery-pl-profit";
      const pLbl = document.createElement("span");
      pLbl.textContent = "月間営業利益";
      const pVal = document.createElement("span");
      pVal.className = res.profit >= 0 ? "profit-positive" : "profit-negative";
      const opMargin = res.sales > 0 ? ((res.profit / res.sales) * 100).toFixed(1) : "0.0";
      pVal.textContent = formatSignedYen(res.profit) + " (" + opMargin + "%)";
      profitRow.appendChild(pLbl);
      profitRow.appendChild(pVal);
      plBox.appendChild(profitRow);

      const noteP = document.createElement("p");
      noteP.className = "delivery-meta-note";
      noteP.textContent = "💡 " + res.subNote;

      const breakP = document.createElement("p");
      breakP.className = "delivery-meta-note";
      breakP.style.fontWeight = "600";
      breakP.textContent = "📌 " + (res.meta.breakevenStoresNote || "");

      card.appendChild(badges);
      card.appendChild(title);
      card.appendChild(plBox);
      card.appendChild(noteP);
      card.appendChild(breakP);
      grid.appendChild(card);
    });
  }

  // Export CSV with BOM
  function exportProgressCsv() {
    const headers = [
      "No",
      "店舗名",
      "確度",
      "江坂からの距離(km)",
      "最寄駅",
      "勝ち筋セグメント",
      "所在地・TEL",
      "業態・単価",
      "最優先フック商材",
      "月1万円カスタム定期便レシピ",
      "推奨架電時間",
      "架電ステータス",
      "富田君メモ"
    ];
    const rows = STORES.map((s) => [
      s.id,
      s.name,
      s.rank,
      s.distanceKm.toFixed(1),
      s.station,
      s.segmentLabel,
      s.address,
      s.genre + " " + s.priceRange,
      s.hookProduct,
      s.customPlan10k,
      s.callWindow.replace(/\n/g, " / "),
      getStoreStatus(s.id),
      getStoreMemo(s.id)
    ]);

    const escapeCsv = (val) => {
      const raw = String(val == null ? "" : val);
      const safe = /^[=+\-@]/.test(raw) ? "'" + raw : raw;
      return '"' + safe.replace(/"/g, '""') + '"';
    };

    const csvBody = [headers.map(escapeCsv).join(",")]
      .concat(rows.map((r) => r.map(escapeCsv).join(",")))
      .join("\r\n");

    const blob = new Blob(["\uFEFF" + csvBody], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ファインアトラス_江坂20km営業進捗メモ_60店舗.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast("💾 全" + STORES.length + "店舗の営業進捗・メモをCSV出力しました");
  }

  // Sub-Tabs Activation inside Sales Workspace
  function activateTab(tabId) {
    const pairs = [
      { tab: "tab-stores", panel: "panel-stores" },
      { tab: "tab-strategy", panel: "panel-strategy" },
      { tab: "tab-playbook", panel: "panel-playbook" }
    ];
    pairs.forEach((p) => {
      const t = document.getElementById(p.tab);
      const pnl = document.getElementById(p.panel);
      const active = p.tab === tabId;
      if (t) t.setAttribute("aria-selected", active ? "true" : "false");
      if (pnl) pnl.hidden = !active;
    });
  }

  // Theme Initialization & Toggle
  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    const toggleBtn = document.getElementById("btn-theme-toggle");
    const apply = (mode) => {
      document.documentElement.setAttribute("data-theme", mode);
      if (toggleBtn) {
        toggleBtn.textContent = mode === "dark" ? "☀️ 朝凪ライトモードに切替" : "🌙 深海ナイトモードに切替";
      }
    };
    apply(saved === "dark" ? "dark" : "light");

    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
        localStorage.setItem(THEME_KEY, next);
        apply(next);
      });
    }
  }

  // Bind UI Events
  function bindEvents() {
    const modeSalesBtn = document.getElementById("mode-sales");
    const modeProcBtn = document.getElementById("mode-procurement");
    if (modeSalesBtn) modeSalesBtn.addEventListener("click", () => activateMode("sales"));
    if (modeProcBtn) modeProcBtn.addEventListener("click", () => activateMode("procurement"));

    ["tab-stores", "tab-strategy", "tab-playbook"].forEach((id) => {
      const btn = document.getElementById(id);
      if (btn) btn.addEventListener("click", () => activateTab(id));
    });

    document.querySelectorAll(".seg-jump-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const seg = btn.getAttribute("data-jump-seg") || "ALL";
        state.segment = seg;
        const sel = document.getElementById("segment-filter");
        if (sel) sel.value = seg;
        activateMode("sales");
        activateTab("tab-stores");
        renderStores();
        window.scrollTo({ top: 260, behavior: "smooth" });
      });
    });

    const searchInput = document.getElementById("search-input");
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        state.search = searchInput.value;
        renderStores();
      });
    }

    const segSel = document.getElementById("segment-filter");
    if (segSel) {
      segSel.addEventListener("change", () => {
        state.segment = segSel.value;
        renderStores();
      });
    }

    const areaSel = document.getElementById("area-filter");
    if (areaSel) {
      areaSel.addEventListener("change", () => {
        state.area = areaSel.value;
        renderStores();
      });
    }

    const sortSel = document.getElementById("sort-select");
    if (sortSel) {
      sortSel.addEventListener("change", () => {
        state.sort = sortSel.value;
        renderStores();
      });
    }

    document.querySelectorAll("#quick-tag-group .tag-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        const tag = pill.getAttribute("data-tag");
        if (state.activeTags.has(tag)) {
          state.activeTags.delete(tag);
          pill.classList.remove("is-active");
        } else {
          state.activeTags.add(tag);
          pill.classList.add("is-active");
        }
        renderStores();
      });
    });

    const resetBtn = document.getElementById("btn-reset-filters");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        state.fish = "ALL";
        state.search = "";
        state.segment = "ALL";
        state.area = "ALL";
        state.sort = "priority";
        state.activeTags.clear();
        if (searchInput) searchInput.value = "";
        if (segSel) segSel.value = "ALL";
        if (areaSel) areaSel.value = "ALL";
        if (sortSel) sortSel.value = "priority";
        document.querySelectorAll("#quick-tag-group .tag-pill").forEach((p) => p.classList.remove("is-active"));
        renderFishBar();
        renderStores();
      });
    }

    // Procurement Tier Filter Pills
    document.querySelectorAll("#proc-tier-filter .tag-pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.procTier = btn.getAttribute("data-tier") || "ALL";
        document.querySelectorAll("#proc-tier-filter .tag-pill").forEach((b) => {
          b.classList.toggle("is-active", b === btn);
        });
        renderProcurementTable();
      });
    });

    // Delivery Simulator Inputs & Presets
    const storesInput = document.getElementById("sim-stores-input");
    const orderInput = document.getElementById("sim-order-input");
    const dropsSelect = document.getElementById("sim-drops-select");
    const gmInput = document.getElementById("sim-gm-input");

    const clearPresetActive = () => {
      document.querySelectorAll(".sim-preset-btn").forEach((b) => b.classList.remove("is-active"));
    };

    if (storesInput) {
      storesInput.addEventListener("input", () => {
        state.sim.stores = parseInt(storesInput.value, 10) || 1;
        clearPresetActive();
        renderDeliverySimulator();
      });
    }
    if (orderInput) {
      orderInput.addEventListener("input", () => {
        state.sim.order = parseInt(orderInput.value, 10) || 10000;
        clearPresetActive();
        renderDeliverySimulator();
      });
    }
    if (dropsSelect) {
      dropsSelect.addEventListener("change", () => {
        state.sim.drops = parseInt(dropsSelect.value, 10) || 2;
        clearPresetActive();
        renderDeliverySimulator();
      });
    }
    if (gmInput) {
      gmInput.addEventListener("input", () => {
        state.sim.gm = parseInt(gmInput.value, 10) || 40;
        clearPresetActive();
        renderDeliverySimulator();
      });
    }

    document.querySelectorAll(".sim-preset-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.sim.stores = parseInt(btn.getAttribute("data-stores"), 10) || 28;
        state.sim.order = parseInt(btn.getAttribute("data-order"), 10) || 28000;
        state.sim.drops = parseInt(btn.getAttribute("data-drops"), 10) || 4;
        state.sim.gm = parseInt(btn.getAttribute("data-gm"), 10) || 40;
        if (storesInput) storesInput.value = String(state.sim.stores);
        if (orderInput) orderInput.value = String(state.sim.order);
        if (dropsSelect) dropsSelect.value = String(state.sim.drops);
        if (gmInput) gmInput.value = String(state.sim.gm);
        document.querySelectorAll(".sim-preset-btn").forEach((b) => b.classList.toggle("is-active", b === btn));
        renderDeliverySimulator();
      });
    });

    const exportBtn = document.getElementById("btn-export-csv");
    if (exportBtn) {
      exportBtn.addEventListener("click", exportProgressCsv);
    }
  }

  // Bootstrap
  initTheme();
  bindEvents();
  updateSummaryMetrics();
  renderFishBar();
  renderStores();
  renderRadarMap();
  renderPlaybook();
  renderProcurementStaticMeta();
  renderProcurementTable();
  renderDeliverySimulator();
  if (window.location.hash === "#procurement") {
    activateMode("procurement");
  }
  setInterval(updateSummaryMetrics, 30000);
})();
