// Visit counter (GoatCounter: no cookies, no personal data).
// 1) Create a free site at goatcounter.com with the code below.
// 2) In its Settings, turn on "Allow adding visitor counts on your website".
// If the service is unreachable or not set up yet, the badge simply stays hidden.
(function () {
  var CODE = 'oliverlee';
  var base = 'https://' + CODE + '.goatcounter.com';
  var box = document.querySelector('.visits');

  // Record this page view (count.js skips localhost and file:// on its own).
  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://gc.zgo.at/count.js';
  s.setAttribute('data-goatcounter', base + '/count');
  document.head.appendChild(s);

  if (!box || !window.fetch) return;
  var num = box.querySelector('.visits-n');
  var ctrl = window.AbortController ? new AbortController() : null;
  var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, 6000);

  fetch(base + '/counter/TOTAL.json', ctrl ? { signal: ctrl.signal } : {})
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      clearTimeout(timer);
      if (!d || !d.count) return;
      var target = parseInt(String(d.count).replace(/[^0-9]/g, ''), 10);
      if (!target) return;
      box.hidden = false;
      var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (still) { num.textContent = target.toLocaleString('en-US'); return; }
      // Count up quickly, like a detector settling on a reading.
      var t0 = null, dur = 900;
      function step(t) {
        if (!t0) t0 = t;
        var k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
        num.textContent = Math.round(target * e).toLocaleString('en-US');
        if (k < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    })
    .catch(function () { clearTimeout(timer); });
})();
