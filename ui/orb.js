// Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
// The boot orb: a bright, evenly lit blue sphere drawn at the screen's own resolution, so it is never soft. Light stays inside
// its outline (no halo, bloom or specular spot); clouds drift and turn inside it while the sphere itself turns once a minute.
// It can also be a liquid: a smooth union with a pool below the screen edge (the drop rising from behind the Dock), with
// a small drop it lets go of (the logo's dot), and with the notch at the top (where it is drawn up into Kira's home at the end). One WebGL fragment shader does all of it; without WebGL a 2D canvas paints a
// plain sphere instead. A classic script: loadPage() inlines it into boot.html (the ORB marker).
// makeOrb(canvas) -> { gl: bool, draw(state), resize(), scale, octaves }
//   state, in CSS px with the origin top left: { main: {x, y, r}, drop: {x, y, r}, pool: y of the liquid's surface or null,
//   sink: the notch {x, w, h} or null, k1: how far main and pool melt together, k2: main and drop, k3: main and the notch,
//   stretch: main's height / width, time: s of spin, voice: 0..1, alpha }
function makeOrb(canvas) {
  const VERT = 'attribute vec2 p; void main() { gl_Position = vec4(p, 0.0, 1.0); }';
  const FRAG = `
precision highp float;
uniform vec2 uRes; uniform float uDpr;
uniform vec3 uMain, uDrop, uSink; uniform float uPool, uK1, uK2, uK3, uStretch, uTime, uVoice, uAlpha, uOct;
float smin(float a, float b, float k) {
  if (k <= 0.0) return min(a, b);
  float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
  return mix(b, a, h) - k * h * (1.0 - h);
}
float field(vec2 p) {
  vec2 q = p - uMain.xy; q.y /= uStretch;
  float d = length(q) * min(1.0, uStretch) - uMain.z;
  if (uPool > -1.0) d = smin(d, uPool - p.y, uK1);
  if (uDrop.z > 0.0) d = smin(d, length(p - uDrop.xy) - uDrop.z, uK2);
  if (uSink.y > 0.0) {   // the notch: a box hanging from the top edge with rounded lower corners (x, half width, bottom)
    float rad = min(uSink.y, uSink.z) * 0.45, top = -4.0 * uSink.z;
    vec2 c = vec2(uSink.x, (top + uSink.z) * 0.5), b = vec2(uSink.y, (uSink.z - top) * 0.5), e = abs(p - c) - (b - rad);
    d = smin(d, length(max(e, 0.0)) + min(max(e.x, e.y), 0.0) - rad, uK3);
  }
  return d;
}
float hash(vec3 p) { p = fract(p * 0.1031); p += dot(p, p.zyx + 31.32); return fract((p.x + p.y) * p.z); }
float noise(vec3 x) {
  vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
             mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}
float fbm(vec3 p) {
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++) { if (float(i) >= uOct) break; v += a * noise(p); p = p * 2.03 + vec3(1.7, 9.2, 3.1); a *= 0.5; }
  return v / (1.0 - pow(0.5, uOct));
}
vec3 turn(vec3 v, float a) { float c = cos(a), s = sin(a); return vec3(c * v.x + s * v.z, v.y, -s * v.x + c * v.z); }
float fbm2(vec3 p) { return noise(p) * 0.66 + noise(p * 2.03 + vec3(4.1, 1.3, 7.7)) * 0.34; }
vec3 spun(vec3 n) {   // the sphere turns once in 60 s about a tilted axis; the cloud layer turns again, once in 170 s
  float tilt = 0.36; vec3 q = vec3(n.x, n.y * cos(tilt) - n.z * sin(tilt), n.y * sin(tilt) + n.z * cos(tilt));
  return turn(q, uTime * 6.2832 / 60.0 + uTime * 6.2832 / 170.0);
}
float clouds(vec3 q) {
  // a warped field: swirls that slowly change shape as they drift
  float t = uTime * 0.018;
  vec3 w = vec3(fbm2(q * 1.25 + vec3(0.0, 0.0, t)), fbm2(q * 1.25 + vec3(5.2, 1.3, 2.8 - t)), fbm2(q * 1.25 + vec3(1.7, 9.2, 4.1 + t)));
  float f = fbm(q * 2.4 + (w - 0.5) * 1.25);
  return smoothstep(0.48, 0.67, f);
}
float sea(vec3 q) { return fbm2(q * 0.9 + vec3(3.0, 0.0, uTime * 0.01)); }
void main() {
  vec2 p = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y);
  float d = field(p);
  float a = clamp(0.5 - d / uDpr, 0.0, 1.0);   // one screen pixel of antialiasing: a crisp edge, nothing outside it
  if (a <= 0.0) { gl_FragColor = vec4(0.0); return; }
  // depth inside the outline -> height of a round cross-section; on the sphere this is exact
  float rDrop = uDrop.z > 0.0 ? uDrop.z : uMain.z;
  vec2 qm = p - uMain.xy;
  float near = uDrop.z > 0.0 ? clamp(0.5 + 0.5 * (length(qm) - uMain.z - (length(p - uDrop.xy) - uDrop.z)) / max(uK2, 1.0), 0.0, 1.0) : 0.0;
  float R = mix(uMain.z, rDrop, near), depth = min(-d, R);
  vec2 g = vec2(field(p + vec2(1.0, 0.0)) - d, field(p + vec2(0.0, 1.0)) - d);
  g = length(g) > 1e-5 ? normalize(g) : vec2(0.0);
  float z = sqrt(max(0.0, depth * (2.0 * R - depth))) / R;
  vec2 xy = g * (R - depth) / R;
  vec3 n = normalize(vec3(xy.x, -xy.y, z));
  vec3 L = normalize(vec3(-0.42, 0.58, 0.70));
  float lam = dot(n, L) * 0.5 + 0.5;   // half-Lambert: soft, even light, no hot spot
  vec3 q = spun(n), ql = spun(normalize(n + L * 0.06));
  // the blue: azure to cyan in slow patches, deeper on the far side (the volume), paler toward the light
  vec3 deep = vec3(0.040, 0.330, 0.860), mid = vec3(0.200, 0.590, 1.000), cyan = vec3(0.250, 0.760, 1.000), pale = vec3(0.640, 0.870, 1.000);
  vec3 col = mix(mid, cyan, smoothstep(0.35, 0.75, sea(q)) * 0.55);
  col = mix(deep, col, smoothstep(0.0, 0.62, lam));
  col = mix(col, pale, smoothstep(0.66, 1.0, lam) * 0.5);
  float rim = pow(1.0 - n.z, 3.0);
  col = mix(col, vec3(0.62, 0.84, 1.0), rim * 0.30);   // the glass edge is a little paler, inside the outline only
  float c = clouds(q), lit = clouds(ql), shadow = clouds(spun(normalize(n - L * 0.07)));
  col *= 1.0 - 0.16 * shadow;   // clouds cast a soft shadow on the blue below them: depth without shine
  // a cloud is bright where it faces the light and blue-grey underneath, so each one has a little volume of its own
  float side = clamp(0.62 + (c - lit) * 1.8, 0.0, 1.0);
  vec3 cloud = mix(vec3(0.70, 0.82, 0.97), vec3(1.0), side * smoothstep(0.0, 0.85, lam) * 0.85 + 0.15);
  col = mix(col, cloud, c * (0.95 - rim * 0.5));
  col *= 1.0 + 0.07 * uVoice;
  float o = a * uAlpha;
  gl_FragColor = vec4(min(col, vec3(1.0)) * o, o);
}`;
  const orb = { gl: false, scale: 1, octaves: 5 };
  let gl = null, prog = null, loc = {}, ctx2d = null, globe = null;
  try {
    gl = canvas.getContext('webgl', { premultipliedAlpha: true, alpha: true, antialias: false, preserveDrawingBuffer: !!window.__ORB_KEEP });
  } catch (e) { gl = null; }
  if (gl) {
    const shader = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null; };
    const v = shader(gl.VERTEX_SHADER, VERT), f = shader(gl.FRAGMENT_SHADER, FRAG);
    if (v && f) {
      prog = gl.createProgram(); gl.attachShader(prog, v); gl.attachShader(prog, f); gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) prog = null;
    }
    if (prog) {
      gl.useProgram(prog);
      const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
      const at = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(at); gl.vertexAttribPointer(at, 2, gl.FLOAT, false, 0, 0);
      for (const u of ['uRes', 'uDpr', 'uMain', 'uDrop', 'uSink', 'uPool', 'uK1', 'uK2', 'uK3', 'uStretch', 'uTime', 'uVoice', 'uAlpha', 'uOct']) loc[u] = gl.getUniformLocation(prog, u);
      gl.disable(gl.DEPTH_TEST);
      orb.gl = true;
    } else gl = null;
  }
  if (!gl) {   // no WebGL: a 2D sphere from globe.js (when inlined), else a soft gradient ball
    ctx2d = canvas.getContext('2d');
    if (typeof makeGlobe === 'function') globe = makeGlobe(160, { slide: .6, cloudSpin: .1, depth: .35, gloss: 0, cover: -1 });
  }
  let dpr = 1;
  orb.resize = () => {
    dpr = Math.min(2, window.devicePixelRatio || 1) * orb.scale;
    const w = Math.max(1, Math.round(canvas.clientWidth * dpr)), h = Math.max(1, Math.round(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  };
  orb.resize();
  orb.draw = s => {
    const W = canvas.width, H = canvas.height, m = s.main, dr = s.drop || { x: 0, y: 0, r: 0 };
    if (gl) {
      gl.viewport(0, 0, W, H);
      gl.disable(gl.SCISSOR_TEST); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
      if (!(s.alpha > 0) || !(m.r > 0)) return;
      // only the pixels that can be inside the shape are shaded
      const pad = Math.max(s.k1 || 0, s.k2 || 0) + 4, st = Math.max(1, s.stretch || 1);
      let x0 = m.x - m.r - pad, x1 = m.x + m.r + pad, y0 = m.y - m.r * st - pad, y1 = m.y + m.r * st + pad;
      if (dr.r > 0) { x0 = Math.min(x0, dr.x - dr.r - pad); x1 = Math.max(x1, dr.x + dr.r + pad); y0 = Math.min(y0, dr.y - dr.r - pad); y1 = Math.max(y1, dr.y + dr.r + pad); }
      if (s.pool != null) { x0 -= (s.k1 || 0) * 1.6; x1 += (s.k1 || 0) * 1.6; y1 = Math.max(y1, s.pool + 2); }
      if (s.sink) { const k = s.k3 || 0; x0 = Math.min(x0, s.sink.x - s.sink.w / 2 - k); x1 = Math.max(x1, s.sink.x + s.sink.w / 2 + k); y0 = 0; }
      const sx = Math.max(0, Math.floor(x0 * dpr)), sy = Math.max(0, Math.floor(H - y1 * dpr)), sw = Math.min(W, Math.ceil(x1 * dpr)) - sx, sh = Math.min(H, Math.ceil(H - y0 * dpr)) - sy;
      if (sw <= 0 || sh <= 0) return;
      gl.enable(gl.SCISSOR_TEST); gl.scissor(sx, sy, sw, sh);
      gl.uniform2f(loc.uRes, W, H); gl.uniform1f(loc.uDpr, Math.max(1, dpr));
      gl.uniform3f(loc.uMain, m.x * dpr, m.y * dpr, m.r * dpr);
      gl.uniform3f(loc.uDrop, dr.x * dpr, dr.y * dpr, Math.max(0, dr.r) * dpr);
      gl.uniform1f(loc.uPool, s.pool == null ? -2 : s.pool * dpr);
      gl.uniform1f(loc.uK1, (s.k1 || 0) * dpr); gl.uniform1f(loc.uK2, (s.k2 || 0) * dpr); gl.uniform1f(loc.uK3, (s.k3 || 0) * dpr);
      gl.uniform3f(loc.uSink, s.sink ? s.sink.x * dpr : 0, s.sink ? s.sink.w / 2 * dpr : 0, s.sink ? s.sink.h * dpr : 0);
      gl.uniform1f(loc.uStretch, s.stretch || 1); gl.uniform1f(loc.uTime, s.time || 0);
      gl.uniform1f(loc.uVoice, s.voice || 0); gl.uniform1f(loc.uAlpha, s.alpha); gl.uniform1f(loc.uOct, orb.octaves);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      return;
    }
    ctx2d.clearRect(0, 0, W, H);
    if (!(s.alpha > 0) || !(m.r > 0)) return;
    ctx2d.globalAlpha = Math.min(1, s.alpha);
    const balls = [[m.x, m.y, m.r]].concat(dr.r > 0 ? [[dr.x, dr.y, dr.r]] : []);
    for (const [x, y, r] of balls) {
      if (globe) { globe.paint(s.time || 0); ctx2d.imageSmoothingQuality = 'high'; ctx2d.drawImage(globe.sky, (x - r) * dpr, (y - r) * dpr, 2 * r * dpr, 2 * r * dpr); continue; }
      const g = ctx2d.createRadialGradient((x - r * .3) * dpr, (y - r * .35) * dpr, r * .1 * dpr, x * dpr, y * dpr, r * dpr);
      g.addColorStop(0, '#a6dbff'); g.addColorStop(.55, '#459eff'); g.addColorStop(1, '#1a6bed');
      ctx2d.fillStyle = g; ctx2d.beginPath(); ctx2d.arc(x * dpr, y * dpr, r * dpr, 0, Math.PI * 2); ctx2d.fill();
    }
    ctx2d.globalAlpha = 1;
  };
  return orb;
}
