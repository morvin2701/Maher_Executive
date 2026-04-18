(function () {
  window.showToast = function (message, type) {
    const root = document.getElementById("toast-root");
    if (!root) return;
    const el = document.createElement("div");
    el.className = "toast " + (type || "");
    el.textContent = message;
    root.appendChild(el);
    setTimeout(() => el.remove(), 4200);
  };

  const burger = document.getElementById("nav-burger");
  if (burger) {
    burger.addEventListener("click", () => {
      showToast("Mobile menu: use desktop nav links in this build.", "info");
    });
  }

  document.addEventListener("click", (event) => {
    const link = event.target && event.target.closest ? event.target.closest("a[href]") : null;
    if (!link) return;
    const href = link.getAttribute("href") || "";
    if (href.includes("/product/")) {
      sessionStorage.setItem("pdpTransition", "1");
    }
  });

  document.querySelectorAll(".footer-newsletter-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const wrap = btn.closest(".home-newsletter-row");
      if (!wrap) return;
      const input = wrap.querySelector(".footer-newsletter-email");
      const email = input && input.value ? input.value.trim() : "";
      if (!email || !email.includes("@")) {
        if (window.showToast) window.showToast("Enter a valid email.", "warning");
        return;
      }
      try {
        const db = window.firebaseDb;
        if (db) {
          await db.collection("newsletter_subscribers").add({
            email: email,
            source: "footer",
            createdAt: new Date().toISOString(),
          });
        }
        if (input) input.value = "";
        if (window.showToast) window.showToast("Subscribed successfully.", "success");
      } catch (_e) {
        if (window.showToast) window.showToast("Could not subscribe right now.", "warning");
      }
    });
  });
})();
