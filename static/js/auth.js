(function () {
  async function syncSession(user) {
    if (!user || !window.firebaseAuth) return;
    const idToken = await user.getIdToken(true);
    localStorage.setItem("idToken", idToken);
    localStorage.removeItem("userRole");
    try {
      const response = await fetch("/api/auth/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idToken }),
      });
      let payload = null;
      try {
        payload = await response.json();
      } catch (_ignore) {
        payload = null;
      }
      if (payload && payload.role) {
        localStorage.setItem("userRole", payload.role);
      }
      if (!response.ok && window.showToast) {
        const detail = payload && payload.error ? " " + payload.error : "";
        window.showToast(
          "Signed in, but server sync failed. Check backend Firebase admin setup." + detail,
          "warning"
        );
      }
    } catch (_err) {
      if (window.showToast) {
        window.showToast("Signed in, but server sync is offline.", "warning");
      }
    }
    const nav = document.getElementById("nav-auth");
    if (nav) {
      nav.href = "/account/profile";
      nav.title = "Account";
      nav.setAttribute("aria-label", "Account");
    }
    const navAdmin = document.getElementById("nav-admin");
    if (navAdmin) {
      navAdmin.style.display = localStorage.getItem("userRole") === "admin" ? "" : "none";
    }
  }

  function clearClientSession() {
    localStorage.removeItem("idToken");
    localStorage.removeItem("userRole");
    const nav = document.getElementById("nav-auth");
    if (nav) {
      nav.href = "/account/profile";
      nav.title = "Account";
      nav.setAttribute("aria-label", "Account");
    }
    const navAdmin = document.getElementById("nav-admin");
    if (navAdmin) {
      navAdmin.style.display = "none";
    }
  }

  if (window.firebaseAuth) {
    window.firebaseAuth.onAuthStateChanged(async (user) => {
      if (user) await syncSession(user);
      else clearClientSession();
    });
  }

  window.signOutME = async function () {
    if (window.firebaseAuth) await window.firebaseAuth.signOut();
    clearClientSession();
    window.location.href = "/";
  };

  window.getBearerHeaders = async function () {
    let u = window.firebaseAuth && window.firebaseAuth.currentUser;
    if (!u && window.firebaseAuth) {
      u = await new Promise((resolve) => {
        let done = false;
        const timer = setTimeout(() => {
          if (!done) {
            done = true;
            resolve(window.firebaseAuth.currentUser || null);
          }
        }, 1500);
        const off = window.firebaseAuth.onAuthStateChanged((user) => {
          if (done) return;
          done = true;
          clearTimeout(timer);
          if (off) off();
          resolve(user || null);
        });
      });
    }
    if (!u) return {};
    const t = await u.getIdToken(true);
    return { Authorization: "Bearer " + t };
  };
})();
