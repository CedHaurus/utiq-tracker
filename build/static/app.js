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

  function norm(s) {
    return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function matches(c, needle) {
    if (needle && c.getAttribute("data-search").indexOf(needle) === -1) return false;
    if (state.scope !== "all" && c.getAttribute("data-region") !== state.scope) return false;
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

  // Mémorise la langue choisie via le bouton de bascule
  var lang = document.getElementById("lang-toggle");
  if (lang) lang.addEventListener("click", function () {
    try { localStorage.setItem("utiq-lang", lang.getAttribute("data-target")); } catch (e) {}
  });

  // état initial : n'afficher que les 30 premières
  apply(true);
})();
