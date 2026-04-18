(function () {
  const STORAGE_CURRENCY = "me_currency_code";
  const STORAGE_RATES = "me_currency_rates_v1";
  const STORAGE_FIRST_VISIT = "me_currency_onboarded";
  const DEFAULT_BASE = "INR";
  const DEFAULT_CURRENCY = "INR";
  const PRIORITY = ["INR", "USD", "EUR", "GBP", "AED", "CAD", "AUD", "JPY", "SGD"];
  const FALLBACK_RATES = {
    INR: 1,
    USD: 0.012,
    EUR: 0.011,
    GBP: 0.0095,
    AED: 0.044,
    CAD: 0.016,
    AUD: 0.018,
    JPY: 1.84,
    SGD: 0.016,
  };

  const state = {
    currency: DEFAULT_CURRENCY,
    rates: { ...FALLBACK_RATES },
  };

  function detectSuggestedCurrency() {
    const lang = (navigator.language || "").toUpperCase();
    if (lang.includes("-IN")) return "INR";
    if (lang.includes("-US")) return "USD";
    if (lang.includes("-GB")) return "GBP";
    if (lang.includes("-AE")) return "AED";
    return DEFAULT_CURRENCY;
  }

  function safeParse(json) {
    try {
      return JSON.parse(json);
    } catch (_e) {
      return null;
    }
  }

  function loadStoredRates() {
    const raw = localStorage.getItem(STORAGE_RATES);
    const parsed = safeParse(raw || "");
    if (!parsed || !parsed.rates || !parsed.updatedAt) return false;
    const ageMs = Date.now() - Number(parsed.updatedAt || 0);
    if (ageMs > 24 * 60 * 60 * 1000) return false;
    state.rates = { ...FALLBACK_RATES, ...(parsed.rates || {}) };
    return true;
  }

  async function refreshRates() {
    try {
      const res = await fetch("https://api.frankfurter.app/latest?from=INR");
      if (!res.ok) return;
      const data = await res.json();
      if (!data || !data.rates) return;
      state.rates = { ...FALLBACK_RATES, INR: 1, ...(data.rates || {}) };
      localStorage.setItem(
        STORAGE_RATES,
        JSON.stringify({
          base: DEFAULT_BASE,
          updatedAt: Date.now(),
          rates: state.rates,
        })
      );
    } catch (_e) {
      // keep fallback rates
    }
  }

  function getAvailableCurrencies() {
    const set = new Set(PRIORITY.concat(Object.keys(state.rates || {})));
    return Array.from(set);
  }

  function convertFromInr(amount) {
    const n = Number(amount || 0);
    const rate = Number(state.rates[state.currency] || 1);
    return n * rate;
  }

  function formatFromInr(amount) {
    const converted = convertFromInr(amount);
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: state.currency,
        maximumFractionDigits: converted >= 1000 ? 0 : 2,
      }).format(converted);
    } catch (_e) {
      return state.currency + " " + converted.toFixed(2);
    }
  }

  function updateSelectorOptions(select) {
    if (!select) return;
    const currencies = getAvailableCurrencies();
    select.innerHTML = currencies
      .map((c) => '<option value="' + c + '">' + c + "</option>")
      .join("");
    select.value = state.currency;
  }

  function isInsideManagedPrice(el) {
    return !!(el && el.closest && el.closest("[data-price-inr]"));
  }

  function wrapPriceTextNode(textNode) {
    if (isInsideManagedPrice(textNode.parentElement)) return;
    const raw = textNode.nodeValue || "";
    if (!raw.includes("₹")) return;
    const regex = /₹\s*([\d,]+(?:\.\d+)?)/g;
    regex.lastIndex = 0;
    if (!regex.test(raw)) return;

    const frag = document.createDocumentFragment();
    regex.lastIndex = 0;
    let cursor = 0;
    let m;
    while ((m = regex.exec(raw)) !== null) {
      const start = m.index;
      const end = regex.lastIndex;
      if (start > cursor) frag.appendChild(document.createTextNode(raw.slice(cursor, start)));
      const amount = Number((m[1] || "0").replace(/,/g, ""));
      const span = document.createElement("span");
      span.setAttribute("data-price-inr", String(amount));
      span.textContent = formatFromInr(amount);
      frag.appendChild(span);
      cursor = end;
    }
    if (cursor < raw.length) frag.appendChild(document.createTextNode(raw.slice(cursor)));
    textNode.parentNode.replaceChild(frag, textNode);
  }

  function scanForRupeeText(root) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    const bucket = [];
    let node;
    while ((node = walker.nextNode())) {
      const parent = node.parentElement;
      if (!parent) continue;
      const tag = parent.tagName;
      if (tag === "SCRIPT" || tag === "STYLE" || tag === "TEXTAREA") continue;
      if (isInsideManagedPrice(parent)) continue;
      if ((node.nodeValue || "").includes("₹")) bucket.push(node);
    }
    bucket.forEach(wrapPriceTextNode);
  }

  let renderDepth = 0;

  function renderPrices(root) {
    const host = root || document.body;
    renderDepth += 1;
    try {
      scanForRupeeText(host);
      host.querySelectorAll("[data-price-inr]").forEach((el) => {
        const amount = Number(el.getAttribute("data-price-inr") || 0);
        const next = formatFromInr(amount);
        if (el.textContent !== next) el.textContent = next;
      });
      const code = state.currency;
      document.querySelectorAll("[data-selected-currency]").forEach((el) => {
        el.textContent = code;
      });
    } finally {
      renderDepth -= 1;
    }
  }

  function setCurrency(code) {
    const next = String(code || "").toUpperCase();
    if (!next) return;
    state.currency = next;
    localStorage.setItem(STORAGE_CURRENCY, state.currency);
    updateSelectorOptions(document.getElementById("currency-selector"));
    updateSelectorOptions(document.getElementById("currency-modal-selector"));
    renderPrices(document.body);
    window.dispatchEvent(new CustomEvent("currency:changed", { detail: { currency: state.currency } }));
  }

  function setupModal() {
    const modal = document.getElementById("currency-modal");
    const modalSelect = document.getElementById("currency-modal-selector");
    const saveBtn = document.getElementById("currency-modal-save");
    if (!modal || !modalSelect || !saveBtn) return;

    updateSelectorOptions(modalSelect);
    const seen = localStorage.getItem(STORAGE_FIRST_VISIT) === "1";
    if (!seen) {
      const suggested = detectSuggestedCurrency();
      if (getAvailableCurrencies().includes(suggested)) modalSelect.value = suggested;
      modal.classList.add("open");
    }

    saveBtn.addEventListener("click", function () {
      setCurrency(modalSelect.value || DEFAULT_CURRENCY);
      localStorage.setItem(STORAGE_FIRST_VISIT, "1");
      modal.classList.remove("open");
    });
  }

  function setupNavbarSelector() {
    const navSelect = document.getElementById("currency-selector");
    if (!navSelect) return;
    updateSelectorOptions(navSelect);
    navSelect.addEventListener("change", function () {
      setCurrency(navSelect.value);
      localStorage.setItem(STORAGE_FIRST_VISIT, "1");
    });
  }

  async function init() {
    const storedCurrency = String(localStorage.getItem(STORAGE_CURRENCY) || "").toUpperCase();
    state.currency = storedCurrency || detectSuggestedCurrency() || DEFAULT_CURRENCY;
    loadStoredRates();
    setupNavbarSelector();
    setupModal();
    renderPrices(document.body);
    await refreshRates();
    updateSelectorOptions(document.getElementById("currency-selector"));
    updateSelectorOptions(document.getElementById("currency-modal-selector"));
    renderPrices(document.body);

    let scheduled = false;
    function scheduleRefresh() {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(function () {
        scheduled = false;
        if (renderDepth > 0) return;
        renderPrices(document.body);
      });
    }

    const observer = new MutationObserver(function (mutations) {
      if (renderDepth > 0) return;
      let needRefresh = false;
      mutations.forEach((m) => {
        m.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            needRefresh = true;
            return;
          }
          if (node.nodeType === Node.TEXT_NODE && (node.nodeValue || "").includes("₹")) {
            if (!isInsideManagedPrice(node.parentElement)) {
              wrapPriceTextNode(node);
            }
          }
        });
      });
      if (needRefresh) scheduleRefresh();
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  window.CurrencyPreference = {
    getCurrency: function () {
      return state.currency;
    },
    setCurrency: setCurrency,
    formatFromInr: formatFromInr,
    convertFromInr: convertFromInr,
    renderPrices: renderPrices,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
