// Information buttons (PRD 9.7): open on hover, keyboard focus, click or tap; close on Escape or when focus leaves.
// The text comes from the glossary file, inserted by the server; this script only shows and hides it. Events are
// handled on the document, so buttons in a part of the page replaced by poll.js work too.
(function () {
  var pinned = null;

  function set(box, open) {
    var b = box.querySelector(".info-button"), t = box.querySelector(".info-text");
    if (!b || !t) return;
    t.hidden = !open;
    b.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {  // open towards the side with room, so the text stays on the screen
      box.classList.remove("flip");
      if (t.getBoundingClientRect().right > document.documentElement.clientWidth - 8) box.classList.add("flip");
    }
  }

  function boxOf(node) { return node && node.closest ? node.closest(".info") : null; }

  document.addEventListener("mouseover", function (ev) {
    var box = boxOf(ev.target);
    if (box) set(box, true);
  });
  document.addEventListener("mouseout", function (ev) {
    var box = boxOf(ev.target);
    if (box && box !== pinned && !box.contains(ev.relatedTarget)) set(box, false);
  });
  document.addEventListener("focusin", function (ev) {
    var box = boxOf(ev.target);
    if (box) set(box, true);
  });
  document.addEventListener("focusout", function (ev) {
    var box = boxOf(ev.target);
    if (box && !box.contains(ev.relatedTarget)) { if (pinned === box) pinned = null; set(box, false); }
  });
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest ? ev.target.closest(".info-button") : null;
    if (!b) return;
    ev.preventDefault();
    var box = boxOf(b);
    pinned = pinned === box ? null : box;
    set(box, pinned === box);
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Escape") return;
    var box = boxOf(ev.target);
    if (box) { if (pinned === box) pinned = null; set(box, false); }
  });
})();
