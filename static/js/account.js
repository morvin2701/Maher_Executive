(function () {
  const shell = document.querySelector(".account-shell");
  if (!shell) return;

  const page = shell.dataset.accountPage || "profile";

  function formatCurrency(value) {
    return "₹" + Number(value || 0).toLocaleString("en-IN");
  }

  function formatDate(raw) {
    if (!raw) return "Recent";
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return "Recent";
    return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
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

  function orderStatusClass(status) {
    const value = String(status || "").toLowerCase();
    if (value.includes("deliver")) return "delivered";
    if (value.includes("transit") || value.includes("ship")) return "transit";
    return "pending";
  }

  async function bindOrders(userCtx) {
    const host = document.getElementById("orders-list");
    if (!host) return;
    try {
      const payload = await fetchJson("/api/orders", { headers: userCtx.headers });
      const orders = payload.orders || [];
      if (!orders.length) {
        host.innerHTML = '<div class="account-empty">No orders yet. Place your first order to see tracking details here.</div>';
        return;
      }
      host.innerHTML = orders
        .map((order) => {
          const items = Array.isArray(order.items) ? order.items : [];
          const lineItems = items
            .slice(0, 3)
            .map(
              (item) =>
                '<div class="order-item-row"><p>' +
                (item.name || "Product") +
                '</p><span>Qty ' +
                Number(item.qty || 1) +
                "</span></div>"
            )
            .join("");
          return (
            '<article class="order-card">' +
            '<div class="order-card-head">' +
            "<div><p>Order Ref.</p><h4>" +
            String(order.id || "").toUpperCase() +
            "</h4></div>" +
            "<div><p>Date</p><h4>" +
            formatDate(order.createdAt) +
            "</h4></div>" +
            "<div><p>Status</p><h4 class='order-status " +
            orderStatusClass(order.status) +
            "'>" +
            String(order.status || "pending") +
            "</h4></div>" +
            '<a class="btn btn-outline" href="/account/orders/' +
            encodeURIComponent(order.id) +
            '">Track Order</a>' +
            "</div>" +
            '<div class="order-card-items">' +
            lineItems +
            "</div>" +
            '<div class="order-total-row"><span>Acquisition Total</span><strong>' +
            formatCurrency(order.total) +
            "</strong></div>" +
            "</article>"
          );
        })
        .join("");
    } catch (err) {
      host.innerHTML = '<div class="account-empty">Unable to load orders right now.</div>';
    }
  }

  async function bindOrderDetail(userCtx) {
    const host = document.getElementById("order-detail-host");
    if (!host) return;
    const orderId = shell.dataset.orderId || "";
    if (!orderId) {
      host.innerHTML = '<div class="account-empty">Order reference missing.</div>';
      return;
    }
    try {
      const order = await fetchJson("/api/orders/" + encodeURIComponent(orderId), {
        headers: userCtx.headers,
      });
      const items = Array.isArray(order.items) ? order.items : [];
      host.innerHTML =
        '<article class="order-card">' +
        '<div class="order-card-head">' +
        "<div><p>Order Ref.</p><h4>" +
        String(order.id || "").toUpperCase() +
        "</h4></div>" +
        "<div><p>Date</p><h4>" +
        formatDate(order.createdAt) +
        "</h4></div>" +
        "<div><p>Status</p><h4 class='order-status " +
        orderStatusClass(order.status) +
        "'>" +
        String(order.status || "pending") +
        "</h4></div>" +
        '<a class="btn btn-outline" href="/account/orders">Back to Orders</a>' +
        "</div>" +
        '<div class="order-card-items">' +
        items
          .map(
            (item) =>
              '<div class="order-item-row"><p>' +
              (item.name || "Product") +
              '</p><span>' +
              Number(item.qty || 1) +
              " x " +
              formatCurrency(item.price || 0) +
              "</span></div>"
          )
          .join("") +
        "</div>" +
        '<div class="order-total-row"><span>Total Paid</span><strong>' +
        formatCurrency(order.total) +
        "</strong></div>" +
        "</article>";
    } catch (err) {
      host.innerHTML = '<div class="account-empty">Unable to load this order.</div>';
    }
  }

  function addressPayloadFromPrompt(existing) {
    const label = window.prompt("Address label (e.g. Home, Office)", (existing && existing.label) || "Home");
    if (!label) return null;
    const name = window.prompt("Recipient name", (existing && existing.name) || "");
    if (!name) return null;
    const line1 = window.prompt("Address line 1", (existing && existing.line1) || "");
    if (!line1) return null;
    const line2 = window.prompt("Address line 2 (optional)", (existing && existing.line2) || "") || "";
    const city = window.prompt("City", (existing && existing.city) || "");
    if (!city) return null;
    const state = window.prompt("State", (existing && existing.state) || "");
    if (!state) return null;
    const pincode = window.prompt("Pincode", (existing && existing.pincode) || "");
    if (!pincode) return null;
    const country = window.prompt("Country", (existing && existing.country) || "India");
    if (!country) return null;
    const phone = window.prompt("Phone (optional)", (existing && existing.phone) || "") || "";
    return { label, name, line1, line2, city, state, pincode, country, phone, isDefault: !!(existing && existing.isDefault) };
  }

  async function bindAddresses(userCtx) {
    const host = document.getElementById("addresses-list");
    const addBtn = document.getElementById("address-add-btn");
    if (!host || !addBtn) return;

    async function render() {
      try {
        const payload = await fetchJson("/api/addresses", { headers: userCtx.headers });
        const addresses = payload.addresses || [];
        if (!addresses.length) {
          host.innerHTML = '<div class="account-empty">No saved addresses. Use "Add New Residence" to create one.</div>';
          return;
        }
        host.innerHTML = addresses
          .map(
            (addr) =>
              '<article class="address-card">' +
              '<div class="address-top"><p>' +
              (addr.label || "Address") +
              "</p>" +
              (addr.isDefault ? '<span class="badge">Default</span>' : "") +
              "</div>" +
              "<h4>" +
              (addr.name || "") +
              "</h4>" +
              "<p>" +
              [addr.line1, addr.line2, addr.city, addr.state, addr.pincode, addr.country]
                .filter(Boolean)
                .join(", ") +
              "</p>" +
              '<div class="address-actions">' +
              '<button data-edit="' +
              addr.id +
              '">Edit Address</button>' +
              '<button data-remove="' +
              addr.id +
              '">Remove</button>' +
              "</div>" +
              "</article>"
          )
          .join("");

        host.querySelectorAll("[data-edit]").forEach((btn) => {
          btn.addEventListener("click", async () => {
            const id = btn.getAttribute("data-edit");
            const current = addresses.find((x) => x.id === id);
            const payload = addressPayloadFromPrompt(current);
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
            if (!window.confirm("Remove this address?")) return;
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
      } catch (err) {
        host.innerHTML = '<div class="account-empty">Unable to load addresses right now.</div>';
      }
    }

    addBtn.addEventListener("click", async () => {
      const payload = addressPayloadFromPrompt(null);
      if (!payload) return;
      try {
        await fetchJson("/api/addresses", {
          method: "POST",
          headers: { "Content-Type": "application/json", ...userCtx.headers },
          body: JSON.stringify(payload),
        });
        if (window.showToast) window.showToast("Address added", "success");
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
