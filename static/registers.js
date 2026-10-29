// Cross-view of the grid registers: loads registers/index.json, filters and pages it in place.
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var SYM = { L: '✓', R: '✓*', T: '⏱', P: '⏱!', E: 'exp', N: 'Nein', O: '?', '-': '' };
  var WORD = { L: 'listed', R: 'listed with restrictions', T: 'time-limited', P: 'time-limited, date passed',
               E: 'expired', N: 'Nein (the list’s own word)', O: 'see the list', '-': 'no matching entry found' };
  var CLS = { inverter: 'PV inverter', hybrid: 'hybrid', battery: 'battery', 'plug-in': 'plug-in', wallbox: 'wallbox' };
  var ids = ['q', 'brand', 'cls', 'c', 'st', 'n'];
  var data, hits = [], shown = 0, PAGE = 100;

  function esc(s) { return s.replace(/[&<>"]/g, function (ch) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]; }); }

  function apply() {
    var q = $('q').value.trim().toLowerCase(), b = $('brand').value, cls = $('cls').value, c = $('c').value,
        st = $('st').value, n = +$('n').value || 0, ci = data.countries.indexOf(c);
    hits = data.rows.filter(function (r) {
      var cells = r[4];
      if (b && data.brands[r[0]] !== b) return false;
      if (cls && r[2] !== cls) return false;
      if (ci >= 0 && cells[ci] === '-') return false;
      if (st && (ci >= 0 ? cells[ci] !== st : cells.indexOf(st) < 0)) return false;
      if (n && cells.replace(/-/g, '').length < n) return false;
      if (q && (data.brands[r[0]] + ' ' + r[1]).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    $('xcount').textContent = hits.length + (hits.length === 1 ? ' model' : ' models');
    shown = 0;
    var head = '<table class="xv"><thead><tr><th scope="col">Model</th>' +
      data.countries.map(function (k) { return '<th scope="col"><a href="country/' + k.toLowerCase() + '/">' + k + '</a></th>'; }).join('') +
      '</tr></thead><tbody id="xb"></tbody></table>';
    $('xv').innerHTML = head;
    more();
    var p = new URLSearchParams();
    ids.forEach(function (id) { if ($(id).value) p.set(id, $(id).value); });
    history.replaceState(null, '', p.toString() ? '?' + p : location.pathname);
  }

  function more() {
    var html = hits.slice(shown, shown + PAGE).map(function (r) {
      var cells = r[4].split('').map(function (s, i) {
        return '<td class="st st-' + (s === '-' ? 'none' : s) + '" title="' + data.countries[i] + ': ' + WORD[s] + '">' + SYM[s] + '</td>';
      }).join('');
      return '<tr><td><a href="' + r[3] + '"><span class="brand">' + esc(data.brands[r[0]]) + '</span> ' + esc(r[1]) +
        '</a> <span class="muted cls">' + CLS[r[2]] + '</span></td>' + cells + '</tr>';
    }).join('');
    $('xb').insertAdjacentHTML('beforeend', html);
    shown = Math.min(shown + PAGE, hits.length);
    $('more').hidden = shown >= hits.length;
    $('more').textContent = 'Show more (' + (hits.length - shown) + ' left)';
  }

  fetch('index.json').then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    $('brand').insertAdjacentHTML('beforeend', d.brands.map(function (b) {
      return '<option>' + esc(b) + '</option>';
    }).join(''));
    $('xf').hidden = false;
    var init = new URLSearchParams(location.search);
    ids.forEach(function (id) {
      if (init.get(id)) $(id).value = init.get(id);
      $(id).addEventListener(id === 'q' ? 'input' : 'change', apply);
    });
    $('more').addEventListener('click', more);
    apply();
  });
})();
