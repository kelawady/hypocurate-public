// Live state of an open run (step 10a; owner, 2026-10-11: a small script of our own, not HTMX).
// The server decides when polling ends: a state fragment of an open run (queued, waiting or running) carries
// data-poll with its own address; one of an ended run (completed or failed) carries data-ended="true" and no address.
// This script asks again only when the fragment it just received carries data-poll; on data-ended it reloads the
// page once to show the results and schedules nothing more. A page without data-poll never polls.
(function () {
  var INTERVAL_MS = 5000;

  function schedule(url) {
    window.setTimeout(function () { tick(url); }, INTERVAL_MS);
  }

  function tick(url) {
    fetch(url, { credentials: "same-origin", cache: "no-store", headers: { "Accept": "text/html" } })
      .then(function (response) {
        if (!response.ok) { throw new Error("state " + response.status); }
        return response.text();
      })
      .then(function (html) {
        var holder = document.createElement("div");
        holder.innerHTML = html;
        var next = holder.querySelector("#run-state");
        var current = document.getElementById("run-state");
        if (!next || !current) { return; }  // not a state (for example the sign-in page): stop
        if (next.getAttribute("data-ended") === "true") { window.location.reload(); return; }  // ended: stop
        current.replaceWith(next);
        var again = next.getAttribute("data-poll");
        if (again) { schedule(again); }
      })
      .catch(function () { schedule(url); });  // the network or the service is down for a moment: ask again
  }

  document.addEventListener("DOMContentLoaded", function () {
    var state = document.getElementById("run-state");
    var url = state && state.getAttribute("data-poll");
    if (url) { schedule(url); }
  });
})();
