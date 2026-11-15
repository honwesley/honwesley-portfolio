/* =========================================================
   Light / dark theme switch
   ========================================================= */
(() => {
  const root = document.documentElement;
  const btn = document.querySelector('.theme-toggle');
  if (!btn) return;
  const sync = () => {
    const dark = root.dataset.theme === 'dark';
    btn.setAttribute('aria-checked', String(dark));
  };
  sync();
  btn.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('theme', root.dataset.theme); } catch (e) { /* storage off: still switches for this page */ }
    sync();
    document.dispatchEvent(new Event('themechange'));
  });
})();

/* =========================================================
   Pendubot simulation
   Plant: two aluminum links (6061, 2 in x 1/4 in), 8 in and 14 in.
   Angles: q1 = link 1 from upright, q2 = link 2 relative to link 1.
   Controller: LQR designed on the linearization about upright
   (Q = diag(10, 40, 1, 1), R = 2), torque saturated at 3 N·m.
   ========================================================= */
(() => {
  const rho = 2700, w = 0.0508, t = 0.00635, g = 9.81, b = 0.002;
  const l1 = 8 * 0.0254, l2 = 14 * 0.0254;
  const m1 = rho * l1 * w * t, m2 = rho * l2 * w * t;
  const lc1 = l1 / 2, lc2 = l2 / 2;
  const I1 = m1 * l1 * l1 / 12, I2 = m2 * l2 * l2 / 12;
  const K = [-40.7099, -36.4411, -8.6855, -5.5252];
  const UMAX = 3;

  function f(x, u, damp) {
    const [q1, q2, d1, d2] = x;
    const c2 = Math.cos(q2), s2 = Math.sin(q2);
    const M11 = m1 * lc1 * lc1 + m2 * (l1 * l1 + lc2 * lc2 + 2 * l1 * lc2 * c2) + I1 + I2;
    const M12 = m2 * (lc2 * lc2 + l1 * lc2 * c2) + I2;
    const M22 = m2 * lc2 * lc2 + I2;
    const h = m2 * l1 * lc2 * s2;
    const C1 = -h * (2 * d1 * d2 + d2 * d2), C2 = h * d1 * d1;
    const G1 = -(m1 * lc1 + m2 * l1) * g * Math.sin(q1) - m2 * lc2 * g * Math.sin(q1 + q2);
    const G2 = -m2 * lc2 * g * Math.sin(q1 + q2);
    const r1 = u - damp * d1 - C1 - G1, r2 = -damp * d2 - C2 - G2;
    const det = M11 * M22 - M12 * M12;
    return [d1, d2, (M22 * r1 - M12 * r2) / det, (-M12 * r1 + M11 * r2) / det];
  }
  function rk4(x, u, h, damp) {
    const a = f(x, u, damp);
    const k2 = f(x.map((v, i) => v + h / 2 * a[i]), u, damp);
    const k3 = f(x.map((v, i) => v + h / 2 * k2[i]), u, damp);
    const k4 = f(x.map((v, i) => v + h * k3[i]), u, damp);
    return x.map((v, i) => v + h / 6 * (a[i] + 2 * k2[i] + 2 * k3[i] + k4[i]));
  }
  const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));

  const cv = document.getElementById('pendubot');
  const sc = document.getElementById('scope');
  if (!cv || !sc) return;
  const ctx = cv.getContext('2d'), sctx = sc.getContext('2d');
  const elQ2 = document.getElementById('r-q2'), elU = document.getElementById('r-u'), elS = document.getElementById('r-state');
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Start slightly off balance so the first thing you see is the catch.
  let x = reduce ? [0, 0, 0, 0] : [0.12, -0.32, 0, 0];
  let u = 0, mode = 'balance', modeT = 0, resetFrom = null;
  const N = 480; const histQ = new Float32Array(N), histU = new Float32Array(N); let head = 0;

  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const col = {};
  const readColors = () => { ['ink', 'steel', 'rule', 'link', 'ch1', 'ch2', 'signal', 'plate'].forEach((k) => { col[k] = css('--' + k); }); };
  readColors();
  document.addEventListener('themechange', readColors);

  let W = 0, H = 0, dpr = 1, SW = 0, SH = 0;
  function size() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    const r = cv.getBoundingClientRect(); W = r.width; H = r.height;
    cv.width = W * dpr; cv.height = H * dpr;
    const s = sc.getBoundingClientRect(); SW = s.width; SH = s.height;
    sc.width = SW * dpr; sc.height = SH * dpr;
  }
  new ResizeObserver(size).observe(cv);
  size();

  function geom() {
    const scale = H * 0.42 / (l1 + l2);
    const bx = W / 2, by = H * 0.56;
    const p1 = [bx + l1 * scale * Math.sin(x[0]), by - l1 * scale * Math.cos(x[0])];
    const a2 = x[0] + x[1];
    const p2 = [p1[0] + l2 * scale * Math.sin(a2), p1[1] - l2 * scale * Math.cos(a2)];
    return { bx, by, p1, p2, scale };
  }

  function push(dir) {
    if (mode !== 'balance') return;
    const mag = 0.9 + Math.random() * 0.6;   // rad/s, sometimes enough to lose it
    x[3] += dir * mag; x[2] -= dir * mag * 0.25;
  }
  document.querySelectorAll('[data-push]').forEach((btn) =>
    btn.addEventListener('click', () => push(+btn.dataset.push)));
  cv.addEventListener('click', (e) => {
    const r = cv.getBoundingClientRect(); const { p1, p2 } = geom();
    const cx = (p1[0] + p2[0]) / 2;
    push(e.clientX - r.left < cx ? 1 : -1);    // push away from where you clicked
  });

  function step(dt) {
    const h = 0.001; const n = Math.round(dt / h);
    for (let i = 0; i < n; i++) {
      if (mode === 'balance') {
        const e = [wrap(x[0]), wrap(x[1]), x[2], x[3]];
        u = -(K[0] * e[0] + K[1] * e[1] + K[2] * e[2] + K[3] * e[3]);
        u = Math.max(-UMAX, Math.min(UMAX, u));
        x = rk4(x, u, h, b);
        if (Math.abs(wrap(x[1])) > 0.95 || Math.abs(wrap(x[0])) > 1.3) { mode = 'fallen'; modeT = 0; }
      } else if (mode === 'fallen') {
        u = 0; x = rk4(x, 0, h, 0.02);           // motor off, extra drag
        modeT += h;
        if (modeT > 3) { mode = 'reset'; modeT = 0; resetFrom = x.slice(); }
      } else {
        modeT += h; u = 0;
        const s = Math.min(modeT / 1.4, 1), e = s * s * (3 - 2 * s);
        const a0 = resetFrom[0], a1 = resetFrom[1];
        // take the short way back to upright for each joint
        const t0 = a0 - 2 * Math.PI * Math.round(a0 / (2 * Math.PI));
        const t1 = a1 - 2 * Math.PI * Math.round(a1 / (2 * Math.PI));
        x = [t0 * (1 - e), t1 * (1 - e), 0, 0];
        if (s >= 1) { mode = 'balance'; x = [0, 0, 0, 0]; }
      }
    }
  }

  function draw() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    const { bx, by, p1, p2, scale } = geom();
    // bench: table edge and post
    ctx.fillStyle = col.rule; ctx.fillRect(bx - 70, by + 22, 140, 10);
    ctx.fillStyle = col.steel; ctx.fillRect(bx - 9, by, 18, 26);
    // upright reference
    ctx.setLineDash([4, 6]); ctx.strokeStyle = col.rule; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx, by - (l1 + l2) * scale - 14); ctx.stroke(); ctx.setLineDash([]);
    // links
    ctx.lineCap = 'round';
    ctx.strokeStyle = col.ink; ctx.lineWidth = 15;
    ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(p1[0], p1[1]); ctx.stroke();
    ctx.strokeStyle = col.link; ctx.lineWidth = 12;
    ctx.beginPath(); ctx.moveTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]); ctx.stroke();
    // motor (shoulder) and passive elbow
    ctx.fillStyle = mode === 'balance' ? col.signal : col.steel;
    ctx.beginPath(); ctx.arc(bx, by, 13, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = col.plate; ctx.beginPath(); ctx.arc(bx, by, 4.5, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = col.plate; ctx.strokeStyle = col.ink; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(p1[0], p1[1], 7, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    // torque arc at the shoulder
    if (Math.abs(u) > 0.02) {
      ctx.strokeStyle = col.ch2; ctx.lineWidth = 3;
      const span = Math.min(Math.abs(u) / UMAX, 1) * Math.PI * 0.9;
      ctx.beginPath();
      ctx.arc(bx, by, 22, -Math.PI / 2, -Math.PI / 2 + Math.sign(u) * span, u < 0);
      ctx.stroke();
    }

    // scope
    sctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    sctx.clearRect(0, 0, SW, SH);
    sctx.strokeStyle = 'rgba(230,233,236,.12)'; sctx.lineWidth = 1;
    for (let i = 1; i < 8; i++) { const gx = SW * i / 8; sctx.beginPath(); sctx.moveTo(gx, 0); sctx.lineTo(gx, SH); sctx.stroke(); }
    for (let i = 1; i < 4; i++) { const gy = SH * i / 4; sctx.beginPath(); sctx.moveTo(0, gy); sctx.lineTo(SW, gy); sctx.stroke(); }
    const trace = (arr, c, s) => {
      sctx.strokeStyle = c; sctx.lineWidth = 1.75; sctx.beginPath();
      for (let i = 0; i < N; i++) {
        const v = arr[(head + i) % N];
        const px = SW * i / (N - 1), py = SH / 2 - Math.max(-1, Math.min(1, v / s)) * (SH / 2 - 6);
        i ? sctx.lineTo(px, py) : sctx.moveTo(px, py);
      }
      sctx.stroke();
    };
    trace(histU, col.ch2, UMAX);
    trace(histQ, col.ch1, 60);
    sctx.fillStyle = 'rgba(230,233,236,.55)'; sctx.font = '11px Archivo, sans-serif';
    sctx.fillText('CH1 θ₂ ±60°   CH2 τ ±3 N·m   8 s', 8, SH - 7);
  }

  let last = performance.now(), acc = 0, sampleAcc = 0, visible = true;
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; }).observe(cv);
  function frame(now) {
    let dt = Math.min((now - last) / 1000, 1 / 20); last = now;
    if (visible && !document.hidden) {
      step(dt);
      sampleAcc += dt;
      while (sampleAcc >= 1 / 60) {
        sampleAcc -= 1 / 60;
        histQ[head] = wrap(x[1]) * 180 / Math.PI; histU[head] = u; head = (head + 1) % N;
      }
      draw();
      elQ2.textContent = (wrap(x[1]) * 180 / Math.PI).toFixed(1) + '°';
      elU.textContent = u.toFixed(2) + ' N·m';
      const label = mode === 'balance' ? 'Balancing' : mode === 'fallen' ? 'Lost it. Motor off.' : 'Resetting';
      if (elS.textContent !== label) { elS.textContent = label; elS.classList.toggle('fallen', mode !== 'balance'); }
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();

/* =========================================================
   Lightbox
   ========================================================= */
(() => {
  const dlg = document.getElementById('lightbox');
  if (!dlg) return;
  const img = dlg.querySelector('img'), cap = dlg.querySelector('.lb-cap');
  let opener = null;
  document.querySelectorAll('.shot[data-full]').forEach((btn) => {
    const alt = btn.querySelector('img')?.alt || '';
    btn.setAttribute('aria-label', 'Enlarge: ' + alt);
    btn.addEventListener('click', () => {
      opener = btn; img.src = btn.dataset.full; img.alt = alt; cap.textContent = alt;
      dlg.showModal();
    });
  });
  dlg.querySelector('.lb-close').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener('close', () => { img.removeAttribute('src'); opener?.focus(); });
})();

/* =========================================================
   Project tiles: flip through photos on hover / focus
   ========================================================= */
(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.tile').forEach((t) => {
    const imgs = [...t.querySelectorAll('.tile-media img')];
    const ticks = [...t.querySelectorAll('.ticks i')];
    if (imgs.length < 2) return;
    let k = 0, timer = null;
    const show = (n) => {
      imgs.forEach((im, j) => im.classList.toggle('on', j === n));
      ticks.forEach((tk, j) => tk.classList.toggle('on', j === n));
      k = n;
    };
    show(0);
    const start = () => {
      if (reduce || timer) return;
      show((k + 1) % imgs.length);
      timer = setInterval(() => show((k + 1) % imgs.length), 1100);
    };
    const stop = () => { clearInterval(timer); timer = null; show(0); };
    t.addEventListener('pointerenter', (ev) => { if (ev.pointerType === 'mouse') start(); });
    t.addEventListener('pointerleave', stop);
    t.addEventListener('focus', start);
    t.addEventListener('blur', stop);
  });
})();

/* =========================================================
   Projects page filter, with tiles gliding to new spots
   ========================================================= */
(() => {
  const grid = document.getElementById('tiles');
  if (!grid) return;
  const chips = [...document.querySelectorAll('.chip')];
  const tiles = [...grid.querySelectorAll('.tile')];
  const count = document.getElementById('count');
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function apply(filter) {
    const before = new Map(tiles.filter((t) => !t.hidden).map((t) => [t, t.getBoundingClientRect()]));
    tiles.forEach((t) => { t.hidden = filter !== 'all' && !t.dataset.cats.split(' ').includes(filter); });
    count.textContent = tiles.filter((t) => !t.hidden).length;
    if (reduce) return;
    tiles.filter((t) => !t.hidden).forEach((t) => {
      t.querySelectorAll('.tile-media, .tile-info').forEach((el) => { el.style.animation = 'none'; });
      const a = before.get(t), b = t.getBoundingClientRect();
      if (a) {
        const dx = a.left - b.left, dy = a.top - b.top, sx = a.width / b.width;
        if (dx || dy || sx !== 1) {
          t.animate([{ transformOrigin: 'top left', transform: `translate(${dx}px, ${dy}px) scale(${sx})` },
                     { transformOrigin: 'top left', transform: 'none' }],
                    { duration: 450, easing: 'cubic-bezier(.2,.7,.2,1)' });
        }
      } else {
        t.animate([{ opacity: 0, transform: 'scale(.96)' }, { opacity: 1, transform: 'none' }],
                  { duration: 350, easing: 'ease-out' });
      }
    });
  }

  chips.forEach((c) => c.addEventListener('click', () => {
    chips.forEach((x) => x.setAttribute('aria-pressed', String(x === c)));
    apply(c.dataset.filter);
    history.replaceState(null, '', c.dataset.filter === 'all' ? location.pathname : '#' + c.dataset.filter);
  }));

  const start = location.hash.slice(1);
  const chip = chips.find((c) => c.dataset.filter === start);
  if (chip) chip.click();
})();
