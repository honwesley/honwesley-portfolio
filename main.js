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
   Plant: two aluminum links (6061, 2 in x 1/4 in), 8 in and 14 in long.
   Angles: q1 = link 1 from upright, q2 = link 2 relative to link 1.
   The motor never switches off. A hybrid supervisor runs:
     - swing-up: energy pumping through collocated partial feedback
       linearization of the shoulder, until the state is near upright
     - balance: the selected controller (PID, LQR, NMPC or fuzzy)
   All four were tuned and tested offline on the same model: each
   recovers from hanging straight down and from random states up to
   10 rad/s on link 1 and 20 rad/s on link 2.
   ========================================================= */
(() => {
  const cv = document.getElementById('pendubot');
  if (!cv) return;

  // ---------- plant ----------
  const rho = 2700, wd = 0.0508, th = 0.00635, g = 9.81, b = 0.002;
  const l1 = 8 * 0.0254, l2 = 14 * 0.0254;
  const m1 = rho * l1 * wd * th, m2 = rho * l2 * wd * th;
  const lc1 = l1 / 2, lc2 = l2 / 2;
  const I1 = m1 * l1 * l1 / 12, I2 = m2 * l2 * l2 / 12;
  const UMAX = 3;                       // N·m, motor torque limit
  const H = 0.001;                      // s, physics and control step (1 kHz)

  const K = [-40.70993, -36.44109, -8.68555, -5.52524];          // LQR, Q = diag(10, 40, 1, 1), R = 2
  const P = [[352.699384, 264.773243, 74.904033, 40.579896],     // Riccati solution, used for the
             [264.773243, 207.297711, 56.775024, 30.792226],     // catch region and NMPC terminal cost
             [74.904033, 56.775024, 16.061388, 8.701128],
             [40.579896, 30.792226, 8.701128, 4.71874]];
  const QD = [10, 40, 1, 1], RW = 2;
  const ETOP = 1.333991;                                         // J, energy at rest upright
  const PID = { kp1: -3.41507, kp2: -36.44109, kd1: -2.68626, kd2: -5.52524, ki1: -2.0 };
  const SW = { kp: 3, kd: 2, ke: 20 };                           // swing-up gains
  const CATCH = { pid: 25, lqr: 25, nmpc: 25, fuzzy: 25 }, LOSE = 75;
  const NM = { NB: 4, Hz: 0.2, h: 0.004, Ts: 0.02, iters: 2, step: 2.0 };
  const FZ = 30;                                                  // fuzzy universe scale

  const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
  const clampU = (u) => Math.max(-UMAX, Math.min(UMAX, u));

  function terms(x) {
    const c2 = Math.cos(x[1]), s2 = Math.sin(x[1]);
    const M11 = m1 * lc1 * lc1 + m2 * (l1 * l1 + lc2 * lc2 + 2 * l1 * lc2 * c2) + I1 + I2;
    const M12 = m2 * (lc2 * lc2 + l1 * lc2 * c2) + I2;
    const M22 = m2 * lc2 * lc2 + I2;
    const hh = m2 * l1 * lc2 * s2;
    const C1 = -hh * (2 * x[2] * x[3] + x[3] * x[3]), C2 = hh * x[2] * x[2];
    const G1 = -(m1 * lc1 + m2 * l1) * g * Math.sin(x[0]) - m2 * lc2 * g * Math.sin(x[0] + x[1]);
    const G2 = -m2 * lc2 * g * Math.sin(x[0] + x[1]);
    return [M11, M12, M22, C1, C2, G1, G2];
  }
  function f(x, u, e1, e2) {
    const [M11, M12, M22, C1, C2, G1, G2] = terms(x);
    const r1 = u - b * x[2] - C1 - G1 + e1, r2 = -b * x[3] - C2 - G2 + e2;
    const det = M11 * M22 - M12 * M12;
    return [x[2], x[3], (M22 * r1 - M12 * r2) / det, (-M12 * r1 + M11 * r2) / det];
  }
  function rk4(x, u, h, e1 = 0, e2 = 0) {
    const a = f(x, u, e1, e2);
    const k2 = f(x.map((v, i) => v + h / 2 * a[i]), u, e1, e2);
    const k3 = f(x.map((v, i) => v + h / 2 * k2[i]), u, e1, e2);
    const k4 = f(x.map((v, i) => v + h * k3[i]), u, e1, e2);
    return x.map((v, i) => v + h / 6 * (a[i] + 2 * k2[i] + 2 * k3[i] + k4[i]));
  }
  function energy(x) {
    const [M11, M12, M22] = terms(x);
    const T = 0.5 * (M11 * x[2] * x[2] + 2 * M12 * x[2] * x[3] + M22 * x[3] * x[3]);
    const V = m1 * g * lc1 * Math.cos(x[0]) + m2 * g * (l1 * Math.cos(x[0]) + lc2 * Math.cos(x[0] + x[1]));
    return T + V;
  }
  const err = (x) => [wrap(x[0]), wrap(x[1]), x[2], x[3]];
  const quad = (z) => { let s = 0; for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) s += z[i] * P[i][j] * z[j]; return s; };
  const lqrU = (z) => -(K[0] * z[0] + K[1] * z[1] + K[2] * z[2] + K[3] * z[3]);

  // ---------- controllers ----------
  function swingup(x) {
    const [M11, M12, M22, C1, C2, G1, G2] = terms(x);
    const E = energy(x);
    let v = -SW.kp * wrap(x[0]) - SW.kd * x[2] + SW.ke * (ETOP - E) * x[2];
    if (Math.abs(x[2]) < 0.05 && Math.abs(x[3]) < 0.05 && Math.abs(ETOP - E) > 0.2) v += 8;  // start pumping from rest
    const q2dd = -(M12 * v + C2 + G2 + b * x[3]) / M22;
    return M11 * v + M12 * q2dd + C1 + G1 + b * x[2];
  }

  const tri = (v, c) => Math.max(0, 1 - Math.abs(v - c) / 0.5);
  const CENT = [-1, -0.5, 0, 0.5, 1];
  function memb(v) {
    return CENT.map((c) => (c === -1 ? Math.min(1, Math.max(0, (-0.5 - v) / 0.5)) : c === 1 ? Math.min(1, Math.max(0, (v - 0.5) / 0.5)) : tri(v, c)));
  }

  const ctl = {
    pidI: 0, nmV: null, nmT: 0, nmCost: 0,
    reset() { this.pidI = 0; this.nmV = null; this.nmT = 0; },
    pid(z) {
      const a1 = z[0], a2 = z[0] + z[1], w1 = z[2], w2 = z[2] + z[3];
      this.pidI = Math.max(-0.5, Math.min(0.5, this.pidI + a1 * H));
      return -(PID.kp1 * a1 + PID.kd1 * w1 + PID.kp2 * a2 + PID.kd2 * w2 + PID.ki1 * this.pidI);
    },
    lqr(z) { return lqrU(z); },
    fuzzy(z) {
      // Mamdani-style 5x5 rule base on LQR-projected angle error and rate error,
      // product inference, weighted-average defuzzification
      const e = -(K[0] * z[0] + K[1] * z[1]), de = -(K[2] * z[2] + K[3] * z[3]);
      const E = Math.max(-1, Math.min(1, e / FZ)), D = Math.max(-1, Math.min(1, de / FZ));
      const mE = memb(E), mD = memb(D);
      let num = 0, den = 0;
      for (let i = 0; i < 5; i++) for (let j = 0; j < 5; j++) {
        const w = mE[i] * mD[j];
        if (w > 0) { num += w * Math.max(-1, Math.min(1, CENT[i] + CENT[j])); den += w; }
      }
      return den > 0 ? FZ * num / den : 0;
    },
    nmpc(x, z) {
      // pre-stabilized NMPC: u = sat(-K z + v), v piecewise constant over NB blocks,
      // horizon 0.2 s, re-solved at 50 Hz by gradient descent with backtracking
      this.nmT += H;
      if (this.nmV && this.nmT < NM.Ts - 1e-9) return lqrU(z) + this.nmV[0];
      this.nmT = 0;
      const nb = NM.NB, per = Math.round(NM.Hz / NM.NB / NM.h);
      let v = this.nmV ? [...this.nmV.slice(1), 0] : new Array(nb).fill(0);
      const cost = (vv) => {
        let xx = x.slice(), J = 0;
        for (let k = 0; k < nb; k++) for (let s = 0; s < per; s++) {
          const zz = err(xx), u = clampU(lqrU(zz) + vv[k]);
          J += NM.h * (QD[0] * zz[0] * zz[0] + QD[1] * zz[1] * zz[1] + QD[2] * zz[2] * zz[2] + QD[3] * zz[3] * zz[3] + RW * u * u);
          xx = rk4(xx, u, NM.h);
        }
        return J + quad(err(xx));
      };
      let J = cost(v);
      for (let it = 0; it < NM.iters; it++) {
        const gr = v.map((_, k) => { const vp = v.slice(); vp[k] += 1e-2; return (cost(vp) - J) / 1e-2; });
        let step = NM.step;
        for (let t = 0; t < 5; t++) {
          const vn = v.map((vk, k) => Math.max(-UMAX, Math.min(UMAX, vk - step * gr[k])));
          const Jn = cost(vn);
          if (Jn < J) { v = vn; J = Jn; break; }
          step *= 0.4;
        }
      }
      this.nmV = v; this.nmCost = J;
      return lqrU(z) + v[0];
    },
  };

  // ---------- state ----------
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let x = reduce ? [0, 0, 0, 0] : [Math.PI - 0.02, 0, 0, 0];   // start hanging down: watch it swing up
  let u = 0, mode = 'swing', kind = 'lqr', solveUs = 0, grab = null;
  const N = 600;   // 10 s of history at 60 Hz
  const hist = { q1: new Float32Array(N), q2: new Float32Array(N), u: new Float32Array(N), e: new Float32Array(N) };
  let head = 0;

  // ---------- controller picker ----------
  const picker = document.querySelectorAll('[data-ctl]');
  const ctlNote = document.getElementById('ctl-note');
  const NOTES = {
    pid: 'Two PID loops, on the link 1 angle and the absolute link 2 angle, summed into one torque.',
    lqr: 'Full-state feedback from the Riccati solution on the linearized model.',
    nmpc: 'Optimizes torque over a 0.2 s horizon on the full nonlinear model, re-solved 50 times a second.',
    fuzzy: '25-rule fuzzy controller on angle error and rate error, with product inference.',
  };
  picker.forEach((btn) => btn.addEventListener('click', () => {
    kind = btn.dataset.ctl; ctl.reset();
    picker.forEach((p) => p.setAttribute('aria-pressed', String(p === btn)));
    if (ctlNote) ctlNote.textContent = NOTES[kind];
  }));

  // ---------- drawing setup ----------
  const sA = document.getElementById('scope-a'), sB = document.getElementById('scope-b');
  const ctx = cv.getContext('2d'), cA = sA.getContext('2d'), cB = sB.getContext('2d');
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const col = {};
  const readColors = () => { ['ink', 'steel', 'rule', 'link', 'ch1', 'ch2', 'signal', 'plate'].forEach((k) => { col[k] = css('--' + k); }); };
  readColors();
  document.addEventListener('themechange', readColors);

  let W = 0, Hh = 0, dpr = 1;
  const dims = new Map();
  function size() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    [cv, sA, sB].forEach((c) => {
      const r = c.getBoundingClientRect();
      c.width = r.width * dpr; c.height = r.height * dpr; dims.set(c, [r.width, r.height]);
    });
    [W, Hh] = dims.get(cv);
  }
  new ResizeObserver(size).observe(cv);
  size();

  const geom = () => {
    const scale = Hh * 0.44 / (l1 + l2), bx = W / 2, by = Hh * 0.5;
    const p1 = [bx + l1 * scale * Math.sin(x[0]), by - l1 * scale * Math.cos(x[0])];
    const a2 = x[0] + x[1];
    const p2 = [p1[0] + l2 * scale * Math.sin(a2), p1[1] - l2 * scale * Math.cos(a2)];
    return { scale, bx, by, p1, p2 };
  };

  // ---------- grab and throw ----------
  const toLocal = (ev) => { const r = cv.getBoundingClientRect(); return [ev.clientX - r.left, ev.clientY - r.top]; };
  cv.addEventListener('pointerdown', (ev) => {
    const [mx, my] = toLocal(ev), { p1, p2 } = geom();
    const d = (a) => Math.hypot(a[0] - mx, a[1] - my);
    if (Math.min(d(p1), d(p2), d([(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2])) > 60) return;
    grab = [mx, my]; cv.setPointerCapture(ev.pointerId); ev.preventDefault();
  });
  cv.addEventListener('pointermove', (ev) => { if (grab) grab = toLocal(ev); });
  const release = () => { grab = null; };
  cv.addEventListener('pointerup', release);
  cv.addEventListener('pointercancel', release);

  // Spring from the pointer to the tip of link 2, mapped to joint torques through the Jacobian.
  function external() {
    if (!grab) return [0, 0];
    const { scale, bx, by } = geom();
    const tx = (grab[0] - bx) / scale, ty = (by - grab[1]) / scale;   // pointer in metres, y up
    const a2 = x[0] + x[1];
    const px = l1 * Math.sin(x[0]) + l2 * Math.sin(a2), py = l1 * Math.cos(x[0]) + l2 * Math.cos(a2);
    const j11 = l1 * Math.cos(x[0]) + l2 * Math.cos(a2), j12 = l2 * Math.cos(a2);
    const j21 = -l1 * Math.sin(x[0]) - l2 * Math.sin(a2), j22 = -l2 * Math.sin(a2);
    const vx = j11 * x[2] + j12 * x[3], vy = j21 * x[2] + j22 * x[3];
    let Fx = 40 * (tx - px) - 1.5 * vx, Fy = 40 * (ty - py) - 1.5 * vy;
    const Fm = Math.hypot(Fx, Fy); if (Fm > 25) { Fx *= 25 / Fm; Fy *= 25 / Fm; }
    return [j11 * Fx + j21 * Fy, j12 * Fx + j22 * Fy];
  }

  // ---------- step ----------
  function step(dt) {
    const n = Math.round(dt / H);
    let t0 = performance.now(), calls = 0;
    for (let i = 0; i < n; i++) {
      const z = err(x), V = quad(z);
      if (mode === 'balance' && V > LOSE) mode = 'swing';
      if (mode === 'swing' && V < CATCH[kind] && !grab) { mode = 'balance'; ctl.reset(); }
      const c0 = performance.now();
      u = clampU(mode === 'balance' ? (kind === 'nmpc' ? ctl.nmpc(x, z) : ctl[kind](z)) : swingup(x));
      const us = (performance.now() - c0) * 1000;
      // NMPC only solves every 20 ms, so time its solves; time every update for the others
      if (!(mode === 'balance' && kind === 'nmpc') || ctl.nmT === 0) solveUs = 0.85 * solveUs + 0.15 * us;
      calls++;
      const [e1, e2] = external();
      x = rk4(x, u, H, e1, e2);
    }
    return performance.now() - t0;
  }

  // ---------- draw ----------
  function drawRig() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, Hh);
    const { scale, bx, by, p1, p2 } = geom();
    ctx.fillStyle = col.rule; ctx.fillRect(bx - 70, by + 18, 140, 8);
    ctx.fillStyle = col.steel; ctx.fillRect(bx - 9, by, 18, 22);
    ctx.setLineDash([4, 6]); ctx.strokeStyle = col.rule; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.arc(bx, by, (l1 + l2) * scale, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]);
    if (grab) {
      ctx.strokeStyle = col.signal; ctx.lineWidth = 1.5; ctx.setLineDash([3, 4]);
      ctx.beginPath(); ctx.moveTo(p2[0], p2[1]); ctx.lineTo(grab[0], grab[1]); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = col.signal; ctx.beginPath(); ctx.arc(grab[0], grab[1], 5, 0, Math.PI * 2); ctx.fill();
    }
    ctx.lineCap = 'round';
    ctx.strokeStyle = col.ink; ctx.lineWidth = 14;
    ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(p1[0], p1[1]); ctx.stroke();
    ctx.strokeStyle = col.link; ctx.lineWidth = 11;
    ctx.beginPath(); ctx.moveTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]); ctx.stroke();
    ctx.fillStyle = col.signal; ctx.beginPath(); ctx.arc(bx, by, 12, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = col.plate; ctx.beginPath(); ctx.arc(bx, by, 4, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = col.plate; ctx.strokeStyle = col.ink; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(p1[0], p1[1], 6.5, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    if (Math.abs(u) > 0.02) {
      ctx.strokeStyle = col.ch1; ctx.lineWidth = 3;
      const span = Math.min(Math.abs(u) / UMAX, 1) * Math.PI * 0.9;
      ctx.beginPath(); ctx.arc(bx, by, 21, -Math.PI / 2, -Math.PI / 2 + Math.sign(u) * span, u < 0); ctx.stroke();
    }
  }
  function drawScope(c, el, series, label) {
    const [w, h] = dims.get(el);
    c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, w, h);
    c.strokeStyle = 'rgba(255,247,232,.1)'; c.lineWidth = 1;
    for (let i = 1; i < 10; i++) { const gx = w * i / 10; c.beginPath(); c.moveTo(gx, 0); c.lineTo(gx, h); c.stroke(); }
    for (let i = 1; i < 4; i++) { const gy = h * i / 4; c.beginPath(); c.moveTo(0, gy); c.lineTo(w, gy); c.stroke(); }
    series.forEach(([arr, color, sc]) => {
      c.strokeStyle = color; c.lineWidth = 1.6; c.beginPath();
      for (let i = 0; i < N; i++) {
        const v = arr[(head + i) % N], px = w * i / (N - 1), py = h / 2 - Math.max(-1, Math.min(1, v / sc)) * (h / 2 - 5);
        i ? c.lineTo(px, py) : c.moveTo(px, py);
      }
      c.stroke();
    });
  }

  // ---------- telemetry ----------
  const T = {};
  ['mode', 'q1', 'q2', 'w1', 'w2', 'u', 'e', 'solve'].forEach((k) => { T[k] = document.getElementById('t-' + k); });
  const fx = (v, d) => (Math.abs(v) < 0.5 * 10 ** -d ? 0 : v).toFixed(d);
  const deg = (r) => fx(r * 180 / Math.PI, 1) + '°';
  const MODE = { swing: 'Swinging up', balance: 'Balancing' };

  let last = performance.now(), acc = 0, visible = true, tick = 0;
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; }).observe(cv);
  function frame(now) {
    const dt = Math.min((now - last) / 1000, 1 / 20); last = now;
    if (visible && !document.hidden) {
      step(dt);
      acc += dt;
      while (acc >= 1 / 60) {
        acc -= 1 / 60;
        const z = err(x);
        hist.q1[head] = z[0] * 180 / Math.PI; hist.q2[head] = z[1] * 180 / Math.PI;
        hist.u[head] = u; hist.e[head] = energy(x) - ETOP; head = (head + 1) % N;
      }
      drawRig();
      drawScope(cA, sA, [[hist.q1, col.ch1, 180], [hist.q2, col.ch2, 180]], 'θ₁  θ₂   ±180°   10 s');
      drawScope(cB, sB, [[hist.u, col.ch1, UMAX], [hist.e, col.ch2, 1.5]], 'τ ±3 N·m   E − E_top ±1.5 J');
      if (++tick % 6 === 0) {
        const z = err(x);
        T.mode.textContent = grab ? 'Held' : MODE[mode];
        T.mode.dataset.mode = grab ? 'held' : mode;
        T.q1.textContent = deg(z[0]); T.q2.textContent = deg(z[1]);
        T.w1.textContent = fx(x[2], 2); T.w2.textContent = fx(x[3], 2);
        T.u.textContent = fx(u, 2); T.e.textContent = fx(energy(x) - ETOP, 3);
        T.solve.textContent = solveUs < 1 ? '< 1' : solveUs < 10 ? solveUs.toFixed(1) : Math.round(solveUs).toString();
      }
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
