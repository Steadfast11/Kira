// Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
// The sky globe: a glass sphere of blue with clouds that drift while it turns, painted pixel by pixel into a G×G canvas.
// Shared by ui.html (the logo) and boot.html (its fallback when WebGL is missing). A classic script: loadPage() inlines it into each page (the GLOBE marker).
// makeGlobe(G, look) -> { sky, paint(time) }: draw `sky` onto your own canvas after each paint(time); time is in seconds of spin.
// `look` (all optional, 0 = the logo's calm default): slide = how fast the clouds drift on their own, cloudSpin = a turn of the cloud layer
// against the sphere (rad/s), depth = a darker night side for a rounder 3D look, gloss = a bright specular spot, cover = more cloud when positive, less when negative.
function makeGlobe(G = 48, look = {}) {
  const { slide = 1, cloudSpin = 0, depth = 0, gloss = 0, cover = 0 } = look;
  const sky = document.createElement('canvas'); sky.width = sky.height = G;
  const skyCtx = sky.getContext('2d'), image = skyCtx.createImageData(G, G);
  const lattice = new Float32Array(16 * 16 * 16); { let a = 0x9e3779b9; for (let i = 0; i < lattice.length; i++) { a = (a + 0x6d2b79f5) | 0; let r = Math.imul(a ^ (a >>> 15), 1 | a); r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r; lattice[i] = ((r ^ (r >>> 14)) >>> 0) / 4294967296; } }
  const cell = (x, y, z) => lattice[((z & 15) << 8) | ((y & 15) << 4) | (x & 15)];
  const noise = (x, y, z) => {
    const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
    let fx = x - xi, fy = y - yi, fz = z - zi; fx *= fx * (3 - 2 * fx); fy *= fy * (3 - 2 * fy); fz *= fz * (3 - 2 * fz);
    const l = (a, b, f) => a + (b - a) * f;
    return l(l(l(cell(xi, yi, zi), cell(xi + 1, yi, zi), fx), l(cell(xi, yi + 1, zi), cell(xi + 1, yi + 1, zi), fx), fy),
             l(l(cell(xi, yi, zi + 1), cell(xi + 1, yi, zi + 1), fx), l(cell(xi, yi + 1, zi + 1), cell(xi + 1, yi + 1, zi + 1), fx), fy), fz);
  };
  const clouds = (x, y, z) => (noise(x, y, z) * .5 + noise(x * 2.1, y * 2.1, z * 2.1) * .3 + noise(x * 4.3, y * 4.3, z * 4.3) * .2);
  const smooth = (a, b, v) => { const k = Math.min(1, Math.max(0, (v - a) / (b - a))); return k * k * (3 - 2 * k); };
  const paintGlobe = time => {
    const d = image.data, spin = time * .35, cs = Math.cos(spin), sn = Math.sin(spin), tilt = .38, ct = Math.cos(tilt), st = Math.sin(tilt);
    for (let j = 0; j < G; j++) for (let i = 0; i < G; i++) {
      const x = (i + .5) / G * 2 - 1, y = 1 - (j + .5) / G * 2, r2 = x * x + y * y, o = (j * G + i) * 4;
      if (r2 >= 1.04) { d[o + 3] = 0; continue; }
      const z = Math.sqrt(Math.max(0, 1 - r2)), edge = 1 - smooth(.94, 1.02, Math.sqrt(r2));
      // the surface point, turned about the tilted axis; the clouds also slide on their own (time added to the lookup)
      const y1 = y * ct - z * st, z1 = y * st + z * ct, px = x * cs + z1 * sn, pz = -x * sn + z1 * cs;
      const ca = time * cloudSpin, cc = Math.cos(ca), cn = Math.sin(ca), qx = px * cc + pz * cn, qz = -px * cn + pz * cc;   // the cloud layer turns against the sphere
      const c = smooth(.46 - cover * .04, .66 - cover * .04, clouds(qx * 2.2 + time * .12 * slide, y1 * 2.2, qz * 2.2 - time * .09 * slide));
      const light = Math.max(0, x * -.45 + y * .55 + z * .7), shade = .62 + .5 * light;
      const rim = Math.pow(1 - z, 2.4);   // the glass edge: paler, and the cloud thins out there
      let rC = 30 + 62 * (1 - shade * .6), gC = 108 + 60 * shade * .8, bC = 208 + 30 * shade * .6;   // the blue, deeper at the shadowed side
      const white = Math.min(1, c * (.95 - rim * .25)), lit = 226 + 40 * shade * .6;
      rC += (lit - rC) * white; gC += (lit + 4 - gC) * white; bC += (255 - bC) * white;
      rC += (255 - rC) * rim * .35; gC += (255 - gC) * rim * .35; bC += (255 - bC) * rim * .3;
      if (depth) { const night = 1 - depth * (1 - Math.min(1, light * 1.4)); rC *= night; gC *= night; bC *= night; }   // the far side falls into shadow
      if (gloss) { const spec = Math.pow(light, 16) * gloss * 255; rC += spec; gC += spec; bC += spec; }
      d[o] = Math.min(255, rC); d[o + 1] = Math.min(255, gC); d[o + 2] = Math.min(255, bC); d[o + 3] = 255 * edge;
    }
    skyCtx.putImageData(image, 0, 0);
  };
  return { sky, paint: paintGlobe };
}
