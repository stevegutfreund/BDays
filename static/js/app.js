/**
 * BDays – client-side behaviour.
 *  - confirm dialog for forms with data-confirm
 *  - dropdown menus (<details class="menu">): one open at a time, close on outside click / Esc
 *  - entries table: type filter, search, sort
 *  - settings: "Edit" fills the connection form
 *  - dismissible / auto-fading toasts
 */

/* ---------- Confirm dialog ---------- */
function initConfirm() {
  const dialog = document.getElementById("confirm-dialog");
  const titleEl = document.getElementById("confirm-title");
  const bodyEl = document.getElementById("confirm-body");
  const okBtn = document.getElementById("confirm-ok");

  document.addEventListener("submit", (ev) => {
    const form = ev.target;
    if (!(form instanceof HTMLFormElement) || !form.dataset.confirm) return;
    if (form.dataset.confirmed === "1") return;

    // No <dialog> support: fall back to the browser prompt.
    if (!dialog || typeof dialog.showModal !== "function") {
      if (!window.confirm(form.dataset.confirm)) ev.preventDefault();
      return;
    }

    ev.preventDefault();
    titleEl.textContent = form.dataset.confirmTitle || "Are you sure?";
    bodyEl.textContent = form.dataset.confirm;
    okBtn.textContent = form.dataset.confirmOk || "Confirm";
    const primary = form.dataset.confirmTone === "primary";
    okBtn.className = "btn " + (primary ? "btn-primary" : "btn-danger");
    dialog.classList.toggle("is-primary", primary);

    closeMenus();
    dialog.returnValue = "";
    dialog.showModal();
    dialog.addEventListener(
      "close",
      () => {
        if (dialog.returnValue === "ok") {
          form.dataset.confirmed = "1";
          form.requestSubmit ? form.requestSubmit() : form.submit();
        }
      },
      { once: true }
    );
  });

  // Coming back via the back button must ask again.
  window.addEventListener("pageshow", () => {
    document.querySelectorAll("form[data-confirmed]").forEach((f) => delete f.dataset.confirmed);
  });

  // Click on the backdrop closes the dialog.
  dialog?.addEventListener("click", (ev) => {
    if (ev.target === dialog) dialog.close("cancel");
  });
}

/* ---------- Menus ---------- */
function closeMenus(except) {
  document.querySelectorAll("details.menu[open]").forEach((d) => {
    if (d !== except) d.removeAttribute("open");
  });
}

function initMenus() {
  document.addEventListener("toggle", (ev) => {
    const d = ev.target;
    if (d instanceof HTMLDetailsElement && d.classList.contains("menu") && d.open) {
      closeMenus(d);
      // Flip upward if the popover would run off the bottom of the viewport.
      const pop = d.querySelector(".menu-pop");
      d.classList.remove("menu-up");
      if (pop && pop.getBoundingClientRect().bottom > window.innerHeight - 8) {
        d.classList.add("menu-up");
      }
    }
  }, true);

  document.addEventListener("click", (ev) => {
    if (!ev.target.closest("details.menu")) closeMenus();
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") closeMenus();
  });
}

/* ---------- Entries table ---------- */
function initEntryTable() {
  const table = document.getElementById("entry-table");
  if (!table) return;

  const searchInput = document.getElementById("entry-search");
  const typeGroup = document.getElementById("entry-type-filter");
  const sortSelect = document.getElementById("entry-sort");
  const countEl = document.getElementById("entry-count");
  const noResultsEl = document.getElementById("entry-no-results");
  const tbody = table.querySelector("tbody");
  const rows = Array.from(tbody.querySelectorAll("tr"));
  let type = "";

  function applyFilter() {
    const term = searchInput.value.trim().toLowerCase();
    let visible = 0;
    for (const row of rows) {
      const show = (!term || row.dataset.search.includes(term)) && (!type || row.dataset.type === type);
      row.hidden = !show;
      if (show) visible++;
    }
    countEl.textContent =
      visible === rows.length ? `${rows.length} entries` : `Showing ${visible} of ${rows.length} entries`;
    noResultsEl.hidden = visible !== 0;
    table.closest(".table-wrap").hidden = visible === 0;
  }

  function applySort() {
    const mode = sortSelect.value;
    const sorted = [...rows].sort((a, b) => {
      if (mode === "upcoming") {
        return Number(a.dataset.days) - Number(b.dataset.days) || a.dataset.name.localeCompare(b.dataset.name);
      }
      if (mode === "name") return a.dataset.name.localeCompare(b.dataset.name);
      if (mode === "age-asc" || mode === "age-desc") {
        const ageA = a.dataset.age === "" ? -Infinity : Number(a.dataset.age);
        const ageB = b.dataset.age === "" ? -Infinity : Number(b.dataset.age);
        if (ageA !== ageB) return mode === "age-asc" ? ageA - ageB : ageB - ageA;
        // Same whole-year age: younger = more recent date.
        const dateCmp = a.dataset.date.localeCompare(b.dataset.date);
        return mode === "age-asc" ? -dateCmp : dateCmp;
      }
      return a.dataset.date.localeCompare(b.dataset.date);
    });
    for (const row of sorted) tbody.appendChild(row);
    try { localStorage.setItem("bdays.sort", mode); } catch (_) {}
  }

  typeGroup.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".seg");
    if (!btn) return;
    typeGroup.querySelectorAll(".seg").forEach((b) => b.classList.toggle("active", b === btn));
    type = btn.dataset.type;
    applyFilter();
  });
  searchInput.addEventListener("input", applyFilter);
  sortSelect.addEventListener("change", applySort);

  try {
    const saved = localStorage.getItem("bdays.sort");
    if (saved && [...sortSelect.options].some((o) => o.value === saved)) sortSelect.value = saved;
  } catch (_) {}

  // "/" focuses search.
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "/" && !/input|textarea|select/i.test(document.activeElement.tagName)) {
      ev.preventDefault();
      searchInput.focus();
    }
  });

  applySort();
  applyFilter();
}

/* ---------- Settings ---------- */
function initSettings() {
  const form = document.getElementById("mapping-form");
  if (!form) return;
  document.querySelectorAll("[data-fill-mapping]").forEach((btn) => {
    btn.addEventListener("click", () => {
      form.family.value = btn.dataset.family;
      form.calendar_id.value = btn.dataset.calendar;
      const radio = form.querySelector(`input[name="color"][value="${btn.dataset.color}"]`);
      if (radio) radio.checked = true;
      form.scrollIntoView({ behavior: "smooth", block: "start" });
      form.calendar_id.focus({ preventScroll: true });
    });
  });
}

/* ---------- Toasts ---------- */
function initToasts() {
  document.querySelectorAll(".toast").forEach((t) => {
    t.querySelector("[data-dismiss]")?.addEventListener("click", () => t.remove());
    if (t.classList.contains("toast-success")) {
      setTimeout(() => {
        t.classList.add("is-leaving");
        setTimeout(() => t.remove(), 300);
      }, 5000);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initConfirm();
  initMenus();
  initEntryTable();
  initSettings();
  initToasts();
});
