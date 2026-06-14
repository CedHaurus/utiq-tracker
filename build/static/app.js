(function () {
  "use strict";
  var grid = document.getElementById("grid");
  if (!grid) return;
  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
  var q = document.getElementById("q");
  var cat = document.getElementById("f-cat");
  var country = document.getElementById("f-country");
  var countEl = document.getElementById("count-n");
  var empty = document.getElementById("empty");
  var reset = document.getElementById("reset");
  var more = document.getElementById("more");
  var moreWrap = document.getElementById("more-wrap");
  var scopeBtns = Array.prototype.slice.call(document.querySelectorAll("[data-scope]"));
  var PAGE = 30;
  var limit = PAGE;
  var state = { q: "", scope: "all", cat: "all", country: "all" };

  // Pays « maison » : défaut serveur (langue de la page), affiné par le navigateur.
  var U = window.__UTRK || { home: "FR", countries: {} };
  var HOME = U.home;
  var homeBtn = document.querySelector('[data-scope="home"]');

  function detectCountry() {
    var l = (navigator.languages && navigator.languages[0]) || navigator.language || "";
    var m = /[-_]([A-Za-z]{2})(?:[-_]|$)/.exec(l);
    if (m) {
      var cc = m[1].toUpperCase();
      if (U.countries[cc]) return cc;
    }
    return null;
  }

  (function initHome() {
    var cc = detectCountry();
    if (cc && U.countries[cc]) HOME = cc;
    if (homeBtn && U.countries[HOME]) {
      var f = homeBtn.querySelector(".seg-flag"), n = homeBtn.querySelector(".seg-home");
      if (f) f.textContent = U.countries[HOME][0];
      if (n) n.textContent = U.countries[HOME][1];
    }
  })();

  function norm(s) {
    return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function matches(c, needle) {
    if (needle && c.getAttribute("data-search").indexOf(needle) === -1) return false;
    if (state.scope === "home" && c.getAttribute("data-country") !== HOME) return false;
    if (state.scope === "world" && c.getAttribute("data-country") === HOME) return false;
    if (state.cat !== "all" && c.getAttribute("data-cat") !== state.cat) return false;
    if (state.country !== "all" && c.getAttribute("data-country") !== state.country) return false;
    return true;
  }

  function apply(resetLimit) {
    if (resetLimit) limit = PAGE;
    var needle = norm(state.q.trim());
    var total = 0;   // nb de correspondances
    var shown = 0;   // nb affichées (<= limit)
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      if (matches(c, needle)) {
        total++;
        if (shown < limit) { c.hidden = false; shown++; }
        else c.hidden = true;
      } else {
        c.hidden = true;
      }
    }
    if (countEl) countEl.textContent = total;
    if (empty) empty.style.display = total ? "none" : "block";
    if (moreWrap) {
      var rest = total - shown;
      if (rest > 0) {
        moreWrap.style.display = "block";
        if (more) more.textContent = (more.getAttribute("data-tpl") || "Voir plus ({n})").replace("{n}", rest);
      } else {
        moreWrap.style.display = "none";
      }
    }
  }

  var t;
  if (q) q.addEventListener("input", function () {
    clearTimeout(t);
    t = setTimeout(function () { state.q = q.value; apply(true); }, 90);
  });
  if (cat) cat.addEventListener("change", function () { state.cat = cat.value; apply(true); });
  if (country) country.addEventListener("change", function () { state.country = country.value; apply(true); });
  scopeBtns.forEach(function (b) {
    b.addEventListener("click", function () {
      state.scope = b.getAttribute("data-scope");
      scopeBtns.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      apply(true);
    });
  });
  if (more) more.addEventListener("click", function () { limit += PAGE; apply(false); });
  if (reset) reset.addEventListener("click", function () {
    state = { q: "", scope: "all", cat: "all", country: "all" };
    if (q) q.value = "";
    if (cat) cat.value = "all";
    if (country) country.value = "all";
    scopeBtns.forEach(function (x) { x.setAttribute("aria-pressed", x.getAttribute("data-scope") === "all" ? "true" : "false"); });
    apply(true);
  });

  // état initial : n'afficher que les 30 premières
  apply(true);
})();

// Menu de langues : présent sur toutes les pages (hors IIFE de la grille)
(function () {
  "use strict";
  document.querySelectorAll("a[data-lang]").forEach(function (a) {
    a.addEventListener("click", function () {
      try { localStorage.setItem("utiq-lang", a.getAttribute("data-lang")); } catch (e) {}
    });
  });
  document.addEventListener("click", function (e) {
    document.querySelectorAll("details.langmenu[open]").forEach(function (d) {
      if (!d.contains(e.target)) d.removeAttribute("open");
    });
  });
})();
