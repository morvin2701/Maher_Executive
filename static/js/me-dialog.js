/**
 * Maher Executive branded dialogs — replaces native prompt/confirm/alert UX.
 * Use: await window.MeDialog.prompt(...) | confirm | alert | form(...)
 */
(function () {
  let overlayEl = null;
  let resolver = null;

  function ensureRoot() {
    if (overlayEl && overlayEl.isConnected) return overlayEl;
    overlayEl = document.createElement("div");
    overlayEl.id = "me-dialog-overlay";
    overlayEl.className = "me-dialog-overlay";
    overlayEl.setAttribute("role", "presentation");
    overlayEl.hidden = true;
    document.body.appendChild(overlayEl);
    return overlayEl;
  }

  function trapFocus(dialog) {
    const focusables = dialog.querySelectorAll(
      'button, [href], input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (first) first.focus();
    dialog.addEventListener("keydown", function onKey(e) {
      if (e.key === "Escape") {
        e.preventDefault();
        dialog.dispatchEvent(new CustomEvent("me-cancel", { bubbles: true }));
      }
      if (e.key !== "Tab" || focusables.length === 0) return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    });
  }

  function finish(value) {
    document.body.style.overflow = "";
    const ov = ensureRoot();
    ov.hidden = true;
    ov.innerHTML = "";
    const fn = resolver;
    resolver = null;
    if (fn) fn(value);
  }

  function openShell(innerHtml, onMount) {
    const ov = ensureRoot();
    if (resolver) finish(undefined);
    ov.innerHTML =
      '<div class="me-dialog-backdrop" data-me-close="1"></div>' +
      '<div class="me-dialog" role="dialog" aria-modal="true" aria-labelledby="me-dialog-title">' +
      innerHtml +
      "</div>";
    ov.hidden = false;
    document.body.style.overflow = "hidden";
    const dialog = ov.querySelector(".me-dialog");
    ov.querySelectorAll("[data-me-close]").forEach((n) => {
      n.addEventListener("click", function () {
        dialog.dispatchEvent(new CustomEvent("me-cancel", { bubbles: true }));
      });
    });
    if (onMount) onMount(dialog, ov);
    trapFocus(dialog);
  }

  function escAttr(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;");
  }

  const MeDialog = {};

  MeDialog.alert = function (message, opts) {
    opts = opts || {};
    const title = opts.title || "Maher Executive";
    const msg = String(message || "");
    return new Promise(function (resolve) {
      resolver = function () {
        resolve();
      };
      openShell(
        '<div class="me-dialog-brand"><span class="me-dialog-mark">ME</span><span class="me-dialog-brand-text">Maher Executive</span></div>' +
          '<h2 id="me-dialog-title" class="me-dialog-title">' +
          escAttr(title) +
          "</h2>" +
          '<p class="me-dialog-message">' +
          escAttr(msg) +
          "</p>" +
          '<div class="me-dialog-actions">' +
          '<button type="button" class="btn btn-primary me-dialog-primary" id="me-alert-ok">Continue</button>' +
          "</div>",
        function (dialog) {
          dialog.addEventListener(
            "me-cancel",
            function () {
              finish();
            },
            { once: true }
          );
          dialog.querySelector("#me-alert-ok").addEventListener("click", function () {
            finish();
          });
        }
      );
    });
  };

  MeDialog.confirm = function (message, opts) {
    opts = opts || {};
    const title = opts.title || "Confirm";
    const msg = String(message || "");
    const okText = opts.okText || "Confirm";
    const cancelText = opts.cancelText || "Cancel";
    return new Promise(function (resolve) {
      resolver = function (v) {
        resolve(v);
      };
      openShell(
        '<div class="me-dialog-brand"><span class="me-dialog-mark">ME</span><span class="me-dialog-brand-text">Maher Executive</span></div>' +
          '<h2 id="me-dialog-title" class="me-dialog-title">' +
          escAttr(title) +
          "</h2>" +
          '<p class="me-dialog-message">' +
          escAttr(msg) +
          "</p>" +
          '<div class="me-dialog-actions me-dialog-actions--split">' +
          '<button type="button" class="btn btn-outline" id="me-confirm-cancel">' +
          escAttr(cancelText) +
          "</button>" +
          '<button type="button" class="btn btn-primary me-dialog-primary" id="me-confirm-ok">' +
          escAttr(okText) +
          "</button>" +
          "</div>",
        function (dialog) {
          dialog.addEventListener(
            "me-cancel",
            function () {
              finish(false);
            },
            { once: true }
          );
          dialog.querySelector("#me-confirm-cancel").addEventListener("click", function () {
            finish(false);
          });
          dialog.querySelector("#me-confirm-ok").addEventListener("click", function () {
            finish(true);
          });
        }
      );
    });
  };

  MeDialog.prompt = function (message, defaultValue, opts) {
    opts = opts || {};
    const title = opts.title || "Enter value";
    const msg = String(message || "");
    const placeholder = opts.placeholder || "";
    const inputType = opts.inputType || "text";
    const defaultVal = defaultValue != null ? String(defaultValue) : "";
    const okText = opts.okText || "OK";
    const cancelText = opts.cancelText || "Cancel";
    return new Promise(function (resolve) {
      resolver = function (v) {
        resolve(v);
      };
      openShell(
        '<div class="me-dialog-brand"><span class="me-dialog-mark">ME</span><span class="me-dialog-brand-text">Maher Executive</span></div>' +
          '<h2 id="me-dialog-title" class="me-dialog-title">' +
          escAttr(title) +
          "</h2>" +
          (msg ? '<p class="me-dialog-message">' + escAttr(msg) + "</p>" : "") +
          '<label class="me-dialog-field"><span class="me-dialog-label">' +
          escAttr(opts.fieldLabel || "Value") +
          '</span><input type="' +
          escAttr(inputType) +
          '" id="me-prompt-input" class="me-dialog-input" placeholder="' +
          escAttr(placeholder) +
          '" value="' +
          escAttr(defaultVal) +
          '" autocomplete="off" /></label>' +
          '<div class="me-dialog-actions me-dialog-actions--split">' +
          '<button type="button" class="btn btn-outline" id="me-prompt-cancel">' +
          escAttr(cancelText) +
          "</button>" +
          '<button type="button" class="btn btn-primary me-dialog-primary" id="me-prompt-ok">' +
          escAttr(okText) +
          "</button>" +
          "</div>",
        function (dialog) {
          const input = dialog.querySelector("#me-prompt-input");
          dialog.addEventListener(
            "me-cancel",
            function () {
              finish(null);
            },
            { once: true }
          );
          dialog.querySelector("#me-prompt-cancel").addEventListener("click", function () {
            finish(null);
          });
          function submit() {
            finish(input.value);
          }
          dialog.querySelector("#me-prompt-ok").addEventListener("click", submit);
          input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
              e.preventDefault();
              submit();
            }
          });
          setTimeout(function () {
            input.focus();
            input.select();
          }, 10);
        }
      );
    });
  };

  /**
   * fields: [{ name, label, type?: 'text'|'email'|'number'|'textarea'|'checkbox', value?, placeholder?, required? }]
   * Returns object of values or null if cancelled.
   */
  MeDialog.form = function (opts) {
    opts = opts || {};
    const title = opts.title || "Details";
    const subtitle = opts.subtitle || "";
    const fields = Array.isArray(opts.fields) ? opts.fields : [];
    const okText = opts.okText || "Save";
    const cancelText = opts.cancelText || "Cancel";
    const fieldsHtml = fields
      .map(function (f) {
        const name = escAttr(f.name);
        const label = escAttr(f.label || f.name);
        const req = f.required ? " required" : "";
        const ph = escAttr(f.placeholder || "");
        const val =
          f.value !== undefined && f.value !== null ? escAttr(String(f.value)) : "";
        const typ = String(f.type || "text").toLowerCase();
        if (typ === "textarea") {
          return (
            '<label class="me-dialog-field"><span class="me-dialog-label">' +
            label +
            '</span><textarea name="' +
            name +
            '" class="me-dialog-input me-dialog-textarea" placeholder="' +
            ph +
            '"' +
            req +
            ">" +
            val +
            "</textarea></label>"
          );
        }
        if (typ === "checkbox") {
          const checked = f.value ? " checked" : "";
          return (
            '<label class="me-dialog-check"><input type="checkbox" name="' +
            name +
            '" id="me-f-' +
            name +
            '"' +
            checked +
            ' /><span>' +
            label +
            "</span></label>"
          );
        }
        const inputType = typ === "email" || typ === "number" ? typ : "text";
        return (
          '<label class="me-dialog-field"><span class="me-dialog-label">' +
          label +
          '</span><input type="' +
          inputType +
          '" name="' +
          name +
          '" class="me-dialog-input" placeholder="' +
          ph +
          '" value="' +
          val +
          '"' +
          req +
          " /></label>"
        );
      })
      .join("");

    return new Promise(function (resolve) {
      resolver = function (v) {
        resolve(v);
      };
      openShell(
        '<div class="me-dialog-brand"><span class="me-dialog-mark">ME</span><span class="me-dialog-brand-text">Maher Executive</span></div>' +
          '<h2 id="me-dialog-title" class="me-dialog-title">' +
          escAttr(title) +
          "</h2>" +
          (subtitle ? '<p class="me-dialog-sub">' + escAttr(subtitle) + "</p>" : "") +
          '<form class="me-dialog-form" id="me-dialog-form">' +
          fieldsHtml +
          '<div class="me-dialog-actions me-dialog-actions--split">' +
          '<button type="button" class="btn btn-outline" id="me-form-cancel">' +
          escAttr(cancelText) +
          "</button>" +
          '<button type="submit" class="btn btn-primary me-dialog-primary" id="me-form-ok">' +
          escAttr(okText) +
          "</button>" +
          "</div></form>",
        function (dialog) {
          const form = dialog.querySelector("#me-dialog-form");
          dialog.addEventListener(
            "me-cancel",
            function () {
              finish(null);
            },
            { once: true }
          );
          dialog.querySelector("#me-form-cancel").addEventListener("click", function () {
            finish(null);
          });
          form.addEventListener("submit", function (e) {
            e.preventDefault();
            const out = {};
            fields.forEach(function (f) {
              const n = f.name;
              const typ = String(f.type || "text").toLowerCase();
              const el = form.elements[n];
              if (typ === "checkbox") {
                out[n] = !!(el && el.checked);
              } else {
                out[n] = el && "value" in el ? String(el.value || "") : "";
              }
            });
            finish(out);
          });
        }
      );
    });
  };

  window.MeDialog = MeDialog;

  /** Optional: route native dialogs for older code paths (still sync-broken — prefer MeDialog.*) */
  if (typeof window.alert === "function") {
    var _alert = window.alert.bind(window);
    window.meNativeAlert = _alert;
  }
})();
