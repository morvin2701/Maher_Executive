/**
 * Client helpers for admin-managed coupons (see POST /api/coupons/validate).
 */
(function () {
  var CODE_KEY = "cart_promo_code";
  var META_KEY = "cart_coupon_meta";

  function readMeta() {
    try {
      var raw = localStorage.getItem(META_KEY);
      if (!raw) return null;
      var o = JSON.parse(raw);
      if (!o || typeof o !== "object") return null;
      return o;
    } catch (_e) {
      return null;
    }
  }

  function discountFromMeta(subtotal, meta) {
    if (!meta) return 0;
    var t = Number(subtotal || 0);
    if (t <= 0) return 0;
    var type = String(meta.type || "percentage").toLowerCase();
    var value = Number(meta.value || 0);
    if (type === "fixed") {
      return Math.min(Math.max(0, value), t);
    }
    return Math.min(t * (Math.max(0, value) / 100), t);
  }

  function clear() {
    localStorage.removeItem(CODE_KEY);
    localStorage.removeItem(META_KEY);
  }

  function getCode() {
    return (localStorage.getItem(CODE_KEY) || "").trim();
  }

  /**
   * @returns {Promise<{ ok: boolean, discount?: number, type?: string, value?: number, error?: string }>}
   */
  function validate(code, subtotal) {
    return fetch("/api/coupons/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: String(code || "").trim(), subtotal: Number(subtotal) || 0 }),
    }).then(function (r) {
      return r.json();
    });
  }

  function persistFromValidate(data) {
    if (!data || !data.ok) return false;
    localStorage.setItem(CODE_KEY, String(data.code || "").toUpperCase());
    localStorage.setItem(
      META_KEY,
      JSON.stringify({ type: data.type || "percentage", value: Number(data.value) || 0 })
    );
    return true;
  }

  window.CouponClient = {
    CODE_KEY: CODE_KEY,
    META_KEY: META_KEY,
    readMeta: readMeta,
    discountFromMeta: discountFromMeta,
    clear: clear,
    getCode: getCode,
    validate: validate,
    persistFromValidate: persistFromValidate,
  };
})();
