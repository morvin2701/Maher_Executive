(function () {
  const shell = document.querySelector(".account-shell");
  if (!shell) return;

  const page = shell.dataset.accountPage || "profile";

  function formatCurrency(value) {
    return "₹" + Number(value || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function formatDate(raw) {
    if (!raw) return "Recent";
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return "Recent";
    return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  }

  const MONTHS_UP = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

  function formatOrderDateLuxury(raw) {
    if (!raw) return "—";
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return "—";
    return MONTHS_UP[d.getMonth()] + " " + d.getDate() + ", " + d.getFullYear();
  }

  function orderRefLuxury(id) {
    const s = String(id || "").replace(/[^a-fA-F0-9]/g, "");
    if (s.length >= 4) return "AU-" + s.slice(0, 4).toUpperCase();
    return "AU-" + String(id || "0000").slice(0, 4).toUpperCase();
  }

  function escapeHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function orderStatusPill(order) {
    const s = String(order.status || "").toLowerCase();
    if (s.includes("deliver") || s === "delivered" || s === "completed") {
      return { cls: "oh-pill oh-pill--delivered", label: "DELIVERED" };
    }
    if (s === "confirmed" || s.includes("transit") || s.includes("ship")) {
      return { cls: "oh-pill oh-pill--transit", label: "IN TRANSIT" };
    }
    return { cls: "oh-pill oh-pill--transit", label: "PROCESSING" };
  }

  async function getHeaders() {
    if (!window.getBearerHeaders) return {};
    return window.getBearerHeaders();
  }

  async function fetchJson(url, options) {
    const res = await fetch(url, options || {});
    let data = {};
    try {
      data = await res.json();
    } catch (_ignore) {
      data = {};
    }
    if (!res.ok) {
      throw new Error(data.error || "Request failed");
    }
    return data;
  }

  function bindSignout() {
    const signoutBtn = document.getElementById("account-signout");
    if (!signoutBtn) return;
    signoutBtn.addEventListener("click", async () => {
      if (window.signOutME) await window.signOutME();
    });
  }

  function hydrateSidebar(user) {
    const name = user.name || user.email || "Maher Executive";
    const initials = name
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((x) => x[0].toUpperCase())
      .join("");
    const sideName = document.getElementById("account-name-side");
    const avatar = document.getElementById("account-avatar");
    if (sideName) sideName.textContent = name;
    if (avatar) avatar.textContent = initials || "A";
  }

  async function loadUser() {
    const headers = await getHeaders();
    if (!headers.Authorization) {
      window.location.href = "/auth";
      return null;
    }
    try {
      const me = await fetchJson("/api/me", { headers });
      hydrateSidebar(me);
      return { me, headers };
    } catch (err) {
      if (window.showToast) window.showToast("Please sign in again.", "warning");
      window.location.href = "/auth";
      return null;
    }
  }

  function bindProfile(userCtx) {
    const me = userCtx.me;
    const headers = userCtx.headers;
    const nameNode = document.getElementById("profile-name");
    const emailNode = document.getElementById("profile-email");
    const phoneNode = document.getElementById("profile-phone");
    const editBtn = document.getElementById("profile-edit");
    const saveBtn = document.getElementById("profile-save");
    const editWrap = document.querySelector(".account-inline-edit");
    const nameInput = document.getElementById("profile-name-input");
    const phoneInput = document.getElementById("profile-phone-input");

    if (!nameNode || !emailNode || !phoneNode || !editBtn || !saveBtn || !editWrap || !nameInput || !phoneInput) {
      return;
    }

    nameNode.textContent = me.name || "Elite Client";
    emailNode.textContent = me.email || "client@me.luxury";
    phoneNode.textContent = me.phone || "+91 00000 00000";
    nameInput.value = me.name || "";
    phoneInput.value = me.phone || "";

    editBtn.addEventListener("click", () => {
      editWrap.classList.toggle("active");
    });

    saveBtn.addEventListener("click", async () => {
      const payload = {
        name: nameInput.value.trim(),
        phone: phoneInput.value.trim(),
      };
      try {
        const updated = await fetchJson("/api/me", {
          method: "PATCH",
          headers: { "Content-Type": "application/json", ...headers },
          body: JSON.stringify(payload),
        });
        const user = updated.user || {};
        nameNode.textContent = user.name || payload.name || me.name;
        phoneNode.textContent = user.phone || payload.phone || me.phone;
        hydrateSidebar(user);
        editWrap.classList.remove("active");
        if (window.showToast) window.showToast("Profile updated", "success");
      } catch (err) {
        if (window.showToast) window.showToast(err.message || "Could not save profile", "error");
      }
    });
  }

  async function bindOrders(userCtx) {
    const host = document.getElementById("orders-list");
    if (!host) return;
    try {
      const payload = await fetchJson("/api/orders", { headers: userCtx.headers });
      const orders = payload.orders || [];
      if (!orders.length) {
        host.innerHTML =
          '<div class="oh-empty">No orders yet. Place your first acquisition to see tracking details here.</div>';
        return;
      }
      host.innerHTML = orders
        .map((order) => {
          const items = Array.isArray(order.items) ? order.items : [];
          const pill = orderStatusPill(order);
          const lineItems = items
            .map((item) => {
              const qty = Number(item.qty || 1);
              const unit = Number(item.price || 0);
              const line = qty * unit;
              const name = escapeHtml(item.name || "Product");
              const thumb =
                item.image && String(item.image).trim()
                  ? '<div class="oh-line__thumb"><img src="' +
                    escapeHtml(item.image) +
                    '" alt="" loading="lazy" onerror="this.parentElement.classList.add(\'oh-line__thumb--empty\'); this.remove();" /></div>'
                  : '<div class="oh-line__thumb oh-line__thumb--empty"></div>';
              return (
                '<div class="oh-line">' +
                thumb +
                '<div class="oh-line__meta">' +
                '<p class="oh-line__name">' +
                name +
                "</p>" +
                '<p class="oh-line__qty">QTY: ' +
                qty +
                "</p>" +
                "</div>" +
                '<div class="oh-line__price">' +
                formatCurrency(line) +
                "</div>" +
                "</div>"
              );
            })
            .join("");
          return (
            '<article class="oh-card">' +
            '<div class="oh-card__head">' +
            '<div class="oh-card__col">' +
            '<div class="oh-card__label">ORDER REF.</div>' +
            '<div class="oh-card__ref">' +
            orderRefLuxury(order.id) +
            "</div>" +
            "</div>" +
            '<div class="oh-card__col">' +
            '<div class="oh-card__label">DATE</div>' +
            '<div class="oh-card__date">' +
            formatOrderDateLuxury(order.createdAt) +
            "</div>" +
            "</div>" +
            '<div class="oh-card__col oh-card__col--status">' +
            '<div class="oh-card__label">STATUS</div>' +
            '<span class="' +
            pill.cls +
            '">' +
            pill.label +
            "</span>" +
            "</div>" +
            '<a class="oh-track" href="/account/orders/' +
            encodeURIComponent(order.id) +
            '">TRACK ORDER</a>' +
            "</div>" +
            '<div class="oh-card__items">' +
            (lineItems || '<p class="oh-line__empty muted">No line items.</p>') +
            "</div>" +
            '<div class="oh-card__footer">' +
            '<span class="oh-card__total-label">ACQUISITION TOTAL</span>' +
            '<span class="oh-card__total-val">' +
            formatCurrency(order.total) +
            "</span>" +
            "</div>" +
            "</article>"
          );
        })
        .join("");
    } catch (err) {
      host.innerHTML = '<div class="oh-empty">Unable to load orders right now.</div>';
    }
  }

  async function bindOrderDetail(userCtx) {
    const host = document.getElementById("order-detail-host");
    if (!host) return;
    const orderId = shell.dataset.orderId || "";
    if (!orderId) {
      host.innerHTML = '<div class="oh-empty">Order reference missing.</div>';
      return;
    }
    try {
      const order = await fetchJson("/api/orders/" + encodeURIComponent(orderId), {
        headers: userCtx.headers,
      });
      const items = Array.isArray(order.items) ? order.items : [];
      const pill = orderStatusPill(order);
      const lineItems = items
        .map((item) => {
          const qty = Number(item.qty || 1);
          const unit = Number(item.price || 0);
          const line = qty * unit;
          const name = escapeHtml(item.name || "Product");
          const thumb =
            item.image && String(item.image).trim()
              ? '<div class="oh-line__thumb"><img src="' +
                escapeHtml(item.image) +
                '" alt="" loading="lazy" onerror="this.parentElement.classList.add(\'oh-line__thumb--empty\'); this.remove();" /></div>'
              : '<div class="oh-line__thumb oh-line__thumb--empty"></div>';
          return (
            '<div class="oh-line">' +
            thumb +
            '<div class="oh-line__meta">' +
            '<p class="oh-line__name">' +
            name +
            "</p>" +
            '<p class="oh-line__qty">QTY: ' +
            qty +
            "</p>" +
            "</div>" +
            '<div class="oh-line__price">' +
            formatCurrency(line) +
            "</div>" +
            "</div>"
          );
        })
        .join("");
      host.innerHTML =
        '<article class="oh-card">' +
        '<div class="oh-card__head">' +
        '<div class="oh-card__col">' +
        '<div class="oh-card__label">ORDER REF.</div>' +
        '<div class="oh-card__ref">' +
        orderRefLuxury(order.id) +
        "</div>" +
        "</div>" +
        '<div class="oh-card__col">' +
        '<div class="oh-card__label">DATE</div>' +
        '<div class="oh-card__date">' +
        formatOrderDateLuxury(order.createdAt) +
        "</div>" +
        "</div>" +
        '<div class="oh-card__col oh-card__col--status">' +
        '<div class="oh-card__label">STATUS</div>' +
        '<span class="' +
        pill.cls +
        '">' +
        pill.label +
        "</span>" +
        "</div>" +
        '<a class="oh-track" href="/account/orders">BACK TO ORDERS</a>' +
        "</div>" +
        '<div class="oh-card__items">' +
        (lineItems || '<p class="oh-line__empty muted">No line items.</p>') +
        "</div>" +
        '<div class="oh-card__footer">' +
        '<span class="oh-card__total-label">ACQUISITION TOTAL</span>' +
        '<span class="oh-card__total-val">' +
        formatCurrency(order.total) +
        "</span>" +
        "</div>" +
        "</article>";
    } catch (err) {
      host.innerHTML = '<div class="oh-empty">Unable to load this order.</div>';
    }
  }

  async function addressPayloadFromDialog(existing) {
    const Me = window.MeDialog;
    if (!Me || typeof Me.form !== "function") {
      if (window.showToast) window.showToast("Dialog UI not loaded.", "warning");
      return null;
    }
    const ex = existing || {};
    const data = await Me.form({
      title: "Shipping address",
      subtitle: "Deliver with precision — saved securely to your profile.",
      okText: "Save address",
      fields: [
        { name: "label", label: "Address label", type: "text", value: ex.label || "Home", required: true },
        { name: "name", label: "Recipient name", type: "text", value: ex.name || "", required: true },
        { name: "line1", label: "Address line 1", type: "text", value: ex.line1 || "", required: true },
        { name: "line2", label: "Address line 2 (optional)", type: "text", value: ex.line2 || "" },
        { name: "city", label: "City", type: "text", value: ex.city || "", required: true },
        { name: "state", label: "State", type: "text", value: ex.state || "", required: true },
        { name: "pincode", label: "Pincode", type: "text", value: ex.pincode || "", required: true },
        { name: "country", label: "Country", type: "text", value: ex.country || "India", required: true },
        { name: "phone", label: "Phone (optional)", type: "text", value: ex.phone || "" },
        { name: "isDefault", label: "Set as default shipping address", type: "checkbox", value: !!ex.isDefault },
      ],
    });
    if (!data) return null;
    return {
      label: String(data.label || "").trim(),
      name: String(data.name || "").trim(),
      line1: String(data.line1 || "").trim(),
      line2: String(data.line2 || "").trim(),
      city: String(data.city || "").trim(),
      state: String(data.state || "").trim(),
      pincode: String(data.pincode || "").trim(),
      country: String(data.country || "").trim(),
      phone: String(data.phone || "").trim(),
      isDefault: !!data.isDefault,
    };
  }

  function addressLinesHtml(addr) {
    const parts = [];
    if (addr.line1) parts.push(addr.line1);
    if (addr.line2) parts.push(addr.line2);
    const cityState = [addr.city, addr.state].filter(Boolean).join(", ");
    if (cityState) parts.push(cityState);
    if (addr.pincode) parts.push(String(addr.pincode));
    if (addr.country) parts.push(addr.country);
    return parts.map((line) => '<p class="addr-card__line">' + escapeHtml(line) + "</p>").join("");
  }

  async function bindAddresses(userCtx) {
    const host = document.getElementById("addresses-list");
    const addBtn = document.getElementById("address-add-btn");
    if (!host || !addBtn) return;

    async function render() {
      let res;
      try {
        res = await fetch("/api/addresses", { headers: userCtx.headers });
      } catch (_net) {
        host.innerHTML =
          '<div class="addr-empty">Network error. Check your connection and try again.</div>';
        return;
      }
      let data = {};
      try {
        data = await res.json();
      } catch (_e) {
        data = {};
      }
      if (!res.ok) {
        host.innerHTML =
          '<div class="addr-empty">Could not load addresses: ' +
          escapeHtml(data.error || String(res.status)) +
          "</div>";
        return;
      }
      const addresses = Array.isArray(data.addresses) ? data.addresses : [];
      if (data.warning && window.console && console.warn) {
        console.warn("addresses:", data.warning);
      }
      if (!addresses.length) {
        host.innerHTML =
          '<div class="addr-empty">No saved addresses yet. Use <strong>ADD NEW RESIDENCE</strong> below to create one.</div>';
        return;
      }
      host.innerHTML = addresses
        .map((addr) => {
          const id = escapeHtml(addr.id || "");
          const label = escapeHtml((addr.label || "Address").toUpperCase());
          const nm = escapeHtml(addr.name || "");
          const defBadge = addr.isDefault ? '<span class="addr-card__badge">DEFAULT</span>' : "";
          return (
            '<article class="addr-card" data-address-id="' +
            id +
            '">' +
            '<div class="addr-card__top">' +
            '<span class="addr-card__label">' +
            label +
            "</span>" +
            defBadge +
            "</div>" +
            '<h2 class="addr-card__name">' +
            nm +
            "</h2>" +
            '<div class="addr-card__body">' +
            addressLinesHtml(addr) +
            "</div>" +
            '<div class="addr-card__foot">' +
            '<button type="button" class="addr-card__edit" data-edit="' +
            id +
            '">EDIT ADDRESS</button>' +
            '<button type="button" class="addr-card__remove" data-remove="' +
            id +
            '">REMOVE</button>' +
            "</div>" +
            "</article>"
          );
        })
        .join("");

      host.querySelectorAll("[data-edit]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.getAttribute("data-edit");
          const current = addresses.find((x) => x.id === id);
          const payload = await addressPayloadFromDialog(current);
          if (!payload) return;
          try {
            await fetchJson("/api/addresses/" + encodeURIComponent(id), {
              method: "PUT",
              headers: { "Content-Type": "application/json", ...userCtx.headers },
              body: JSON.stringify(payload),
            });
            if (window.showToast) window.showToast("Address updated", "success");
            render();
          } catch (err) {
            if (window.showToast) window.showToast(err.message || "Could not update address", "error");
          }
        });
      });

      host.querySelectorAll("[data-remove]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.getAttribute("data-remove");
          const ok = await window.MeDialog.confirm("Remove this address from your profile?", {
            title: "Remove address",
            okText: "Remove",
            cancelText: "Keep",
          });
          if (!ok) return;
          try {
            await fetchJson("/api/addresses/" + encodeURIComponent(id), {
              method: "DELETE",
              headers: userCtx.headers,
            });
            if (window.showToast) window.showToast("Address removed", "success");
            render();
          } catch (err) {
            if (window.showToast) window.showToast(err.message || "Could not remove address", "error");
          }
        });
      });
    }

    addBtn.addEventListener("click", async () => {
      const payload = await addressPayloadFromDialog(null);
      if (!payload) return;
      try {
        await fetchJson("/api/addresses", {
          method: "POST",
          headers: { "Content-Type": "application/json", ...userCtx.headers },
          body: JSON.stringify(payload),
        });
        if (window.showToast) window.showToast("Address saved", "success");
        render();
      } catch (err) {
        if (window.showToast) window.showToast(err.message || "Could not add address", "error");
      }
    });

    render();
  }

  async function bindWishlist() {
    const host = document.getElementById("wishlist-list");
    if (!host) return;
    const ids = JSON.parse(localStorage.getItem("wishlist_ids") || "[]");
    if (!ids.length) {
      host.innerHTML = '<div class="account-empty">Your wishlist is empty. Tap the heart icon on products you love.</div>';
      return;
    }
    try {
      const payload = await fetchJson("/api/products?limit=500");
      const products = (payload.products || []).filter((p) => ids.includes(p.id));
      if (!products.length) {
        host.innerHTML = '<div class="account-empty">Your wishlist is empty. Tap the heart icon on products you love.</div>';
        return;
      }
      host.innerHTML = products
        .map(
          (p) =>
            '<article class="wishlist-card">' +
            '<div class="wishlist-img">' +
            ((p.images && p.images[0] && p.images[0].url) ? '<img src="' + p.images[0].url + '" alt="' + (p.name || "") + '">' : "") +
            "</div>" +
            '<div class="wishlist-body">' +
            "<h3>" +
            (p.name || "Product") +
            "</h3>" +
            "<p>" +
            formatCurrency(p.price) +
            "</p>" +
            '<div class="wishlist-actions">' +
            '<button class="btn btn-primary" data-bag="' +
            p.id +
            '">Move to Bag</button>' +
            '<button class="btn btn-outline" data-remove="' +
            p.id +
            '">Remove</button>' +
            "</div>" +
            "</div>" +
            "</article>"
        )
        .join("");

      host.querySelectorAll("[data-bag]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = btn.getAttribute("data-bag");
          const cart = JSON.parse(localStorage.getItem("cart") || "{}");
          cart[id] = (cart[id] || 0) + 1;
          localStorage.setItem("cart", JSON.stringify(cart));
          if (window.showToast) window.showToast("Moved to bag", "success");
        });
      });

      host.querySelectorAll("[data-remove]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = btn.getAttribute("data-remove");
          const next = ids.filter((x) => x !== id);
          localStorage.setItem("wishlist_ids", JSON.stringify(next));
          btn.closest(".wishlist-card").remove();
          if (window.showToast) window.showToast("Removed from wishlist", "success");
        });
      });
    } catch (err) {
      host.innerHTML = '<div class="account-empty">Unable to load wishlist right now.</div>';
    }
  }

  (async function init() {
    bindSignout();
    const userCtx = await loadUser();
    if (!userCtx) return;
    if (page === "profile") bindProfile(userCtx);
    if (page === "orders") bindOrders(userCtx);
    if (page === "order_detail") bindOrderDetail(userCtx);
    if (page === "addresses") bindAddresses(userCtx);
    if (page === "wishlist") bindWishlist();
  })();
})();
