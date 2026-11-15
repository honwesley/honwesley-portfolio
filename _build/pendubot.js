/* =========================================================
   Pendubot simulation
   Plant: two equal aluminum links (6061, 2 in x 1/4 in), each 11 in long.
   Angles: q1 = link 1 from upright, q2 = link 2 relative to link 1.
   The motor never switches off. A hybrid supervisor runs:
     - swing-up: energy pumping through collocated partial feedback
       linearization of the shoulder, until the state is near upright
     - balance: the selected controller (PID, LQR, NMPC or fuzzy)
   The motor torque acts on the shoulder only. The elbow is a free,
   frictionless pin: only gravity and the motion of link 1 move link 2.
   All four were tuned and tested offline on the same model: each
   recovers from hanging straight down, from link 2 spinning at 20 rad/s,
   and from random states up to 10 rad/s on link 1 and 20 rad/s on link 2.
   ========================================================= */
(() => {
  const cv = document.getElementById('pendubot');
  if (!cv) return;

  // ---------- plant ----------
  const rho = 2700, wd = 0.0508, th = 0.00635, g = 9.81;
  const b = 0.002;                      // N·m·s/rad, shoulder bearing and motor friction (the elbow is frictionless)
  const l1 = 11 * 0.0254, l2 = 11 * 0.0254;
  const m1 = rho * l1 * wd * th, m2 = rho * l2 * wd * th;
  const lc1 = l1 / 2, lc2 = l2 / 2;
  const I1 = m1 * l1 * l1 / 12, I2 = m2 * l2 * l2 / 12;
  const UMAX = 3;                       // N·m, motor torque limit
  const H = 0.001;                      // s, physics and control step (1 kHz)

  const K = [-29.31094, -25.21231, -6.46627, -3.42211];          // LQR, Q = diag(10, 40, 1, 1), R = 2
  const P = [[190.330032, 124.401891, 41.286795, 16.774564],    // Riccati solution, used for the
             [124.401891, 89.502381, 27.468373, 11.210861],      // catch region and NMPC terminal cost
             [41.286795, 27.468373, 9.117194, 3.704202],
             [16.774564, 11.210861, 3.704202, 1.512019]];
  const QD = [10, 40, 1, 1], RW = 2;
  const ETOP = 1.333991;                                         // J, energy at rest upright
  const PID = { kp1: -3.2789, kp2: -25.21231, kd1: -2.58753, kd2: -3.42211, ki1: -2.0 };
  const SW = { kp: 6, kd: 4, ke: 80, kx: 8 };                    // swing-up gains
  const CATCH = 40, LOSE = 120;                                  // hand-off thresholds on the LQR cost-to-go
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
  function f(x, u, e1) {
    const [M11, M12, M22, C1, C2, G1, G2] = terms(x);
    // Only the shoulder sees the motor torque u and the external disturbance e1.
    // The elbow equation has nothing in it but inertia, coupling and gravity.
    const r1 = u - b * x[2] - C1 - G1 + e1, r2 = -C2 - G2;
    const det = M11 * M22 - M12 * M12;
    return [x[2], x[3], (M22 * r1 - M12 * r2) / det, (-M12 * r1 + M11 * r2) / det];
  }
  function rk4(x, u, h, e1 = 0) {
    const a = f(x, u, e1);
    const k2 = f(x.map((v, i) => v + h / 2 * a[i]), u, e1);
    const k3 = f(x.map((v, i) => v + h / 2 * k2[i]), u, e1);
    const k4 = f(x.map((v, i) => v + h * k3[i]), u, e1);
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
    // The motor can only change the energy by moving link 1, so when link 1 is still and link 2
    // is spinning (elbow frictionless), drive link 1 with link 2's velocity to add or remove energy.
    v += SW.kx * (ETOP - E) * x[3];
    if (Math.abs(x[2]) < 0.05 && Math.abs(x[3]) < 0.05 && Math.abs(ETOP - E) > 0.2) v += 8;  // start pumping from rest
    const q2dd = -(M12 * v + C2 + G2) / M22;
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
  let running = true;   // false after a reset: the arm is frozen and the motor is off until started
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

  // ---------- reset and start ----------
  // A reset puts the arm in a known position with the motor off and time frozen
  // (upright would otherwise fall straight away). Start motor, or the same reset
  // button again, releases it.
  const resetBtns = document.querySelectorAll('[data-reset]');
  const startBtn = document.querySelector('[data-start]');
  const rigNote = document.getElementById('rig-status');
  let armed = null;
  function setButtons() {
    resetBtns.forEach((b) => b.setAttribute('aria-pressed', String(!running && armed === b.dataset.reset)));
    if (startBtn) startBtn.disabled = running;
    if (rigNote) rigNote.textContent = running ? '' : 'Motor off. Press Start motor, or the same reset again.';
  }
  function resetTo(where) {
    x = where === 'up' ? [0, 0, 0, 0] : [Math.PI, 0, 0, 0];
    u = 0; grab = null; ctl.reset(); solveUs = 0;
    mode = where === 'up' ? 'balance' : 'swing';
    Object.values(hist).forEach((a) => a.fill(0));
    if (where !== 'up') { hist.q1.fill(180); hist.e.fill(energy(x) - ETOP); }
    running = false; armed = where; setButtons();
  }
  function startMotor() {
    if (running) return;
    running = true; armed = null; last = performance.now(); setButtons();
  }
  resetBtns.forEach((b) => b.addEventListener('click', () => {
    if (!running && armed === b.dataset.reset) startMotor(); else resetTo(b.dataset.reset);
  }));
  if (startBtn) startBtn.addEventListener('click', startMotor);

  // ---------- drawing setup ----------
  const sA = document.getElementById('scope-a'), sB = document.getElementById('scope-b');
  const ctx = cv.getContext('2d'), cA = sA.getContext('2d'), cB = sB.getContext('2d');
  const css = (n) => getComputedStyle(cv).getPropertyValue(n).trim();  // read on the canvas: the rig sets its own palette
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

  // ---------- shove link 1 ----------
  // Only link 1 can be grabbed. A force on link 1 enters the equations as a torque on the shoulder
  // alone, so the free elbow still only feels gravity and the motion of link 1.
  const toLocal = (ev) => { const r = cv.getBoundingClientRect(); return [ev.clientX - r.left, ev.clientY - r.top]; };
  let grabS = 0;   // where on link 1 it was grabbed, metres from the shoulder
  cv.addEventListener('pointerdown', (ev) => {
    const [mx, my] = toLocal(ev), { scale, bx, by, p1 } = geom();
    const dx = p1[0] - bx, dy = p1[1] - by, len2 = dx * dx + dy * dy;
    const t = Math.max(0, Math.min(1, ((mx - bx) * dx + (my - by) * dy) / len2));
    const cx = bx + t * dx, cy = by + t * dy;
    if (!running || Math.hypot(mx - cx, my - cy) > 36) return;
    grabS = Math.max(0.25, t) * l1;
    grab = [mx, my]; cv.setPointerCapture(ev.pointerId); ev.preventDefault();
  });
  cv.addEventListener('pointermove', (ev) => { if (grab) grab = toLocal(ev); });
  const release = () => { grab = null; };
  cv.addEventListener('pointerup', release);
  cv.addEventListener('pointercancel', release);

  // Spring from the pointer to the grabbed point on link 1, mapped to a shoulder torque: tau = J^T F.
  function external() {
    if (!grab) return 0;
    const { scale, bx, by } = geom();
    const tx = (grab[0] - bx) / scale, ty = (by - grab[1]) / scale;   // pointer in metres, y up
    const px = grabS * Math.sin(x[0]), py = grabS * Math.cos(x[0]);
    const jx = grabS * Math.cos(x[0]), jy = -grabS * Math.sin(x[0]);
    let Fx = 60 * (tx - px) - 2 * jx * x[2], Fy = 60 * (ty - py) - 2 * jy * x[2];
    const Fm = Math.hypot(Fx, Fy); if (Fm > 30) { Fx *= 30 / Fm; Fy *= 30 / Fm; }
    return jx * Fx + jy * Fy;
  }

  // ---------- step ----------
  function step(dt) {
    const n = Math.round(dt / H);
    let t0 = performance.now(), calls = 0;
    for (let i = 0; i < n; i++) {
      const z = err(x), V = quad(z);
      if (mode === 'balance' && V > LOSE) mode = 'swing';
      if (mode === 'swing' && V < CATCH && !grab) { mode = 'balance'; ctl.reset(); }
      const c0 = performance.now();
      u = clampU(mode === 'balance' ? (kind === 'nmpc' ? ctl.nmpc(x, z) : ctl[kind](z)) : swingup(x));
      const us = (performance.now() - c0) * 1000;
      // NMPC only solves every 20 ms, so time its solves; time every update for the others
      if (!(mode === 'balance' && kind === 'nmpc') || ctl.nmT === 0) solveUs = 0.85 * solveUs + 0.15 * us;
      calls++;
      x = rk4(x, u, H, external());
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
      const gx = bx + grabS * scale * Math.sin(x[0]), gy = by - grabS * scale * Math.cos(x[0]);
      ctx.strokeStyle = col.signal; ctx.lineWidth = 1.5; ctx.setLineDash([3, 4]);
      ctx.beginPath(); ctx.moveTo(gx, gy); ctx.lineTo(grab[0], grab[1]); ctx.stroke(); ctx.setLineDash([]);
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
  setButtons();

  let last = performance.now(), acc = 0, visible = true, tick = 0;
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; }).observe(cv);
  function frame(now) {
    const dt = Math.min((now - last) / 1000, 1 / 20); last = now;
    if (visible && !document.hidden) {
      if (running) step(dt);
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
        T.mode.textContent = !running ? 'Motor off' : grab ? 'Held' : MODE[mode];
        T.mode.dataset.mode = !running ? 'off' : grab ? 'held' : mode;
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
