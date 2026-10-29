// Filters the family list in place; the list itself is plain HTML so the page works without JS.
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var items = Array.prototype.slice.call(document.querySelectorAll('#list > li'));
  var text = items.map(function (li) { return li.textContent.toLowerCase(); });
  var ids = ['q', 'brand', 'cls', 'conn', 'ctl', 'reg'];

  function apply() {
    var q = $('q').value.trim().toLowerCase(), b = $('brand').value, c = $('cls').value,
        n = $('conn').value, ctl = $('ctl').value, r = $('reg').value, shown = 0;
    items.forEach(function (li, i) {
      var d = li.dataset;
      var ok = (!q || text[i].indexOf(q) >= 0) && (!b || d.b === b) && (!c || d.c === c) &&
        (!n || (' ' + d.n + ' ').indexOf(' ' + n + ' ') >= 0) &&
        (!r || (' ' + d.r + ' ').indexOf(' ' + r + ' ') >= 0) &&
        (!ctl || (ctl === 'ha' && d.l === '2') || (ctl === 'any' && d.l !== '0') || (ctl === 'write' && d.w === '1'));
      li.hidden = !ok;
      if (ok) shown++;
    });
    $('count').textContent = shown + (shown === 1 ? ' family' : ' families');
    var p = new URLSearchParams();
    ids.forEach(function (id) { if ($(id).value) p.set(id, $(id).value); });
    history.replaceState(null, '', p.toString() ? '?' + p : location.pathname);
  }

  var init = new URLSearchParams(location.search);
  ids.forEach(function (id) {
    if (init.get(id)) $(id).value = init.get(id);
    $(id).addEventListener(id === 'q' ? 'input' : 'change', apply);
  });
  apply();
})();
