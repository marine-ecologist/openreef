import { C as Xn, G as jn, Q as $n, b as Qn } from "./QuantizedMeshLoaderBase-DIIZywLI.js";
import { Vector3 as C, MathUtils as w, PlaneGeometry as Zs, Mesh as _e, MeshBasicMaterial as xe, Sphere as Te, Texture as Kn, SRGBColorSpace as ct, TextureUtils as Zn, Matrix4 as Y, BufferGeometry as Fe, BufferAttribute as G, Triangle as Os, Vector4 as be, CanvasTexture as ht, Color as Vs, Box3 as Ft, DefaultLoadingManager as Jn, MeshStandardMaterial as ln, DataTexture as zt, RGFormat as cn, UnsignedByteType as hn, LinearMipMapLinearFilter as er, LinearFilter as un, Vector2 as k, Matrix3 as tr, Matrix2 as sr, WebGLRenderer as ir, WebGLRenderTarget as Js, ShaderMaterial as nr, OneFactor as rr, ZeroFactor as or, CustomBlending as ar, Box2 as lr, FileLoader as cr, Quaternion as dn, BatchedMesh as hr, Source as ur, REVISION as dr, WebGLArrayRenderTarget as ei, Raycaster as fn, DoubleSide as Pt, Ray as fr, LineSegments as ks, LineBasicMaterial as pr, EdgesGeometry as mr, BoxGeometry as pn, Group as Le, Box3Helper as gr, SphereGeometry as yr, PointsMaterial as mn, EventDispatcher as Ns, Frustum as xr, Points as As, GreaterDepth as _r } from "three";
import { W as Tr, g as br, a as gn, c as vr, O as wr, b as Fs } from "./MemoryUtils-ZzXvtRjr.js";
import { GLTFLoader as Sr } from "three/addons/loaders/GLTFLoader.js";
import { FullScreenQuad as yn } from "three/addons/postprocessing/Pass.js";
import { c as zs, D as Mr, u as Cr, b as Ar, e as xn } from "./TilesRendererBase-BGxy2Uih.js";
import { c as Lr, L as _n } from "./LoaderBase-CU5shB7w.js";
const jt = /* @__PURE__ */ new C(), ft = /* @__PURE__ */ new C();
function Er(h, e, t) {
  const i = t + 1e-5;
  let n = e + 1e-5;
  Math.abs(n) > Math.PI / 2 && (n = n - 1e-5), h.getCartographicToPosition(e, t, 0, jt), h.getCartographicToPosition(n, t, 0, ft);
  const r = jt.distanceTo(ft) / 1e-5;
  return h.getCartographicToPosition(e, i, 0, ft), [jt.distanceTo(ft) / 1e-5, r];
}
class ee {
  get isMercator() {
    return this.scheme === "EPSG:3857";
  }
  get isCartographic() {
    return this.scheme !== "none";
  }
  constructor(e = "EPSG:4326") {
    this.scheme = e, this.tileCountX = 1, this.tileCountY = 1, this.setScheme(e);
  }
  setScheme(e) {
    switch (this.scheme = e, e) {
      // equirect
      case "CRS:84":
      case "EPSG:4326":
        this.tileCountX = 2, this.tileCountY = 1;
        break;
      // mercator
      case "EPSG:3857":
        this.tileCountX = 1, this.tileCountY = 1;
        break;
      case "none":
        this.tileCountX = 1, this.tileCountY = 1;
        break;
      default:
        throw new Error(`ProjectionScheme: Unknown projection scheme "${e}"`);
    }
  }
  convertNormalizedToLatitude(e) {
    if (this.scheme === "none")
      return e;
    if (this.isMercator) {
      const t = w.mapLinear(e, 0, 1, -1, 1);
      return 2 * Math.atan(Math.exp(t * Math.PI)) - Math.PI / 2;
    } else
      return w.mapLinear(e, 0, 1, -Math.PI / 2, Math.PI / 2);
  }
  convertNormalizedToLongitude(e) {
    return this.scheme === "none" ? e : w.mapLinear(e, 0, 1, -Math.PI, Math.PI);
  }
  convertLatitudeToNormalized(e) {
    if (this.scheme === "none")
      return e;
    if (this.isMercator) {
      const t = Math.log(Math.tan(Math.PI / 4 + e / 2));
      return 1 / 2 + 1 * t / (2 * Math.PI);
    } else
      return w.mapLinear(e, -Math.PI / 2, Math.PI / 2, 0, 1);
  }
  convertLongitudeToNormalized(e) {
    return this.scheme === "none" ? e : (e + Math.PI) / (2 * Math.PI);
  }
  getLongitudeDerivativeAtNormalized(e) {
    return this.scheme === "none" ? 1 : 2 * Math.PI;
  }
  getLatitudeDerivativeAtNormalized(e) {
    if (this.scheme === "none")
      return 1;
    {
      let s = e - 1e-5;
      return s < 0 && (s = e + 1e-5), this.isMercator ? Math.abs(this.convertNormalizedToLatitude(e) - this.convertNormalizedToLatitude(s)) / 1e-5 : Math.PI;
    }
  }
  getBounds() {
    return this.scheme === "none" ? [0, 0, 1, 1] : [
      this.convertNormalizedToLongitude(0),
      this.convertNormalizedToLatitude(0),
      this.convertNormalizedToLongitude(1),
      this.convertNormalizedToLatitude(1)
    ];
  }
  toNormalizedPoint(e, t) {
    const s = [e, t];
    return s[0] = this.convertLongitudeToNormalized(s[0]), s[1] = this.convertLatitudeToNormalized(s[1]), s;
  }
  toNormalizedRange(e) {
    return [
      ...this.toNormalizedPoint(e[0], e[1]),
      ...this.toNormalizedPoint(e[2], e[3])
    ];
  }
  toCartographicPoint(e, t) {
    const s = [e, t];
    return s[0] = this.convertNormalizedToLongitude(s[0]), s[1] = this.convertNormalizedToLatitude(s[1]), s;
  }
  toCartographicRange(e) {
    return [
      ...this.toCartographicPoint(e[0], e[1]),
      ...this.toCartographicPoint(e[2], e[3])
    ];
  }
  clampToBounds(e, t = !1) {
    const s = [...e];
    let i;
    t ? i = [0, 0, 1, 1] : i = this.getBounds();
    const [n, r, o, a] = i;
    return s[0] = w.clamp(s[0], n, o), s[2] = w.clamp(s[2], n, o), s[1] = w.clamp(s[1], r, a), s[3] = w.clamp(s[3], r, a), s;
  }
}
function ti(h, e) {
  const [t, s, i, n] = h, [r, o, a, l] = e;
  return !(t >= a || i <= r || s >= l || n <= o);
}
class Gt {
  get levelCount() {
    return this._levels.length;
  }
  get maxLevel() {
    return this.levelCount - 1;
  }
  get minLevel() {
    const e = this._levels;
    for (let t = 0; t < e.length; t++)
      if (e[t] !== null)
        return t;
    return -1;
  }
  // prioritize user-set bounds over projection bounds if present
  get contentBounds() {
    return this._contentBounds ?? this.projection.getBounds();
  }
  get aspectRatio() {
    const { pixelWidth: e, pixelHeight: t } = this.getLevel(this.maxLevel);
    return e / t;
  }
  constructor() {
    this.flipY = !1, this.pixelOverlap = 0, this._contentBounds = null, this.projection = new ee("none"), this._levels = [];
  }
  // build the zoom levels
  setLevel(e, t = {}) {
    const s = this._levels;
    for (; s.length < e; )
      s.push(null);
    const {
      tileSplitX: i = 2,
      tileSplitY: n = 2
    } = t, {
      tilePixelWidth: r = 256,
      tilePixelHeight: o = 256,
      tileCountX: a = i ** e,
      tileCountY: l = n ** e,
      tileBounds: c = null
    } = t, {
      pixelWidth: u = r * a,
      pixelHeight: d = o * l
    } = t;
    s[e] = {
      // The pixel resolution of each tile.
      tilePixelWidth: r,
      tilePixelHeight: o,
      // The total pixel resolution of the final image at this level. These numbers
      // may not be a round multiple of the tile width.
      pixelWidth: u,
      pixelHeight: d,
      // Or the total number of tiles that can be loaded at this level.
      tileCountX: a,
      tileCountY: l,
      // The number of tiles that the tiles at this layer split in to
      tileSplitX: i,
      tileSplitY: n,
      // The bounds covered by the extent of the tiles at this loaded. The actual content covered by the overall tileset
      // may be a subset of this range (eg there may be unused space).
      tileBounds: c
    };
  }
  generateLevels(e, t, s, i = {}) {
    const {
      minLevel: n = 0,
      tilePixelWidth: r = 256,
      tilePixelHeight: o = 256
    } = i, a = e - 1, {
      pixelWidth: l = r * t * 2 ** a,
      pixelHeight: c = o * s * 2 ** a
    } = i;
    for (let u = n; u < e; u++) {
      const d = e - u - 1, p = Math.ceil(l * 2 ** -d), m = Math.ceil(c * 2 ** -d), f = Math.ceil(p / r), g = Math.ceil(m / o);
      this.setLevel(u, {
        tilePixelWidth: r,
        tilePixelHeight: o,
        pixelWidth: p,
        pixelHeight: m,
        tileCountX: f,
        tileCountY: g
      });
    }
  }
  getLevel(e) {
    return this._levels[e];
  }
  // bounds representing the contentful region of the image
  setContentBounds(e, t, s, i) {
    this._contentBounds = [e, t, s, i];
  }
  setProjection(e) {
    this.projection = e;
  }
  // query functions
  getTileAtPoint(e, t, s, i = !1) {
    const { flipY: n } = this, { tileCountY: r, tileBounds: o, pixelHeight: a, pixelWidth: l, tilePixelHeight: c, tilePixelWidth: u } = this.getLevel(s), d = u / l, p = c / a;
    if (i || ([e, t] = this.toNormalizedPoint(e, t)), o) {
      const g = this.toNormalizedRange(o);
      e = w.mapLinear(e, g[0], g[2], 0, 1), t = w.mapLinear(t, g[1], g[3], 0, 1);
    }
    const m = Math.floor(e / d);
    let f = Math.floor(t / p);
    return n && (f = r - 1 - f), [m, f];
  }
  getTilesInRange(e, t, s, i, n, r = !1) {
    const o = [e, t, s, i], a = this.getContentBounds(r);
    let l = this.getLevel(n).tileBounds;
    if (!ti(o, a))
      return [0, 0, -1, -1];
    if (l && (r && (l = this.toNormalizedRange(l)), !ti(o, a)))
      return [0, 0, -1, -1];
    const [c, u, d, p] = this.clampToContentBounds(o, r), m = this.getTileAtPoint(c, u, n, r), f = this.getTileAtPoint(d, p, n, r);
    this.flipY && ([m[1], f[1]] = [f[1], m[1]]);
    const { tileCountX: g, tileCountY: y } = this.getLevel(n), [x, _] = m, [b, T] = f;
    return b < 0 || T < 0 || x >= g || _ >= y ? [0, 0, -1, -1] : [
      w.clamp(x, 0, g - 1),
      w.clamp(_, 0, y - 1),
      w.clamp(b, 0, g - 1),
      w.clamp(T, 0, y - 1)
    ];
  }
  getTileExists(e, t, s) {
    const [i, n, r, o] = this.contentBounds, [a, l, c, u] = this.getTileBounds(e, t, s);
    return !(a >= c || l >= u) && a <= r && l <= o && c >= i && u >= n;
  }
  getContentBounds(e = !1) {
    const { projection: t } = this, s = [...this.contentBounds];
    return e && (s[0] = t.convertLongitudeToNormalized(s[0]), s[1] = t.convertLatitudeToNormalized(s[1]), s[2] = t.convertLongitudeToNormalized(s[2]), s[3] = t.convertLatitudeToNormalized(s[3])), s;
  }
  // returns the UV range associated with the content in the given tile
  getTileContentUVBounds(e, t, s) {
    const [i, n, r, o] = this.getTileBounds(e, t, s, !0, !0), [a, l, c, u] = this.getTileBounds(e, t, s, !0, !1);
    return [
      w.mapLinear(i, a, c, 0, 1),
      w.mapLinear(n, l, u, 0, 1),
      w.mapLinear(r, a, c, 0, 1),
      w.mapLinear(o, l, u, 0, 1)
    ];
  }
  getTileBounds(e, t, s, i = !1, n = !0) {
    const { flipY: r, pixelOverlap: o, projection: a } = this, { tilePixelWidth: l, tilePixelHeight: c, pixelWidth: u, pixelHeight: d, tileBounds: p } = this.getLevel(s);
    let m = l * e - o, f = c * t - o, g = m + l + o * 2, y = f + c + o * 2;
    if (m = Math.max(m, 0), f = Math.max(f, 0), g = Math.min(g, u), y = Math.min(y, d), m = m / u, g = g / u, f = f / d, y = y / d, r) {
      const _ = (y - f) / 2, T = 1 - (f + y) / 2;
      f = T - _, y = T + _;
    }
    let x = [m, f, g, y];
    if (p) {
      const _ = this.toNormalizedRange(p);
      x[0] = w.mapLinear(x[0], 0, 1, _[0], _[2]), x[2] = w.mapLinear(x[2], 0, 1, _[0], _[2]), x[1] = w.mapLinear(x[1], 0, 1, _[1], _[3]), x[3] = w.mapLinear(x[3], 0, 1, _[1], _[3]);
    }
    return n && (x = this.clampToBounds(x, !0)), i || (x[0] = a.convertNormalizedToLongitude(x[0]), x[1] = a.convertNormalizedToLatitude(x[1]), x[2] = a.convertNormalizedToLongitude(x[2]), x[3] = a.convertNormalizedToLatitude(x[3])), x;
  }
  toNormalizedPoint(e, t) {
    return this.projection.toNormalizedPoint(e, t);
  }
  toNormalizedRange(e) {
    return this.projection.toNormalizedRange(e);
  }
  toCartographicPoint(e, t) {
    return this.projection.toCartographicPoint(e, t);
  }
  toCartographicRange(e) {
    return this.projection.toCartographicRange(e);
  }
  clampToContentBounds(e, t = !1) {
    const s = [...e], [i, n, r, o] = this.getContentBounds(t);
    return s[0] = w.clamp(s[0], i, r), s[1] = w.clamp(s[1], n, o), s[2] = w.clamp(s[2], i, r), s[3] = w.clamp(s[3], n, o), s;
  }
  clampToBounds(e, t = !1) {
    return this.projection.clampToBounds(e, t);
  }
}
const Pe = Symbol("TILE_X"), Re = Symbol("TILE_Y"), ve = Symbol("TILE_LEVEL"), Ir = 30, Pr = 15, si = 20, pt = Symbol("OVERLAY_RANGE"), mt = Symbol("OVERLAY_LEVEL"), We = /* @__PURE__ */ new C(), He = /* @__PURE__ */ new C(), $t = /* @__PURE__ */ new Te();
class Rr {
  constructor(e = {}) {
    const {
      overlay: t = null,
      shape: s = "ellipsoid",
      endCaps: i = !0,
      center: n = !0,
      useRecommendedSettings: r = !0,
      applyOverlayTexture: o = !1
    } = e;
    this.priority = -10, this.tiles = null, this.overlay = t, this.shape = s, this.endCaps = i, this.center = n, this.useRecommendedSettings = r, this.applyOverlayTexture = o, this._tiling = null;
  }
  // Plugin functions
  init(e) {
    this.useRecommendedSettings && (e.errorTarget = 1), this.tiles = e;
  }
  async loadRootTileset() {
    const { overlay: e } = this;
    return e ? (await e.init(), this._tiling = e.tiling || this._createDefaultTiling()) : this._tiling = this._createDefaultTiling(), this.getTileset();
  }
  async parseToMesh(e, t, s, i, n) {
    if (s !== "generated_surface")
      return null;
    let r;
    this._useEllipsoid() ? r = this._createEllipsoidMesh(t) : r = this._createPlanarMesh(t);
    const { overlay: o, applyOverlayTexture: a } = this;
    if (o && a) {
      const l = t[Pe], c = t[Re], u = t[ve], d = this._tiling.getTileBounds(l, c, u, !0, !1);
      if (o.hasContent(d, u)) {
        try {
          await o.lockTexture(d, u);
        } catch (m) {
          if (m.name !== "AbortError")
            throw m;
          return null;
        }
        const p = o.getTexture(d, u);
        if (t[pt] = d, t[mt] = u, n.aborted)
          return o.releaseTexture(d, u), delete t[pt], delete t[mt], null;
        r.material.map = p, r.material.needsUpdate = !0;
      }
    }
    return r;
  }
  preprocessNode(e) {
    const s = this._tiling.maxLevel;
    e[ve] < s && e.parent !== null && this.expandChildren(e);
  }
  disposeTile(e) {
    const t = e[pt];
    this.overlay && t && (this.overlay.releaseTexture(t, e[mt]), delete e[pt], delete e[mt]);
  }
  dispose() {
    this.tiles.forEachLoadedModel((e, t) => {
      this.disposeTile(t);
    });
  }
  /**
   * Returns the cartographic coordinates for a given world-space position. "lat" and "lon" are assigned
   * to the target object.
   * @param {Vector3} position - World-space position. For ellipsoid surfaces this is a
   * 3D point on the surface; for planar surfaces it is a 2D point in the plane.
   * @param {{ lat: number, lon: number }} [target={}] - Optional target object to write results into.
   * @returns {{ lat: number, lon: number }} The cartographic coordinates in radians.
   * @throws {Error} If the tiling projection is not cartographic.
   */
  getCartographicFromPosition(e, t = {}) {
    const { _tiling: s } = this, { projection: i } = s;
    if (!i.isCartographic)
      throw new Error("GeneratedSurfacePlugin: getCartographicFromPosition requires a cartographic projection.");
    if (this._useEllipsoid())
      return this.tiles.ellipsoid.getPositionToCartographic(e, t);
    const { center: n } = this, r = e.x / s.aspectRatio + (n ? 0.5 : 0), o = e.y + (n ? 0.5 : 0);
    return t.lat = i.convertNormalizedToLatitude(o), t.lon = i.convertNormalizedToLongitude(r), t;
  }
  /**
   * Returns the world-space position for a given cartographic coordinate.
   * @param {number} lat - Latitude in radians.
   * @param {number} lon - Longitude in radians.
   * @param {Vector3} [target=new Vector3()] - Optional target Vector3 to write results into.
   * @returns {Vector3} The world-space position. For planar surfaces z is set to 0.
   * @throws {Error} If the tiling projection is not cartographic.
   */
  getPositionFromCartographic(e, t, s = new C()) {
    const { _tiling: i } = this, { projection: n } = i;
    if (!n.isCartographic)
      throw new Error("GeneratedSurfacePlugin: getPositionFromCartographic requires a cartographic projection.");
    if (this._useEllipsoid())
      return this.tiles.ellipsoid.getCartographicToPosition(e, t, 0, s);
    const { center: r } = this, o = n.convertLongitudeToNormalized(t), a = n.convertLatitudeToNormalized(e);
    return s.x = (o - (r ? 0.5 : 0)) * i.aspectRatio, s.y = a - (r ? 0.5 : 0), s.z = 0, s;
  }
  // whether the plugin is loading as an ellipsoid or not
  _useEllipsoid() {
    return this._tiling.projection.isCartographic && this.shape === "ellipsoid";
  }
  _createPlanarMesh(e) {
    const t = e[Pe], s = e[Re], i = e[ve], n = e.boundingVolume.box;
    let r = 1, o = 1, a = 0, l = 0, c = 0;
    n && ([a, l, c] = n, r = n[3], o = n[7]);
    const u = new Zs(2 * r, 2 * o), d = new _e(u, new xe());
    d.position.set(a, l, c);
    const p = this._tiling.getTileContentUVBounds(t, s, i), { uv: m } = u.attributes;
    for (let f = 0; f < m.count; f++)
      m.setXY(
        f,
        w.mapLinear(m.getX(f), 0, 1, p[0], p[2]),
        w.mapLinear(m.getY(f), 0, 1, p[1], p[3])
      );
    return d;
  }
  _createEllipsoidMesh(e) {
    const { tiles: t, endCaps: s, _tiling: i } = this, { projection: n } = i, r = e[ve], o = e[Pe], a = e[Re], [l, c, u, d] = e.boundingVolume.region, p = Math.max(Pr, Math.ceil((d - c) * w.RAD2DEG * 0.25)), m = Math.max(Ir, Math.ceil((u - l) * w.RAD2DEG * 0.25)), f = m + 3, g = p + 3, y = new Zs(1, 1, m + 2, p + 2), [x, _, b, T] = i.getTileBounds(o, a, r, !0, !0), v = i.getTileContentUVBounds(o, a, r), { position: S, normal: M, uv: P } = y.attributes, E = S.count;
    e.engineData.boundingVolume.getSphere($t);
    for (let B = 0; B < E; B++) {
      const W = B % f, q = Math.floor(B / f), K = W === 0 || W === f - 1 || q === 0 || q === g - 1, A = Math.max(1, Math.min(f - 2, W)), L = Math.max(1, Math.min(g - 2, q)), D = (A - 1) / m, R = 1 - (L - 1) / p, I = n.convertNormalizedToLongitude(w.mapLinear(D, 0, 1, x, b));
      let O = n.convertNormalizedToLatitude(w.mapLinear(R, 0, 1, _, T));
      if (n.isMercator && s && (T === 1 && R === 1 && (O = Math.PI / 2), _ === 0 && R === 0 && (O = -Math.PI / 2)), n.isMercator && R !== 0 && R !== 1) {
        const N = n.convertNormalizedToLatitude(1), V = 1 / p, $ = w.mapLinear(R - V, 0, 1, c, d), ae = w.mapLinear(R + V, 0, 1, c, d);
        O > N && $ < N && (O = N), O < -N && ae > -N && (O = -N);
      }
      t.ellipsoid.getCartographicToPosition(O, I, 0, We).sub($t.center), t.ellipsoid.getCartographicToNormal(O, I, He), K && We.addScaledVector(He, -e.geometricError);
      const J = w.mapLinear(n.convertLongitudeToNormalized(I), x, b, v[0], v[2]), H = w.mapLinear(n.convertLatitudeToNormalized(O), _, T, v[1], v[3]);
      S.setXYZ(B, We.x, We.y, We.z), M.setXYZ(B, He.x, He.y, He.z), P.setXY(B, J, H);
    }
    const F = new _e(y, new xe());
    return F.position.copy($t.center), F;
  }
  getTileset() {
    const { tiles: e, _tiling: t } = this, s = t.minLevel, { tileCountX: i, tileCountY: n } = t.getLevel(s), r = [];
    for (let a = 0; a < i; a++)
      for (let l = 0; l < n; l++) {
        const c = this.createChild(a, l, s);
        c !== null && r.push(c);
      }
    const o = {
      asset: { version: "1.1" },
      geometricError: 1 / 0,
      root: {
        refine: "REPLACE",
        geometricError: 1 / 0,
        boundingVolume: this.createBoundingVolume(0, 0, -1),
        children: r,
        [ve]: -1,
        [Pe]: 0,
        [Re]: 0
      }
    };
    return e.preprocessTileset(o, ""), o;
  }
  getUrl() {
    return "tile.generated_surface";
  }
  fetchData(e) {
    if (/generated_surface/.test(e))
      return new ArrayBuffer();
  }
  createBoundingVolume(e, t, s, i = 0) {
    const { _tiling: n } = this, r = s === -1;
    if (this._useEllipsoid()) {
      const { endCaps: o } = this;
      let a, l;
      return r ? (a = n.getContentBounds(!0), l = n.getContentBounds()) : (a = n.getTileBounds(e, t, s, !0, !0), l = n.getTileBounds(e, t, s, !1, !0)), o && (a[3] === 1 && (l[3] = Math.PI / 2), a[1] === 0 && (l[1] = -Math.PI / 2)), { region: [...l, -i, 1] };
    } else {
      const { center: o } = this;
      let a;
      r ? a = n.getContentBounds(!0) : a = n.getTileBounds(e, t, s, !0);
      const [l, c, u, d] = a;
      let p = (u - l) / 2, m = (d - c) / 2, f = l + p, g = c + m;
      return o && (f -= 0.5, g -= 0.5), f *= n.aspectRatio, p *= n.aspectRatio, {
        box: [
          // center
          f,
          g,
          0,
          // x, y, z half extents
          p,
          0,
          0,
          0,
          m,
          0,
          0,
          0,
          0
        ]
      };
    }
  }
  createChild(e, t, s) {
    const { _tiling: i } = this, { projection: n } = i;
    if (!i.getTileExists(e, t, s))
      return null;
    let r;
    const o = this._useEllipsoid();
    if (o) {
      const [a, l, c, u] = i.getTileBounds(e, t, s, !0), { tilePixelWidth: d, tilePixelHeight: p } = i.getLevel(s), m = (c - a) / d, f = (u - l) / p, [
        /* west */
        ,
        g,
        y,
        x
      ] = i.getTileBounds(e, t, s), _ = g > 0 != x > 0 ? 0 : Math.min(Math.abs(g), Math.abs(x)), b = n.convertLatitudeToNormalized(_), T = n.getLongitudeDerivativeAtNormalized(a), v = n.getLatitudeDerivativeAtNormalized(b), [S, M] = Er(this.tiles.ellipsoid, _, y);
      r = Math.max(m * T * S, f * v * M);
    } else {
      const { pixelWidth: a, pixelHeight: l } = i.getLevel(s);
      r = Math.max(i.aspectRatio / a, 1 / l);
    }
    return {
      refine: "REPLACE",
      geometricError: r,
      boundingVolume: this.createBoundingVolume(e, t, s, o ? r : 0),
      content: {
        uri: this.getUrl(e, t, s)
      },
      children: [],
      // save the tile params so we can expand later
      [Pe]: e,
      [Re]: t,
      [ve]: s
    };
  }
  expandChildren(e) {
    const t = e[ve], s = e[Pe], i = e[Re], { tileSplitX: n, tileSplitY: r } = this._tiling.getLevel(t);
    for (let o = 0; o < n; o++)
      for (let a = 0; a < r; a++) {
        const l = this.createChild(n * s + o, r * i + a, t + 1);
        l && e.children.push(l);
      }
  }
  _createDefaultTiling() {
    const e = new Gt();
    if (this.shape === "ellipsoid") {
      const t = new ee("EPSG:3857");
      e.setProjection(t), e.generateLevels(si, t.tileCountX, t.tileCountY);
    } else {
      const t = new ee("none");
      e.setProjection(t), e.generateLevels(si, 1, 1);
    }
    return e;
  }
}
class ii extends DOMException {
  constructor() {
    super("DataCache: Item removed", "AbortError");
  }
}
function Ye(...h) {
  return h.join("_");
}
class Gs {
  constructor() {
    this.cache = {}, this.count = 0, this.cachedBytes = 0, this.active = 0;
  }
  // overridable
  fetchItem(e, t) {
  }
  // called with null if the fetch failed
  disposeItem(e, t) {
  }
  getMemoryUsage(e) {
    return 0;
  }
  // sets the data in the cache explicitly without need to load
  setData(...e) {
    const { cache: t } = this, s = e.pop(), i = Ye(...e);
    if (i in t)
      throw new Error(`DataCache: "${i}" is already present.`);
    return this.cache[i] = {
      abortController: new AbortController(),
      result: s,
      count: 1,
      bytes: this.getMemoryUsage(s)
    }, this.count++, this.cachedBytes += this.cache[i].bytes, s;
  }
  // fetches the associated data if it doesn't exist and increments the lock counter
  lock(...e) {
    const { cache: t } = this, s = Ye(...e);
    if (s in t)
      t[s].count++;
    else {
      const i = new AbortController(), n = {
        abortController: i,
        result: null,
        count: 1,
        bytes: 0,
        args: e
      };
      this.active++, n.result = this.fetchItem(e, i.signal), n.result instanceof Promise ? n.result = n.result.then((r) => (i.signal.throwIfAborted(), n.result = r, n.bytes = this.getMemoryUsage(r), this.cachedBytes += n.bytes, r)).finally(() => {
        this.active--;
      }) : (this.active--, n.bytes = this.getMemoryUsage(n.result), this.cachedBytes += n.bytes), this.cache[s] = n, this.count++;
    }
    return t[s].result;
  }
  // decrements the lock counter for the item and deletes the item if it has reached zero
  release(...e) {
    const t = Ye(...e);
    this.releaseViaFullKey(t);
  }
  // get the loaded item
  get(...e) {
    const { cache: t } = this, s = Ye(...e);
    return s in t && t[s].count > 0 ? t[s].result : null;
  }
  has(...e) {
    const { cache: t } = this;
    return Ye(...e) in t;
  }
  forEachItem(e) {
    const { cache: t } = this;
    for (const s in t) {
      const i = t[s];
      i.result instanceof Promise || e(i.result, i.args);
    }
  }
  // dispose all items
  dispose() {
    const { cache: e } = this;
    for (const t in e) {
      const { abortController: s } = e[t];
      s.abort(new ii()), this.releaseViaFullKey(t, !0);
    }
    this.cache = {};
  }
  // releases an item with an optional force flag
  releaseViaFullKey(e, t = !1) {
    const { cache: s } = this;
    if (e in s && s[e].count > 0) {
      const i = s[e];
      if (i.count--, i.count === 0 || t) {
        const n = () => {
          if (s[e] !== i)
            return;
          const { result: r, abortController: o } = i;
          o.abort(new ii()), r instanceof Promise ? r.then((a) => {
            this.disposeItem(a, i.args);
          }).catch(() => {
            this.disposeItem(null, i.args);
          }).finally(() => {
            this.count--, this.cachedBytes -= i.bytes;
          }) : (this.disposeItem(r, i.args), this.count--, this.cachedBytes -= i.bytes), delete s[e];
        };
        t ? n() : queueMicrotask(() => {
          i.count === 0 && n();
        });
      }
      return !0;
    }
    throw new Error("DataCache: Attempting to release key that does not exist");
  }
}
class Ge extends Gs {
  constructor(e = {}) {
    super();
    const {
      fetchOptions: t = {}
    } = e;
    this.tiling = new Gt(), this.fetchOptions = t, this.fetchData = (...s) => fetch(...s);
  }
  // async function for initializing the tiled image set
  init() {
  }
  // helper for processing the buffer into a texture
  async processBufferToTexture(e) {
    const t = new Blob([e]), s = await createImageBitmap(t, {
      premultiplyAlpha: "none",
      colorSpaceConversion: "none",
      imageOrientation: "flipY"
    }), i = new Kn(s);
    return i.generateMipmaps = !1, i.colorSpace = ct, i.needsUpdate = !0, i;
  }
  getMemoryUsage(e) {
    const { format: t, type: s, image: i, generateMipmaps: n } = e, { width: r, height: o } = i, a = Zn.getByteLength(r, o, t, s);
    return n ? a * 4 / 3 : a;
  }
  // fetch the item with the given key fields
  fetchItem(e, t) {
    const s = {
      ...this.fetchOptions,
      signal: t
    }, i = this.getUrl(...e);
    return this.fetchData(i, s).then((n) => n.arrayBuffer()).then((n) => this.processBufferToTexture(n));
  }
  // dispose of the item that was fetched
  disposeItem(e) {
    e && (e.dispose(), e.image instanceof ImageBitmap && e.image.close());
  }
  getUrl(...e) {
  }
}
class Wt extends Ge {
  constructor(e = {}) {
    const {
      levels: t = 20,
      tileDimension: s = 256,
      projection: i = "EPSG:3857",
      url: n = null,
      ...r
    } = e;
    super(r), this.tileDimension = s, this.levels = t, this.projection = i, this.url = n;
  }
  getUrl(e, t, s) {
    return this.url.replace(/{\s*z\s*}/gi, s).replace(/{\s*x\s*}/gi, e).replace(/{\s*(y|reverseY|-\s*y)\s*}/gi, t);
  }
  init() {
    const { tiling: e, tileDimension: t, levels: s, url: i, projection: n } = this;
    return e.flipY = !/{\s*reverseY|-\s*y\s*}/g.test(i), e.setProjection(new ee(n)), e.setContentBounds(...e.projection.getBounds()), Array.isArray(s) ? s.forEach((r, o) => {
      r !== null && e.setLevel(o, {
        tilePixelWidth: t,
        tilePixelHeight: t,
        ...r
      });
    }) : e.generateLevels(s, e.projection.tileCountX, e.projection.tileCountY, {
      tilePixelWidth: t,
      tilePixelHeight: t
    }), this.url = i, Promise.resolve();
  }
}
class Dr extends Wt {
  constructor(e = {}) {
    const {
      subdomains: t = ["t0"],
      ...s
    } = e;
    super(s), this.subdomains = t, this.subDomainIndex = 0;
  }
  getUrl(e, t, s) {
    return this.url.replace(/{\s*subdomain\s*}/gi, this._getSubdomain()).replace(/{\s*quadkey\s*}/gi, this._tileToQuadKey(e, t, s));
  }
  _tileToQuadKey(e, t, s) {
    let i = "";
    for (let n = s; n > 0; n--) {
      let r = 0;
      const o = 1 << n - 1;
      (e & o) !== 0 && (r += 1), (t & o) !== 0 && (r += 2), i += r.toString();
    }
    return i;
  }
  _getSubdomain() {
    return this.subDomainIndex = (this.subDomainIndex + 1) % this.subdomains.length, this.subdomains[this.subDomainIndex];
  }
}
class Tn extends Ge {
  constructor(e = {}) {
    const {
      url: t = null,
      ...s
    } = e;
    super(s), this.tileSets = null, this.extension = null, this.url = t;
  }
  getUrl(e, t, s) {
    const { url: i, extension: n, tileSets: r, tiling: o } = this;
    return new URL(`${parseInt(r[s - o.minLevel].href)}/${e}/${t}.${n}`, i).toString();
  }
  init() {
    const { url: e } = this;
    return this.fetchData(new URL("tilemapresource.xml", e), this.fetchOptions).then((t) => t.text()).then((t) => {
      const { tiling: s } = this, i = new DOMParser().parseFromString(t, "text/xml"), n = i.querySelector("BoundingBox"), r = i.querySelector("TileFormat"), a = [...i.querySelector("TileSets").querySelectorAll("TileSet")].map((y) => ({
        href: parseInt(y.getAttribute("href")),
        unitsPerPixel: parseFloat(y.getAttribute("units-per-pixel")),
        order: parseInt(y.getAttribute("order"))
      })).sort((y, x) => y.order - x.order), l = parseFloat(n.getAttribute("minx")) * w.DEG2RAD, c = parseFloat(n.getAttribute("maxx")) * w.DEG2RAD, u = parseFloat(n.getAttribute("miny")) * w.DEG2RAD, d = parseFloat(n.getAttribute("maxy")) * w.DEG2RAD, p = parseInt(r.getAttribute("width")), m = parseInt(r.getAttribute("height")), f = r.getAttribute("extension"), g = i.querySelector("SRS").textContent;
      this.extension = f, this.url = e, this.tileSets = a, s.setProjection(new ee(g)), s.setContentBounds(l, u, c, d), a.forEach(({ order: y }) => {
        s.setLevel(y, {
          tileCountX: s.projection.tileCountX * 2 ** y,
          tilePixelWidth: p,
          tilePixelHeight: m
        });
      });
    });
  }
}
function le(h, e, t, s) {
  let [i, n, r, o] = h;
  n += 1e-8, i += 1e-8, o -= 1e-8, r -= 1e-8;
  const a = Math.max(Math.min(e, t.maxLevel), t.minLevel), [l, c, u, d] = t.getTilesInRange(i, n, r, o, a, !0);
  for (let p = l; p <= u; p++)
    for (let m = c; m <= d; m++)
      s(p, m, a);
}
function Br(h, e, t) {
  const s = new C(), i = {}, n = [], r = h.getAttribute("position");
  h.computeBoundingBox(), h.boundingBox.getCenter(s).applyMatrix4(e), t.getPositionToCartographic(s, i);
  const o = i.lat || 0, a = i.lon || 0;
  let l = 1 / 0, c = 1 / 0, u = 1 / 0, d = -1 / 0, p = -1 / 0, m = -1 / 0;
  for (let y = 0; y < r.count; y++)
    s.fromBufferAttribute(r, y).applyMatrix4(e), t.getPositionToCartographic(s, i), Math.abs(Math.abs(i.lat) - Math.PI / 2) < 1e-5 && (i.lon = a), Math.abs(a - i.lon) > Math.PI && (i.lon += Math.sign(a - i.lon) * Math.PI * 2), Math.abs(o - i.lat) > Math.PI && (i.lat += Math.sign(o - i.lat) * Math.PI * 2), n.push(i.lon, i.lat, i.height), l = Math.min(l, i.lat), d = Math.max(d, i.lat), c = Math.min(c, i.lon), p = Math.max(p, i.lon), u = Math.min(u, i.height), m = Math.max(m, i.height);
  const f = [c, l, p, d], g = [...f, u, m];
  return {
    uv: n,
    range: f,
    region: g
  };
}
function Ls(h, e, t = null, s = null, i = null) {
  let n = 1 / 0, r = 1 / 0, o = 1 / 0, a = -1 / 0, l = -1 / 0, c = -1 / 0;
  const u = [], d = new Y();
  if (h.forEach((p) => {
    d.copy(p.matrixWorld), t && d.premultiply(t);
    const { uv: m, region: f } = Br(p.geometry, d, e);
    u.push(m), n = Math.min(n, f[1]), a = Math.max(a, f[3]), r = Math.min(r, f[0]), l = Math.max(l, f[2]), o = Math.min(o, f[4]), c = Math.max(c, f[5]);
  }), s !== null) {
    i === null && (i = s.clampToBounds([r, n, l, a]), i = s.toNormalizedRange(i));
    const [p, m, f, g] = i;
    u.forEach((y) => {
      for (let x = 0, _ = y.length; x < _; x += 3) {
        const b = y[x + 0], T = y[x + 1], v = y[x + 2];
        let [S, M] = s.toNormalizedPoint(b, T);
        S = w.clamp(S, 0, 1), M = w.clamp(M, 0, 1), y[x + 0] = w.mapLinear(S, p, f, 0, 1), y[x + 1] = w.mapLinear(M, m, g, 0, 1), y[x + 2] = w.mapLinear(v, o, c, 0, 1);
      }
    });
  }
  return {
    uvs: u,
    range: i,
    region: [r, n, l, a, o, c]
  };
}
function Ur(h, e) {
  const t = new C(), s = [], i = h.getAttribute("position");
  let n = 1 / 0, r = 1 / 0, o = 1 / 0, a = -1 / 0, l = -1 / 0, c = -1 / 0;
  for (let d = 0; d < i.count; d++)
    t.fromBufferAttribute(i, d).applyMatrix4(e), s.push(t.x, t.y, t.z), n = Math.min(n, t.x), a = Math.max(a, t.x), r = Math.min(r, t.y), l = Math.max(l, t.y), o = Math.min(o, t.z), c = Math.max(c, t.z);
  return {
    uv: s,
    range: [n, r, a, l],
    heightRange: [o, c]
  };
}
function Or(h, e) {
  let t = 1 / 0, s = 1 / 0, i = 1 / 0, n = -1 / 0, r = -1 / 0, o = -1 / 0;
  const a = [], l = new Y();
  return h.forEach((c) => {
    l.copy(c.matrixWorld), e && l.premultiply(e);
    const { uv: u, range: d, heightRange: p } = Ur(c.geometry, l);
    a.push(u), t = Math.min(t, d[0]), n = Math.max(n, d[2]), s = Math.min(s, d[1]), r = Math.max(r, d[3]), i = Math.min(i, p[0]), o = Math.max(o, p[1]);
  }), a.forEach((c) => {
    for (let u = 0, d = c.length; u < d; u += 3) {
      const p = c[u + 0], m = c[u + 1];
      c[u + 0] = w.mapLinear(p, t, n, 0, 1), c[u + 1] = w.mapLinear(m, s, r, 0, 1);
    }
  }), {
    uvs: a,
    range: [t, s, n, r],
    heightRange: [i, o]
  };
}
const Qt = Symbol("OVERLAY_PARAMS");
function Vr(h, e) {
  if (h[Qt])
    return h[Qt];
  const t = {
    layerMaps: { value: [] },
    layerInfo: { value: [] }
  };
  return h[Qt] = t, h.defines = {
    ...h.defines || {},
    LAYER_COUNT: 0
  }, h.onBeforeCompile = (s) => {
    e && e(s), s.uniforms = {
      ...s.uniforms,
      ...t
    }, s.vertexShader = s.vertexShader.replace(/void main\(\s*\)\s*{/, (i) => (
      /* glsl */
      `

				#pragma unroll_loop_start
					for ( int i = 0; i < 10; i ++ ) {

						#if UNROLLED_LOOP_INDEX < LAYER_COUNT

							attribute vec3 layer_uv_UNROLLED_LOOP_INDEX;
							varying vec3 v_layer_uv_UNROLLED_LOOP_INDEX;

						#endif


					}
				#pragma unroll_loop_end

				${i}

				#pragma unroll_loop_start
					for ( int i = 0; i < 10; i ++ ) {

						#if UNROLLED_LOOP_INDEX < LAYER_COUNT

							v_layer_uv_UNROLLED_LOOP_INDEX = layer_uv_UNROLLED_LOOP_INDEX;

						#endif

					}
				#pragma unroll_loop_end

			`
    )), s.fragmentShader = s.fragmentShader.replace(/void main\(/, (i) => (
      /* glsl */
      `

				#if LAYER_COUNT != 0
					struct LayerInfo {
						vec3 color;
						float opacity;

						int alphaMask;
						int alphaInvert;
					};

					uniform sampler2D layerMaps[ LAYER_COUNT ];
					uniform LayerInfo layerInfo[ LAYER_COUNT ];
				#endif

				#pragma unroll_loop_start
					for ( int i = 0; i < 10; i ++ ) {

						#if UNROLLED_LOOP_INDEX < LAYER_COUNT

							varying vec3 v_layer_uv_UNROLLED_LOOP_INDEX;

						#endif

					}
				#pragma unroll_loop_end

				${i}

			`
    )).replace(/#include <color_fragment>/, (i) => (
      /* glsl */
      `

				${i}

				#if LAYER_COUNT != 0
				{
					vec4 tint;
					vec3 layerUV;
					float layerOpacity;
					float wOpacity;
					float wDelta;
					#pragma unroll_loop_start
						for ( int i = 0; i < 10; i ++ ) {

							#if UNROLLED_LOOP_INDEX < LAYER_COUNT

								layerUV = v_layer_uv_UNROLLED_LOOP_INDEX;
								tint = texture( layerMaps[ i ], layerUV.xy );

								// discard texture outside 0, 1 on w - offset the stepped value by an epsilon to avoid cases
								// where wDelta is near 0 (eg a flat surface) at the w boundary, resulting in artifacts on some
								// hardware.
								wDelta = max( fwidth( layerUV.z ), 1e-7 );
								wOpacity =
									smoothstep( - wDelta, 0.0, layerUV.z ) *
									smoothstep( 1.0 + wDelta, 1.0, layerUV.z );

								// apply tint & opacity
								tint.rgb *= layerInfo[ i ].color;
								tint.rgba *= layerInfo[ i ].opacity * wOpacity;

								// invert the alpha
								if ( layerInfo[ i ].alphaInvert > 0 ) {

									tint.a = 1.0 - tint.a;

								}

								// apply the alpha across all existing layers if alpha mask is true
								if ( layerInfo[ i ].alphaMask > 0 ) {

									diffuseColor.a *= tint.a;

								} else {

									tint.rgb *= tint.a;
									diffuseColor = tint + diffuseColor * ( 1.0 - tint.a );

								}

							#endif

						}
					#pragma unroll_loop_end
				}
				#endif
			`
    ));
  }, t;
}
const X = 0, pe = ["a", "b", "c"], U = /* @__PURE__ */ new be(), ni = /* @__PURE__ */ new be(), ri = /* @__PURE__ */ new be(), oi = /* @__PURE__ */ new be();
class bn {
  constructor() {
    this.attributeList = null, this.splitOperations = [], this.trianglePool = new kr();
  }
  forEachSplitPermutation(e) {
    const { splitOperations: t } = this, s = (i = 0) => {
      if (i >= t.length) {
        e();
        return;
      }
      t[i].keepPositive = !0, s(i + 1), t[i].keepPositive = !1, s(i + 1);
    };
    s();
  }
  // Takes an operation that returns a value for the given vertex passed to the callback. Triangles
  // are clipped along edges where the interpolated value is equal to 0. The polygons on the positive
  // side of the operation are kept if "keepPositive" is true.
  // callback( geometry, i0, i1, i2, barycoord );
  addSplitOperation(e, t = !0) {
    this.splitOperations.push({
      callback: e,
      keepPositive: t
    });
  }
  // Removes all split operations
  clearSplitOperations() {
    this.splitOperations.length = 0;
  }
  // clips an object hierarchy
  clipObject(e) {
    const t = e.clone(), s = [];
    return t.traverse((i) => {
      i.isMesh && (i.geometry = this.clip(i).geometry, (i.geometry.index ? i.geometry.index.count / 3 : i.attributes.position.count / 3) === 0 && s.push(i));
    }), s.forEach((i) => {
      i.removeFromParent();
    }), t;
  }
  // Returns a new mesh that has been clipped by the split operations. Range indicates the range of
  // elements to include when clipping.
  clip(e, t = null) {
    const s = this.getClippedData(e, t);
    return this.constructMesh(s.attributes, s.index, e);
  }
  // Appends the clip operation data to the given "target" object so multiple ranges can be appended.
  // The "target" object is returned with an "index" field, "vertexIsClipped" field, and series of arrays
  // in "attributes".
  // attributes - set of attribute arrays
  // index - triangle indices referencing vertices in attributes
  // vertexIsClipped - array indicating whether a vertex is on a clipped edge
  getClippedData(e, t = null, s = {}) {
    const { trianglePool: i, splitOperations: n, attributeList: r } = this, o = e.geometry, a = o.attributes.position, l = o.index;
    let c = 0;
    const u = {};
    s.index = s.index || [], s.vertexIsClipped = s.vertexIsClipped || [], s.attributes = s.attributes || {};
    for (const f in o.attributes) {
      if (r !== null) {
        if (r instanceof Function && !r(f))
          continue;
        if (Array.isArray(r) && !r.includes(f))
          continue;
      }
      s.attributes[f] = [];
    }
    let d = 0, p = l ? l.count : a.count;
    t !== null && (d = t.start, p = t.count);
    for (let f = d, g = d + p; f < g; f += 3) {
      let y = f + 0, x = f + 1, _ = f + 2;
      l && (y = l.getX(y), x = l.getX(x), _ = l.getX(_));
      const b = i.get();
      b.initFromIndices(y, x, _);
      let T = [b];
      for (let v = 0; v < n.length; v++) {
        const { keepPositive: S, callback: M } = n[v], P = [];
        for (let E = 0; E < T.length; E++) {
          const F = T[E], { indices: B, barycoord: W } = F;
          F.clipValues.a = M(o, B.a, B.b, B.c, W.a, e.matrixWorld), F.clipValues.b = M(o, B.a, B.b, B.c, W.b, e.matrixWorld), F.clipValues.c = M(o, B.a, B.b, B.c, W.c, e.matrixWorld), this.splitTriangle(F, !S, P);
        }
        T = P;
      }
      for (let v = 0, S = T.length; v < S; v++) {
        const M = T[v];
        m(M, o);
      }
      i.reset();
    }
    return s;
    function m(f, g) {
      for (let y = 0; y < 3; y++) {
        const x = f.getVertexHash(y, g);
        x in u || (u[x] = c, c++, f.getVertexData(y, g, s.attributes), s.vertexIsClipped.push(f.clipValues[pe[y]] === X));
        const _ = u[x];
        s.index.push(_);
      }
    }
  }
  // Takes the set of resultant data and constructs a mesh
  constructMesh(e, t, s) {
    const i = s.geometry, n = new Fe(), r = e.position.length / 3 > 65535 ? new Uint32Array(t) : new Uint16Array(t);
    n.setIndex(new G(r, 1, !1));
    for (const a in e) {
      const l = i.getAttribute(a), c = new l.array.constructor(e[a]), u = new G(c, l.itemSize, l.normalized);
      u.gpuType = l.gpuType, n.setAttribute(a, u);
    }
    const o = new _e(n, s.material.clone());
    return o.position.copy(s.position), o.quaternion.copy(s.quaternion), o.scale.copy(s.scale), o;
  }
  // Splits the given triangle
  splitTriangle(e, t, s) {
    const { trianglePool: i } = this, n = [], r = [], o = [];
    for (let a = 0; a < 3; a++) {
      const l = pe[a], c = pe[(a + 1) % 3], u = e.clipValues[l], d = e.clipValues[c];
      (u < X != d < X || u === X) && (n.push(a), r.push([l, c]), u === d ? o.push(0) : o.push(w.mapLinear(X, u, d, 0, 1)));
    }
    if (n.length !== 2)
      Math.min(
        e.clipValues.a,
        e.clipValues.b,
        e.clipValues.c
      ) < X === t && s.push(e);
    else if (n.length === 2) {
      const a = i.get().initFromTriangle(e), l = i.get().initFromTriangle(e), c = i.get().initFromTriangle(e);
      (n[0] + 1) % 3 === n[1] ? (a.lerpVertexFromEdge(e, r[0][0], r[0][1], o[0], "a"), a.copyVertex(e, r[0][1], "b"), a.lerpVertexFromEdge(e, r[1][0], r[1][1], o[1], "c"), a.clipValues.a = X, a.clipValues.c = X, l.lerpVertexFromEdge(e, r[0][0], r[0][1], o[0], "a"), l.copyVertex(e, r[1][1], "b"), l.copyVertex(e, r[0][0], "c"), l.clipValues.a = X, c.lerpVertexFromEdge(e, r[0][0], r[0][1], o[0], "a"), c.lerpVertexFromEdge(e, r[1][0], r[1][1], o[1], "b"), c.copyVertex(e, r[1][1], "c"), c.clipValues.a = X, c.clipValues.b = X) : (a.lerpVertexFromEdge(e, r[0][0], r[0][1], o[0], "a"), a.lerpVertexFromEdge(e, r[1][0], r[1][1], o[1], "b"), a.copyVertex(e, r[0][0], "c"), a.clipValues.a = X, a.clipValues.b = X, l.lerpVertexFromEdge(e, r[0][0], r[0][1], o[0], "a"), l.copyVertex(e, r[0][1], "b"), l.lerpVertexFromEdge(e, r[1][0], r[1][1], o[1], "c"), l.clipValues.a = X, l.clipValues.c = X, c.copyVertex(e, r[0][1], "a"), c.copyVertex(e, r[1][0], "b"), c.lerpVertexFromEdge(e, r[1][0], r[1][1], o[1], "c"), c.clipValues.c = X);
      let d, p;
      d = Math.min(a.clipValues.a, a.clipValues.b, a.clipValues.c), p = d < X, p === t && s.push(a), d = Math.min(l.clipValues.a, l.clipValues.b, l.clipValues.c), p = d < X, p === t && s.push(l), d = Math.min(c.clipValues.a, c.clipValues.b, c.clipValues.c), p = d < X, p === t && s.push(c);
    }
  }
}
class kr {
  constructor() {
    this.pool = [], this.index = 0;
  }
  get() {
    if (this.index >= this.pool.length) {
      const t = new Nr();
      this.pool.push(t);
    }
    const e = this.pool[this.index];
    return this.index++, e;
  }
  reset() {
    this.index = 0;
  }
}
class Nr {
  constructor() {
    this.indices = {
      a: -1,
      b: -1,
      c: -1
    }, this.clipValues = {
      a: -1,
      b: -1,
      c: -1
    }, this.barycoord = new Os();
  }
  // returns a hash for the given [0, 2] index based on attributes of the referenced geometry
  getVertexHash(e, t) {
    const { barycoord: s, indices: i } = this, n = pe[e], r = s[n];
    if (r.x === 1)
      return i[pe[0]];
    if (r.y === 1)
      return i[pe[1]];
    if (r.z === 1)
      return i[pe[2]];
    {
      const { attributes: o } = t;
      let a = "";
      for (const l in o) {
        const c = o[l];
        switch (ai(c, i.a, i.b, i.c, r, U), (l === "normal" || l === "tangent" || l === "bitangent") && U.normalize(), c.itemSize) {
          case 4:
            a += it(U.x, U.y, U.z, U.w);
            break;
          case 3:
            a += it(U.x, U.y, U.z);
            break;
          case 2:
            a += it(U.x, U.y);
            break;
          case 1:
            a += it(U.x);
            break;
        }
        a += "|";
      }
      return a;
    }
  }
  // Accumulate the vertex data in the given attribute arrays
  getVertexData(e, t, s) {
    const { barycoord: i, indices: n } = this, r = pe[e], o = i[r], { attributes: a } = t;
    for (const l in a) {
      if (!s[l])
        continue;
      const c = a[l], u = s[l];
      switch (ai(c, n.a, n.b, n.c, o, U), (l === "normal" || l === "tangent" || l === "bitangent") && U.normalize(), c.itemSize) {
        case 4:
          u.push(U.x, U.y, U.z, U.w);
          break;
        case 3:
          u.push(U.x, U.y, U.z);
          break;
        case 2:
          u.push(U.x, U.y);
          break;
        case 1:
          u.push(U.x);
          break;
      }
    }
  }
  // Copy the indices from a target triangle
  initFromTriangle(e) {
    return this.initFromIndices(
      e.indices.a,
      e.indices.b,
      e.indices.c
    );
  }
  // Set the indices for the given
  initFromIndices(e, t, s) {
    return this.indices.a = e, this.indices.b = t, this.indices.c = s, this.clipValues.a = -1, this.clipValues.b = -1, this.clipValues.c = -1, this.barycoord.a.set(1, 0, 0), this.barycoord.b.set(0, 1, 0), this.barycoord.c.set(0, 0, 1), this;
  }
  // Lerp the given vertex along to the provided edge of the provided triangle
  lerpVertexFromEdge(e, t, s, i, n) {
    this.clipValues[n] = w.lerp(e.clipValues[t], e.clipValues[s], i), this.barycoord[n].lerpVectors(e.barycoord[t], e.barycoord[s], i);
  }
  // Copy a vertex from the provided triangle
  copyVertex(e, t, s) {
    this.clipValues[s] = e.clipValues[t], this.barycoord[s].copy(e.barycoord[t]);
  }
}
function ai(h, e, t, s, i, n) {
  switch (ni.fromBufferAttribute(h, e), ri.fromBufferAttribute(h, t), oi.fromBufferAttribute(h, s), n.set(0, 0, 0, 0).addScaledVector(ni, i.x).addScaledVector(ri, i.y).addScaledVector(oi, i.z), h.itemSize) {
    case 3:
      U.w = 0;
      break;
    case 2:
      U.w = 0, U.z = 0;
      break;
    case 1:
      U.w = 0, U.z = 0, U.y = 0;
      break;
  }
  return n;
}
function it(...h) {
  let s = "";
  for (let i = 0, n = h.length; i < n; i++)
    s += ~~(h[i] * 1e5 + 0.5), i !== n - 1 && (s += "_");
  return s;
}
class Fr extends Ge {
  /**
   * @param {WMTSImageSourceOptions} options - Configuration options.
   */
  constructor(e = {}) {
    const {
      layer: t = null,
      tileMatrixSet: s = "default",
      style: i = "default",
      url: n = null,
      format: r = "image/jpeg",
      dimensions: o = null,
      tileMatrixLabels: a = null,
      tileMatrices: l = null,
      projection: c = null,
      levels: u = 20,
      tileDimension: d = 256,
      contentBoundingBox: p = null,
      ...m
    } = e;
    super(m), this.layer = t, this.tileMatrixSet = s, this.style = i, this.url = n, this.format = r, this.dimensions = o, this.tileMatrixLabels = a, this.tileMatrices = l, this.projection = c, this.levels = u, this.tileDimension = d, this.contentBoundingBox = p, this._useKvp = !1;
  }
  /**
   * Detects whether the URL uses KVP or RESTful mode.
   * If the URL contains no template variables, it is considered a KVP endpoint.
   */
  _detectRequestMode(e) {
    return !/\{/.test(e);
  }
  init() {
    const {
      tiling: e,
      tileDimension: t,
      levels: s,
      dimensions: i,
      contentBoundingBox: n,
      tileMatrices: r,
      style: o,
      tileMatrixSet: a
    } = this;
    let { url: l } = this;
    const c = this.projection || "EPSG:3857";
    if (e.flipY = !0, e.setProjection(new ee(c)), n !== null ? e.setContentBounds(
      n[0],
      n[1],
      n[2],
      n[3]
    ) : e.setContentBounds(...e.projection.getBounds()), Array.isArray(r) ? r.forEach((u, d) => {
      const p = u.tileWidth || t, m = u.tileHeight || t;
      e.setLevel(d, {
        tilePixelWidth: p,
        tilePixelHeight: m,
        tileCountX: u.matrixWidth,
        tileCountY: u.matrixHeight,
        tileBounds: u.tileBounds || u.bounds
      });
    }) : e.generateLevels(
      s,
      e.projection.tileCountX,
      e.projection.tileCountY,
      {
        tilePixelWidth: t,
        tilePixelHeight: t
      }
    ), this._useKvp = this._detectRequestMode(l), !this._useKvp && (l = l.replace(/{\s*TileMatrixSet\s*}/gi, a).replace(/{\s*Style\s*}/gi, o), i))
      for (const u in i)
        l = l.replace(new RegExp(`{\\s*${u}\\s*}`, "gi"), i[u]);
    return this.url = l, Promise.resolve();
  }
  getUrl(e, t, s) {
    const { tileMatrices: i, tileMatrixLabels: n } = this;
    let r;
    return i !== null && i.length > 0 ? r = i[s].identifier : n ? r = n[s] : r = s.toString(), this._useKvp ? this._buildKvpUrl(e, t, r) : this._buildRestfulUrl(e, t, r);
  }
  _buildRestfulUrl(e, t, s) {
    return this.url.replace(/{\s*TileMatrix\s*}/gi, s).replace(/{\s*TileCol\s*}/gi, e).replace(/{\s*TileRow\s*}/gi, t);
  }
  _buildKvpUrl(e, t, s) {
    const { dimensions: i, format: n } = this, r = this.url, o = new URLSearchParams({
      SERVICE: "WMTS",
      VERSION: "1.0.0",
      REQUEST: "GetTile",
      LAYER: this.layer,
      STYLE: this.style,
      TILEMATRIXSET: this.tileMatrixSet,
      TILEMATRIX: s,
      TILEROW: t,
      TILECOL: e,
      FORMAT: n
    });
    if (i)
      for (const l in i)
        o.set(l, i[l]);
    const a = r.includes("?") ? "&" : "?";
    return r + a + o.toString();
  }
}
class vn {
  constructor() {
    this.canvas = null, this.context = null, this.range = [0, 0, 1, 1];
  }
  // set the target render texture and the range that represents the full span
  setTarget(e, t) {
    this.canvas = e.image, this.context = e.image.getContext("2d"), this.range = [...t];
  }
  // draw the given texture at the given span with the provided projection
  draw(e, t) {
    const { canvas: s, range: i, context: n } = this, { width: r, height: o } = s, { image: a } = e, l = Math.round(w.mapLinear(t[0], i[0], i[2], 0, r)), c = Math.round(w.mapLinear(t[1], i[1], i[3], 0, o)), u = Math.round(w.mapLinear(t[2], i[0], i[2], 0, r)), d = Math.round(w.mapLinear(t[3], i[1], i[3], 0, o)), p = u - l, m = d - c;
    a instanceof ImageBitmap ? (n.save(), n.translate(l, o - c), n.scale(1, -1), n.drawImage(a, 0, 0, p, m), n.restore()) : n.drawImage(a, l, o - c, p, -m);
  }
  // clear the set target
  clear() {
    const { context: e, canvas: t } = this;
    e.clearRect(0, 0, t.width, t.height);
  }
}
const zr = 1e-10;
function Gr(h, e, t = 0) {
  if (h.length !== e.length)
    return !1;
  for (let s = 0, i = h.length; s < i; s++)
    if (Math.abs(h[s] - e[s]) > t)
      return !1;
  return !0;
}
class Ht extends Gs {
  hasContent(...e) {
    return !0;
  }
}
class wn extends Ht {
  constructor(e) {
    super(), this.tiledImageSource = e, this.tileComposer = new vn(), this.resolution = 256;
  }
  hasContent(e, t, s, i, n) {
    const r = this.tiledImageSource.tiling;
    let o = 0;
    return le([e, t, s, i], n, r, () => {
      o++;
    }), o !== 0;
  }
  async fetchItem([e, t, s, i, n], r) {
    const { tiledImageSource: o, tileComposer: a } = this, l = [e, t, s, i], c = o.tiling;
    await this._markImages(l, n, !1), r == null || r.throwIfAborted();
    let u = null;
    if (le(l, n, c, (m, f, g) => {
      const y = c.getTileBounds(m, f, g, !0, !1);
      Gr(y, l, zr) && (u = [m, f, g]);
    }), u !== null) {
      const [m, f, g] = u;
      return o.get(m, f, g).clone();
    }
    const d = document.createElement("canvas");
    d.width = this.resolution, d.height = this.resolution;
    const p = new ht(d);
    return p.colorSpace = ct, p.generateMipmaps = !1, a.setTarget(p, l), a.clear(16777215, 0), le(l, n, c, (m, f, g) => {
      const y = c.getTileBounds(m, f, g, !0, !1), x = o.get(m, f, g);
      a.draw(x, y);
    }), p;
  }
  disposeItem(e, [t, s, i, n, r]) {
    e && e.dispose(), this._markImages([t, s, i, n], r, !0);
  }
  dispose() {
    super.dispose(), this.tiledImageSource.dispose();
  }
  _markImages(e, t, s = !1) {
    const i = this.tiledImageSource, n = i.tiling, r = [];
    le(e, t, n, (a, l, c) => {
      s ? i.release(a, l, c) : r.push(i.lock(a, l, c));
    });
    const o = r.filter((a) => a instanceof Promise);
    return o.length !== 0 ? Promise.all(o) : null;
  }
}
const we = Object.freeze({
  fill: "#cccccc",
  stroke: "transparent",
  strokeWidth: 1,
  radius: 2,
  order: 0,
  visible: !0
});
class Rt {
  static get DEFAULT_STYLE() {
    return we;
  }
  get fill() {
    return this._ctx.fillStyle;
  }
  set fill(e) {
    this._ctx.fillStyle = e;
  }
  get stroke() {
    return this._ctx.strokeStyle;
  }
  set stroke(e) {
    this._ctx.strokeStyle = e;
  }
  get strokeWidth() {
    return this._ctx.lineWidth;
  }
  set strokeWidth(e) {
    this._ctx.lineWidth = e;
  }
  constructor(e = {}) {
    const {
      getX: t = (r) => r.x,
      getY: s = (r) => r.y,
      flipY: i = !1,
      tileExtent: n = null
    } = e;
    this.getX = t, this.getY = s, this.flipY = i, this.tileExtent = n, this.radius = we.radius, this.visible = !0, this._invScale = 1, this._ctx = null;
  }
  // Sets up the canvas transform and clip for a tile.
  // tileBounds and regionBounds are in the same coordinate space as getX/getY returns.
  setFrame(e, t, s) {
    e.restore();
    const [i, n, r, o] = t, [a, l, c, u] = s, { width: d, height: p } = e.canvas, { flipY: m, tileExtent: f } = this, g = f ?? r - i, y = f ?? o - n, x = Math.round(d * (i - a) / (c - a)), _ = Math.round(d * (r - a) / (c - a)), b = Math.round(p * (u - o) / (u - l)), T = Math.round(p * (u - n) / (u - l)), v = (_ - x) / g, S = (m ? -1 : 1) * (T - b) / y, M = f ? 0 : i, P = f ? 0 : m ? o : n, E = x - M * v, F = b - P * S;
    e.save(), e.setTransform(v, 0, 0, S, E, F), e.beginPath(), e.rect(M, f ? 0 : n, g, y), e.clip(), e.clearRect(M, f ? 0 : n, g, y), this._ctx = e, this._invScale = 1 / v;
  }
  // Applies a style object (as returned by getStyle) to the current canvas context.
  setStyle(e) {
    const { _invScale: t } = this;
    this.fill = (e == null ? void 0 : e.fill) ?? we.fill, this.stroke = (e == null ? void 0 : e.stroke) ?? we.stroke, this.strokeWidth = ((e == null ? void 0 : e.strokeWidth) ?? we.strokeWidth) * t, this.radius = ((e == null ? void 0 : e.radius) ?? we.radius) * t, this.visible = e ? (e == null ? void 0 : e.visible) ?? we.visible : !1;
  }
  _renderPoints(e, t = 1) {
    const { _ctx: s, radius: i, getX: n, getY: r, visible: o } = this;
    if (o) {
      for (const a of e)
        for (const l of a) {
          const c = n(l), u = r(l);
          s.beginPath(), s.ellipse(c, u, i / t, i, 0, 0, Math.PI * 2), s.fill();
        }
      s.stroke();
    }
  }
  _renderLines(e) {
    const { _ctx: t, getX: s, getY: i, visible: n } = this;
    if (n) {
      if (e instanceof Path2D) {
        t.stroke(e);
        return;
      }
      t.beginPath();
      for (const r of e)
        for (let o = 0; o < r.length; o++)
          o === 0 ? t.moveTo(s(r[o]), i(r[o])) : t.lineTo(s(r[o]), i(r[o]));
      t.stroke();
    }
  }
  _renderPolygons(e) {
    const { _ctx: t, getX: s, getY: i, visible: n } = this;
    if (n) {
      if (e instanceof Path2D) {
        t.fill(e, "evenodd"), t.stroke(e);
        return;
      }
      t.beginPath();
      for (const r of e) {
        for (let o = 0; o < r.length; o++)
          o === 0 ? t.moveTo(s(r[o]), i(r[o])) : t.lineTo(s(r[o]), i(r[o]));
        t.closePath();
      }
      t.fill("evenodd"), t.stroke();
    }
  }
}
const Wr = /* @__PURE__ */ new Set(["Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"]), Kt = /* @__PURE__ */ new C(), gt = /* @__PURE__ */ new C();
function Hr(h, e, t) {
  h.getCartographicToPosition(e, t, 0, Kt), h.getCartographicToPosition(e + 0.01, t, 0, gt);
  const i = Kt.distanceTo(gt);
  return h.getCartographicToPosition(e, t + 0.01, 0, gt), Kt.distanceTo(gt) / i;
}
class Yr extends Ht {
  constructor({
    geojson: e = null,
    url: t = null,
    // URL or GeoJson object can be provided
    resolution: s = 256,
    pointRadius: i = 6,
    strokeStyle: n = "white",
    strokeWidth: r = 2,
    fillStyle: o = "rgba( 255, 255, 255, 0.5 )",
    getStyle: a = ((c, u) => ({
      fill: u.fillStyle || this.fillStyle,
      stroke: u.strokeStyle || this.strokeStyle,
      strokeWidth: u.strokeWidth || this.strokeWidth,
      radius: u.pointRadius || this.pointRadius
    })),
    ...l
  } = {}) {
    super(l), this.geojson = e, this.url = t, this.resolution = s, this.pointRadius = i, this.strokeStyle = n, this.strokeWidth = r, this.fillStyle = o, this.getStyle = a, this.features = null, this.featureBounds = /* @__PURE__ */ new Map(), this.contentBounds = null, this.projection = new ee(), this.fetchData = (...c) => fetch(...c), this._canvasRenderer = new Rt({
      flipY: !0,
      getX: (c) => c[0],
      getY: (c) => c[1]
    });
  }
  async init() {
    const { geojson: e, url: t } = this;
    if (!e && t) {
      const s = await this.fetchData(t);
      this.geojson = await s.json();
    }
    this._updateCache(!0);
  }
  hasContent(e, t, s, i) {
    const n = [e, t, s, i].map((r) => r * Math.RAD2DEG);
    return this._boundsIntersectBounds(n, this.contentBounds);
  }
  // main fetch per region -> returns CanvasTexture
  fetchItem(e, t) {
    const s = document.createElement("canvas"), i = new ht(s);
    return i.colorSpace = ct, i.generateMipmaps = !1, this._drawToCanvas(s, e), i.needsUpdate = !0, i;
  }
  disposeItem(e) {
    e && e.dispose();
  }
  redraw(...e) {
    const t = this.get(...e);
    t && (this._drawToCanvas(t.image, e), t.needsUpdate = !0);
  }
  _updateCache(e = !1) {
    const { geojson: t, featureBounds: s } = this;
    if (!t || this.features && !e)
      return;
    s.clear();
    let i = 1 / 0, n = 1 / 0, r = -1 / 0, o = -1 / 0;
    this.features = this._featuresFromGeoJSON(t);
    for (const a of this.features) {
      const l = this._getFeatureBounds(a);
      s.set(a, l);
      const [c, u, d, p] = l;
      i = Math.min(i, c), n = Math.min(n, u), r = Math.max(r, d), o = Math.max(o, p);
    }
    this.contentBounds = [i, n, r, o];
  }
  _drawToCanvas(e, t) {
    this._updateCache();
    const [s, i, n, r] = t, { projection: o, resolution: a, features: l, _canvasRenderer: c } = this;
    e.width = a, e.height = a;
    const u = o.convertNormalizedToLongitude(s), d = o.convertNormalizedToLatitude(i), p = o.convertNormalizedToLongitude(n), m = o.convertNormalizedToLatitude(r), f = [
      u * w.RAD2DEG,
      d * w.RAD2DEG,
      p * w.RAD2DEG,
      m * w.RAD2DEG
    ], g = e.getContext("2d");
    c.setFrame(g, f, f);
    for (const y of l)
      this._featureIntersectsTile(y, f) && this._drawFeatureOnCanvas(y, f, a);
  }
  // bounding box quick test in projected units
  _featureIntersectsTile(e, t) {
    const s = this.featureBounds.get(e);
    return s ? this._boundsIntersectBounds(s, t) : !1;
  }
  _boundsIntersectBounds(e, t) {
    const [s, i, n, r] = e, [o, a, l, c] = t;
    return !(n < o || s > l || r < a || i > c);
  }
  _getFeatureBounds(e) {
    const { geometry: t } = e;
    if (!t)
      return null;
    const { type: s, coordinates: i } = t;
    let n = 1 / 0, r = 1 / 0, o = -1 / 0, a = -1 / 0;
    const l = (c, u) => {
      n = Math.min(n, c), o = Math.max(o, c), r = Math.min(r, u), a = Math.max(a, u);
    };
    return s === "Point" ? l(i[0], i[1]) : s === "MultiPoint" || s === "LineString" ? i.forEach((c) => l(c[0], c[1])) : s === "MultiLineString" || s === "Polygon" ? i.forEach((c) => c.forEach((u) => l(u[0], u[1]))) : s === "MultiPolygon" && i.forEach(
      (c) => c.forEach((u) => u.forEach((d) => l(d[0], d[1])))
    ), [n, r, o, a];
  }
  // Normalize top-level geojson into an array of Feature objects
  _featuresFromGeoJSON(e) {
    const t = e.type;
    return t === "FeatureCollection" ? e.features : t === "Feature" ? [e] : t === "GeometryCollection" ? e.geometries.map((s) => ({ type: "Feature", geometry: s, properties: {} })) : Wr.has(t) ? [{ type: "Feature", geometry: e, properties: {} }] : [];
  }
  // draw feature on canvas ( assumes intersects already )
  _drawFeatureOnCanvas(e, t, s) {
    const { geometry: i = null, properties: n = {} } = e;
    if (!i)
      return;
    const [, r, , o] = t, { _canvasRenderer: a } = this, l = this.getStyle(e, n);
    a.setStyle(l);
    const c = i.type;
    if (c === "Point" || c === "MultiPoint") {
      a.radius = l.radius * (o - r) / s;
      const u = c === "Point" ? [i.coordinates] : i.coordinates;
      for (const d of u) {
        const p = Hr(
          Tr,
          d[1] * w.DEG2RAD,
          d[0] * w.DEG2RAD
        ), m = [d];
        a._renderPoints([m], p);
      }
    } else c === "LineString" ? a._renderLines([i.coordinates]) : c === "MultiLineString" ? a._renderLines(i.coordinates) : c === "Polygon" ? a._renderPolygons(i.coordinates) : c === "MultiPolygon" && i.coordinates.forEach((u) => a._renderPolygons(u));
  }
}
class qr extends Ge {
  // TODO: layer and styles can be arrays, comma separated lists
  constructor(e = {}) {
    const {
      url: t = null,
      layer: s = null,
      styles: i = null,
      contentBoundingBox: n = null,
      version: r = "1.3.0",
      crs: o = "EPSG:4326",
      format: a = "image/png",
      transparent: l = !1,
      levels: c = 18,
      tileDimension: u = 256,
      ...d
    } = e;
    super(d), this.url = t, this.layer = s, this.crs = o, this.format = a, this.tileDimension = u, this.styles = i, this.version = r, this.levels = c, this.transparent = l, this.contentBoundingBox = n;
  }
  init() {
    const { tiling: e, levels: t, tileDimension: s, contentBoundingBox: i } = this;
    return e.setProjection(new ee(this.crs)), e.flipY = !0, e.generateLevels(t, e.projection.tileCountX, e.projection.tileCountY, {
      tilePixelWidth: s,
      tilePixelHeight: s
    }), i !== null ? e.setContentBounds(...i) : e.setContentBounds(...e.projection.getBounds()), Promise.resolve();
  }
  // TODO: handle this in ProjectionScheme or TilingScheme? Or Loader?
  normalizedToMercatorX(e) {
    return w.mapLinear(e, 0, 1, -20037508342789244e-9, 20037508342789244e-9);
  }
  normalizedToMercatorY(e) {
    return w.mapLinear(e, 0, 1, -20037508342789244e-9, 20037508342789244e-9);
  }
  getUrl(e, t, s) {
    const {
      tiling: i,
      layer: n,
      crs: r,
      format: o,
      tileDimension: a,
      styles: l,
      version: c,
      transparent: u
    } = this, d = c === "1.1.1" ? "SRS" : "CRS";
    let p;
    if (r === "EPSG:3857") {
      const f = i.getTileBounds(e, t, s, !0, !1), g = this.normalizedToMercatorX(f[0]), y = this.normalizedToMercatorY(f[1]), x = this.normalizedToMercatorX(f[2]), _ = this.normalizedToMercatorY(f[3]);
      p = [g, y, x, _];
    } else {
      const [f, g, y, x] = i.getTileBounds(e, t, s, !1, !1).map((_) => _ * w.RAD2DEG);
      r === "EPSG:4326" ? c === "1.1.1" ? p = [f, g, y, x] : p = [g, f, x, y] : p = [f, g, y, x];
    }
    const m = new URLSearchParams({
      SERVICE: "WMS",
      REQUEST: "GetMap",
      VERSION: c,
      LAYERS: n,
      [d]: r,
      BBOX: p.join(","),
      WIDTH: a,
      HEIGHT: a,
      FORMAT: o,
      TRANSPARENT: u ? "TRUE" : "FALSE"
    });
    return l != null && m.set("STYLES", l), new URL("?" + m.toString(), this.url).toString();
  }
}
class Xr extends Ge {
  constructor(e = {}) {
    const { url: t = null, ...s } = e;
    super(s), this.url = t, this.format = null, this.stem = null;
  }
  getUrl(e, t, s) {
    return `${this.stem}_files/${s}/${e}_${t}.${this.format}`;
  }
  init() {
    const { url: e } = this;
    return this.fetchData(e, this.fetchOptions).then((t) => t.text()).then((t) => {
      const s = new DOMParser().parseFromString(t, "text/xml");
      if (s.querySelector("DisplayRects") || s.querySelector("Collection"))
        throw new Error("DeepZoomImagesPlugin: DisplayRect and Collection DZI files not supported.");
      const i = s.querySelector("Image"), n = i.querySelector("Size"), r = parseInt(n.getAttribute("Width")), o = parseInt(n.getAttribute("Height")), a = parseInt(i.getAttribute("TileSize")), l = parseInt(i.getAttribute("Overlap")), c = i.getAttribute("Format");
      this.format = c, this.stem = e.split(/\.[^.]+$/g)[0];
      const { tiling: u } = this, d = Math.ceil(Math.log2(Math.max(r, o))) + 1;
      u.flipY = !0, u.pixelOverlap = l, u.generateLevels(d, 1, 1, {
        tilePixelWidth: a,
        tilePixelHeight: a,
        pixelWidth: r,
        pixelHeight: o
      });
    });
  }
}
const De = /* @__PURE__ */ new Y(), yt = /* @__PURE__ */ new C(), Zt = /* @__PURE__ */ new C(), Jt = /* @__PURE__ */ new C(), re = /* @__PURE__ */ new C(), jr = /* @__PURE__ */ new Ft(), li = Symbol("SPLIT_TILE_DATA"), xt = Symbol("SPLIT_HASH"), _t = Symbol("ORIGINAL_REFINE"), Ws = /* @__PURE__ */ new zs();
Ws.maxJobs = 10;
Ws.priorityCallback = (h, e) => {
  const t = h.tile, s = e.tile, i = t.internal.renderer, n = s.internal.renderer, r = i.visibleTiles.has(t), o = n.visibleTiles.has(s);
  return r !== o ? r ? 1 : -1 : Cr(t, s);
};
class el {
  get enableTileSplitting() {
    return this._enableTileSplitting;
  }
  set enableTileSplitting(e) {
    this._enableTileSplitting !== e && (this._enableTileSplitting = e, this._markNeedsUpdate());
  }
  constructor(e = {}) {
    const {
      overlays: t = [],
      resolution: s = 256,
      enableTileSplitting: i = !0
    } = e;
    this.name = "IMAGE_OVERLAY_PLUGIN", this.priority = -15, this.resolution = s, this._enableTileSplitting = i, this.overlays = [], this.needsUpdate = !1, this.tiles = null, this.tileComposer = null, this.tileControllers = /* @__PURE__ */ new Map(), this.overlayInfo = /* @__PURE__ */ new Map(), this.meshParams = /* @__PURE__ */ new WeakMap(), this.pendingTiles = /* @__PURE__ */ new Map(), this.processedTiles = /* @__PURE__ */ new Set(), this.processQueue = null, this._onUpdateAfter = null, this._onTileDownloadStart = null, this._onTileVisibilityChange = null, this._virtualChildResetId = 0, this._bytesUsed = /* @__PURE__ */ new WeakMap(), t.forEach((n) => {
      this.addOverlay(n);
    });
  }
  // plugin functions
  init(e) {
    const t = new vn();
    this.tiles = e, this.tileComposer = t, this.processQueue = Ws, e.forEachLoadedModel((s, i) => {
      this._processTileModel(s, i, !0);
    }), this._onUpdateAfter = async () => {
      let s = !1;
      if (this.overlayInfo.forEach((i, n) => {
        if (!!n.frame != !!i.frame || n.frame && i.frame && !i.frame.equals(n.frame)) {
          const r = i.order;
          this.deleteOverlay(n), this.addOverlay(n, r), s = !0;
        }
      }), s) {
        const { processQueue: i } = this, n = i.maxJobs;
        let r = 0;
        i.items.forEach((o) => {
          e.visibleTiles.has(o.tile) && r++;
        }), i.maxJobs = r + i.currJobs, i.tryRunJobs(), i.maxJobs = n, this.needsUpdate = !0;
      }
      if (this.needsUpdate) {
        this.needsUpdate = !1;
        const { overlays: i, overlayInfo: n } = this;
        i.sort((r, o) => n.get(r).order - n.get(o).order), this.processedTiles.forEach((r) => {
          this._updateLayers(r);
        }), this.resetVirtualChildren(!this.enableTileSplitting), e.recalculateBytesUsed(), e.dispatchEvent({ type: "needs-render" });
      }
    }, this._onTileDownloadStart = ({ tile: s, url: i }) => {
      !/\.json$/i.test(i) && !/\.subtree/i.test(i) && (this.processedTiles.add(s), this._initTileOverlayInfo(s));
    }, this._onTileVisibilityChange = ({ tile: s, visible: i }) => {
      this.overlayInfo.forEach(({ tileInfo: n }, r) => {
        if (n.has(s)) {
          const { range: o } = n.get(s);
          r.setRegionVisible(o, i, s);
        }
      });
    }, e.addEventListener("update-after", this._onUpdateAfter), e.addEventListener("tile-download-start", this._onTileDownloadStart), e.addEventListener("tile-visibility-change", this._onTileVisibilityChange), this.overlays.forEach((s) => {
      this._initOverlay(s);
    });
  }
  _removeVirtualChildren(e) {
    if (!(_t in e))
      return;
    const { tiles: t } = this, { virtualChildCount: s } = e.internal, i = e.children.length, n = i - s;
    for (let r = n; r < i; r++) {
      const o = e.children[r];
      t.processNodeQueue.remove(o), t.lruCache.remove(o), o.parent = null;
    }
    e.children.length -= s, e.internal.virtualChildCount = 0, e.refine = e[_t], delete e[_t], delete e[xt];
  }
  disposeTile(e) {
    const { overlayInfo: t, tileControllers: s, processQueue: i, pendingTiles: n, processedTiles: r } = this;
    r.delete(e), this._removeVirtualChildren(e), s.has(e) && (s.get(e).abort(), s.delete(e), n.delete(e)), t.forEach((({ tileInfo: o }, a) => {
      if (o.has(e)) {
        const { meshInfo: l, range: c } = o.get(e);
        c !== null && a.releaseTexture(c), o.delete(e), l.clear();
      }
    })), i.removeByFilter((o) => o.tile === e);
  }
  calculateBytesUsed(e) {
    const { overlayInfo: t } = this, s = this._bytesUsed;
    let i = null;
    return t.forEach(({ tileInfo: n }, r) => {
      if (n.has(e)) {
        const { target: o } = n.get(e);
        i = i || 0, i += br(o);
      }
    }), i !== null ? (s.set(e, i), i) : s.has(e) ? s.get(e) : 0;
  }
  processTileModel(e, t) {
    return this._processTileModel(e, t);
  }
  async _processTileModel(e, t, s = !1) {
    const { tileControllers: i, processedTiles: n, pendingTiles: r } = this;
    i.set(t, new AbortController()), s || r.set(t, e), n.add(t), this._wrapMaterials(e), this._initTileOverlayInfo(t), await this._initTileSceneOverlayInfo(e, t), this.expandVirtualChildren(e, t), this._updateLayers(t), r.delete(t);
  }
  dispose() {
    const { tiles: e } = this;
    [...this.overlays].forEach((s) => {
      this.deleteOverlay(s);
    }), this.processedTiles.forEach((s) => {
      this._updateLayers(s), this.disposeTile(s);
    }), e.removeEventListener("update-after", this._onUpdateAfter), e.removeEventListener("tile-download-start", this._onTileDownloadStart), e.removeEventListener("tile-visibility-change", this._onTileVisibilityChange), this.resetVirtualChildren(!0);
  }
  getAttributions(e) {
    this.overlays.forEach((t) => {
      t.opacity > 0 && t.getAttributions(e);
    });
  }
  parseToMesh(e, t, s, i) {
    if (s === "image_overlay_tile_split")
      return t[li];
  }
  async resetVirtualChildren(e = !1) {
    this._virtualChildResetId++;
    const t = this._virtualChildResetId;
    if (await Promise.all(this.overlays.map((n) => n.whenReady())), t !== this._virtualChildResetId)
      return;
    const { tiles: s } = this, i = [];
    this.processedTiles.forEach((n) => {
      xt in n && i.push(n);
    }), i.sort((n, r) => r.internal.depth - n.internal.depth), i.forEach((n) => {
      const r = n.engineData.scene.clone();
      r.updateMatrixWorld(), (e || n[xt] !== this._getSplitVectors(r, n).hash) && this._removeVirtualChildren(n);
    }), e || s.forEachLoadedModel((n, r) => {
      this.expandVirtualChildren(n, r);
    });
  }
  _getSplitVectors(e, t, s = Zt) {
    const { tiles: i, overlayInfo: n } = this, r = new Ft();
    r.setFromObject(e), r.getCenter(s);
    const o = [], a = [];
    n.forEach(({ tileInfo: c }, u) => {
      const d = c.get(t);
      if (d && d.target && u.shouldSplit(d.range)) {
        u.frame ? re.set(0, 0, 1).transformDirection(u.frame) : (i.ellipsoid.getPositionToNormal(s, re), re.length() < 1e-6 && re.set(1, 0, 0));
        const p = `${re.x.toFixed(3)},${re.y.toFixed(3)},${re.z.toFixed(3)}_`;
        a.includes(p) || a.push(p);
        const m = yt.set(0, 0, 1);
        Math.abs(re.dot(m)) > 1 - 1e-4 && m.set(1, 0, 0);
        const f = new C().crossVectors(re, m).normalize(), g = new C().crossVectors(re, f).normalize();
        o.push(f, g);
      }
    });
    const l = [];
    for (; o.length !== 0; ) {
      const c = o.pop().clone(), u = c.clone();
      for (let d = 0; d < o.length; d++) {
        const p = o[d], m = c.dot(p);
        Math.abs(m) > Math.cos(Math.PI / 8) && (u.addScaledVector(p, Math.sign(m)), c.copy(u).normalize(), o.splice(d, 1), d--);
      }
      l.push(u.normalize());
    }
    return { directions: l, hash: a.join("") };
  }
  async expandVirtualChildren(e, t) {
    const { refine: s } = t, i = s === "REPLACE" && t.children.length === 0 || s === "ADD", n = t.internal.virtualChildCount !== 0;
    if (this.enableTileSplitting === !1 || !i || n)
      return;
    const r = e.clone();
    r.updateMatrixWorld();
    const { directions: o, hash: a } = this._getSplitVectors(r, t, Zt);
    if (o.length === 0)
      return;
    t[xt] = a;
    const l = new bn();
    l.attributeList = (u) => !/^layer_uv_\d+/.test(u), o.map((u) => {
      l.addSplitOperation((d, p, m, f, g, y) => (Os.getInterpolatedAttribute(d.attributes.position, p, m, f, g, yt), yt.applyMatrix4(y).sub(Zt).dot(u)));
    });
    const c = [];
    l.forEachSplitPermutation(() => {
      const u = l.clipObject(r);
      u.matrix.premultiply(t.engineData.transformInverse).decompose(u.position, u.quaternion, u.scale);
      const d = [];
      if (u.traverse((m) => {
        if (m.isMesh) {
          const f = m.material.clone();
          m.material = f;
          for (const g in f) {
            const y = f[g];
            if (y && y.isTexture && y.source.data instanceof ImageBitmap) {
              const x = document.createElement("canvas");
              x.width = y.image.width, x.height = y.image.height;
              const _ = x.getContext("2d");
              _.scale(1, -1), _.drawImage(y.source.data, 0, 0, x.width, -x.height);
              const b = new ht(x);
              b.mapping = y.mapping, b.wrapS = y.wrapS, b.wrapT = y.wrapT, b.minFilter = y.minFilter, b.magFilter = y.magFilter, b.format = y.format, b.type = y.type, b.anisotropy = y.anisotropy, b.colorSpace = y.colorSpace, b.generateMipmaps = y.generateMipmaps, f[g] = b;
            }
          }
          d.push(m);
        }
      }), d.length === 0)
        return;
      const p = {};
      if (t.boundingVolume.region && (p.region = Ls(d, this.tiles.ellipsoid).region), t.boundingVolume.box || t.boundingVolume.sphere) {
        jr.setFromObject(u, !0).getCenter(Jt);
        let m = 0;
        u.traverse((f) => {
          const g = f.geometry;
          if (g) {
            const y = g.attributes.position;
            for (let x = 0, _ = y.count; x < _; x++) {
              const b = yt.fromBufferAttribute(y, x).applyMatrix4(f.matrixWorld).distanceToSquared(Jt);
              m = Math.max(m, b);
            }
          }
        }), p.sphere = [...Jt, Math.sqrt(m)];
      }
      c.push({
        internal: { isVirtual: !0 },
        refine: "REPLACE",
        geometricError: t.geometricError * 0.5,
        boundingVolume: p,
        content: { uri: "./child.image_overlay_tile_split" },
        children: [],
        [li]: u
      });
    }), t[_t] = t.refine, t.refine = "REPLACE", t.children.push(...c), t.internal.virtualChildCount += c.length;
  }
  fetchData(e, t) {
    if (/image_overlay_tile_split/.test(e))
      return new ArrayBuffer();
  }
  /**
   * Adds an image overlay source to the plugin. The `order` parameter controls the draw
   * order among overlays; lower values are drawn first. If omitted, the overlay is appended
   * after all existing overlays.
   * @param {ImageOverlay} overlay An image overlay instance.
   * @param {number|null} [order=null] Draw order for this overlay.
   */
  addOverlay(e, t = null) {
    const { tiles: s, overlays: i, overlayInfo: n } = this;
    t === null && (t = i.reduce((o, a) => Math.max(o, a.order + 1), 0));
    const r = new AbortController();
    i.push(e), n.set(e, {
      order: t,
      uniforms: {},
      tileInfo: /* @__PURE__ */ new Map(),
      controller: r,
      frame: e.frame ? e.frame.clone() : null
    }), s !== null && this._initOverlay(e);
  }
  /**
   * Updates the draw order for the given overlay.
   * @param {ImageOverlay} overlay The overlay to reorder.
   * @param {number} order New draw order value.
   */
  setOverlayOrder(e, t) {
    this.overlays.indexOf(e) !== -1 && (this.overlayInfo.get(e).order = t, this._markNeedsUpdate());
  }
  /**
   * Removes the given overlay from the plugin.
   * @param {ImageOverlay} overlay The overlay to remove.
   */
  deleteOverlay(e) {
    const { overlays: t, overlayInfo: s, processQueue: i, processedTiles: n, tiles: r } = this, o = t.indexOf(e);
    if (o !== -1) {
      const { tileInfo: a, controller: l } = s.get(e);
      n.forEach((c) => {
        if (!a.has(c))
          return;
        const {
          meshInfo: u,
          range: d
        } = a.get(c);
        d !== null && (r.visibleTiles.has(c) && e.setRegionVisible(d, !1), e.releaseTexture(d)), a.delete(c), u.clear();
      }), a.clear(), s.delete(e), l.abort(), i.removeByFilter((c) => c.overlay === e && n.has(c.tile)), t.splice(o, 1), n.forEach((c) => {
        this._updateLayers(c);
      }), this._markNeedsUpdate();
    }
  }
  // initialize the overlay to use the right fetch options, load all data for existing tiles
  _initOverlay(e) {
    const { processedTiles: t } = this;
    e.init().then(() => {
      e.setResolution(this.resolution);
    });
    const s = [];
    t.forEach(async (i) => {
      const n = i.engineData.scene;
      this._initTileOverlayInfo(i, e);
      const r = this._initTileSceneOverlayInfo(n, i, e);
      s.push(r), await r, this._updateLayers(i);
    }), Promise.all(s).then(() => {
      this._markNeedsUpdate();
    });
  }
  // wrap all materials in the given scene wit the overlay material shader
  _wrapMaterials(e) {
    e.traverse((t) => {
      if (t.material) {
        const s = Vr(t.material, t.material.onBeforeCompile);
        this.meshParams.set(t, s);
      }
    });
  }
  // Initialize per-tile overlay information. This function triggers an async function but
  // does not need to be awaited for use since it's just locking textures which are awaited later.
  _initTileOverlayInfo(e, t = this.overlays) {
    if (Array.isArray(t)) {
      t.forEach((n) => this._initTileOverlayInfo(e, n));
      return;
    }
    const { overlayInfo: s } = this;
    if (s.get(t).tileInfo.has(e))
      return;
    const i = {
      range: null,
      target: null,
      meshInfo: /* @__PURE__ */ new Map(),
      failed: !1
    };
    if (s.get(t).tileInfo.set(e, i), t.isReady && !t.isPlanarProjection) {
      if (e.boundingVolume.region) {
        const [n, r, o, a] = e.boundingVolume.region;
        let l = [n, r, o, a];
        l = t.projection.clampToBounds(l), l = t.projection.toNormalizedRange(l), i.range = l, t.lockTextureSafe(l);
      }
    }
  }
  // initialize the scene meshes
  async _initTileSceneOverlayInfo(e, t, s = this.overlays) {
    if (Array.isArray(s))
      return Promise.all(s.map((x) => this._initTileSceneOverlayInfo(e, t, x)));
    const { tiles: i, overlayInfo: n, tileControllers: r } = this, { ellipsoid: o } = i, { controller: a, tileInfo: l } = n.get(s), c = r.get(t);
    if (s.isReady || await s.whenReady(), a.signal.aborted || c.signal.aborted)
      return;
    const u = [];
    e.updateMatrixWorld(), e.traverse((x) => {
      x.isMesh && u.push(x);
    });
    const { aspectRatio: d, projection: p } = s, m = l.get(t);
    let f, g, y;
    if (s.isPlanarProjection) {
      De.makeScale(1 / d, 1, 1).multiply(s.frame), e.parent !== null && De.multiply(i.group.matrixWorldInverse);
      let x;
      ({ range: f, uvs: g, heightRange: x } = Or(u, De)), y = !(x[0] > 1 || x[1] < 0);
    } else
      De.identity(), e.parent !== null && De.copy(i.group.matrixWorldInverse), { range: f, uvs: g } = Ls(u, o, De, p, m.range), y = !0;
    m.range === null && (m.range = f, s.lockTextureSafe(f)), i.visibleTiles.has(t) && s.setRegionVisible(m.range, !0), y && s.hasContent(f) && await this._fetchTileOverlayTexture(t, s, m), u.forEach((x, _) => {
      const b = new Float32Array(g[_]), T = new G(b, 3);
      m.meshInfo.set(x, { attribute: T });
    });
  }
  // Queues an overlay texture fetch for the given tile, writing the result into info.target.
  // Never throws — failures mark info.failed and dispatch a load-error event instead.
  async _fetchTileOverlayTexture(e, t, s) {
    const { tiles: i, overlayInfo: n, tileControllers: r, processQueue: o } = this, { controller: a } = n.get(t), l = r.get(e), { range: c } = s;
    s.target = await o.add({ tile: e, overlay: t }, async () => {
      if (a.signal.aborted || l.signal.aborted)
        return null;
      const u = await t.getTexture(c);
      return a.signal.aborted || l.signal.aborted ? null : u;
    }).catch((u) => (u.name === "AbortError" || (s.failed = !0, i.dispatchEvent({ type: "load-error", tile: e, overlay: t, error: u, url: null })), null));
  }
  /**
   * Retries any overlay texture fetches that previously failed. Successfully loaded textures
   * are applied to their tiles without requiring a geometry reload. Pairs with the `load-error`
   * event, which fires on the `TilesRenderer` when an overlay texture fetch fails.
   */
  resetFailedOverlays() {
    const { processedTiles: e, overlayInfo: t, overlays: s } = this, i = [];
    e.forEach((n) => {
      s.forEach((r) => {
        const { tileInfo: o } = t.get(r), a = o.get(n);
        a.failed && (a.failed = !1, r.releaseTexture(a.range), i.push({ tile: n, overlay: r, info: a }));
      });
    }), requestAnimationFrame(() => {
      i.forEach(({ tile: n, overlay: r, info: o }) => {
        r.lockTextureSafe(o.range), this._fetchTileOverlayTexture(n, r, o).then(() => {
          this._updateLayers(n);
        }).catch((a) => {
          if (a.name !== "AbortError")
            throw a;
        });
      });
    });
  }
  _updateLayers(e) {
    const { overlayInfo: t, overlays: s, tileControllers: i, meshParams: n } = this, r = i.get(e);
    if (this.tiles.recalculateBytesUsed(e), !(!r || r.signal.aborted)) {
      if (s.length === 0) {
        const o = e.engineData && e.engineData.scene;
        o && o.traverse((a) => {
          if (a.material && n.has(a)) {
            const l = n.get(a);
            l.layerMaps.length = 0, l.layerInfo.length = 0, a.material.defines.LAYER_COUNT = 0, a.material.needsUpdate = !0;
          }
        });
        return;
      }
      s.forEach((o, a) => {
        const { tileInfo: l } = t.get(o), { meshInfo: c, target: u } = l.get(e);
        c.forEach(({ attribute: d }, p) => {
          const { geometry: m, material: f } = p, g = n.get(p), y = `layer_uv_${a}`;
          m.getAttribute(y) !== d && (m.setAttribute(y, d), m.dispose()), g.layerMaps.length = s.length, g.layerInfo.length = s.length, g.layerMaps.value[a] = u !== null ? u : null, g.layerInfo.value[a] = o, f.defines[`LAYER_${a}_EXISTS`] = +(u !== null), f.defines[`LAYER_${a}_ALPHA_INVERT`] = Number(o.alphaInvert), f.defines[`LAYER_${a}_ALPHA_MASK`] = Number(o.alphaMask), f.defines.LAYER_COUNT = s.length, f.needsUpdate = !0;
        });
      });
    }
  }
  _markNeedsUpdate() {
    this.needsUpdate === !1 && (this.needsUpdate = !0, this.tiles !== null && this.tiles.dispatchEvent({ type: "needs-update" }));
  }
}
class Hs {
  get isPlanarProjection() {
    return !!this.frame;
  }
  constructor(e = {}) {
    const {
      opacity: t = 1,
      color: s = 16777215,
      frame: i = null,
      preprocessURL: n = null,
      alphaMask: r = !1,
      alphaInvert: o = !1
    } = e;
    this.preprocessURL = n, this.opacity = t, this.color = new Vs(s), this.frame = i !== null ? i.clone() : null, this.alphaMask = r, this.alphaInvert = o, this.downloadQueue = Mr, this._whenReady = null, this.isReady = !1, this.isInitialized = !1, this._visibleRegionCounts = /* @__PURE__ */ new Map();
  }
  init() {
    return this.isInitialized || (this.isInitialized = !0, this._whenReady = this._init().then(() => this.isReady = !0)), this._whenReady;
  }
  whenReady() {
    return this._whenReady;
  }
  // overrideable
  _init() {
    return Promise.resolve();
  }
  fetch(e, t = {}) {
    this.preprocessURL && (e = this.preprocessURL(e));
    const s = { priority: -performance.now() }, i = this.downloadQueue.add(s, () => fetch(e, t));
    return t.signal && t.signal.addEventListener("abort", () => this.downloadQueue.remove(s), { once: !0 }), i;
  }
  getAttributions(e) {
  }
  hasContent(e, t = null) {
    return !1;
  }
  async getTexture(e, t = null) {
    return null;
  }
  async lockTexture(e, t = null) {
    return null;
  }
  lockTextureSafe(e) {
    const t = this.lockTexture(e);
    return t instanceof Promise && t.catch((s) => {
      if (s.name !== "AbortError") throw s;
    }), t;
  }
  releaseTexture(e, t = null) {
  }
  shouldSplit(e, t = null) {
    return !1;
  }
  setResolution(e) {
  }
  setRegionVisible(e, t) {
    const { _visibleRegionCounts: s } = this, i = e.join("_");
    let n = s.get(i);
    if (n || (n = { range: [...e], count: 0 }, s.set(i, n)), n.count += t ? 1 : -1, n.count < 0)
      throw new Error();
    n.count === 0 && s.delete(i);
  }
}
class Ee extends Hs {
  get tiling() {
    return this.imageSource.tiling;
  }
  get projection() {
    return this.tiling.projection;
  }
  get aspectRatio() {
    return this.tiling && this.isReady ? this.tiling.aspectRatio : 1;
  }
  get fetchOptions() {
    return this.imageSource.fetchOptions;
  }
  set fetchOptions(e) {
    this.imageSource.fetchOptions = e;
  }
  constructor(e = {}) {
    const { imageSource: t = null, ...s } = e;
    super(s), this.imageSource = t, this.regionImageSource = null;
  }
  _init() {
    return this._initImageSource().then(() => {
      this.imageSource.fetchData = (...e) => this.fetch(...e), this.regionImageSource = new wn(this.imageSource);
    });
  }
  _initImageSource() {
    return this.imageSource.init();
  }
  // Texture acquisition API implementations
  calculateLevel(e, t = null) {
    const [s, i, n, r] = e, o = n - s, a = r - i;
    t === null && (t = this.regionImageSource.resolution);
    let l = 0;
    const c = this.tiling.maxLevel;
    for (; l < c; l++) {
      const u = t / o, d = t / a, p = this.tiling.getLevel(l);
      if (p == null)
        continue;
      const { pixelWidth: m, pixelHeight: f } = p;
      if (m >= u || f >= d)
        break;
    }
    return l;
  }
  hasContent(e, t = this.calculateLevel(e)) {
    return this.regionImageSource.hasContent(...e, t);
  }
  getTexture(e, t = this.calculateLevel(e)) {
    return this.regionImageSource.get(...e, t);
  }
  lockTexture(e, t = this.calculateLevel(e)) {
    return this.regionImageSource.lock(...e, t);
  }
  releaseTexture(e, t = this.calculateLevel(e)) {
    this.regionImageSource.release(...e, t);
  }
  shouldSplit(e, t = this.calculateLevel(e)) {
    return this.tiling.maxLevel > t;
  }
  setResolution(e) {
    this.regionImageSource.resolution = e;
  }
}
class tl extends Ee {
  constructor(e = {}) {
    super(e), this.imageSource = new Wt(e);
  }
}
class sl extends Ee {
  constructor(e) {
    super(e), this.imageSource = new Xr(e);
  }
}
class il extends Hs {
  get projection() {
    return this.imageSource.projection;
  }
  get aspectRatio() {
    return 2;
  }
  get pointRadius() {
    return this.imageSource.pointRadius;
  }
  set pointRadius(e) {
    this.imageSource.pointRadius = e;
  }
  get strokeStyle() {
    return this.imageSource.strokeStyle;
  }
  set strokeStyle(e) {
    this.imageSource.strokeStyle = e;
  }
  get strokeWidth() {
    return this.imageSource.strokeWidth;
  }
  set strokeWidth(e) {
    this.imageSource.strokeWidth = e;
  }
  get fillStyle() {
    return this.imageSource.fillStyle;
  }
  set fillStyle(e) {
    this.imageSource.fillStyle = e;
  }
  get geojson() {
    return this.imageSource.geojson;
  }
  set geojson(e) {
    this.imageSource.geojson = e;
  }
  constructor(e = {}) {
    super(e), this.imageSource = new Yr(e), this._redrawQueue = new zs(), this._redrawQueue.maxJobs = 4, this._redrawQueue.priorityCallback = () => 0;
  }
  _init() {
    return this.imageSource.init();
  }
  hasContent(e) {
    return this.imageSource.hasContent(...e);
  }
  getTexture(e) {
    return this.imageSource.get(...e);
  }
  lockTexture(e) {
    return this.imageSource.lock(...e);
  }
  releaseTexture(e) {
    this.imageSource.release(...e);
  }
  setResolution(e) {
    this.imageSource.resolution = e;
  }
  shouldSplit(e) {
    return !0;
  }
  setRegionVisible(e, t) {
    if (super.setRegionVisible(e, t), t) {
      const { _redrawQueue: s } = this, i = e.join("_");
      s.has(i) && s.flush(i);
    }
  }
  redraw() {
    const {
      imageSource: e,
      _redrawQueue: t,
      _visibleRegionCounts: s
    } = this;
    for (const { range: i } of s.values())
      e.redraw(...i);
    e.forEachItem((i, n) => {
      const r = n.join("_");
      !s.has(r) && !t.has(r) && t.add(r, () => {
        e.redraw(...n);
      });
    });
  }
}
class nl extends Ee {
  constructor(e = {}) {
    super(e), this.imageSource = new qr(e);
  }
}
class rl extends Ee {
  constructor(e = {}) {
    super(e), this.imageSource = new Fr(e);
  }
}
class $r extends Ee {
  constructor(e = {}) {
    super(e), this.imageSource = new Tn(e);
  }
}
class ol extends Ee {
  constructor(e = {}) {
    super(e);
    const { apiToken: t, autoRefreshToken: s, assetId: i } = e;
    this.options = e, this.assetId = i, this.auth = new Xn({ apiToken: t, autoRefreshToken: s }), this.auth.authURL = `https://api.cesium.com/v1/assets/${i}/endpoint`, this._attributions = [], this.externalType = !1;
  }
  _initImageSource() {
    return this.auth.refreshToken().then(async (e) => {
      if (this._attributions = e.attributions.map((t) => ({
        value: t.html,
        type: "html",
        collapsible: t.collapsible
      })), e.type !== "IMAGERY")
        throw new Error("CesiumIonOverlay: Only IMAGERY is supported as overlay type.");
      switch (this.externalType = !!e.externalType, e.externalType) {
        case "GOOGLE_2D_MAPS": {
          const { url: t, session: s, key: i, tileWidth: n } = e.options, r = `${t}/v1/2dtiles/{z}/{x}/{y}?session=${s}&key=${i}`;
          this.imageSource = new Wt({
            ...this.options,
            url: r,
            tileDimension: n,
            // Google maps tiles have a fixed depth of 22
            // https://developers.google.com/maps/documentation/tile/2d-tiles-overview
            levels: 22
          });
          break;
        }
        case "BING": {
          const { url: t, mapStyle: s, key: i } = e.options, n = `${t}/REST/v1/Imagery/Metadata/${s}?incl=ImageryProviders&key=${i}&uriScheme=https`, o = (await fetch(n).then((a) => a.json())).resourceSets[0].resources[0];
          this.imageSource = new Dr({
            ...this.options,
            url: o.imageUrl,
            subdomains: o.imageUrlSubdomains,
            tileDimension: o.tileWidth,
            levels: o.zoomMax
          });
          break;
        }
        default:
          this.imageSource = new Tn({
            ...this.options,
            url: e.url
          });
      }
      return this.imageSource.fetchData = (...t) => this.fetch(...t), this.imageSource.init();
    });
  }
  fetch(e, t = {}) {
    if (this.externalType)
      return super.fetch(e, t);
    this.preprocessURL && (e = this.preprocessURL(e));
    const s = { priority: -performance.now() }, i = this.downloadQueue.add(s, () => this.auth.fetch(e, t));
    return t.signal && t.signal.addEventListener("abort", () => this.downloadQueue.remove(s), { once: !0 }), i;
  }
  getAttributions(e) {
    e.push(...this._attributions);
  }
}
class al extends Ee {
  constructor(e = {}) {
    super(e);
    const { apiToken: t, sessionOptions: s, autoRefreshToken: i, logoUrl: n } = e;
    this.logoUrl = n, this.auth = new jn({ apiToken: t, sessionOptions: s, autoRefreshToken: i }), this.imageSource = new Wt(), this.imageSource.fetchData = (...r) => this.fetch(...r), this._logoAttribution = {
      value: "",
      type: "image",
      collapsible: !1
    };
  }
  _initImageSource() {
    return this.auth.refreshToken().then((e) => (this.imageSource.tileDimension = e.tileWidth, this.imageSource.url = "https://tile.googleapis.com/v1/2dtiles/{z}/{x}/{y}", this.imageSource.init()));
  }
  fetch(e, t = {}) {
    this.preprocessURL && (e = this.preprocessURL(e));
    const s = { priority: -performance.now() }, i = this.downloadQueue.add(s, () => this.auth.fetch(e, t));
    return t.signal && t.signal.addEventListener("abort", () => this.downloadQueue.remove(s), { once: !0 }), i;
  }
  getAttributions(e) {
    this.logoUrl && (this._logoAttribution.value = this.logoUrl, e.push(this._logoAttribution));
  }
}
const ci = /* @__PURE__ */ new C(), Tt = /* @__PURE__ */ new Os(), z = /* @__PURE__ */ new C(), ce = /* @__PURE__ */ new C();
class Qr extends $n {
  constructor(e = Jn) {
    super(), this.manager = e, this.ellipsoid = new gn(), this.skirtLength = 1e3, this.smoothSkirtNormals = !0, this.generateNormals = !0, this.solid = !1, this.minLat = -Math.PI / 2, this.maxLat = Math.PI / 2, this.minLon = -Math.PI, this.maxLon = Math.PI;
  }
  parse(e) {
    const {
      ellipsoid: t,
      solid: s,
      skirtLength: i,
      smoothSkirtNormals: n,
      generateNormals: r,
      minLat: o,
      maxLat: a,
      minLon: l,
      maxLon: c
    } = this, {
      header: u,
      indices: d,
      vertexData: p,
      edgeIndices: m,
      extensions: f
    } = super.parse(e), g = new Fe(), y = new ln(), x = new _e(g, y);
    x.position.set(...u.center);
    const _ = "octvertexnormals" in f, b = _ || r, T = p.u.length, v = [], S = [], M = [], P = [];
    let E = 0, F = 0;
    for (let A = 0; A < T; A++)
      W(A, z), q(z.x, z.y, z.z, ce), S.push(z.x, z.y), v.push(...ce);
    for (let A = 0, L = d.length; A < L; A++)
      M.push(d[A]);
    if (b)
      if (_) {
        const A = f.octvertexnormals.normals;
        for (let L = 0, D = A.length; L < D; L++)
          P.push(A[L]);
      } else {
        const A = new Fe(), L = d.length > 21845 ? new Uint32Array(d) : new Uint16Array(d);
        A.setIndex(new G(L, 1, !1)), A.setAttribute("position", new G(new Float32Array(v), 3, !1)), A.computeVertexNormals();
        const R = A.getAttribute("normal").array;
        f.octvertexnormals = { normals: R };
        for (let I = 0, O = R.length; I < O; I++)
          P.push(R[I]);
      }
    if (g.addGroup(E, d.length, F), E += d.length, F++, s) {
      const A = v.length / 3;
      for (let L = 0; L < T; L++)
        W(L, z), q(z.x, z.y, z.z, ce, -i), S.push(z.x, z.y), v.push(...ce);
      for (let L = d.length - 1; L >= 0; L--)
        M.push(d[L] + A);
      if (b) {
        const L = f.octvertexnormals.normals;
        for (let D = 0, R = L.length; D < R; D++)
          P.push(-L[D]);
      }
      g.addGroup(E, d.length, F), E += d.length, F++;
    }
    if (i > 0) {
      const {
        westIndices: A,
        eastIndices: L,
        southIndices: D,
        northIndices: R
      } = m;
      let I;
      const O = K(A);
      I = v.length / 3, S.push(...O.uv), v.push(...O.positions);
      for (let V = 0, $ = O.indices.length; V < $; V++)
        M.push(O.indices[V] + I);
      const J = K(L);
      I = v.length / 3, S.push(...J.uv), v.push(...J.positions);
      for (let V = 0, $ = J.indices.length; V < $; V++)
        M.push(J.indices[V] + I);
      const H = K(D);
      I = v.length / 3, S.push(...H.uv), v.push(...H.positions);
      for (let V = 0, $ = H.indices.length; V < $; V++)
        M.push(H.indices[V] + I);
      const N = K(R);
      I = v.length / 3, S.push(...N.uv), v.push(...N.positions);
      for (let V = 0, $ = N.indices.length; V < $; V++)
        M.push(N.indices[V] + I);
      b && (P.push(...O.normals), P.push(...J.normals), P.push(...H.normals), P.push(...N.normals)), g.addGroup(E, d.length, F), E += d.length, F++;
    }
    for (let A = 0, L = v.length; A < L; A += 3)
      v[A + 0] -= u.center[0], v[A + 1] -= u.center[1], v[A + 2] -= u.center[2];
    const B = v.length / 3 > 65535 ? new Uint32Array(M) : new Uint16Array(M);
    if (g.setIndex(new G(B, 1, !1)), g.setAttribute("position", new G(new Float32Array(v), 3, !1)), g.setAttribute("uv", new G(new Float32Array(S), 2, !1)), b && g.setAttribute("normal", new G(new Float32Array(P), 3, !1)), "watermask" in f) {
      const { mask: A, size: L } = f.watermask, D = new Uint8Array(2 * L * L);
      for (let I = 0, O = A.length; I < O; I++) {
        const J = A[I] === 255 ? 0 : 255;
        D[2 * I + 0] = J, D[2 * I + 1] = J;
      }
      const R = new zt(D, L, L, cn, hn);
      R.flipY = !0, R.minFilter = er, R.magFilter = un, R.needsUpdate = !0, y.roughnessMap = R;
    }
    return x.userData.minHeight = u.minHeight, x.userData.maxHeight = u.maxHeight, "metadata" in f && (x.userData.metadata = f.metadata.json), x;
    function W(A, L) {
      return L.x = p.u[A], L.y = p.v[A], L.z = p.height[A], L;
    }
    function q(A, L, D, R, I = 0) {
      const O = w.lerp(u.minHeight, u.maxHeight, D), J = w.lerp(l, c, A), H = w.lerp(o, a, L);
      return t.getCartographicToPosition(H, J, O + I, R), R;
    }
    function K(A) {
      const L = [], D = [], R = [], I = [], O = [];
      for (let N = 0, V = A.length; N < V; N++)
        W(A[N], z), L.push(z.x, z.y), R.push(z.x, z.y), q(z.x, z.y, z.z, ce), D.push(...ce), q(z.x, z.y, z.z, ce, -i), I.push(...ce);
      const J = A.length - 1;
      for (let N = 0; N < J; N++) {
        const V = N, $ = N + 1, ae = N + A.length, qt = N + A.length + 1;
        O.push(V, ae, $), O.push($, ae, qt);
      }
      let H = null;
      if (b) {
        const N = (D.length + I.length) / 3;
        if (n) {
          H = new Array(N * 3);
          const V = f.octvertexnormals.normals, $ = H.length / 2;
          for (let ae = 0, qt = N / 2; ae < qt; ae++) {
            const Xt = A[ae], Ie = 3 * ae, $s = V[3 * Xt + 0], Qs = V[3 * Xt + 1], Ks = V[3 * Xt + 2];
            H[Ie + 0] = $s, H[Ie + 1] = Qs, H[Ie + 2] = Ks, H[$ + Ie + 0] = $s, H[$ + Ie + 1] = Qs, H[$ + Ie + 2] = Ks;
          }
        } else {
          H = [], Tt.a.fromArray(D, 0), Tt.b.fromArray(I, 0), Tt.c.fromArray(D, 3), Tt.getNormal(ci);
          for (let V = 0; V < N; V++)
            H.push(...ci);
        }
      }
      return {
        uv: [...L, ...R],
        positions: [...D, ...I],
        indices: O,
        normals: H
      };
    }
  }
}
const hi = {}, Kr = /* @__PURE__ */ new C(), es = /* @__PURE__ */ new C(), ts = /* @__PURE__ */ new C(), Zr = /* @__PURE__ */ new C(), Jr = /* @__PURE__ */ new C(), Z = /* @__PURE__ */ new C(), Be = /* @__PURE__ */ new C(), Q = /* @__PURE__ */ new k(), fe = /* @__PURE__ */ new k(), ui = /* @__PURE__ */ new k();
class eo extends bn {
  constructor() {
    super(), this.ellipsoid = new gn(), this.skirtLength = 1e3, this.smoothSkirtNormals = !0, this.solid = !1, this.minLat = -Math.PI / 2, this.maxLat = Math.PI / 2, this.minLon = -Math.PI, this.maxLon = Math.PI, this.attributeList = ["position", "normal", "uv"];
  }
  clipToQuadrant(e, t, s) {
    const { solid: i, skirtLength: n, ellipsoid: r, smoothSkirtNormals: o } = this;
    this.clearSplitOperations(), this.addSplitOperation(di("x"), !t), this.addSplitOperation(di("y"), !s);
    let a, l;
    const c = e.geometry.groups[0], u = this.getClippedData(e, c);
    if (this.adjustVertices(u, e.position, 0), i) {
      a = {
        index: u.index.slice().reverse(),
        attributes: {}
      };
      for (const T in u.attributes)
        a.attributes[T] = u.attributes[T].slice();
      const b = a.attributes.normal;
      if (b)
        for (let T = 0; T < b.length; T += 3)
          b[T + 0] *= -1, b[T + 1] *= -1, b[T + 2] *= -1;
      this.adjustVertices(a, e.position, -n);
    }
    if (n > 0) {
      l = {
        index: [],
        attributes: {
          position: [],
          normal: [],
          uv: []
        }
      };
      let b = 0;
      const T = {}, v = (B, W, q) => {
        const K = it(...B, ...q, ...W);
        K in T || (T[K] = b, b++, l.attributes.position.push(...B), l.attributes.normal.push(...q), l.attributes.uv.push(...W)), l.index.push(T[K]);
      }, S = u.index, M = u.attributes.uv, P = u.attributes.position, E = u.attributes.normal, F = u.index.length / 3;
      for (let B = 0; B < F; B++) {
        const W = 3 * B;
        for (let q = 0; q < 3; q++) {
          const K = (q + 1) % 3, A = S[W + q], L = S[W + K];
          if (Q.fromArray(M, A * 2), fe.fromArray(M, L * 2), Q.x === fe.x && (Q.x === 0 || Q.x === 0.5 || Q.x === 1) || Q.y === fe.y && (Q.y === 0 || Q.y === 0.5 || Q.y === 1)) {
            es.fromArray(P, A * 3), ts.fromArray(P, L * 3);
            const D = es, R = ts, I = Zr.copy(es), O = Jr.copy(ts);
            Z.copy(I).add(e.position), r.getPositionToNormal(Z, Z), I.addScaledVector(Z, -n), Z.copy(O).add(e.position), r.getPositionToNormal(Z, Z), O.addScaledVector(Z, -n), o && E ? (Z.fromArray(E, A * 3), Be.fromArray(E, L * 3)) : (Z.subVectors(D, R), Be.subVectors(D, I).cross(Z).normalize(), Z.copy(Be)), v(R, fe, Be), v(D, Q, Z), v(I, Q, Z), v(R, fe, Be), v(I, Q, Z), v(O, fe, Be);
          }
        }
      }
    }
    const d = u.index.length, p = u;
    if (a) {
      const { index: b, attributes: T } = a, v = p.attributes.position.length / 3;
      for (let S = 0, M = b.length; S < M; S++)
        p.index.push(b[S] + v);
      for (const S in u.attributes)
        p.attributes[S].push(...T[S]);
    }
    if (l) {
      const { index: b, attributes: T } = l, v = p.attributes.position.length / 3;
      for (let S = 0, M = b.length; S < M; S++)
        p.index.push(b[S] + v);
      for (const S in u.attributes)
        p.attributes[S].push(...T[S]);
    }
    const m = t ? 0 : -0.5, f = s ? 0 : -0.5, g = p.attributes.uv;
    for (let b = 0, T = g.length; b < T; b += 2)
      g[b] = (g[b] + m) * 2, g[b + 1] = (g[b + 1] + f) * 2;
    const y = this.constructMesh(p.attributes, p.index, e);
    y.userData.minHeight = e.userData.minHeight, y.userData.maxHeight = e.userData.maxHeight;
    let x = 0, _ = 0;
    return y.geometry.addGroup(_, d, x), _ += d, x++, a && (y.geometry.addGroup(_, a.index.length, x), _ += a.index.length, x++), l && (y.geometry.addGroup(_, l.index.length, x), _ += l.index.length, x++), y;
  }
  adjustVertices(e, t, s) {
    const { ellipsoid: i, minLat: n, maxLat: r, minLon: o, maxLon: a } = this, { attributes: l, vertexIsClipped: c } = e, u = l.position, d = l.uv, p = u.length / 3;
    for (let m = 0; m < p; m++) {
      const f = Q.fromArray(d, m * 2);
      c && c[m] && (Math.abs(f.x - 0.5) < 1e-10 && (f.x = 0.5), Math.abs(f.y - 0.5) < 1e-10 && (f.y = 0.5), Q.toArray(d, m * 2));
      const g = w.lerp(n, r, f.y), y = w.lerp(o, a, f.x), x = Kr.fromArray(u, m * 3).add(t);
      i.getPositionToCartographic(x, hi), i.getCartographicToPosition(g, y, hi.height + s, x), x.sub(t), x.toArray(u, m * 3);
    }
  }
}
function di(h) {
  return (e, t, s, i, n) => {
    const r = e.attributes.uv;
    return Q.fromBufferAttribute(r, t), fe.fromBufferAttribute(r, s), ui.fromBufferAttribute(r, i), Q[h] * n.x + fe[h] * n.y + ui[h] * n.z - 0.5;
  };
}
const fi = Symbol("TILE_X"), pi = Symbol("TILE_Y"), nt = Symbol("TILE_LEVEL"), Se = Symbol("TILE_AVAILABLE"), ss = Symbol("TILE_SPLIT_SOURCE_SCENE"), bt = 1e4, mi = /* @__PURE__ */ new C();
function to(h, e, t, s) {
  if (h && e < h.length) {
    const i = h[e];
    for (let n = 0, r = i.length; n < r; n++) {
      const { startX: o, startY: a, endX: l, endY: c } = i[n];
      if (t >= o && t <= l && s >= a && s <= c)
        return !0;
    }
  }
  return !1;
}
function Sn(h) {
  const { available: e = null, maxzoom: t = null } = h;
  return t === null ? e.length - 1 : t;
}
function so(h) {
  const { metadataAvailability: e = -1 } = h;
  return e;
}
function is(h, e) {
  const t = h[nt], s = so(e), i = Sn(e);
  return t < i && s !== -1 && t % s === 0;
}
function io(h, e, t, s, i) {
  return i.tiles[0].replace(/{\s*z\s*}/g, t).replace(/{\s*x\s*}/g, h).replace(/{\s*y\s*}/g, e).replace(/{\s*version\s*}/g, s);
}
class no {
  constructor(e = {}) {
    const {
      useRecommendedSettings: t = !0,
      skirtLength: s = null,
      smoothSkirtNormals: i = !0,
      generateNormals: n = !0,
      solid: r = !1
    } = e;
    this.name = "QUANTIZED_MESH_PLUGIN", this.priority = -1e3, this.tiles = null, this.layer = null, this.useRecommendedSettings = t, this.skirtLength = s, this.smoothSkirtNormals = i, this.solid = r, this.generateNormals = n, this.attribution = null, this.tiling = new Gt(), this.projection = new ee();
  }
  // Plugin function
  init(e) {
    e.fetchOptions.headers = e.fetchOptions.headers || {}, e.fetchOptions.headers.Accept = "application/vnd.quantized-mesh,application/octet-stream;q=0.9", this.useRecommendedSettings && (e.errorTarget = 2), this.tiles = e;
  }
  loadRootTileset() {
    const { tiles: e } = this;
    let t = new URL("layer.json", new URL(e.rootURL, location.href));
    return e.invokeAllPlugins((s) => t = s.preprocessURL ? s.preprocessURL(t, null) : t), e.invokeOnePlugin((s) => s.fetchData && s.fetchData(t, this.tiles.fetchOptions)).then((s) => s.json()).then((s) => {
      this.layer = s;
      const {
        projection: i = "EPSG:4326",
        extensions: n = [],
        attribution: r = "",
        available: o = null
      } = s, {
        tiling: a,
        tiles: l,
        projection: c
      } = this;
      r && (this.attribution = {
        value: r,
        type: "string",
        collapsible: !0
      }), n.length > 0 && (l.fetchOptions.headers.Accept += `;extensions=${n.join("-")}`), c.setScheme(i);
      const { tileCountX: u, tileCountY: d } = c;
      a.setProjection(c), a.generateLevels(Sn(s) + 1, u, d);
      const p = [];
      for (let g = 0; g < u; g++) {
        const y = this.createChild(0, g, 0, o);
        y && p.push(y);
      }
      const m = {
        asset: {
          version: "1.1"
        },
        geometricError: 1 / 0,
        root: {
          refine: "REPLACE",
          geometricError: 1 / 0,
          boundingVolume: {
            region: [...this.tiling.getContentBounds(), -bt, bt]
          },
          children: p,
          [Se]: o,
          [nt]: -1
        }
      };
      let f = l.rootURL;
      return l.invokeAllPlugins((g) => f = g.preprocessURL ? g.preprocessURL(f, null) : f), l.preprocessTileset(m, f), m;
    });
  }
  parseToMesh(e, t, s, i) {
    const {
      skirtLength: n,
      solid: r,
      smoothSkirtNormals: o,
      generateNormals: a,
      tiles: l
    } = this, c = l.ellipsoid;
    let u;
    if (s === "quantized_tile_split") {
      const f = new URL(i).searchParams, g = f.get("left") === "true", y = f.get("bottom") === "true", x = new eo();
      x.ellipsoid.copy(c), x.solid = r, x.smoothSkirtNormals = o, x.skirtLength = n === null ? t.geometricError : n;
      const [_, b, T, v] = t.parent.boundingVolume.region;
      x.minLat = b, x.maxLat = v, x.minLon = _, x.maxLon = T;
      const S = t.parent.engineData.scene || t.parent[ss];
      u = x.clipToQuadrant(S, g, y);
    } else if (s === "terrain") {
      const f = new Qr(l.manager);
      f.ellipsoid.copy(c), f.solid = r, f.smoothSkirtNormals = o, f.generateNormals = a, f.skirtLength = n === null ? t.geometricError : n;
      const [g, y, x, _] = t.boundingVolume.region;
      f.minLat = y, f.maxLat = _, f.minLon = g, f.maxLon = x, u = f.parse(e);
    } else
      return;
    const { minHeight: d, maxHeight: p, metadata: m } = u.userData;
    return t.boundingVolume.region[4] = d, t.boundingVolume.region[5] = p, t.engineData.boundingVolume.setRegionData(c, ...t.boundingVolume.region), m && ("geometricerror" in m && (t.geometricError = m.geometricerror), is(t, this.layer) && "available" in m && t.children.length === 0 && (t[Se] = [
      ...new Array(t[nt] + 1).fill(null),
      ...m.available
    ])), t[ss] = u, this.expandChildren(t), u;
  }
  getAttributions(e) {
    this.attribution && e.push(this.attribution);
  }
  // Local functions
  createChild(e, t, s, i) {
    const { tiles: n, layer: r, tiling: o, projection: a } = this, l = n.ellipsoid, c = i === null && e === 0 || to(i, e, t, s), u = io(t, s, e, 1, r), d = [...o.getTileBounds(t, s, e), -bt, bt], [
      /* west */
      ,
      p,
      /* east */
      ,
      m,
      /* minHeight */
      ,
      f
    ] = d, g = p > 0 != m > 0 ? 0 : Math.min(Math.abs(p), Math.abs(m));
    l.getCartographicToPosition(g, 0, f, mi), mi.z = 0;
    const y = a.tileCountX, b = Math.max(...l.radius) * 2 * Math.PI * 0.25 / (65 * y) / 2 ** e, T = {
      [Se]: null,
      [nt]: e,
      [fi]: t,
      [pi]: s,
      refine: "REPLACE",
      geometricError: b,
      boundingVolume: { region: d },
      content: c ? { uri: u } : null,
      children: []
    };
    return is(T, r) || (T[Se] = i), T;
  }
  expandChildren(e) {
    const t = e[nt], s = e[fi], i = e[pi], n = e[Se];
    if (t >= this.tiling.maxLevel)
      return;
    let r = !1;
    for (let o = 0; o < 2; o++)
      for (let a = 0; a < 2; a++) {
        const l = this.createChild(t + 1, 2 * s + o, 2 * i + a, n);
        l.content !== null ? (e.children.push(l), r = !0) : (l.content = { uri: `tile.quantized_tile_split?bottom=${a === 0}&left=${o === 0}` }, l.internal = { isVirtual: !0 }, e.internal.virtualChildCount++, e.children.push(l));
      }
    r || (e.children.length -= e.internal.virtualChildCount, e.internal.virtualChildCount = 0);
  }
  fetchData(e, t) {
    if (/quantized_tile_split/.test(e))
      return new ArrayBuffer();
  }
  disposeTile(e) {
    const { tiles: t, layer: s } = this;
    if (delete e[ss], is(e, s) && (e[Se] = null), Se in e) {
      const { virtualChildCount: i } = e.internal, n = e.children.length, r = n - i;
      for (let o = r; o < n; o++)
        t.processNodeQueue.remove(e.children[o]);
      e.children.length = 0, e.internal.virtualChildCount = 0;
    }
  }
}
class ll extends Qn {
  constructor(e = {}) {
    super({
      assetTypeHandler: (t, s, i) => {
        if (t === "TERRAIN" && s.getPluginByName("QUANTIZED_MESH_PLUGIN") === null)
          s.registerPlugin(new no({
            useRecommendedSettings: this.useRecommendedSettings
          }));
        else if (t === "IMAGERY" && s.getPluginByName("GENERATED_SURFACE_PLUGIN") === null) {
          const n = new $r({ url: s.rootURL });
          s.registerPlugin(new Rr({ shape: "ellipsoid", overlay: n }));
        } else
          console.warn(`CesiumIonAuthPlugin: Cesium Ion asset type "${t}" unhandled.`);
      },
      ...e
    });
  }
}
const ns = /* @__PURE__ */ new Y();
class cl {
  constructor() {
    this.name = "UPDATE_ON_CHANGE_PLUGIN", this.tiles = null, this.needsUpdate = !1, this.cameraMatrices = /* @__PURE__ */ new Map();
  }
  init(e) {
    this.tiles = e, this._needsUpdateCallback = () => {
      this.needsUpdate = !0;
    }, this._onCameraAdd = ({ camera: t }) => {
      this.needsUpdate = !0, this.cameraMatrices.set(t, new Y());
    }, this._onCameraDelete = ({ camera: t }) => {
      this.needsUpdate = !0, this.cameraMatrices.delete(t);
    }, e.addEventListener("needs-update", this._needsUpdateCallback), e.addEventListener("add-camera", this._onCameraAdd), e.addEventListener("delete-camera", this._onCameraDelete), e.addEventListener("camera-resolution-change", this._needsUpdateCallback), e.cameras.forEach((t) => {
      this._onCameraAdd({ camera: t });
    });
  }
  doTilesNeedUpdate() {
    const e = this.tiles;
    let t = !1;
    this.cameraMatrices.forEach((i, n) => {
      ns.copy(e.group.matrixWorld).premultiply(n.matrixWorldInverse).premultiply(n.projectionMatrixInverse), t = t || !ns.equals(i), i.copy(ns);
    });
    const s = this.needsUpdate;
    return this.needsUpdate = !1, s || t;
  }
  preprocessNode() {
    this.needsUpdate = !0;
  }
  dispose() {
    const e = this.tiles;
    e.removeEventListener("camera-resolution-change", this._needsUpdateCallback), e.removeEventListener("needs-update", this._needsUpdateCallback), e.removeEventListener("add-camera", this._onCameraAdd), e.removeEventListener("delete-camera", this._onCameraDelete);
  }
}
const gi = /* @__PURE__ */ new C();
function qe(h, e) {
  if (h.isInterleavedBufferAttribute || h.array instanceof e)
    return h;
  const s = e === Int8Array || e === Int16Array || e === Int32Array ? -1 : 0, i = new e(h.count * h.itemSize), n = new G(i, h.itemSize, !0), r = h.itemSize, o = h.count;
  for (let a = 0; a < o; a++)
    for (let l = 0; l < r; l++) {
      const c = w.clamp(h.getComponent(a, l), s, 1);
      n.setComponent(a, l, c);
    }
  return n;
}
function ro(h, e = Int16Array) {
  const t = h.geometry, s = t.attributes, i = s.position;
  if (i.isInterleavedBufferAttribute || i.array instanceof e)
    return i;
  const n = new e(i.count * i.itemSize), r = new G(n, i.itemSize, !1), o = i.itemSize, a = i.count;
  t.computeBoundingBox();
  const l = t.boundingBox, { min: c, max: u } = l, d = 2 ** (8 * e.BYTES_PER_ELEMENT - 1) - 1, p = -d;
  for (let m = 0; m < a; m++)
    for (let f = 0; f < o; f++) {
      const g = f === 0 ? "x" : f === 1 ? "y" : "z", y = c[g], x = u[g], _ = w.mapLinear(
        i.getComponent(m, f),
        y,
        x,
        p,
        d
      );
      r.setComponent(m, f, _);
    }
  l.getCenter(gi).multiply(h.scale).applyQuaternion(h.quaternion), h.position.add(gi), h.scale.x *= 0.5 * (u.x - c.x) / d, h.scale.y *= 0.5 * (u.y - c.y) / d, h.scale.z *= 0.5 * (u.z - c.z) / d, s.position = r, h.geometry.boundingBox = null, h.geometry.boundingSphere = null, h.updateMatrixWorld();
}
class hl {
  constructor(e) {
    this._options = {
      // whether to generate normals if they don't already exist.
      generateNormals: !1,
      // whether to disable use of mipmaps since they are typically not necessary
      // with something like 3d tiles.
      disableMipmaps: !0,
      // whether to compress certain attributes
      compressIndex: !0,
      compressNormals: !1,
      compressUvs: !1,
      compressPosition: !1,
      // the TypedArray type to use when compressing the attributes
      uvType: Int8Array,
      normalType: Int8Array,
      positionType: Int16Array,
      ...e
    }, this.name = "TILES_COMPRESSION_PLUGIN", this.priority = -100;
  }
  processTileModel(e, t) {
    const {
      generateNormals: s,
      disableMipmaps: i,
      compressIndex: n,
      compressUvs: r,
      compressNormals: o,
      compressPosition: a,
      uvType: l,
      normalType: c,
      positionType: u
    } = this._options;
    e.traverse((d) => {
      if (d.material && i) {
        const p = d.material;
        for (const m in p) {
          const f = p[m];
          f && f.isTexture && f.generateMipmaps && (f.generateMipmaps = !1, f.minFilter = un);
        }
      }
      if (d.geometry) {
        const p = d.geometry, m = p.attributes;
        if (r) {
          const { uv: f, uv1: g, uv2: y, uv3: x } = m;
          f && (m.uv = qe(f, l)), g && (m.uv1 = qe(g, l)), y && (m.uv2 = qe(y, l)), x && (m.uv3 = qe(x, l));
        }
        if (s && !m.normals && p.computeVertexNormals(), o && m.normals && (m.normals = qe(m.normals, c)), a && ro(d, u), n && p.index) {
          const f = m.position.count, g = p.index, y = f > 65535 ? Uint32Array : f > 255 ? Uint16Array : Uint8Array;
          if (!(g.array instanceof y)) {
            const x = new y(p.index.count);
            x.set(g.array);
            const _ = new G(x, 1);
            p.setIndex(_);
          }
        }
      }
    });
  }
}
function j(h, e, t) {
  return h && e in h ? h[e] : t;
}
function Mn(h) {
  return h !== "BOOLEAN" && h !== "STRING" && h !== "ENUM";
}
function oo(h) {
  return /^FLOAT/.test(h);
}
function ut(h) {
  return /^VEC/.test(h);
}
function dt(h) {
  return /^MAT/.test(h);
}
function Cn(h, e, t, s = null) {
  return dt(t) || ut(t) ? s.fromArray(h, e) : h[e];
}
function Es(h) {
  const { type: e, componentType: t } = h;
  switch (e) {
    case "SCALAR":
      return t === "INT64" ? 0n : 0;
    case "VEC2":
      return new k();
    case "VEC3":
      return new C();
    case "VEC4":
      return new be();
    case "MAT2":
      return new sr();
    case "MAT3":
      return new tr();
    case "MAT4":
      return new Y();
    case "BOOLEAN":
      return !1;
    case "STRING":
      return "";
    // the final value for enums is a string but are represented as integers
    // during intermediate steps
    case "ENUM":
      return 0;
  }
}
function yi(h, e) {
  if (e == null)
    return !1;
  switch (h) {
    case "SCALAR":
      return typeof e == "number" || typeof e == "bigint";
    case "VEC2":
      return e.isVector2;
    case "VEC3":
      return e.isVector3;
    case "VEC4":
      return e.isVector4;
    case "MAT2":
      return e.isMatrix2;
    case "MAT3":
      return e.isMatrix3;
    case "MAT4":
      return e.isMatrix4;
    case "BOOLEAN":
      return typeof e == "boolean";
    case "STRING":
      return typeof e == "string";
    case "ENUM":
      return typeof e == "number" || typeof e == "bigint";
  }
  throw new Error("ClassProperty: invalid type.");
}
function lt(h, e = null) {
  switch (h) {
    case "INT8":
      return Int8Array;
    case "INT16":
      return Int16Array;
    case "INT32":
      return Int32Array;
    case "INT64":
      return BigInt64Array;
    case "UINT8":
      return Uint8Array;
    case "UINT16":
      return Uint16Array;
    case "UINT32":
      return Uint32Array;
    case "UINT64":
      return BigUint64Array;
    case "FLOAT32":
      return Float32Array;
    case "FLOAT64":
      return Float64Array;
  }
  switch (e) {
    case "BOOLEAN":
      return Uint8Array;
    case "STRING":
      return Uint8Array;
  }
  throw new Error("ClassProperty: invalid type.");
}
function ao(h, e = null) {
  if (h.array) {
    e = e && Array.isArray(e) ? e : [], e.length = h.count;
    for (let s = 0, i = e.length; s < i; s++)
      e[s] = Bt(h, e[s]);
  } else
    e = Bt(h, e);
  return e;
}
function Bt(h, e = null) {
  const t = h.default, s = h.type;
  if (e = e || Es(h), t === null) {
    switch (s) {
      case "SCALAR":
        return 0;
      case "VEC2":
        return e.set(0, 0);
      case "VEC3":
        return e.set(0, 0, 0);
      case "VEC4":
        return e.set(0, 0, 0, 0);
      case "MAT2":
        return e.identity();
      case "MAT3":
        return e.identity();
      case "MAT4":
        return e.identity();
      case "BOOLEAN":
        return !1;
      case "STRING":
        return "";
      case "ENUM":
        return "";
    }
    throw new Error("ClassProperty: invalid type.");
  } else if (dt(s))
    e.fromArray(t);
  else if (ut(s))
    e.fromArray(t);
  else
    return t;
}
function lo(h, e) {
  if (h.noData === null)
    return e;
  const t = h.noData, s = h.type;
  if (Array.isArray(e))
    for (let r = 0, o = e.length; r < o; r++)
      e[r] = i(e[r]);
  else
    e = i(e);
  return e;
  function i(r) {
    return n(r) && (r = Bt(h, r)), r;
  }
  function n(r) {
    if (dt(s)) {
      const o = r.elements;
      for (let a = 0, l = t.length; a < l; a++)
        if (t[a] !== o[a])
          return !1;
      return !0;
    } else if (ut(s)) {
      for (let o = 0, a = t.length; o < a; o++)
        if (t[o] !== r.getComponent(o))
          return !1;
      return !0;
    } else
      return t === r;
  }
}
function co(h, e) {
  switch (h) {
    case "INT8":
      return Math.max(e / 127, -1);
    case "INT16":
      return Math.max(e, 32767, -1);
    case "INT32":
      return Math.max(e / 2147483647, -1);
    case "INT64":
      return Math.max(Number(e) / 9223372036854776e3, -1);
    // eslint-disable-line no-loss-of-precision
    case "UINT8":
      return e / 255;
    case "UINT16":
      return e / 65535;
    case "UINT32":
      return e / 4294967295;
    case "UINT64":
      return Number(e) / 18446744073709552e3;
  }
}
function ho(h, e) {
  const {
    type: t,
    componentType: s,
    scale: i,
    offset: n,
    normalized: r
  } = h;
  if (Array.isArray(e))
    for (let u = 0, d = e.length; u < d; u++)
      e[u] = o(e[u]);
  else
    e = o(e);
  return e;
  function o(u) {
    return dt(t) ? u = l(u) : ut(t) ? u = a(u) : u = c(u), u;
  }
  function a(u) {
    return u.x = c(u.x), u.y = c(u.y), "z" in u && (u.z = c(u.z)), "w" in u && (u.w = c(u.w)), u;
  }
  function l(u) {
    const d = u.elements;
    for (let p = 0, m = d.length; p < m; p++)
      d[p] = c(d[p]);
    return u;
  }
  function c(u) {
    return r && (u = co(s, u)), (r || oo(s)) && (u = u * i + n), u;
  }
}
function Ys(h, e, t = null) {
  if (h.array) {
    Array.isArray(e) || (e = new Array(h.count || 0)), e.length = t !== null ? t : h.count;
    for (let s = 0, i = e.length; s < i; s++)
      yi(h.type, e[s]) || (e[s] = Es(h));
  } else
    yi(h.type, e) || (e = Es(h));
  return e;
}
function Ut(h, e) {
  for (const t in e)
    t in h || delete e[t];
  for (const t in h) {
    const s = h[t];
    e[t] = Ys(s, e[t]);
  }
}
function uo(h) {
  switch (h) {
    case "ENUM":
      return 1;
    case "SCALAR":
      return 1;
    case "VEC2":
      return 2;
    case "VEC3":
      return 3;
    case "VEC4":
      return 4;
    case "MAT2":
      return 4;
    case "MAT3":
      return 9;
    case "MAT4":
      return 16;
    // unused
    case "BOOLEAN":
      return -1;
    case "STRING":
      return -1;
    default:
      return -1;
  }
}
class Yt {
  constructor(e, t, s = null) {
    this.name = t.name || null, this.description = t.description || null, this.type = t.type, this.componentType = t.componentType || null, this.enumType = t.enumType || null, this.array = t.array || !1, this.count = t.count || 0, this.normalized = t.normalized || !1, this.offset = t.offset || 0, this.scale = j(t, "scale", 1), this.max = j(t, "max", 1 / 0), this.min = j(t, "min", -1 / 0), this.required = t.required || !1, this.noData = j(t, "noData", null), this.default = j(t, "default", null), this.semantic = j(t, "semantic", null), this.enumSet = null, this.accessorProperty = s, s && (this.offset = j(s, "offset", this.offset), this.scale = j(s, "scale", this.scale), this.max = j(s, "max", this.max), this.min = j(s, "min", this.min)), t.type === "ENUM" && (this.enumSet = e[this.enumType], this.componentType === null && (this.componentType = j(this.enumSet, "valueType", "UINT16")));
  }
  // shape the given target to match the data type of the property
  // enums are set to their integer value
  shapeToProperty(e, t = null) {
    return Ys(this, e, t);
  }
  // resolve the given object to the default value for the property for a single element
  // enums are set to a default string
  resolveDefaultElement(e) {
    return Bt(this, e);
  }
  // resolve the target to the default value for the property for every element if it's an array
  // enums are set to a default string
  resolveDefault(e) {
    return ao(this, e);
  }
  // converts any instances of no data to the default value
  resolveNoData(e) {
    return lo(this, e);
  }
  // converts enums integers in the given target to strings
  resolveEnumsToStrings(e) {
    const t = this.enumSet;
    if (this.type === "ENUM")
      if (Array.isArray(e))
        for (let i = 0, n = e.length; i < n; i++)
          e[i] = s(e[i]);
      else
        e = s(e);
    return e;
    function s(i) {
      const n = t.values.find((r) => r.value === i);
      return n === null ? "" : n.name;
    }
  }
  // apply scales
  adjustValueScaleOffset(e) {
    return Mn(this.type) ? ho(this, e) : e;
  }
}
class qs {
  constructor(e, t = {}, s = {}, i = null) {
    this.definition = e, this.class = t[e.class], this.className = e.class, this.enums = s, this.data = i, this.name = "name" in e ? e.name : null, this.properties = null;
  }
  getPropertyNames() {
    return Object.keys(this.class.properties);
  }
  includesData(e) {
    return !!this.definition.properties[e];
  }
  dispose() {
  }
  _initProperties(e = Yt) {
    const t = {};
    for (const s in this.class.properties)
      t[s] = new e(this.enums, this.class.properties[s], this.definition.properties[s]);
    this.properties = t;
  }
}
class fo extends Yt {
  constructor(e, t, s = null) {
    super(e, t, s), this.attribute = (s == null ? void 0 : s.attribute) ?? null;
  }
}
class po extends qs {
  constructor(...e) {
    super(...e), this.isPropertyAttributeAccessor = !0, this._initProperties(fo);
  }
  getData(e, t, s = {}) {
    const i = this.properties;
    Ut(i, s);
    for (const n in i)
      s[n] = this.getPropertyValue(n, e, t, s[n]);
    return s;
  }
  getPropertyValue(e, t, s, i = null) {
    if (t >= this.count)
      throw new Error("PropertyAttributeAccessor: Requested index is outside the range of the buffer.");
    const n = this.properties[e], r = n.type;
    if (n) {
      if (!this.definition.properties[e])
        return n.resolveDefault(i);
    } else throw new Error("PropertyAttributeAccessor: Requested class property does not exist.");
    i = n.shapeToProperty(i);
    const o = s.getAttribute(n.attribute.toLowerCase());
    if (dt(r)) {
      const a = i.elements;
      for (let l = 0, c = a.length; l < c; l < c)
        a[l] = o.getComponent(t, l);
    } else if (ut(r))
      i.fromBufferAttribute(o, t);
    else if (r === "SCALAR" || r === "ENUM")
      i = o.getX(t);
    else
      throw new Error("StructuredMetadata.PropertyAttributeAccessor: BOOLEAN and STRING types are not supported by property attributes.");
    return i = n.adjustValueScaleOffset(i), i = n.resolveEnumsToStrings(i), i = n.resolveNoData(i), i;
  }
}
class mo extends Yt {
  constructor(e, t, s = null) {
    super(e, t, s), this.values = (s == null ? void 0 : s.values) ?? null, this.valueLength = uo(this.type), this.arrayOffsets = j(s, "arrayOffsets", null), this.stringOffsets = j(s, "stringOffsets", null), this.arrayOffsetType = j(s, "arrayOffsetType", "UINT32"), this.stringOffsetType = j(s, "stringOffsetType", "UINT32");
  }
  // returns the necessary array length based on the array offsets if present
  getArrayLengthFromId(e, t) {
    let s = this.count;
    if (this.arrayOffsets !== null) {
      const { arrayOffsets: i, arrayOffsetType: n } = this, r = lt(n), o = new r(e[i]);
      s = o[t + 1] - o[t];
    }
    return s;
  }
  // returns the index offset into the data buffer for the given id based on the
  // the array offsets if present
  getIndexOffsetFromId(e, t) {
    let s = t;
    if (this.arrayOffsets) {
      const { arrayOffsets: i, arrayOffsetType: n } = this, r = lt(n);
      s = new r(e[i])[s];
    } else this.array && (s *= this.count);
    return s;
  }
}
class go extends qs {
  constructor(...e) {
    super(...e), this.isPropertyTableAccessor = !0, this.count = this.definition.count, this._initProperties(mo);
  }
  getData(e, t = {}) {
    const s = this.properties;
    Ut(s, t);
    for (const i in s)
      t[i] = this.getPropertyValue(i, e, t[i]);
    return t;
  }
  // reads an individual element
  _readValueAtIndex(e, t, s, i = null) {
    const n = this.properties[e], { componentType: r, type: o } = n, a = this.data, l = a[n.values], c = lt(r, o), u = new c(l), d = n.getIndexOffsetFromId(a, t);
    if (Mn(o) || o === "ENUM")
      return Cn(u, (d + s) * n.valueLength, o, i);
    if (o === "STRING") {
      let p = d + s, m = 0;
      if (n.stringOffsets !== null) {
        const { stringOffsets: g, stringOffsetType: y } = n, x = lt(y), _ = new x(a[g]);
        m = _[p + 1] - _[p], p = _[p];
      }
      const f = new Uint8Array(u.buffer, p, m);
      i = new TextDecoder().decode(f);
    } else if (o === "BOOLEAN") {
      const p = d + s, m = Math.floor(p / 8), f = p % 8;
      i = (u[m] >> f & 1) === 1;
    }
    return i;
  }
  // Reads the data for the given table index
  getPropertyValue(e, t, s = null) {
    if (t >= this.count)
      throw new Error("PropertyTableAccessor: Requested index is outside the range of the table.");
    const i = this.properties[e];
    if (i) {
      if (!this.definition.properties[e])
        return i.resolveDefault(s);
    } else throw new Error("PropertyTableAccessor: Requested property does not exist.");
    const n = i.array, r = this.data, o = i.getArrayLengthFromId(r, t);
    if (s = i.shapeToProperty(s, o), n)
      for (let a = 0, l = s.length; a < l; a++)
        s[a] = this._readValueAtIndex(e, t, a, s[a]);
    else
      s = this._readValueAtIndex(e, t, 0, s);
    return s = i.adjustValueScaleOffset(s), s = i.resolveEnumsToStrings(s), s = i.resolveNoData(s), s;
  }
}
const Xe = /* @__PURE__ */ new lr();
class xi {
  constructor() {
    this._renderer = new ir(), this._target = new Js(1, 1), this._texTarget = new Js(), this._quad = new yn(new nr({
      blending: ar,
      blendDst: or,
      blendSrc: rr,
      uniforms: {
        map: { value: null },
        pixel: { value: new k() }
      },
      vertexShader: (
        /* glsl */
        `
				void main() {

					gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );

				}
			`
      ),
      fragmentShader: (
        /* glsl */
        `
				uniform sampler2D map;
				uniform ivec2 pixel;

				void main() {

					gl_FragColor = texelFetch( map, pixel, 0 );

				}
			`
      )
    }));
  }
  // increases the width of the target render target to support more data
  increaseSizeTo(e) {
    this._target.setSize(Math.max(this._target.width, e), 1);
  }
  // read data from the rendered texture asynchronously
  readDataAsync(e) {
    const { _renderer: t, _target: s } = this;
    return t.readRenderTargetPixelsAsync(s, 0, 0, e.length / 4, 1, e);
  }
  // read data from the rendered texture
  readData(e) {
    const { _renderer: t, _target: s } = this;
    t.readRenderTargetPixels(s, 0, 0, e.length / 4, 1, e);
  }
  // render a single pixel from the source at the destination point on the render target
  // takes the texture, pixel to read from, and pixel to render in to
  renderPixelToTarget(e, t, s) {
    const { _renderer: i, _target: n } = this;
    Xe.min.copy(t), Xe.max.copy(t), Xe.max.x += 1, Xe.max.y += 1, i.initRenderTarget(n), i.copyTextureToTexture(e, n.texture, Xe, s, 0);
  }
}
const ge = /* @__PURE__ */ new class {
  constructor() {
    let h = null;
    Object.getOwnPropertyNames(xi.prototype).forEach((e) => {
      e !== "constructor" && (this[e] = (...t) => (h = h || new xi(), h[e](...t)));
    });
  }
}(), _i = /* @__PURE__ */ new k(), Ti = /* @__PURE__ */ new k(), bi = /* @__PURE__ */ new k();
function yo(h, e) {
  return e === 0 ? h.getAttribute("uv") : h.getAttribute(`uv${e}`);
}
function An(h, e, t = new Array(3)) {
  let s = 3 * e, i = 3 * e + 1, n = 3 * e + 2;
  return h.index && (s = h.index.getX(s), i = h.index.getX(i), n = h.index.getX(n)), t[0] = s, t[1] = i, t[2] = n, t;
}
function Ln(h, e, t, s, i) {
  const [n, r, o] = s, a = yo(h, e);
  _i.fromBufferAttribute(a, n), Ti.fromBufferAttribute(a, r), bi.fromBufferAttribute(a, o), i.set(0, 0, 0).addScaledVector(_i, t.x).addScaledVector(Ti, t.y).addScaledVector(bi, t.z);
}
function En(h, e, t, s) {
  const i = h.x - Math.floor(h.x), n = h.y - Math.floor(h.y), r = Math.floor(i * e % e), o = Math.floor(n * t % t);
  return s.set(r, o), s;
}
const vi = /* @__PURE__ */ new k(), wi = /* @__PURE__ */ new k(), Si = /* @__PURE__ */ new k();
class xo extends Yt {
  constructor(e, t, s = null) {
    super(e, t, s), this.channels = j(s, "channels", [0]), this.index = j(s, "index", null), this.texCoord = j(s, "texCoord", null), this.valueLength = parseInt(this.type.replace(/[^0-9]/g, "")) || 1;
  }
  // takes the buffer to read from and the value index to read
  readDataFromBuffer(e, t, s = null) {
    const i = this.type;
    if (i === "BOOLEAN" || i === "STRING")
      throw new Error("PropertyTextureAccessor: BOOLEAN and STRING types not supported.");
    return Cn(e, t * this.valueLength, i, s);
  }
}
class _o extends qs {
  constructor(...e) {
    super(...e), this.isPropertyTextureAccessor = !0, this._asyncRead = !1, this._initProperties(xo);
  }
  // Reads the full set of property data
  getData(e, t, s, i = {}) {
    const n = this.properties;
    Ut(n, i);
    const r = Object.keys(n), o = r.map((a) => i[a]);
    return this.getPropertyValuesAtTexel(r, e, t, s, o), r.forEach((a, l) => i[a] = o[l]), i;
  }
  // Reads the full set of property data asynchronously
  async getDataAsync(e, t, s, i = {}) {
    const n = this.properties;
    Ut(n, i);
    const r = Object.keys(n), o = r.map((a) => i[a]);
    return await this.getPropertyValuesAtTexelAsync(r, e, t, s, o), r.forEach((a, l) => i[a] = o[l]), i;
  }
  // Reads values asynchronously
  getPropertyValuesAtTexelAsync(...e) {
    this._asyncRead = !0;
    const t = this.getPropertyValuesAtTexel(...e);
    return this._asyncRead = !1, t;
  }
  // Reads values from the textures synchronously
  getPropertyValuesAtTexel(e, t, s, i, n = []) {
    for (; n.length < e.length; ) n.push(null);
    n.length = e.length, ge.increaseSizeTo(n.length);
    const r = this.data, o = this.definition.properties, a = this.properties, l = An(i, t);
    for (let d = 0, p = e.length; d < p; d++) {
      const m = e[d];
      if (!o[m])
        continue;
      const f = a[m], g = r[f.index];
      Ln(i, f.texCoord, s, l, vi), En(vi, g.image.width, g.image.height, wi), Si.set(d, 0), ge.renderPixelToTarget(g, wi, Si);
    }
    const c = new Uint8Array(e.length * 4);
    if (this._asyncRead)
      return ge.readDataAsync(c).then(() => (u.call(this), n));
    return ge.readData(c), u.call(this), n;
    function u() {
      for (let d = 0, p = e.length; d < p; d++) {
        const m = e[d], f = a[m], g = f.type;
        if (n[d] = Ys(f, n[d]), f) {
          if (!o[m]) {
            n[d] = f.resolveDefault(n);
            continue;
          }
        } else throw new Error("PropertyTextureAccessor: Requested property does not exist.");
        const y = f.valueLength * (f.count || 1), x = f.channels.map((v) => c[4 * d + v]), _ = f.componentType, b = lt(_, g), T = new b(y);
        if (new Uint8Array(T.buffer).set(x), f.array) {
          const v = n[d];
          for (let S = 0, M = v.length; S < M; S++)
            v[S] = f.readDataFromBuffer(T, S, v[S]);
        } else
          n[d] = f.readDataFromBuffer(T, 0, n[d]);
        n[d] = f.adjustValueScaleOffset(n[d]), n[d] = f.resolveEnumsToStrings(n[d]), n[d] = f.resolveNoData(n[d]);
      }
    }
  }
  // dispose all of the texture data used
  dispose() {
    this.data.forEach((e) => {
      e && (e.dispose(), e.image instanceof ImageBitmap && e.image.close());
    });
  }
}
class Mi {
  constructor(e, t, s, i = null, n = null) {
    const {
      schema: r,
      propertyTables: o = [],
      propertyTextures: a = [],
      propertyAttributes: l = []
    } = e, { enums: c, classes: u } = r, d = o.map((f) => new go(f, u, c, s));
    let p = [], m = [];
    i && (i.propertyTextures && (p = i.propertyTextures.map((f) => new _o(a[f], u, c, t))), i.propertyAttributes && (m = i.propertyAttributes.map((f) => new po(l[f], u, c)))), this.schema = r, this.tableAccessors = d, this.textureAccessors = p, this.attributeAccessors = m, this.object = n, this.textures = t, this.nodeMetadata = i;
  }
  // Property Tables
  /**
   * Returns data from one or more property tables. Pass a single table index and row ID to
   * get one object, or parallel arrays of table indices and row IDs to get an array of
   * results. Each returned object conforms to the structure class referenced in the schema.
   * @param {number|Array<number>} tableIndices Table index or array of table indices.
   * @param {number|Array<number>} ids Row ID or array of row IDs.
   * @param {Object|Array|null} [target=null] Optional target object or array to write into.
   * @returns {Object|Array}
   */
  getPropertyTableData(e, t, s = null) {
    if (!Array.isArray(e))
      s = s || {}, s = this.tableAccessors[e].getData(t, s);
    else {
      s = s || [];
      const i = Math.min(e.length, t.length);
      s.length = i;
      for (let n = 0; n < i; n++) {
        const r = this.tableAccessors[e[n]];
        s[n] = r.getData(t[n], s[n]);
      }
    }
    if (Array.isArray(e) !== Array.isArray(s) || Array.isArray(e) !== Array.isArray(t))
      throw new Error("StructuralMetadata: Scalar and array inputs cannot be mixed.");
    return s;
  }
  /**
   * Returns name and class information for one or more property tables. Defaults to all
   * tables when `tableIndices` is `null`.
   * @param {Array<number>|null} [tableIndices=null]
   * @returns {Array<{name: string, className: string}>|{name: string, className: string}}
   */
  getPropertyTableInfo(e = null) {
    if (e === null && (e = this.tableAccessors.map((t, s) => s)), Array.isArray(e))
      return e.map((t) => {
        const s = this.tableAccessors[t];
        return {
          name: s.name,
          className: s.definition.class
        };
      });
    {
      const t = this.tableAccessors[e];
      return {
        name: t.name,
        className: t.definition.class
      };
    }
  }
  // Property Textures
  /**
   * Returns data from property textures at the given point on the mesh. Takes the triangle
   * index and barycentric coordinate from a raycast result. See `MeshFeatures.getFeatures`
   * for how to obtain these values.
   * @param {number} triangle Triangle index from a raycast hit.
   * @param {Vector3} barycoord Barycentric coordinate of the hit point.
   * @param {Array} [target=[]] Optional target array to write into.
   * @returns {Array}
   */
  getPropertyTextureData(e, t, s = []) {
    const i = this.textureAccessors;
    s.length = i.length;
    for (let n = 0; n < i.length; n++) {
      const r = i[n];
      s[n] = r.getData(e, t, this.object.geometry, s[n]);
    }
    return s;
  }
  /**
   * Returns the same data as `getPropertyTextureData` but performs texture reads
   * asynchronously.
   * @param {number} triangle Triangle index from a raycast hit.
   * @param {Vector3} barycoord Barycentric coordinate of the hit point.
   * @param {Array} [target=[]] Optional target array to write into.
   * @returns {Array}
   */
  async getPropertyTextureDataAsync(e, t, s = []) {
    const i = this.textureAccessors;
    s.length = i.length;
    const n = [];
    for (let r = 0; r < i.length; r++) {
      const a = i[r].getDataAsync(e, t, this.object.geometry, s[r]).then((l) => {
        s[r] = l;
      });
      n.push(a);
    }
    return await Promise.all(n), s;
  }
  /**
   * Returns information about the property texture accessors, including their class names
   * and per-property channel/texcoord mappings.
   * @returns {Array<{name: string, className: string, properties: Object}>}
   */
  getPropertyTextureInfo() {
    return this.textureAccessors;
  }
  // Property Attributes
  /**
   * Returns data stored as property attributes for the given vertex index.
   * @param {number} attributeIndex Vertex index.
   * @param {Array} [target=[]] Optional target array to write into.
   * @returns {Array}
   */
  getPropertyAttributeData(e, t = []) {
    const s = this.attributeAccessors;
    t.length = s.length;
    for (let i = 0; i < s.length; i++) {
      const n = s[i];
      t[i] = n.getData(e, this.object.geometry, t[i]);
    }
    return t;
  }
  /**
   * Returns name and class information for all property attribute accessors.
   * @returns {Array<{name: string, className: string}>}
   */
  getPropertyAttributeInfo() {
    return this.attributeAccessors.map((e) => ({
      name: e.name,
      className: e.definition.class
    }));
  }
  /**
   * Disposes all texture, table, and attribute accessors.
   */
  dispose() {
    this.textureAccessors.forEach((e) => e.dispose()), this.tableAccessors.forEach((e) => e.dispose()), this.attributeAccessors.forEach((e) => e.dispose());
  }
}
const je = "EXT_structural_metadata";
function To(h, e = []) {
  var i;
  const t = ((i = h.json.textures) == null ? void 0 : i.length) || 0, s = new Array(t).fill(null);
  return e.forEach(({ properties: n }) => {
    for (const r in n) {
      const { index: o } = n[r];
      s[o] === null && (s[o] = h.loadTexture(o));
    }
  }), Promise.all(s);
}
function bo(h, e = []) {
  var i;
  const t = ((i = h.json.bufferViews) == null ? void 0 : i.length) || 0, s = new Array(t).fill(null);
  return e.forEach(({ properties: n }) => {
    for (const r in n) {
      const { values: o, arrayOffsets: a, stringOffsets: l } = n[r];
      s[o] === null && (s[o] = h.loadBufferView(o)), s[a] === null && (s[a] = h.loadBufferView(a)), s[l] === null && (s[l] = h.loadBufferView(l));
    }
  }), Promise.all(s);
}
class vo {
  constructor(e) {
    this.parser = e, this.name = je;
  }
  async afterRoot({ scene: e, parser: t }) {
    const s = t.json.extensionsUsed;
    if (!s || !s.includes(je))
      return;
    let i = null, n = t.json.extensions[je];
    if (n.schemaUri) {
      const { manager: l, path: c, requestHeader: u, crossOrigin: d } = t.options, p = new URL(n.schemaUri, c).toString(), m = new cr(l);
      m.setCrossOrigin(d), m.setResponseType("json"), m.setRequestHeader(u), i = m.loadAsync(p).then((f) => {
        n = { ...n, schema: f };
      });
    }
    const [r, o] = await Promise.all([
      To(t, n.propertyTextures),
      bo(t, n.propertyTables),
      i
    ]), a = new Mi(n, r, o);
    e.userData.structuralMetadata = a, e.traverse((l) => {
      var c;
      if (t.associations.has(l)) {
        const { meshes: u, primitives: d } = t.associations.get(l), p = (c = t.json.meshes[u]) == null ? void 0 : c.primitives[d];
        if (p && p.extensions && p.extensions[je]) {
          const m = p.extensions[je];
          l.userData.structuralMetadata = new Mi(n, r, o, m, l);
        } else
          l.userData.structuralMetadata = a;
      }
    });
  }
}
const Ci = /* @__PURE__ */ new k(), Ai = /* @__PURE__ */ new k(), Li = /* @__PURE__ */ new k();
function wo(h) {
  return h.x > h.y && h.x > h.z ? 0 : h.y > h.z ? 1 : 2;
}
class So {
  constructor(e, t, s) {
    this.geometry = e, this.textures = t, this.data = s, this._asyncRead = !1, this.featureIds = s.featureIds.map((i) => {
      const { texture: n, ...r } = i, o = {
        label: null,
        propertyTable: null,
        nullFeatureId: null,
        ...r
      };
      return n && (o.texture = {
        texCoord: 0,
        channels: [0],
        ...n
      }), o;
    });
  }
  /**
   * Returns an indexed list of all textures used by features in the extension.
   * @returns {Array<Texture>}
   */
  getTextures() {
    return this.textures;
  }
  /**
   * Returns the feature ID info for each feature set defined on this primitive.
   * @returns {Array<FeatureInfo>}
   */
  getFeatureInfo() {
    return this.featureIds;
  }
  /**
   * Performs the same function as `getFeatures` but reads texture data asynchronously.
   * @param {number} triangle Triangle index from a raycast hit.
   * @param {Vector3} barycoord Barycentric coordinate of the hit point.
   * @returns {Promise<Array<number|null>>}
   */
  getFeaturesAsync(...e) {
    this._asyncRead = !0;
    const t = this.getFeatures(...e);
    return this._asyncRead = !1, t;
  }
  /**
   * Returns the list of feature IDs at the given point on the mesh. Takes the triangle
   * index from a raycast result and a barycentric coordinate. Results are indexed in the
   * same order as the feature info returned by `getFeatureInfo()`.
   * @param {number} triangle Triangle index from a raycast hit.
   * @param {Vector3} barycoord Barycentric coordinate of the hit point.
   * @returns {Array<number|null>}
   */
  getFeatures(e, t) {
    const { geometry: s, textures: i, featureIds: n } = this, r = new Array(n.length).fill(null), o = n.length;
    ge.increaseSizeTo(o);
    const a = An(s, e), l = a[wo(t)];
    for (let d = 0, p = n.length; d < p; d++) {
      const m = n[d], f = "nullFeatureId" in m ? m.nullFeatureId : null;
      if ("texture" in m) {
        const g = i[m.texture.index];
        Ln(s, m.texture.texCoord, t, a, Ci), En(Ci, g.image.width, g.image.height, Ai), Li.set(d, 0), ge.renderPixelToTarget(i[m.texture.index], Ai, Li);
      } else if ("attribute" in m) {
        const y = s.getAttribute(`_feature_id_${m.attribute}`).getX(l);
        y !== f && (r[d] = y);
      } else {
        const g = l;
        g !== f && (r[d] = g);
      }
    }
    const c = new Uint8Array(o * 4);
    if (this._asyncRead)
      return ge.readDataAsync(c).then(() => (u(), r));
    return ge.readData(c), u(), r;
    function u() {
      const d = new Uint32Array(1);
      for (let p = 0, m = n.length; p < m; p++) {
        const f = n[p], g = "nullFeatureId" in f ? f.nullFeatureId : null;
        if ("texture" in f) {
          const { channels: y } = f.texture, x = y.map((b) => c[4 * p + b]);
          new Uint8Array(d.buffer).set(x);
          const _ = d[0];
          _ !== g && (r[p] = _);
        }
      }
    }
  }
  /**
   * Disposes all textures used by this instance.
   */
  dispose() {
    this.textures.forEach((e) => {
      e && (e.dispose(), e.image instanceof ImageBitmap && e.image.close());
    });
  }
}
const Ot = "EXT_mesh_features";
function Ei(h, e, t) {
  h.traverse((s) => {
    var i;
    if (e.associations.has(s)) {
      const { meshes: n, primitives: r } = e.associations.get(s), o = (i = e.json.meshes[n]) == null ? void 0 : i.primitives[r];
      o && o.extensions && o.extensions[Ot] && t(s, o.extensions[Ot]);
    }
  });
}
class Mo {
  constructor(e) {
    this.parser = e, this.name = Ot;
  }
  async afterRoot({ scene: e, parser: t }) {
    var o;
    const s = t.json.extensionsUsed;
    if (!s || !s.includes(Ot))
      return;
    const i = ((o = t.json.textures) == null ? void 0 : o.length) || 0, n = new Array(i).fill(null);
    Ei(e, t, (a, { featureIds: l }) => {
      l.forEach((c) => {
        if (c.texture && n[c.texture.index] === null) {
          const u = c.texture.index;
          n[u] = t.loadTexture(u);
        }
      });
    });
    const r = await Promise.all(n);
    Ei(e, t, (a, l) => {
      a.userData.meshFeatures = new So(a.geometry, r, l);
    });
  }
}
class Co {
  constructor() {
    this.name = "CESIUM_RTC";
  }
  afterRoot(e) {
    if (e.parser.json.extensions && e.parser.json.extensions.CESIUM_RTC) {
      const { center: t } = e.parser.json.extensions.CESIUM_RTC;
      t && (e.scene.position.x += t[0], e.scene.position.y += t[1], e.scene.position.z += t[2]);
    }
  }
}
class ul {
  constructor(e) {
    e = {
      metadata: !0,
      rtc: !0,
      plugins: [],
      dracoLoader: null,
      ktxLoader: null,
      meshoptDecoder: null,
      autoDispose: !0,
      ...e
    }, this.tiles = null, this.metadata = e.metadata, this.rtc = e.rtc, this.plugins = e.plugins, this.dracoLoader = e.dracoLoader, this.ktxLoader = e.ktxLoader, this.meshoptDecoder = e.meshoptDecoder, this._gltfRegex = /\.(gltf|glb)$/g, this._dracoRegex = /\.drc$/g, this._loader = null;
  }
  init(e) {
    const t = new Sr(e.manager);
    this.dracoLoader && (t.setDRACOLoader(this.dracoLoader), e.manager.addHandler(this._dracoRegex, this.dracoLoader)), this.ktxLoader && t.setKTX2Loader(this.ktxLoader), this.meshoptDecoder && t.setMeshoptDecoder(this.meshoptDecoder), this.rtc && t.register(() => new Co()), this.metadata && (t.register(() => new vo()), t.register(() => new Mo())), this.plugins.forEach((s) => t.register(s)), e.manager.addHandler(this._gltfRegex, t), this.tiles = e, this._loader = t;
  }
  dispose() {
    this.tiles.manager.removeHandler(this._gltfRegex), this.tiles.manager.removeHandler(this._dracoRegex), this.autoDispose && (this.ktxLoader.dispose(), this.dracoLoader.dispose());
  }
}
const vt = /* @__PURE__ */ new Te();
class dl {
  constructor(e) {
    e = {
      up: "+z",
      recenter: !0,
      lat: null,
      lon: null,
      height: 0,
      azimuth: 0,
      elevation: 0,
      roll: 0,
      ...e
    }, this.tiles = null, this.up = e.up.toLowerCase().replace(/\s+/, ""), this.lat = e.lat, this.lon = e.lon, this.height = e.height, this.azimuth = e.azimuth, this.elevation = e.elevation, this.roll = e.roll, this.recenter = e.recenter, this._callback = null;
  }
  init(e) {
    this.tiles = e, this._callback = () => {
      const { up: t, lat: s, lon: i, height: n, azimuth: r, elevation: o, roll: a, recenter: l } = this;
      if (s !== null && i !== null)
        this.transformLatLonHeightToOrigin(s, i, n, r, o, a);
      else {
        const { ellipsoid: c } = e, u = Math.min(...c.radius);
        if (e.getBoundingSphere(vt), vt.center.length() > u * 0.5) {
          const d = {};
          c.getPositionToCartographic(vt.center, d), this.transformLatLonHeightToOrigin(d.lat, d.lon, d.height);
        } else {
          const d = e.group;
          switch (d.rotation.set(0, 0, 0), t) {
            case "x":
            case "+x":
              d.rotation.z = Math.PI / 2;
              break;
            case "-x":
              d.rotation.z = -Math.PI / 2;
              break;
            case "y":
            case "+y":
              break;
            case "-y":
              d.rotation.z = Math.PI;
              break;
            case "z":
            case "+z":
              d.rotation.x = -Math.PI / 2;
              break;
            case "-z":
              d.rotation.x = Math.PI / 2;
              break;
          }
          e.group.position.copy(vt.center).applyEuler(d.rotation).multiplyScalar(-1);
        }
      }
      l || e.group.position.setScalar(0), e.removeEventListener("load-root-tileset", this._callback);
    }, e.addEventListener("load-root-tileset", this._callback), e.root && this._callback();
  }
  /**
   * Centers the tileset such that the given coordinates are positioned at the origin
   * with X facing west and Z facing north.
   * @param {number} lat Latitude in radians.
   * @param {number} lon Longitude in radians.
   * @param {number} [height=0] Height in metres above the ellipsoid surface.
   * @param {number} [azimuth=0] Azimuth rotation in radians.
   * @param {number} [elevation=0] Elevation rotation in radians.
   * @param {number} [roll=0] Roll rotation in radians.
   */
  transformLatLonHeightToOrigin(e, t, s = 0, i = 0, n = 0, r = 0) {
    const { group: o, ellipsoid: a } = this.tiles;
    a.getObjectFrame(e, t, s, i, n, r, o.matrix, vr), o.matrix.invert().decompose(o.position, o.quaternion, o.scale), o.updateMatrixWorld();
  }
  dispose() {
    const { group: e } = this.tiles;
    e.position.setScalar(0), e.quaternion.identity(), e.scale.set(1, 1, 1), this.tiles.removeEventListener("load-root-tileset", this._callback);
  }
}
class fl {
  set delay(e) {
    this.deferCallbacks.delay = e;
  }
  get delay() {
    return this.deferCallbacks.delay;
  }
  set bytesTarget(e) {
    this.lruCache.minBytesSize = e;
  }
  get bytesTarget() {
    return this.lruCache.minBytesSize;
  }
  /**
   * The number of bytes currently uploaded to the GPU for rendering. Compare to
   * `lruCache.cachedBytes` which reports all downloaded bytes including those not
   * yet on the GPU.
   * @type {number}
   */
  get estimatedGpuBytes() {
    return this.lruCache.cachedBytes;
  }
  constructor(e = {}) {
    const {
      delay: t = 0,
      bytesTarget: s = 0
    } = e;
    this.name = "UNLOAD_TILES_PLUGIN", this.tiles = null, this.lruCache = new Ar(), this.deferCallbacks = new Ao(), this.delay = t, this.bytesTarget = s;
  }
  init(e) {
    this.tiles = e;
    const { lruCache: t, deferCallbacks: s } = this, i = (n) => {
      const r = n.engineData.scene;
      e.visibleTiles.has(n) || e.invokeOnePlugin((a) => a.unloadTileFromGPU && a.unloadTileFromGPU(r, n));
    };
    this._onUpdateBefore = () => {
      t.unloadPriorityCallback = e.lruCache.unloadPriorityCallback, t.minSize = 1 / 0, t.maxSize = 1 / 0, t.maxBytesSize = 1 / 0, t.unloadPercent = 1, t.autoMarkUnused = !1;
    }, this._onVisibilityChangeCallback = ({ tile: n, scene: r, visible: o }) => {
      o ? (t.add(n, i), t.setMemoryUsage(n, e.calculateBytesUsed(n, r) || 1), e.markTileUsed(n), s.cancel(n)) : s.run(n);
    }, this._onDisposeModel = ({ tile: n }) => {
      t.remove(n), s.cancel(n);
    }, s.callback = (n) => {
      t.markUnused(n), t.scheduleUnload();
    }, e.forEachLoadedModel((n, r) => {
      const o = e.visibleTiles.has(r);
      this._onVisibilityChangeCallback({ tile: r, visible: o });
    }), e.addEventListener("tile-visibility-change", this._onVisibilityChangeCallback), e.addEventListener("update-before", this._onUpdateBefore), e.addEventListener("dispose-model", this._onDisposeModel);
  }
  unloadTileFromGPU(e, t) {
    e && e.traverse((s) => {
      if (s.material) {
        const i = s.material;
        i.dispose();
        for (const n in i) {
          const r = i[n];
          r && r.isTexture && r.dispose();
        }
      }
      s.geometry && s.geometry.dispose();
    });
  }
  dispose() {
    const { lruCache: e, tiles: t, deferCallbacks: s } = this;
    t.removeEventListener("tile-visibility-change", this._onVisibilityChangeCallback), t.removeEventListener("update-before", this._onUpdateBefore), t.removeEventListener("dispose-model", this._onDisposeModel), s.cancelAll(), e.minBytesSize = 0, e.minSize = 0, e.maxSize = 0, e.markAllUnused(), e.scheduleUnload();
  }
}
class Ao {
  constructor(e = () => {
  }) {
    this.map = /* @__PURE__ */ new Map(), this.callback = e, this.delay = 0;
  }
  run(e) {
    const { map: t, delay: s } = this;
    if (t.has(e))
      throw new Error("DeferCallbackManager: Callback already initialized.");
    s === 0 ? this.callback(e) : t.set(e, setTimeout(() => {
      this.callback(e), t.delete(e);
    }, s));
  }
  cancel(e) {
    const { map: t } = this;
    t.has(e) && (clearTimeout(t.get(e)), t.delete(e));
  }
  cancelAll() {
    this.map.forEach((e, t) => {
      this.cancel(t);
    });
  }
}
const { clamp: rs } = w;
class Lo {
  constructor() {
    this.duration = 250, this.fadeCount = 0, this._lastTick = -1, this._fadeState = /* @__PURE__ */ new Map(), this.onFadeComplete = null, this.onFadeStart = null, this.onFadeSetComplete = null, this.onFadeSetStart = null;
  }
  // delete the object from the fade, reset the material data
  deleteObject(e) {
    e && this.completeFade(e);
  }
  // Ensure we're storing a fade timer for the provided object
  // Returns whether a new state had to be added
  guaranteeState(e) {
    const t = this._fadeState;
    if (t.has(e))
      return !1;
    const s = {
      fadeInTarget: 0,
      fadeOutTarget: 0,
      fadeIn: 0,
      fadeOut: 0
    };
    return t.set(e, s), !0;
  }
  // Force the fade to complete in the direction it is already trending
  completeFade(e) {
    const t = this._fadeState;
    if (!t.has(e))
      return;
    const s = t.get(e).fadeOutTarget === 0;
    t.delete(e), this.fadeCount--, this.onFadeComplete && this.onFadeComplete(e, s), this.fadeCount === 0 && this.onFadeSetComplete && this.onFadeSetComplete();
  }
  completeAllFades() {
    this._fadeState.forEach((e, t) => {
      this.completeFade(t);
    });
  }
  forEachObject(e) {
    this._fadeState.forEach((t, s) => {
      e(s, t);
    });
  }
  // Fade the object in
  fadeIn(e) {
    const t = this.guaranteeState(e), s = this._fadeState.get(e);
    s.fadeInTarget = 1, s.fadeOutTarget = 0, s.fadeOut = 0, t && (this.fadeCount++, this.fadeCount === 1 && this.onFadeSetStart && this.onFadeSetStart(), this.onFadeStart && this.onFadeStart(e));
  }
  // Fade the object out
  fadeOut(e) {
    const t = this.guaranteeState(e), s = this._fadeState.get(e);
    s.fadeOutTarget = 1, t && (s.fadeInTarget = 1, s.fadeIn = 1, this.fadeCount++, this.fadeCount === 1 && this.onFadeSetStart && this.onFadeSetStart(), this.onFadeStart && this.onFadeStart(e));
  }
  isFading(e) {
    return this._fadeState.has(e);
  }
  isFadingOut(e) {
    const t = this._fadeState.get(e);
    return t && t.fadeOutTarget === 1;
  }
  // Tick the fade timer for each actively fading object
  update() {
    const e = window.performance.now();
    this._lastTick === -1 && (this._lastTick = e);
    const t = rs((e - this._lastTick) / this.duration, 0, 1);
    this._lastTick = e, this._fadeState.forEach((i, n) => {
      const {
        fadeOutTarget: r,
        fadeInTarget: o
      } = i;
      let {
        fadeOut: a,
        fadeIn: l
      } = i;
      const c = Math.sign(o - l);
      l = rs(l + c * t, 0, 1);
      const u = Math.sign(r - a);
      a = rs(a + u * t, 0, 1), i.fadeIn = l, i.fadeOut = a, ((a === 1 || a === 0) && (l === 1 || l === 0) || a >= l) && this.completeFade(n);
    });
  }
}
const os = Symbol("FADE_PARAMS");
function In(h, e) {
  if (h[os])
    return h[os];
  const t = {
    fadeIn: { value: 0 },
    fadeOut: { value: 0 },
    fadeTexture: { value: null }
  };
  return h[os] = t, h.defines = {
    ...h.defines || {},
    FEATURE_FADE: 0
  }, h.onBeforeCompile = (s) => {
    e && e(s), s.uniforms = {
      ...s.uniforms,
      ...t
    }, s.vertexShader = s.vertexShader.replace(
      /void\s+main\(\)\s+{/,
      (i) => (
        /* glsl */
        `
					#ifdef USE_BATCHING_FRAG

					varying float vBatchId;

					#endif

					${i}

						#ifdef USE_BATCHING_FRAG

						// add 0.5 to the value to avoid floating error that may cause flickering
						vBatchId = getIndirectIndex( gl_DrawID ) + 0.5;

						#endif
				`
      )
    ), s.fragmentShader = s.fragmentShader.replace(/void main\(/, (i) => (
      /* glsl */
      `
				#if FEATURE_FADE

				// adapted from https://www.shadertoy.com/view/Mlt3z8
				float bayerDither2x2( vec2 v ) {

					return mod( 3.0 * v.y + 2.0 * v.x, 4.0 );

				}

				float bayerDither4x4( vec2 v ) {

					vec2 P1 = mod( v, 2.0 );
					vec2 P2 = floor( 0.5 * mod( v, 4.0 ) );
					return 4.0 * bayerDither2x2( P1 ) + bayerDither2x2( P2 );

				}

				// the USE_BATCHING define is not available in fragment shaders
				#ifdef USE_BATCHING_FRAG

				// functions for reading the fade state of a given batch id
				uniform sampler2D fadeTexture;
				varying float vBatchId;
				vec2 getFadeValues( const in float i ) {

					int size = textureSize( fadeTexture, 0 ).x;
					int j = int( i );
					int x = j % size;
					int y = j / size;
					return texelFetch( fadeTexture, ivec2( x, y ), 0 ).rg;

				}

				#else

				uniform float fadeIn;
				uniform float fadeOut;

				#endif

				#endif

				${i}
			`
    )).replace(/#include <dithering_fragment>/, (i) => (
      /* glsl */
      `

				${i}

				#if FEATURE_FADE

				#ifdef USE_BATCHING_FRAG

				vec2 fadeValues = getFadeValues( vBatchId );
				float fadeIn = fadeValues.r;
				float fadeOut = fadeValues.g;

				#endif

				float bayerValue = bayerDither4x4( floor( mod( gl_FragCoord.xy, 4.0 ) ) );
				float bayerBins = 16.0;
				float dither = ( 0.5 + bayerValue ) / bayerBins;
				if ( dither >= fadeIn ) {

					discard;

				}

				if ( dither < fadeOut ) {

					discard;

				}

				#endif

			`
    ));
  }, t;
}
class Eo {
  constructor() {
    this._fadeParams = /* @__PURE__ */ new WeakMap(), this.fading = 0;
  }
  // Set the fade parameters for the given scene
  setFade(e, t, s) {
    if (!e)
      return;
    const i = this._fadeParams;
    e.traverse((n) => {
      const r = n.material;
      if (r && i.has(r)) {
        const o = i.get(r);
        o.fadeIn.value = t, o.fadeOut.value = s;
        const c = +(!(t === 0 || t === 1) || !(s === 0 || s === 1));
        r.defines.FEATURE_FADE !== c && (this.fading += c === 1 ? 1 : -1, r.defines.FEATURE_FADE = c, r.needsUpdate = !0);
      }
    });
  }
  // initialize materials in the object
  prepareScene(e) {
    e.traverse((t) => {
      t.material && this.prepareMaterial(t.material);
    });
  }
  // delete the object from the fade, reset the material data
  deleteScene(e) {
    if (!e)
      return;
    this.setFade(e, 1, 0);
    const t = this._fadeParams;
    e.traverse((s) => {
      const i = s.material;
      i && t.delete(i);
    });
  }
  // initialize the material
  prepareMaterial(e) {
    const t = this._fadeParams;
    t.has(e) || t.set(e, In(e, e.onBeforeCompile));
  }
}
class Io {
  constructor(e, t = new xe()) {
    this.other = e, this.material = t, this.visible = !0, this.parent = null, this._instanceInfo = [], this._visibilityChanged = !0;
    const s = new Proxy(this, {
      get(i, n) {
        if (n in i)
          return i[n];
        {
          const r = e[n];
          return r instanceof Function ? (...o) => (i.syncInstances(), r.call(s, ...o)) : e[n];
        }
      },
      set(i, n, r) {
        return n in i ? i[n] = r : e[n] = r, !0;
      },
      deleteProperty(i, n) {
        return n in i ? delete i[n] : delete e[n];
      }
      // ownKeys() {},
      // has(target, key) {},
      // defineProperty(target, key, descriptor) {},
      // getOwnPropertyDescriptor(target, key) {},
    });
    return s;
  }
  syncInstances() {
    const e = this._instanceInfo, t = this.other._instanceInfo;
    for (; t.length > e.length; ) {
      const s = e.length;
      e.push(new Proxy({ visible: !1 }, {
        get(i, n) {
          return n in i ? i[n] : t[s][n];
        },
        set(i, n, r) {
          return n in i ? i[n] = r : t[s][n] = r, !0;
        }
      }));
    }
  }
}
class Po extends Io {
  constructor(...e) {
    super(...e);
    const t = this.material, s = In(t, t.onBeforeCompile);
    t.defines.FEATURE_FADE = 1, t.defines.USE_BATCHING_FRAG = 1, t.needsUpdate = !0, this.fadeTexture = null, this._fadeParams = s;
  }
  // Set the fade state
  setFadeAt(e, t, s) {
    this._initFadeTexture(), this.fadeTexture.setValueAt(e, t * 255, s * 255);
  }
  // initialize the texture and resize it if needed
  _initFadeTexture() {
    let e = Math.sqrt(this._maxInstanceCount);
    e = Math.ceil(e);
    const t = e * e * 2, s = this.fadeTexture;
    if (!s || s.image.data.length !== t) {
      const i = new Uint8Array(t), n = new Ro(i, e, e, cn, hn);
      if (s) {
        s.dispose();
        const r = s.image.data, o = this.fadeTexture.image.data, a = Math.min(r.length, o.length);
        o.set(new r.constructor(r.buffer, 0, a));
      }
      this.fadeTexture = n, this._fadeParams.fadeTexture.value = n, n.needsUpdate = !0;
    }
  }
  // dispose the fade texture. Super cannot be used here due to proxy
  dispose() {
    this.fadeTexture && this.fadeTexture.dispose();
  }
}
class Ro extends zt {
  setValueAt(e, ...t) {
    const { data: s, width: i, height: n } = this.image, r = Math.floor(s.length / (i * n));
    let o = !1;
    for (let a = 0; a < r; a++) {
      const l = e * r + a, c = s[l], u = t[a] || 0;
      c !== u && (s[l] = u, o = !0);
    }
    o && (this.needsUpdate = !0);
  }
}
const Ii = Symbol("HAS_POPPED_IN");
function Do(h) {
  let e = h;
  for (; e; ) {
    if (e.traversal.wasSetActive)
      return e.traversal.wasInFrustum;
    e = e.parent;
  }
  return !1;
}
const Pi = /* @__PURE__ */ new C(), Ri = /* @__PURE__ */ new C(), Di = /* @__PURE__ */ new dn(), Bi = /* @__PURE__ */ new dn(), Ui = /* @__PURE__ */ new C();
function Bo() {
  const h = this._fadeManager, e = this._fadeMaterialManager, t = this._fadingBefore, s = this._prevCameraTransforms, { tiles: i, maximumFadeOutTiles: n, batchedMesh: r } = this, { cameras: o } = i;
  h.update();
  const a = h.fadeCount;
  if (t !== 0 && a !== 0 && (i.dispatchEvent({ type: "fade-change" }), i.dispatchEvent({ type: "needs-render" })), n < this._fadingOutCount) {
    let l = !0;
    o.forEach((c) => {
      if (!s.has(c))
        return;
      const u = c.matrixWorld, d = s.get(c);
      u.decompose(Ri, Bi, Ui), d.decompose(Pi, Di, Ui);
      const p = Bi.angleTo(Di), m = Ri.distanceTo(Pi);
      l = l && (p > 0.25 || m > 0.1);
    }), l && h.completeAllFades();
  }
  if (o.forEach((l) => {
    s.get(l).copy(l.matrixWorld);
  }), h.forEachObject((l, { fadeIn: c, fadeOut: u }) => {
    const d = l.engineData.scene;
    i.markTileUsed(l), d && e.setFade(d, c, u), this.forEachBatchIds(l, (p, m, f) => {
      m.setFadeAt(p, c, u), m.setVisibleAt(p, !0), f.batchedMesh.setVisibleAt(p, !1);
    });
  }), r) {
    const l = i.getPluginByName("BATCHED_TILES_PLUGIN").batchedMesh.material;
    r.material.map = l.map;
  }
}
class pl {
  get fadeDuration() {
    return this._fadeManager.duration;
  }
  set fadeDuration(e) {
    this._fadeManager.duration = Number(e);
  }
  get fadingTiles() {
    return this._fadeManager.fadeCount;
  }
  constructor(e) {
    e = {
      maximumFadeOutTiles: 50,
      fadeRootTiles: !1,
      fadeDuration: 250,
      ...e
    }, this.name = "FADE_TILES_PLUGIN", this.priority = -2, this.tiles = null, this.batchedMesh = null, this._quickFadeTiles = /* @__PURE__ */ new Set(), this._fadeManager = new Lo(), this._fadeMaterialManager = new Eo(), this._prevCameraTransforms = null, this._fadingOutCount = 0, this.maximumFadeOutTiles = e.maximumFadeOutTiles, this.fadeRootTiles = e.fadeRootTiles, this.fadeDuration = e.fadeDuration;
  }
  init(e) {
    this._onLoadModel = ({ scene: i }) => {
      this._fadeMaterialManager.prepareScene(i);
    }, this._onDisposeModel = ({ tile: i, scene: n }) => {
      this.tiles.visibleTiles.has(i) && this._quickFadeTiles.add(i.parent), this._fadeManager.deleteObject(i), this._fadeMaterialManager.deleteScene(n);
    }, this._onAddCamera = ({ camera: i }) => {
      this._prevCameraTransforms.set(i, new Y());
    }, this._onDeleteCamera = ({ camera: i }) => {
      this._prevCameraTransforms.delete(i);
    }, this._onTileVisibilityChange = ({ tile: i }) => {
      this.forEachBatchIds(i, (n, r, o) => {
        r.setFadeAt(n, 0, 0), r.setVisibleAt(n, !1), o.batchedMesh.setVisibleAt(n, !1);
      });
    }, this._onUpdateBefore = () => {
      this._fadingBefore = this._fadeManager.fadeCount;
    }, this._onUpdateAfter = () => {
      Bo.call(this);
    }, e.addEventListener("load-model", this._onLoadModel), e.addEventListener("dispose-model", this._onDisposeModel), e.addEventListener("add-camera", this._onAddCamera), e.addEventListener("delete-camera", this._onDeleteCamera), e.addEventListener("update-before", this._onUpdateBefore), e.addEventListener("update-after", this._onUpdateAfter), e.addEventListener("tile-visibility-change", this._onTileVisibilityChange);
    const t = this._fadeManager;
    t.onFadeSetStart = () => {
      e.dispatchEvent({ type: "fade-start" }), e.dispatchEvent({ type: "needs-render" });
    }, t.onFadeSetComplete = () => {
      e.dispatchEvent({ type: "fade-end" }), e.dispatchEvent({ type: "needs-render" });
    }, t.onFadeComplete = (i, n) => {
      this._fadeMaterialManager.setFade(i.engineData.scene, 0, 0), this.forEachBatchIds(i, (r, o, a) => {
        o.setFadeAt(r, 0, 0), o.setVisibleAt(r, !1), a.batchedMesh.setVisibleAt(r, n);
      }), n || (e.invokeOnePlugin((r) => r !== this && r.setTileVisible && r.setTileVisible(i, !1)), this._fadingOutCount--);
    };
    const s = /* @__PURE__ */ new Map();
    e.cameras.forEach((i) => {
      s.set(i, new Y());
    }), e.forEachLoadedModel((i, n) => {
      this._onLoadModel({ scene: i });
    }), this.tiles = e, this._fadeManager = t, this._prevCameraTransforms = s;
  }
  // initializes the batched mesh if it needs to be, dispose if it it's no longer needed
  initBatchedMesh() {
    var t;
    const e = (t = this.tiles.getPluginByName("BATCHED_TILES_PLUGIN")) == null ? void 0 : t.batchedMesh;
    if (e) {
      if (this.batchedMesh === null) {
        this._onBatchedMeshDispose = () => {
          this.batchedMesh.dispose(), this.batchedMesh.removeFromParent(), this.batchedMesh = null, e.removeEventListener("dispose", this._onBatchedMeshDispose);
        };
        const s = e.material.clone();
        s.onBeforeCompile = e.material.onBeforeCompile, this.batchedMesh = new Po(e, s), this.tiles.group.add(this.batchedMesh);
      }
    } else
      this.batchedMesh !== null && (this._onBatchedMeshDispose(), this._onBatchedMeshDispose = null);
  }
  // callback for fading to prevent tiles from being removed until the fade effect has completed
  setTileVisible(e, t) {
    const s = this._fadeManager, i = s.isFading(e);
    if (!Do(e))
      return i && s.completeFade(e), !1;
    if (s.isFadingOut(e) && this._fadingOutCount--, t ? e.internal.depthFromRenderedParent === 1 ? ((e[Ii] || this.fadeRootTiles) && this._fadeManager.fadeIn(e), e[Ii] = !0) : this._fadeManager.fadeIn(e) : (this._fadingOutCount++, s.fadeOut(e)), this._quickFadeTiles.has(e) && (this._fadeManager.completeFade(e), this._quickFadeTiles.delete(e)), i)
      return !0;
    const n = this._fadeManager.isFading(e);
    return !!(!t && n);
  }
  dispose() {
    const e = this.tiles;
    this._fadeManager.completeAllFades(), this.batchedMesh !== null && this._onBatchedMeshDispose(), e.removeEventListener("load-model", this._onLoadModel), e.removeEventListener("dispose-model", this._onDisposeModel), e.removeEventListener("add-camera", this._onAddCamera), e.removeEventListener("delete-camera", this._onDeleteCamera), e.removeEventListener("update-before", this._onUpdateBefore), e.removeEventListener("update-after", this._onUpdateAfter), e.removeEventListener("tile-visibility-change", this._onTileVisibilityChange), e.forEachLoadedModel((t, s) => {
      this._fadeManager.deleteObject(s);
    });
  }
  // helper for iterating over the batch ids for a given tile
  forEachBatchIds(e, t) {
    if (this.initBatchedMesh(), this.batchedMesh) {
      const s = this.tiles.getPluginByName("BATCHED_TILES_PLUGIN"), i = s.getTileBatchIds(e);
      i && i.forEach((n) => {
        t(n, this.batchedMesh, s);
      });
    }
  }
}
const as = /* @__PURE__ */ new Y(), Oi = /* @__PURE__ */ new C(), Vi = /* @__PURE__ */ new C();
class Uo extends hr {
  constructor(...e) {
    super(...e), this.resetDistance = 1e4, this._matricesTextureHandle = null, this._lastCameraPos = new Y(), this._forceUpdate = !0, this._matrices = [];
  }
  setMatrixAt(e, t) {
    super.setMatrixAt(e, t), this._forceUpdate = !0;
    const s = this._matrices;
    for (; s.length <= e; )
      s.push(new Y());
    s[e].copy(t);
  }
  setInstanceCount(...e) {
    super.setInstanceCount(...e);
    const t = this._matrices;
    for (; t.length > this.instanceCount; )
      t.pop();
  }
  onBeforeRender(e, t, s, i, n, r) {
    super.onBeforeRender(e, t, s, i, n, r), Oi.setFromMatrixPosition(s.matrixWorld), Vi.setFromMatrixPosition(this._lastCameraPos);
    const o = this._matricesTexture;
    let a = this._modelViewMatricesTexture;
    if ((!a || a.image.width !== o.image.width || a.image.height !== o.image.height) && (a && a.dispose(), a = o.clone(), a.source = new ur({
      ...a.image,
      data: a.image.data.slice()
    }), this._modelViewMatricesTexture = a), this._forceUpdate || Oi.distanceTo(Vi) > this.resetDistance) {
      const l = this._matrices, c = a.image.data;
      for (let u = 0; u < this.maxInstanceCount; u++) {
        const d = l[u];
        d ? as.copy(d) : as.identity(), as.premultiply(this.matrixWorld).premultiply(s.matrixWorldInverse).toArray(c, u * 16);
      }
      a.needsUpdate = !0, this._lastCameraPos.copy(s.matrixWorld), this._forceUpdate = !1;
    }
    this._matricesTextureHandle = this._matricesTexture, this._matricesTexture = this._modelViewMatricesTexture, this.matrixWorld.copy(this._lastCameraPos);
  }
  onAfterRender() {
    this.updateMatrixWorld(), this._matricesTexture = this._matricesTextureHandle, this._matricesTextureHandle = null;
  }
  onAfterShadow(e, t, s, i, n, r) {
    this.onAfterRender(e, null, i, n, r);
  }
  dispose() {
    super.dispose(), this._modelViewMatricesTexture && this._modelViewMatricesTexture.dispose();
  }
}
const te = /* @__PURE__ */ new _e(), wt = [];
class Oo extends Uo {
  constructor(...e) {
    super(...e), this.expandPercent = 0.25, this.maxInstanceExpansionSize = 1 / 0, this._freeGeometryIds = [];
  }
  // Finds a free id that can fit the geometry with the requested ranges. Returns -1 if it could not be found.
  findFreeId(e, t, s) {
    const i = !!this.geometry.index, n = Math.max(i ? e.index.count : -1, s), r = Math.max(e.attributes.position.count, t);
    let o = -1, a = 1 / 0;
    const l = this._freeGeometryIds;
    if (l.forEach((c, u) => {
      const d = this.getGeometryRangeAt(c), { reservedIndexCount: p, reservedVertexCount: m } = d;
      if (p >= n && m >= r) {
        const f = n - p + (r - m);
        f < a && (o = u, a = f);
      }
    }), o !== -1) {
      const c = l[o];
      return l.splice(o, 1), c;
    } else
      return -1;
  }
  // Overrides addGeometry to find an option geometry slot, expand, or optimized if needed
  addGeometry(e, t, s) {
    const i = !!this.geometry.index;
    s = Math.max(i ? e.index.count : -1, s), t = Math.max(e.attributes.position.count, t);
    const { expandPercent: n, _freeGeometryIds: r } = this;
    let o = this.findFreeId(e, t, s);
    if (o !== -1)
      this.setGeometryAt(o, e);
    else {
      const a = () => {
        const u = this.unusedVertexCount < t, d = this.unusedIndexCount < s;
        return u || d;
      }, l = e.index, c = e.attributes.position;
      if (t = Math.max(t, c.count), s = Math.max(s, l ? l.count : 0), a() && (r.forEach((u) => this.deleteGeometry(u)), r.length = 0, this.optimize(), a())) {
        const u = this.geometry.index, d = this.geometry.attributes.position;
        let p, m;
        if (u) {
          const f = Math.ceil(n * u.count);
          p = Math.max(f, s, l.count) + u.count;
        } else
          p = Math.max(this.unusedIndexCount, s);
        if (d) {
          const f = Math.ceil(n * d.count);
          m = Math.max(f, t, c.count) + d.count;
        } else
          m = Math.max(this.unusedVertexCount, t);
        this.setGeometrySize(m, p);
      }
      o = super.addGeometry(e, t, s);
    }
    return o;
  }
  // add an instance and automatically expand the number of instances if necessary
  addInstance(e) {
    if (this.maxInstanceCount === this.instanceCount) {
      const t = Math.ceil(this.maxInstanceCount * (1 + this.expandPercent));
      this.setInstanceCount(Math.min(t, this.maxInstanceExpansionSize));
    }
    return super.addInstance(e);
  }
  // delete an instance, keeping note that the geometry id is now unused
  deleteInstance(e) {
    const t = this.getGeometryIdAt(e);
    return t !== -1 && this._freeGeometryIds.push(t), super.deleteInstance(e);
  }
  // add a function for raycasting per tile
  raycastInstance(e, t, s) {
    const i = this.geometry, n = this.getGeometryIdAt(e);
    te.material = this.material, te.geometry.index = i.index, te.geometry.attributes = i.attributes;
    const r = this.getGeometryRangeAt(n);
    te.geometry.setDrawRange(r.start, r.count), te.geometry.boundingBox === null && (te.geometry.boundingBox = new Ft()), te.geometry.boundingSphere === null && (te.geometry.boundingSphere = new Te()), this.getMatrixAt(e, te.matrixWorld).premultiply(this.matrixWorld), this.getBoundingBoxAt(n, te.geometry.boundingBox), this.getBoundingSphereAt(n, te.geometry.boundingSphere), te.raycast(t, wt);
    for (let o = 0, a = wt.length; o < a; o++) {
      const l = wt[o];
      l.object = this, l.batchId = e, s.push(l);
    }
    wt.length = 0;
  }
}
function Vo(h) {
  return h.r === 1 && h.g === 1 && h.b === 1;
}
function ko(h) {
  h.needsUpdate = !0, h.onBeforeCompile = (e) => {
    e.vertexShader = e.vertexShader.replace(
      "#include <common>",
      /* glsl */
      `
				#include <common>
				varying float texture_index;
				`
    ).replace(
      "#include <uv_vertex>",
      /* glsl */
      `
				#include <uv_vertex>
				texture_index = getIndirectIndex( gl_DrawID );
				`
    ), e.fragmentShader = e.fragmentShader.replace(
      "#include <map_pars_fragment>",
      /* glsl */
      `
				#ifdef USE_MAP
				precision highp sampler2DArray;
				uniform sampler2DArray map;
				varying float texture_index;
				#endif
				`
    ).replace(
      "#include <map_fragment>",
      /* glsl */
      `
				#ifdef USE_MAP
					diffuseColor *= texture( map, vec3( vMapUv, texture_index ) );
				#endif
				`
    );
  };
}
const ls = new yn(new xe()), Is = new zt(new Uint8Array([255, 255, 255, 255]), 1, 1);
Is.needsUpdate = !0;
class ml {
  constructor(e = {}) {
    if (parseInt(dr) < 170)
      throw new Error("BatchedTilesPlugin: Three.js revision 170 or higher required.");
    e = {
      instanceCount: 500,
      vertexCount: 750,
      indexCount: 2e3,
      expandPercent: 0.25,
      maxInstanceCount: 1 / 0,
      discardOriginalContent: !0,
      textureSize: null,
      material: null,
      renderer: null,
      ...e
    }, this.name = "BATCHED_TILES_PLUGIN", this.priority = -1;
    const t = e.renderer.getContext();
    this.instanceCount = e.instanceCount, this.vertexCount = e.vertexCount, this.indexCount = e.indexCount, this.material = e.material ? e.material.clone() : null, this.expandPercent = e.expandPercent, this.maxInstanceCount = Math.min(e.maxInstanceCount, t.getParameter(t.MAX_3D_TEXTURE_SIZE)), this.renderer = e.renderer, this.discardOriginalContent = e.discardOriginalContent, this.textureSize = e.textureSize, this.batchedMesh = null, this.arrayTarget = null, this.tiles = null, this._tileToInstanceId = /* @__PURE__ */ new Map();
  }
  init(e) {
    this.tiles = e;
  }
  initTextureArray(e) {
    if (this.arrayTarget !== null || e.material.map === null)
      return;
    const { instanceCount: t, renderer: s, textureSize: i, batchedMesh: n } = this, r = e.material.map, o = {
      colorSpace: r.colorSpace,
      wrapS: r.wrapS,
      wrapT: r.wrapT,
      wrapR: r.wrapS,
      // TODO: Generating mipmaps for the volume every time a new texture is added is extremely slow
      // generateMipmaps: map.generateMipmaps,
      // minFilter: map.minFilter,
      magFilter: r.magFilter
    }, a = new ei(i || r.image.width, i || r.image.height, t);
    Object.assign(a.texture, o), s.initRenderTarget(a), n.material.map = a.texture, this.arrayTarget = a, this._tileToInstanceId.forEach((l) => {
      l.forEach((c) => {
        this.assignTextureToLayer(Is, c);
      });
    });
  }
  // init the batched mesh if it's not ready
  initBatchedMesh(e) {
    if (this.batchedMesh !== null)
      return;
    const { instanceCount: t, vertexCount: s, indexCount: i, tiles: n } = this, r = this.material ? this.material : new e.material.constructor(), o = new Oo(t, t * s, t * i, r);
    o.name = "BatchTilesPlugin", o.frustumCulled = !1, n.group.add(o), o.updateMatrixWorld(), ko(o.material), this.batchedMesh = o;
  }
  setTileVisible(e, t) {
    const s = e.engineData.scene;
    if (t && this.addSceneToBatchedMesh(s, e), this._tileToInstanceId.has(e)) {
      this._tileToInstanceId.get(e).forEach((r) => {
        this.batchedMesh.setVisibleAt(r, t);
      });
      const n = this.tiles;
      return t ? n.visibleTiles.add(e) : n.visibleTiles.delete(e), n.dispatchEvent({
        type: "tile-visibility-change",
        scene: s,
        tile: e,
        visible: t
      }), !0;
    }
    return !1;
  }
  disposeTile(e) {
    this.removeSceneFromBatchedMesh(e);
  }
  unloadTileFromGPU(e, t) {
    return !this.discardOriginalContent && this._tileToInstanceId.has(t) ? (this.removeSceneFromBatchedMesh(t), !0) : !1;
  }
  // render the given into the given layer
  assignTextureToLayer(e, t) {
    if (!this.arrayTarget)
      return;
    this.expandArrayTargetIfNeeded();
    const { renderer: s } = this, i = s.getRenderTarget();
    s.setRenderTarget(this.arrayTarget, t), ls.material.map = e, ls.render(s), s.setRenderTarget(i), ls.material.map = null, e.dispose();
  }
  // check if the array texture target needs to be expanded
  expandArrayTargetIfNeeded() {
    const { batchedMesh: e, arrayTarget: t, renderer: s } = this, i = Math.min(e.maxInstanceCount, this.maxInstanceCount);
    if (i > t.depth) {
      const n = {
        colorSpace: t.texture.colorSpace,
        wrapS: t.texture.wrapS,
        wrapT: t.texture.wrapT,
        generateMipmaps: t.texture.generateMipmaps,
        minFilter: t.texture.minFilter,
        magFilter: t.texture.magFilter
      }, r = new ei(t.width, t.height, i);
      Object.assign(r.texture, n), s.initRenderTarget(r), s.copyTextureToTexture(t.texture, r.texture), t.dispose(), e.material.map = r.texture, this.arrayTarget = r;
    }
  }
  removeSceneFromBatchedMesh(e) {
    if (this._tileToInstanceId.has(e)) {
      const t = this._tileToInstanceId.get(e);
      this._tileToInstanceId.delete(e), t.forEach((s) => {
        this.batchedMesh.deleteInstance(s);
      });
    }
  }
  addSceneToBatchedMesh(e, t) {
    if (this._tileToInstanceId.has(t))
      return;
    const s = [];
    e.traverse((r) => {
      r.isMesh && s.push(r);
    });
    let i = !0;
    s.forEach((r) => {
      if (this.batchedMesh && i) {
        const o = r.geometry.attributes, a = this.batchedMesh.geometry.attributes;
        for (const l in a)
          if (!(l in o)) {
            i = !1;
            return;
          }
      }
    });
    const n = !this.batchedMesh || this.batchedMesh.instanceCount + s.length <= this.maxInstanceCount;
    if (i && n) {
      e.updateMatrixWorld();
      const r = [];
      this._tileToInstanceId.set(t, r), s.forEach((o) => {
        this.initBatchedMesh(o), this.initTextureArray(o);
        const { geometry: a, material: l } = o, { batchedMesh: c, expandPercent: u } = this;
        c.expandPercent = u;
        const d = c.addGeometry(a, this.vertexCount, this.indexCount), p = c.addInstance(d);
        r.push(p), c.setMatrixAt(p, o.matrixWorld), c.setVisibleAt(p, !1), Vo(l.color) || (l.color.setHSL(Math.random(), 0.5, 0.5), c.setColorAt(p, l.color));
        const m = l.map;
        m ? this.assignTextureToLayer(m, p) : this.assignTextureToLayer(Is, p);
      }), this.discardOriginalContent && (t.engineData.textures.forEach((o) => {
        o.image instanceof ImageBitmap && o.image.close();
      }), t.engineData.scene = null, t.engineData.materials = [], t.engineData.geometries = [], t.engineData.textures = []);
    }
  }
  // Override raycasting per tile to defer to the batched mesh
  raycastTile(e, t, s, i) {
    return this._tileToInstanceId.has(e) ? (this._tileToInstanceId.get(e).forEach((r) => {
      this.batchedMesh.raycastInstance(r, s, i);
    }), !0) : !1;
  }
  dispose() {
    const { arrayTarget: e, batchedMesh: t } = this;
    e && e.dispose(), t && (t.material.dispose(), t.geometry.dispose(), t.dispose(), t.removeFromParent());
  }
  getTileBatchIds(e) {
    return this._tileToInstanceId.get(e);
  }
}
const cs = /* @__PURE__ */ new Te(), St = /* @__PURE__ */ new C(), $e = /* @__PURE__ */ new Y(), ki = /* @__PURE__ */ new Y(), hs = /* @__PURE__ */ new fn(), No = /* @__PURE__ */ new xe({ side: Pt }), Ni = /* @__PURE__ */ new Ft(), us = 1e5;
function Fi(h, e) {
  return h.isBufferGeometry ? (h.boundingSphere === null && h.computeBoundingSphere(), e.copy(h.boundingSphere)) : (Ni.setFromObject(h), Ni.getBoundingSphere(e), e);
}
class gl {
  constructor() {
    this.name = "TILE_FLATTENING_PLUGIN", this.priority = -100, this.tiles = null, this.shapes = /* @__PURE__ */ new Map(), this.positionsMap = /* @__PURE__ */ new Map(), this.positionsUpdated = /* @__PURE__ */ new Set(), this.needsUpdate = !1;
  }
  init(e) {
    this.tiles = e, this.needsUpdate = !0, this._updateBeforeCallback = () => {
      this.needsUpdate && (this._updateTiles(), this.needsUpdate = !1);
    }, this._disposeModelCallback = ({ tile: t }) => {
      this.positionsMap.delete(t), this.positionsUpdated.delete(t);
    }, e.addEventListener("update-before", this._updateBeforeCallback), e.addEventListener("dispose-model", this._disposeModelCallback);
  }
  // update tile flattening state if it has not been made visible, yet
  setTileActive(e, t) {
    t && !this.positionsUpdated.has(e) && this._updateTile(e);
  }
  _updateTile(e) {
    const { positionsUpdated: t, positionsMap: s, shapes: i, tiles: n } = this;
    t.add(e);
    const r = e.engineData.scene;
    if (s.has(e)) {
      const o = s.get(e);
      r.traverse((a) => {
        if (a.geometry) {
          const l = o.get(a.geometry);
          l && (a.geometry.attributes.position.array.set(l), a.geometry.attributes.position.needsUpdate = !0);
        }
      });
    } else {
      const o = /* @__PURE__ */ new Map();
      s.set(e, o), r.traverse((a) => {
        a.geometry && o.set(a.geometry, a.geometry.attributes.position.array.slice());
      });
    }
    r.updateMatrixWorld(!0), r.traverse((o) => {
      const { geometry: a } = o;
      a && ($e.copy(o.matrixWorld), r.parent !== null && $e.premultiply(n.group.matrixWorldInverse), ki.copy($e).invert(), Fi(a, cs).applyMatrix4($e), i.forEach(({
        shape: l,
        direction: c,
        sphere: u,
        thresholdMode: d,
        threshold: p,
        flattenRange: m
      }) => {
        St.subVectors(cs.center, u.center), St.addScaledVector(c, -c.dot(St));
        const f = (cs.radius + u.radius) ** 2;
        if (St.lengthSq() > f)
          return;
        const { position: g } = a.attributes, { ray: y } = hs;
        y.direction.copy(c).multiplyScalar(-1);
        for (let x = 0, _ = g.count; x < _; x++) {
          y.origin.fromBufferAttribute(g, x).applyMatrix4($e).addScaledVector(c, us), hs.far = us;
          const b = hs.intersectObject(l)[0];
          if (b) {
            let T = (us - b.distance) / p;
            const v = T >= 1;
            (!v || v && d === "flatten") && (T = Math.min(T, 1), b.point.addScaledVector(y.direction, w.mapLinear(T, 0, 1, -m, 0)), b.point.applyMatrix4(ki), g.setXYZ(x, ...b.point));
          }
        }
      }));
    }), this.tiles.dispatchEvent({ type: "needs-render" });
  }
  _updateTiles() {
    this.positionsUpdated.clear(), this.tiles.activeTiles.forEach((e) => this._updateTile(e));
  }
  /**
   * Returns whether the given object has already been added as a shape.
   * @param {Object3D} mesh
   * @returns {boolean}
   */
  hasShape(e) {
    return this.shapes.has(e);
  }
  /**
   * Adds the given mesh as a flattening shape. All coordinates must be in the tileset's local
   * frame. Throws if the shape has already been added.
   * @param {Object3D} mesh The shape mesh to flatten tile vertices onto.
   * @param {Vector3} [direction] Direction to cast rays when flattening (default downward along -Z).
   * @param {Object} [options]
   * @param {number} [options.threshold=Infinity] Maximum distance from the shape surface within which vertices are flattened. `Infinity` always flattens; `0` never flattens.
   */
  addShape(e, t = new C(0, 0, -1), s = {}) {
    if (this.hasShape(e))
      throw new Error("TileFlatteningPlugin: Shape is already used.");
    typeof s == "number" && (console.warn('TileFlatteningPlugin: "addShape" function signature has changed. Please use an options object, instead.'), s = {
      threshold: s
    }), this.needsUpdate = !0;
    const i = e.clone();
    i.updateMatrixWorld(!0), i.traverse((r) => {
      r.material && (r.material = No);
    });
    const n = Fi(i, new Te());
    this.shapes.set(e, {
      shape: i,
      direction: t.clone(),
      sphere: n,
      // "flatten": Flattens the vertices above the shape
      // "none": leaves the vertices above the shape as they are
      thresholdMode: "none",
      // only flatten within this range above the object
      threshold: 1 / 0,
      // the range to flatten vertices in to. 0 is completely flat
      // while 0.1 means a 10cm range.
      flattenRange: 0,
      ...s
    });
  }
  /**
   * Notifies the plugin that a shape's geometry or transform has changed and tile
   * flattening needs to be regenerated.
   * @param {Object3D} mesh
   */
  updateShape(e) {
    if (!this.hasShape(e))
      throw new Error("TileFlatteningPlugin: Shape is not present.");
    const { direction: t, threshold: s, thresholdMode: i, flattenRange: n } = this.shapes.get(e);
    this.deleteShape(e), this.addShape(e, t, {
      threshold: s,
      thresholdMode: i,
      flattenRange: n
    });
  }
  /**
   * Removes the given shape and triggers tile regeneration.
   * @param {Object3D} mesh
   * @returns {boolean} `true` if the shape was found and removed.
   */
  deleteShape(e) {
    return this.needsUpdate = !0, this.shapes.delete(e);
  }
  /**
   * Removes all shapes and resets flattened tiles to their original positions.
   */
  clearShapes() {
    this.shapes.size !== 0 && (this.needsUpdate = !0, this.shapes.clear());
  }
  // reset the vertex positions and remove the update callback
  dispose() {
    this.tiles.removeEventListener("before-update", this._updateBeforeCallback), this.tiles.removeEventListener("dispose-model", this._disposeModelCallback), this.positionsMap.forEach((e) => {
      e.forEach((t, s) => {
        const { position: i } = s.attributes;
        i.array.set(t), i.needsUpdate = !0;
      });
    });
  }
}
class yl {
  constructor(e = {}) {
    const {
      regions: t = []
    } = e;
    this.name = "LOAD_REGION_PLUGIN", this.regions = [], this.tiles = null, t.forEach((s) => this.addRegion(s));
  }
  init(e) {
    this.tiles = e;
  }
  addRegion(e) {
    this.regions.indexOf(e) === -1 && this.regions.push(e);
  }
  removeRegion(e) {
    const t = this.regions.indexOf(e);
    t !== -1 && this.regions.splice(t, 1);
  }
  hasRegion(e) {
    return this.regions.indexOf(e) !== -1;
  }
  clearRegions() {
    this.regions = [];
  }
  // Calculates shape intersections and associated error values to use. If "mask" shapes are present then
  // tiles are only loaded if they are within those shapes.
  calculateTileViewError(e, t) {
    const s = e.engineData.boundingVolume, { regions: i, tiles: n } = this;
    let r = !1, o = null, a = 0, l = 1 / 0;
    for (const c of i) {
      const u = c.intersectsTile(s, e, n);
      r = r || u, u && (a = Math.max(c.calculateError(e, n), a), l = Math.min(c.calculateDistance(s, e, n), l)), c.mask && (o = o || u);
    }
    return t.inView = r && o !== !1, t.error = a, t.distance = l, t.inView || o !== null;
  }
  dispose() {
    this.regions = [];
  }
}
class Xs {
  constructor(e = {}) {
    const {
      errorTarget: t = 10,
      mask: s = !1
    } = e;
    this.errorTarget = t, this.mask = s;
  }
  intersectsTile(e, t, s) {
    return !1;
  }
  calculateDistance(e, t, s) {
    return 1 / 0;
  }
  calculateError(e, t) {
    return e.geometricError - this.errorTarget + t.errorTarget;
  }
}
class xl extends Xs {
  constructor(e = {}) {
    const { sphere: t = new Te() } = e;
    super(e), this.sphere = t.clone();
  }
  intersectsTile(e) {
    return e.intersectsSphere(this.sphere);
  }
}
class _l extends Xs {
  constructor(e = {}) {
    const { ray: t = new fr() } = e;
    super(e), this.ray = t.clone();
  }
  intersectsTile(e) {
    return e.intersectsRay(this.ray);
  }
}
class Tl extends Xs {
  constructor(e = {}) {
    const { obb: t = new wr() } = e;
    super(e), this.obb = t.clone(), this.obb.update();
  }
  intersectsTile(e) {
    return e.intersectsOBB(this.obb);
  }
}
const ie = /* @__PURE__ */ new C(), zi = ["x", "y", "z"];
class Fo extends ks {
  constructor(e, t = 16776960, s = 40) {
    const i = new Fe(), n = [];
    for (let r = 0; r < 3; r++) {
      const o = zi[r], a = zi[(r + 1) % 3];
      ie.set(0, 0, 0);
      for (let l = 0; l < s; l++) {
        let c;
        c = 2 * Math.PI * l / (s - 1), ie[o] = Math.sin(c), ie[a] = Math.cos(c), n.push(ie.x, ie.y, ie.z), c = 2 * Math.PI * (l + 1) / (s - 1), ie[o] = Math.sin(c), ie[a] = Math.cos(c), n.push(ie.x, ie.y, ie.z);
      }
    }
    i.setAttribute("position", new G(new Float32Array(n), 3)), i.computeBoundingSphere(), super(i, new pr({ color: t, toneMapped: !1 })), this.sphere = e, this.type = "SphereHelper";
  }
  updateMatrixWorld(e) {
    const t = this.sphere;
    this.position.copy(t.center), this.scale.setScalar(t.radius), super.updateMatrixWorld(e);
  }
}
const ds = /* @__PURE__ */ new C(), Mt = /* @__PURE__ */ new C(), oe = /* @__PURE__ */ new C(), Gi = /* @__PURE__ */ new C(), Wi = /* @__PURE__ */ new C();
function zo(h) {
  h = h.toNonIndexed();
  const { groups: e } = h, { position: t, normal: s } = h.attributes, i = [], n = [];
  for (const o of e) {
    const { start: a, count: l } = o;
    for (let c = a, u = a + l; c < u; c++)
      Gi.fromBufferAttribute(t, c), Wi.fromBufferAttribute(s, c), n.push(...Gi), i.push(...Wi);
  }
  const r = new Fe();
  return r.setAttribute("position", new G(new Float32Array(n), 3)), r.setAttribute("normal", new G(new Float32Array(i), 3)), r;
}
function Pn(h, { computeNormals: e = !1 } = {}) {
  const {
    latStart: t = -Math.PI / 2,
    latEnd: s = Math.PI / 2,
    lonStart: i = 0,
    lonEnd: n = 2 * Math.PI,
    heightStart: r = 0,
    heightEnd: o = 0
  } = h, a = new pn(1, 1, 1, 32, 32), { normal: l, position: c } = a.attributes, u = c.clone();
  for (let d = 0, p = c.count; d < p; d++) {
    oe.fromBufferAttribute(c, d);
    const m = w.mapLinear(oe.x, -0.5, 0.5, t, s), f = w.mapLinear(oe.y, -0.5, 0.5, i, n);
    let g = r;
    h.getCartographicToNormal(m, f, ds), oe.z < 0 && (g = o), h.getCartographicToPosition(m, f, g, oe), c.setXYZ(d, ...oe);
  }
  e && a.computeVertexNormals();
  for (let d = 0, p = u.count; d < p; d++) {
    oe.fromBufferAttribute(u, d);
    const m = w.mapLinear(oe.x, -0.5, 0.5, t, s), f = w.mapLinear(oe.y, -0.5, 0.5, i, n);
    ds.fromBufferAttribute(l, d), h.getCartographicToNormal(m, f, Mt), Math.abs(ds.dot(Mt)) > 0.1 && (oe.z > 0 && Mt.multiplyScalar(-1), l.setXYZ(d, ...Mt));
  }
  return a;
}
class Rn extends ks {
  constructor(e = new Fs(), t = 16776960) {
    super(), this.ellipsoidRegion = e, this.material.color.set(t), this.update();
  }
  update() {
    const e = Pn(this.ellipsoidRegion);
    this.geometry.dispose(), this.geometry = new mr(e, 80);
  }
  dispose() {
    this.geometry.dispose(), this.material.dispose();
  }
}
class Dn extends _e {
  constructor(e = new Fs(), t = 16776960) {
    super(), this.ellipsoidRegion = e, this.material.color.set(t), this.update();
  }
  update() {
    this.geometry.dispose();
    const e = Pn(this.ellipsoidRegion, { computeNormals: !0 }), { lonStart: t, lonEnd: s } = this;
    s - t >= 2 * Math.PI ? (e.groups.splice(2, 2), this.geometry = zo(e)) : this.geometry = e;
  }
  dispose() {
    this.geometry.dispose(), this.material.dispose();
  }
}
const Hi = Symbol("ORIGINAL_MATERIAL"), Ct = Symbol("HAS_RANDOM_COLOR"), At = Symbol("HAS_RANDOM_NODE_COLOR"), fs = Symbol("LOAD_TIME"), Me = Symbol("PARENT_BOUND_REF_COUNT"), Yi = /* @__PURE__ */ new Te(), Ue = () => {
}, ps = {};
function Ce(h) {
  if (!ps[h]) {
    const e = Math.random(), t = 0.5 + Math.random() * 0.5, s = 0.375 + Math.random() * 0.25;
    ps[h] = new Vs().setHSL(e, t, s);
  }
  return ps[h];
}
const de = 0, Bn = 1, Un = 2, On = 3, Vn = 4, kn = 5, Nn = 6, rt = 7, ot = 8, Fn = 9, Dt = 10, Ps = 11, Go = Object.freeze({
  NONE: de,
  SCREEN_ERROR: Bn,
  GEOMETRIC_ERROR: Un,
  DISTANCE: On,
  DEPTH: Vn,
  RELATIVE_DEPTH: kn,
  IS_LEAF: Nn,
  RANDOM_COLOR: rt,
  RANDOM_NODE_COLOR: ot,
  CUSTOM_COLOR: Fn,
  LOAD_ORDER: Dt,
  INDEXED_COLOR: Ps
});
class bl {
  static get ColorModes() {
    return Go;
  }
  get wireframe() {
    return this._wireframe;
  }
  set wireframe(e) {
    e !== this._wireframe && (this._wireframe = e, this.materialsNeedUpdate = !0);
  }
  get unlit() {
    return this._unlit;
  }
  set unlit(e) {
    e !== this._unlit && (this._unlit = e, this.materialsNeedUpdate = !0);
  }
  get colorMode() {
    return this._colorMode;
  }
  set colorMode(e) {
    e !== this._colorMode && (this._colorMode = e, this.materialsNeedUpdate = !0);
  }
  get boundsColorMode() {
    return this._boundsColorMode;
  }
  set boundsColorMode(e) {
    e !== this._boundsColorMode && (this._boundsColorMode = e, this.materialsNeedUpdate = !0);
  }
  get enabled() {
    return this._enabled;
  }
  set enabled(e) {
    e !== this._enabled && this.tiles !== null && (this._enabled = e, e ? this.init(this.tiles) : this.dispose());
  }
  get displayParentBounds() {
    return this._displayParentBounds;
  }
  set displayParentBounds(e) {
    this._displayParentBounds !== e && (this._displayParentBounds = e, e ? this.tiles.traverse((t) => {
      t.traversal.visible && this._onTileVisibilityChange(t, !0);
    }) : this.tiles.traverse((t) => {
      t[Me] = null, this._onTileVisibilityChange(t, t.traversal.visible);
    }));
  }
  constructor(e) {
    e = {
      displayParentBounds: !1,
      displayBoxBounds: !1,
      displaySphereBounds: !1,
      displayRegionBounds: !1,
      colorMode: de,
      boundsColorMode: de,
      maxDebugDepth: -1,
      maxDebugDistance: -1,
      maxDebugError: -1,
      customColorCallback: null,
      unlit: !1,
      enabled: !0,
      ...e
    }, this.name = "DEBUG_TILES_PLUGIN", this.tiles = null, this._colorMode = null, this._boundsColorMode = null, this._unlit = null, this._wireframe = null, this.materialsNeedUpdate = !1, this.extremeDebugDepth = -1, this.extremeDebugError = -1, this.boxGroup = null, this.sphereGroup = null, this.regionGroup = null, this._enabled = e.enabled, this._displayParentBounds = e.displayParentBounds, this.displayBoxBounds = e.displayBoxBounds, this.displaySphereBounds = e.displaySphereBounds, this.displayRegionBounds = e.displayRegionBounds, this.colorMode = e.colorMode, this.boundsColorMode = e.boundsColorMode, this.maxDebugDepth = e.maxDebugDepth, this.maxDebugDistance = e.maxDebugDistance, this.maxDebugError = e.maxDebugError, this.customColorCallback = e.customColorCallback, this.unlit = e.unlit, this.wireframe = e.wireframe, this.getDebugColor = (t, s) => {
      s.setRGB(t, t, t);
    };
  }
  // initialize the groups for displaying helpers, register events, and initialize existing tiles
  init(e) {
    if (this.tiles = e, !this.enabled)
      return;
    const t = e.group;
    this.boxGroup = new Le(), this.boxGroup.name = "DebugTilesRenderer.boxGroup", t.add(this.boxGroup), this.boxGroup.updateMatrixWorld(), this.sphereGroup = new Le(), this.sphereGroup.name = "DebugTilesRenderer.sphereGroup", t.add(this.sphereGroup), this.sphereGroup.updateMatrixWorld(), this.regionGroup = new Le(), this.regionGroup.name = "DebugTilesRenderer.regionGroup", t.add(this.regionGroup), this.regionGroup.updateMatrixWorld(), this._onLoadTilesetCB = () => {
      this._initExtremes();
    }, this._onLoadModelCB = ({ scene: s, tile: i }) => {
      this._onLoadModel(s, i);
    }, this._onDisposeModelCB = ({ tile: s }) => {
      this._onDisposeModel(s);
    }, this._onUpdateAfterCB = () => {
      this.update();
    }, this._onTileVisibilityChangeCB = ({ scene: s, tile: i, visible: n }) => {
      this._onTileVisibilityChange(i, n);
    }, e.addEventListener("load-tileset", this._onLoadTilesetCB), e.addEventListener("load-model", this._onLoadModelCB), e.addEventListener("dispose-model", this._onDisposeModelCB), e.addEventListener("update-after", this._onUpdateAfterCB), e.addEventListener("tile-visibility-change", this._onTileVisibilityChangeCB), this._initExtremes(), e.traverse((s) => {
      s.engineData.scene && this._onLoadModel(s.engineData.scene, s);
    }), e.visibleTiles.forEach((s) => {
      this._onTileVisibilityChange(s, !0);
    });
  }
  getTileFromObject3D(e) {
    let t = null;
    return this.tiles.activeTiles.forEach((i) => {
      if (t)
        return;
      const n = i.engineData.scene;
      n && n.traverse((r) => {
        r === e && (t = i);
      });
    }), t;
  }
  setEmptyTileVisible(e, t) {
    this._onTileVisibilityChange(e, t);
  }
  _initExtremes() {
    if (!(this.tiles && this.tiles.root))
      return;
    let e = -1, t = -1;
    this.tiles.traverse(null, (s, i, n) => {
      e = Math.max(e, n), t = Math.max(t, s.geometricError);
    }, !1), this.extremeDebugDepth = e, this.extremeDebugError = t;
  }
  /**
   * Applies the current plugin field values to all visible tile geometry. Call this
   * after modifying properties such as `colorMode`, `displayBoxBounds`, or
   * `displayParentBounds` when `TilesRenderer.update` is not being called every frame
   * so changes can be reflected.
   */
  update() {
    const { tiles: e, colorMode: t, boundsColorMode: s } = this;
    if (!e.root)
      return;
    this.materialsNeedUpdate && (e.forEachLoadedModel((p) => {
      this._updateMaterial(p);
    }), this.materialsNeedUpdate = !1), this.boxGroup.visible = this.displayBoxBounds, this.sphereGroup.visible = this.displaySphereBounds, this.regionGroup.visible = this.displayRegionBounds;
    let i = -1;
    this.maxDebugDepth === -1 ? i = this.extremeDebugDepth : i = this.maxDebugDepth;
    let n = -1;
    this.maxDebugError === -1 ? n = this.extremeDebugError : n = this.maxDebugError;
    let r = -1;
    this.maxDebugDistance === -1 ? (e.getBoundingSphere(Yi), r = Yi.radius) : r = this.maxDebugDistance;
    const { errorTarget: o, visibleTiles: a } = e;
    let l;
    (t === Dt || s === Dt) && (l = Array.from(a).sort((p, m) => p[fs] - m[fs]));
    const c = (p, m, f, g, y, x) => {
      switch (p !== rt && delete f.material[Ct], p !== ot && delete f.material[At], p) {
        case Vn: {
          const _ = m.internal.depth / i;
          this.getDebugColor(_, f.material.color);
          break;
        }
        case kn: {
          const _ = m.internal.depthFromRenderedParent / i;
          this.getDebugColor(_, f.material.color);
          break;
        }
        case Bn: {
          const _ = m.traversal.error / o;
          _ > 1 ? f.material.color.setRGB(1, 0, 0) : this.getDebugColor(_, f.material.color);
          break;
        }
        case Un: {
          const _ = Math.min(m.geometricError / n, 1);
          this.getDebugColor(_, f.material.color);
          break;
        }
        case On: {
          const _ = Math.min(m.traversal.distanceFromCamera / r, 1);
          this.getDebugColor(_, f.material.color);
          break;
        }
        case Nn: {
          !m.children || m.children.length === 0 ? this.getDebugColor(1, f.material.color) : this.getDebugColor(0, f.material.color);
          break;
        }
        case ot: {
          f.material[At] || (f.material.color.setHSL(g, y, x), f.material[At] = !0);
          break;
        }
        case rt: {
          f.material[Ct] || (f.material.color.setHSL(g, y, x), f.material[Ct] = !0);
          break;
        }
        case Fn: {
          this.customColorCallback ? this.customColorCallback(m, f) : console.warn("DebugTilesRenderer: customColorCallback not defined");
          break;
        }
        case Dt: {
          const _ = l.indexOf(m);
          this.getDebugColor(_ / (l.length - 1), f.material.color);
          break;
        }
        case Ps: {
          f.material.color.copy(Ce(m.internal.depth)), delete f.material[Ct], delete f.material[At];
          break;
        }
      }
    };
    a.forEach((p) => {
      const m = p.engineData.scene;
      let f, g, y;
      t === rt && (f = Math.random(), g = 0.5 + Math.random() * 0.5, y = 0.375 + Math.random() * 0.25), m.traverse((x) => {
        t === ot && (f = Math.random(), g = 0.5 + Math.random() * 0.5, y = 0.375 + Math.random() * 0.25), x.material && c(t, p, x, f, g, y);
      });
    });
    const u = s === de ? Ps : s, d = [this.boxGroup, this.sphereGroup, this.regionGroup];
    for (const p of d)
      for (const m of p.children) {
        const f = m.userData.tile;
        let g, y, x;
        u === rt && (g = Math.random(), y = 0.5 + Math.random() * 0.5, x = 0.375 + Math.random() * 0.25), m.traverse((_) => {
          u === ot && (g = Math.random(), y = 0.5 + Math.random() * 0.5, x = 0.375 + Math.random() * 0.25), _.material && c(u, f, _, g, y, x);
        });
      }
  }
  _onTileVisibilityChange(e, t) {
    this.displayParentBounds ? Lr(e, (s) => {
      s[Me] == null && (s[Me] = 0), t ? s[Me]++ : s[Me] > 0 && s[Me]--;
      const i = s === e && t || this.displayParentBounds && s[Me] > 0;
      this._updateBoundHelper(s, i);
    }) : this._updateBoundHelper(e, t);
  }
  _createBoundHelper(e) {
    const t = this.tiles, s = e.engineData, { sphere: i, obb: n, region: r } = s.boundingVolume;
    if (n) {
      const o = new Le();
      o.name = "DebugTilesRenderer.boxHelperGroup", o.matrix.copy(n.transform), o.matrixAutoUpdate = !1, o.userData.tile = e, s.boxHelperGroup = o;
      const a = new gr(n.box, Ce(e.internal.depth));
      a.raycast = Ue, o.add(a);
      const l = new _e(new pn(), new xe({
        color: Ce(e.internal.depth),
        transparent: !0,
        depthWrite: !1,
        opacity: 0.05,
        side: Pt
      }));
      n.box.getSize(l.scale), l.raycast = Ue, o.add(l), t.visibleTiles.has(e) && this.displayBoxBounds && (this.boxGroup.add(o), o.updateMatrixWorld(!0));
    }
    if (i) {
      const o = new Fo(i, Ce(e.internal.depth));
      o.raycast = Ue, o.userData.tile = e;
      const a = new _e(new yr(1), new xe({
        color: Ce(e.internal.depth),
        transparent: !0,
        depthWrite: !1,
        opacity: 0.05,
        side: Pt
      }));
      a.raycast = Ue, o.add(a), s.sphereHelper = o, t.visibleTiles.has(e) && this.displaySphereBounds && (this.sphereGroup.add(o), o.updateMatrixWorld(!0));
    }
    if (r) {
      const o = new Rn(r, Ce(e.internal.depth));
      o.raycast = Ue, o.userData.tile = e;
      const a = new Dn(r, Ce(e.internal.depth));
      a.material.transparent = !0, a.material.depthWrite = !1, a.material.opacity = 0.05, a.material.side = Pt, a.raycast = Ue, o.add(a);
      const l = new Te();
      r.getBoundingSphere(l), o.position.copy(l.center), l.center.multiplyScalar(-1), o.geometry.translate(...l.center), a.geometry.translate(...l.center), s.regionHelper = o, t.visibleTiles.has(e) && this.displayRegionBounds && (this.regionGroup.add(o), o.updateMatrixWorld(!0));
    }
  }
  _updateHelperMaterials(e, t) {
    t.traverse((s) => {
      const { material: i } = s;
      if (!i)
        return;
      e.traversal.visible || !this.displayParentBounds ? i.opacity = s.isMesh ? 0.05 : 1 : i.opacity = s.isMesh ? 0.01 : 0.2;
      const n = i.transparent;
      i.transparent = i.opacity < 1, i.transparent !== n && (i.needsUpdate = !0);
    });
  }
  _updateBoundHelper(e, t) {
    const s = e.engineData;
    if (!s)
      return;
    const i = this.sphereGroup, n = this.boxGroup, r = this.regionGroup;
    t && s.boxHelperGroup == null && s.sphereHelper == null && s.regionHelper == null && this._createBoundHelper(e);
    const o = s.boxHelperGroup, a = s.sphereHelper, l = s.regionHelper;
    t ? (o && (n.add(o), o.updateMatrixWorld(!0), this._updateHelperMaterials(e, o)), a && (i.add(a), a.updateMatrixWorld(!0), this._updateHelperMaterials(e, a)), l && (r.add(l), l.updateMatrixWorld(!0), this._updateHelperMaterials(e, l))) : (o && n.remove(o), a && i.remove(a), l && r.remove(l));
  }
  _updateMaterial(e) {
    const { colorMode: t, unlit: s, wireframe: i } = this;
    e.traverse((n) => {
      if (!n.material)
        return;
      const r = n.material, o = n[Hi];
      if (r !== o && r.dispose(), t !== de || s) {
        if (n.isPoints) {
          const a = new mn();
          a.size = o.size, a.sizeAttenuation = o.sizeAttenuation, n.material = a;
        } else s ? n.material = new xe({ wireframe: i }) : (n.material = new ln({ wireframe: i }), n.material.flatShading = !0);
        t === de && (n.material.map = o.map, n.material.color.set(o.color));
      } else
        n.material = o;
    });
  }
  _onLoadModel(e, t) {
    t[fs] = performance.now(), e.traverse((s) => {
      const i = s.material;
      i && (s[Hi] = i);
    }), this._updateMaterial(e);
  }
  _onDisposeModel(e) {
    const t = e.engineData;
    t != null && t.boxHelperGroup && (t.boxHelperGroup.traverse((s) => {
      s.geometry && (s.geometry.dispose(), s.material.dispose());
    }), delete t.boxHelperGroup), t != null && t.sphereHelper && (t.sphereHelper.traverse((s) => {
      s.geometry && (s.geometry.dispose(), s.material.dispose());
    }), delete t.sphereHelper), t != null && t.regionHelper && (t.regionHelper.traverse((s) => {
      s.geometry && (s.geometry.dispose(), s.material.dispose());
    }), delete t.regionHelper);
  }
  dispose() {
    var t, s, i;
    const e = this.tiles;
    e.removeEventListener("load-tileset", this._onLoadTilesetCB), e.removeEventListener("load-model", this._onLoadModelCB), e.removeEventListener("dispose-model", this._onDisposeModelCB), e.removeEventListener("update-after", this._onUpdateAfterCB), e.removeEventListener("tile-visibility-change", this._onTileVisibilityChangeCB), this.colorMode = de, this.boundsColorMode = de, this.unlit = !1, e.forEachLoadedModel((n) => {
      this._updateMaterial(n);
    }), e.traverse((n) => {
      this._onDisposeModel(n);
    }, null, !1), (t = this.boxGroup) == null || t.removeFromParent(), (s = this.sphereGroup) == null || s.removeFromParent(), (i = this.regionGroup) == null || i.removeFromParent();
  }
}
const at = 0, ms = 1, Qe = 2, Ke = 3, Oe = 150;
function Wo(h, e) {
  return h * 1 | e * 2;
}
function gs(h, e, t) {
  return `${h}_${e}_${t}`;
}
class qi {
  constructor() {
    this.parent = null, this.x = 0, this.y = 0, this.level = 0, this.children = new Array(4).fill(null), this.childCount = 0, this.loadingState = at, this.visible = !1, this.target = 0, this.showTimer = 0, this.hideTimer = 0, this.siblingForced = !1, this.forced = !1, this._key = null, this._index = null;
  }
  getKey() {
    return this._key === null && (this._key = `${this.x}_${this.y}_${this.level}`), this._key;
  }
  getIndex() {
    return this._index === null && (this._index = Wo(this.x % 2, this.y % 2)), this._index;
  }
  addChild(e) {
    const t = e.getIndex();
    if (this.children[t] || e.x >> 1 !== this.x || e.y >> 1 !== this.y || e.level - 1 !== this.level)
      throw new Error();
    e.parent = this, this.children[t] = e, this.childCount++;
  }
  remove() {
    if (this.childCount > 0)
      throw new Error();
    this.parent.childCount--, this.parent.children[this.getIndex()] = null, this.parent = null;
  }
}
const ys = /* @__PURE__ */ new Set();
class Ho extends Ns {
  constructor() {
    super(), this.root = new qi(), this.cache = {
      [this.root.getKey()]: this.root
    }, this.contentCache = null, this._lastTime = -1, this.loadSiblings = !0;
  }
  update() {
    const e = performance.now(), t = this._lastTime === -1 ? e : this._lastTime, s = e - t;
    this._lastTime = e;
    const { root: i } = this, n = this;
    r(i), o(i), ys.forEach((a) => this._deleteTile(a)), ys.clear();
    function r(a) {
      const l = a.target > 0 || a.siblingForced, c = a.visible && a.forced;
      if (l || c ? (a.showTimer += s, a.showTimer = Math.min(a.showTimer, Oe), a.showTimer === Oe && (a.hideTimer = 0)) : (a.visible || a.showTimer > 0) && (a.hideTimer += s, a.hideTimer = Math.min(a.hideTimer, Oe), a.hideTimer === Oe && (a.showTimer = 0, a.hideTimer = 0, a.loadingState !== at && (n.contentCache.release(a.x, a.y, a.level), a.loadingState = at))), ((l ? a.showTimer === Oe : a.showTimer > 0) || c) && a.loadingState === at) {
        a.loadingState = ms;
        const { x: p, y: m, level: f } = a, g = n.contentCache.lock(p, m, f);
        g instanceof Promise ? g.then((y) => {
          a.loadingState === ms && (a.loadingState = Qe);
        }).catch((y) => {
          a.loadingState === ms && (a.loadingState = y.name === "AbortError" ? at : Ke);
        }) : a.loadingState = g !== null ? Qe : Ke;
      }
      const { children: d } = a;
      if (n.loadSiblings) {
        let p = !1;
        for (let m = 0, f = d.length; m < f; m++) {
          const g = d[m];
          g !== null && g.target > 0 && (p = !0);
        }
        if (p && a.childCount < 4)
          for (let m = 0; m <= 1; m++)
            for (let f = 0; f <= 1; f++)
              n._ensureTile(2 * a.x + f, 2 * a.y + m, a.level + 1);
        for (let m = 0, f = d.length; m < f; m++) {
          const g = d[m];
          g !== null && (g.siblingForced = p);
        }
      } else
        for (let p = 0, m = d.length; p < m; p++) {
          const f = d[p];
          f !== null && (f.siblingForced = !1);
        }
      for (let p = 0, m = d.length; p < m; p++) {
        const f = d[p];
        f !== null && r(f);
      }
    }
    function o(a, l = !1, c = !0) {
      const u = a.target > 0 || a.siblingForced, d = a.visible && l;
      a.forced = l;
      const p = (u ? a.showTimer === Oe : a.showTimer > 0) || d;
      let m = !1;
      (u || d) && (a.loadingState === Qe && (c || d) ? (m = !0, l = !1) : p && (l = !0));
      const { children: f } = a;
      let g = !0;
      if (n.loadSiblings)
        for (let _ = 0, b = f.length; _ < b; _++) {
          const T = f[_];
          (T === null || T.loadingState !== Qe && T.loadingState !== Ke) && (g = !1);
        }
      let y = a.visible || u || a.showTimer > 0, x = !1;
      for (let _ = 0, b = f.length; _ < b; _++) {
        const T = f[_];
        if (T !== null) {
          y = o(T, l, g) || y;
          const v = T.target > 0 || T.siblingForced, S = n.loadSiblings && T.loadingState === Ke;
          x = x || v && !T.visible && !S;
        }
      }
      if (x && a.loadingState === Qe && (m = !0), n.loadSiblings && m && a.childCount === 4) {
        let _ = !0, b = !1;
        for (let T = 0, v = f.length; T < v; T++) {
          const S = f[T];
          !S.visible && S.loadingState !== Ke && (_ = !1), b = b || S.visible;
        }
        _ && b && (m = !1);
      }
      return m !== a.visible && (a.visible = m, n.dispatchEvent({
        type: "toggle",
        visible: m,
        x: a.x,
        y: a.y,
        level: a.level
      })), a !== n.root && !y && ys.add(a), y;
    }
  }
  getVisibleTiles() {
    let e = [];
    for (const t in this.cache) {
      const s = this.cache[t];
      s.visible && e.push(s);
    }
    return e;
  }
  setTargetState(e, t, s, i) {
    if (i) {
      const n = this._ensureTile(e, t, s);
      n.target++;
    } else {
      const n = this.cache[gs(e, t, s)];
      if (!n || n.target <= 0)
        throw new Error("MVTHierarchy: target ref count went negative — mismatched calls.");
      n.target--;
    }
  }
  _deleteTile(e) {
    if (e === this.root)
      throw new Error();
    const { cache: t } = this, { x: s, y: i, level: n } = e, r = gs(s, i, n);
    if (!(r in t))
      throw new Error();
    t[r].remove(), delete t[r];
  }
  _ensureTile(e, t, s) {
    const { cache: i } = this, n = gs(e, t, s);
    if (n in i)
      return i[n];
    const r = new qi();
    r.x = e, r.y = t, r.level = s;
    const o = e >> 1, a = t >> 1, l = s - 1;
    return this._ensureTile(o, a, l).addChild(r), i[r.getKey()] = r, r;
  }
}
const Yo = {
  test: () => !1,
  mark: () => !1
};
class js {
  constructor() {
    this.id = "", this.layer = "", this.properties = null, this.lodLevel = 0, this.enabled = !0, this.valid = !0, this.ready = !1, this.screenPos = new C(), this.visibleDuration = 1 / 0, this.visibleTime = 1 / 0, this.visible = !1;
  }
  updateTransform(e, t, s) {
  }
  evaluate(e, t) {
    return !1;
  }
  // called by the delayed manager when the item first becomes displayed or hidden, letting
  // subclasses reset any per-appearance state. Driven by the delayed manager
  onShown() {
  }
  onHidden() {
  }
}
class qo extends Ns {
  get hasPendingWork() {
    return this.working || this.needsUpdate;
  }
  constructor() {
    super(), this.camera = null, this.matrix = new Y(), this.maxUpdateTimeMs = 0.5, this._task = null, this._deadline = 0, this.working = !1, this.resolution = new k(1, 1), this.size = 12, this.cells = new Uint32Array(1), this._totalResolution = new k(), this._lastMatrix = new Y(), this._ndcMatrix = new Y(), this._invMatrix = new Y(), this._cameraLocalPos = new C(), this.buffer = 0.15, this.items = [], this.visible = /* @__PURE__ */ new Set(), this.prevVisible = /* @__PURE__ */ new Set(), this.added = /* @__PURE__ */ new Set(), this._itemSet = /* @__PURE__ */ new Set(), this._itemsNeedsUpdate = !1, this.needsUpdate = !1, this._id = -1, this.handle = {
      test: (e, t, s) => {
        const { cells: i, _id: n } = this;
        let r = !1;
        return this._cellRange(e, t, s, (a, l, c) => (r = !0, i[c] !== 0 && i[c] !== n)) || !r;
      },
      mark: (e, t, s) => {
        const { cells: i, _id: n } = this;
        return this._cellRange(e, t, s, (r, o, a) => (i[a] = n, !1));
      }
    }, this.sortCallback = () => 0;
  }
  _cellRange(e, t, s, i) {
    const { size: n, resolution: r, buffer: o } = this, a = r.width, l = r.height, c = a * o, u = l * o, { width: d, height: p } = this._totalResolution, m = e + c, f = t + u, g = Math.max(0, Math.floor((m - s) / n)), y = Math.max(0, Math.floor((f - s) / n)), x = Math.min(d - 1, Math.floor((m + s) / n)), _ = Math.min(p - 1, Math.floor((f + s) / n)), b = s * s;
    for (let T = y; T <= _; T++)
      for (let v = g; v <= x; v++) {
        const S = Math.max(v * n, Math.min(m, (v + 1) * n)), M = Math.max(T * n, Math.min(f, (T + 1) * n)), P = m - S, E = f - M;
        if (P * P + E * E <= b && i(v, T, T * d + v) === !0)
          return !0;
      }
    return !1;
  }
  syncItems() {
    const { items: e, _itemSet: t } = this;
    if (this._itemsNeedsUpdate) {
      this._itemsNeedsUpdate = !1, e.length = t.size;
      let s = 0;
      for (const i of t.values())
        e[s] = i, s++;
    }
  }
  // deadline
  _deadlineExpired() {
    return performance.now() >= this._deadline;
  }
  _resetDeadline() {
    this._deadline = performance.now() + this.maxUpdateTimeMs;
  }
  update() {
    this._task === null && (this._task = this._updateGenerator()), this._task.next();
  }
  // run the in-flight pass (or a fresh one if changes are pending) to completion so the visible
  // sets and "change" event reflect the current state immediately
  flush() {
    this._task === null && (this._task = this._updateGenerator());
    do
      this._task.next();
    while (this.working);
  }
  updateCameraTransform() {
    const { camera: e, matrix: t, _ndcMatrix: s, _invMatrix: i, _cameraLocalPos: n } = this;
    s.copy(t).premultiply(e.matrixWorldInverse).premultiply(e.projectionMatrix), i.copy(t).invert(), n.setFromMatrixPosition(e.matrixWorld).applyMatrix4(i);
  }
  *_updateGenerator() {
    for (this._resetDeadline(); ; ) {
      const {
        resolution: e,
        size: t,
        added: s,
        handle: i,
        sortCallback: n,
        buffer: r,
        items: o,
        _lastMatrix: a,
        _itemSet: l,
        _ndcMatrix: c,
        _cameraLocalPos: u
      } = this;
      if (this.updateCameraTransform(), a.equals(c) && !this.needsUpdate) {
        yield, this._resetDeadline();
        continue;
      }
      a.copy(c), this.needsUpdate = !1, this.working = !0, this.syncItems(), [this.visible, this.prevVisible] = [this.prevVisible, this.visible];
      const { visible: d, prevVisible: p } = this;
      d.clear(), s.clear(), this._totalResolution.copy(e).multiplyScalar(1 + 2 * r).multiplyScalar(1 / t).ceil();
      const { width: m, height: f } = this._totalResolution;
      this.cells.length !== m * f ? this.cells = new Uint8Array(m * f) : this.cells.fill(0);
      for (let g = 0, y = o.length; g < y; g++) {
        const x = o[g];
        x.enabled && x.updateTransform(c, e, u), this._deadlineExpired() && (yield, this._resetDeadline(), this.updateCameraTransform());
      }
      o.sort(n), this._deadlineExpired() && (yield, this._resetDeadline(), this.updateCameraTransform());
      for (let g = 0, y = o.length; g < y; g++) {
        const x = o[g];
        this._id = g + 1, x.enabled && l.has(x) && x.evaluate(i) && (d.add(x), p.has(x) ? (x.visible = !1, p.delete(x)) : (x.visible = !0, s.add(x))), this._deadlineExpired() && (yield, this._resetDeadline(), this.updateCameraTransform());
      }
      this.working = !1, (s.size > 0 || p.size > 0) && this.dispatchEvent({ type: "change", added: s, removed: p }), yield, this._resetDeadline();
    }
  }
  // re-layout a single item at the current view without claiming occupancy, so an item that has
  // lost placement (eg a label fading out) keeps its layout current instead of freezing.
  // Forces placement past the usual fit checks - must be called right after update() so the scratch
  // is fresh.
  refreshLayout(e) {
    const { resolution: t, _ndcMatrix: s, _cameraLocalPos: i } = this;
    e.updateTransform(s, t, i), e.evaluate(Yo, !0);
  }
  register(e) {
    this._itemSet.add(e), this._itemsNeedsUpdate = !0, this.needsUpdate = !0;
  }
  unregister(e) {
    this._itemSet.delete(e), this._itemsNeedsUpdate = !0, this.needsUpdate = !0;
  }
}
class Xo extends Ns {
  // pass through fields
  get camera() {
    return this.manager.camera;
  }
  set camera(e) {
    this.manager.camera = e;
  }
  get matrix() {
    return this.manager.matrix;
  }
  get resolution() {
    return this.manager.resolution;
  }
  get size() {
    return this.manager.size;
  }
  set size(e) {
    this.manager.size = e;
  }
  get cells() {
    return this.manager.cells;
  }
  get working() {
    return this.manager.working;
  }
  get hasPendingWork() {
    return this._showTimers.size > 0 || this._hideTimers.size > 0 || this.manager.hasPendingWork;
  }
  get sortCallback() {
    return this.manager.sortCallback;
  }
  set sortCallback(e) {
    this.manager.sortCallback = e;
  }
  get buffer() {
    return this.manager.buffer;
  }
  set buffer(e) {
    this.manager.buffer = e;
  }
  get needsUpdate() {
    return this.manager.needsUpdate;
  }
  set needsUpdate(e) {
    this.manager.needsUpdate = e;
  }
  constructor() {
    super(), this.manager = new qo(), this.visible = /* @__PURE__ */ new Set(), this.showDelay = 0.5, this.hideDelay = 0.5, this._showTimers = /* @__PURE__ */ new Map(), this._hideTimers = /* @__PURE__ */ new Map(), this._lastUpdateTime = -1, this.added = /* @__PURE__ */ new Set(), this.removed = /* @__PURE__ */ new Set(), this.manager.addEventListener("change", ({ added: e, removed: t }) => {
      const { _showTimers: s, _hideTimers: i, visible: n } = this;
      for (const r of e)
        i.delete(r), n.has(r) || (r.onShown(), s.set(r, 0));
      for (const r of t)
        s.delete(r) ? r.onHidden() : n.has(r) && i.set(r, 0);
    });
  }
  // pass through to the underlying occupation manager
  register(e) {
    return this.manager.register(e);
  }
  unregister(e) {
    this.manager.unregister(e);
  }
  syncItems() {
    this.manager.syncItems();
  }
  // complete any in-flight update pass on the underlying occupation manager immediately
  flush() {
    this.manager.flush();
  }
  update() {
    const e = performance.now() / 1e3, t = this._lastUpdateTime < 0 ? 0 : Math.min(e - this._lastUpdateTime, 0.1);
    this._lastUpdateTime = e, this.manager.update();
    const {
      _showTimers: s,
      _hideTimers: i,
      visible: n,
      added: r,
      removed: o,
      showDelay: a,
      hideDelay: l
    } = this;
    r.clear(), o.clear();
    const c = performance.now();
    for (const [u, d] of s) {
      const p = d + t;
      p >= a ? (s.delete(u), n.add(u), r.add(u), u.visibleTime = c) : s.set(u, p);
    }
    for (const [u, d] of i) {
      const p = d + t;
      p >= l || !u.valid ? (i.delete(u), n.delete(u), o.add(u), u.onHidden()) : i.set(u, p);
    }
    for (const u of n.values())
      u.visibleDuration = c - u.visibleTime, this.manager.refreshLayout(u);
    (r.size > 0 || o.size > 0) && this.dispatchEvent({ type: "change", added: r, removed: o });
  }
  // Immediately complete every pending show / hide timer so a change takes effect immediately. Flushed items
  // are merged into `added` / `removed` and intended to be called right after update() so the caller reads
  // the combined result.
  finishAnimations() {
    const { _showTimers: e, _hideTimers: t, visible: s, added: i, removed: n } = this, r = performance.now();
    for (const o of e.keys())
      s.add(o), i.add(o), o.visibleTime = r;
    e.clear();
    for (const o of t.keys())
      s.delete(o), n.add(o), o.onHidden();
    t.clear();
  }
}
class ye extends js {
  // number of points in the path
  get count() {
    return this.lat.length;
  }
  // number of anchors
  get anchorCount() {
    return this.anchorPositions.length;
  }
  constructor() {
    super(), this.text = "", this.characterWidths = [], this.characterRadius = 0, this.totalTextWidth = 0, this.range = null, this.lat = [], this.lon = [], this.positions = [], this.anchorPositions = [], this.screenPositions = [], this.cumulativeLen = [], this.cachedMatrix = new Y(), this.cachedResolution = new k(), this.needsUpdate = !1;
  }
  // overrides
  evaluate() {
    throw new Error();
  }
  // update screen space points and cumulative values for text placement
  updateTransform(e, t, s) {
    const {
      positions: i,
      screenPositions: n,
      cachedMatrix: r,
      cachedResolution: o,
      cumulativeLen: a
    } = this;
    if (!(!this.needsUpdate && r.equals(e) && o.equals(t))) {
      for (this.needsUpdate = !1, r.copy(e), o.copy(t); n.length < i.length; )
        n.push(new C());
      for (let l = 0, c = n.length; l < c; l++) {
        const u = i[l], d = n[l];
        d.copy(u).applyMatrix4(e), d.x = (d.x * 0.5 + 0.5) * t.width, d.y = (-d.y * 0.5 + 0.5) * t.height, d.z = w.mapLinear(d.z, -1, 1, 0, 1);
      }
      a.length = n.length, a[0] = 0;
      for (let l = 1; l < n.length; l++) {
        const c = n[l - 1], u = n[l], d = u.x - c.x, p = u.y - c.y, m = Math.sqrt(d * d + p * p);
        a[l] = a[l - 1] + m;
      }
    }
  }
  //
  updateCharacterWidthCache(e) {
    const { text: t, characterWidths: s, properties: i, layer: n } = this;
    s.length = t.length;
    let r = 0;
    for (let o = 0, a = t.length; o < a; o++) {
      const l = e(t[o], n, i);
      s[o] = l, r += l;
    }
    this.totalTextWidth = r, this.characterRadius = e("M", n, i);
  }
  // whether a lat / lon falls within the same tile as this line
  hasCoverage(e, t) {
    const [s, i, n, r] = this.range;
    return t >= s && t <= n && e >= i && e <= r;
  }
  // Place anchors along a path at a fixed "spacing" (geographic, in radians), recording the
  // bounding sample indices. Short paths receive a single anchor at their midpoint.
  generateAnchors(e) {
    const { lat: t, lon: s } = this, i = [];
    let n = 0;
    for (let c = 0, u = t.length - 1; c < u; c++) {
      const d = t[c], p = t[c + 1], m = s[c], f = s[c + 1], g = 0.5 * (d + p), y = p - d, x = (f - m) * Math.cos(g), _ = Math.sqrt(y * y + x * x);
      i.push(_), n += _;
    }
    let r = e * 0.5;
    r > n && (r = n * 0.5);
    let o = 0, a = 0;
    const l = [];
    for (; r <= n; ) {
      for (; a < i.length && o + i[a] < r; )
        o += i[a], a++;
      if (a >= i.length)
        break;
      const c = a, u = a + 1, d = i[c], p = d > 0 ? (r - o) / d : 0;
      l.push({
        i0: c,
        i1: u,
        alpha: p,
        ref: null,
        lat: w.lerp(t[c], t[u], p),
        lon: w.lerp(s[c], s[u], p)
      }), r += e;
    }
    this.anchorPositions = l;
  }
}
function jo(h, e) {
  const t = [];
  for (let s = 0, i = h.length - 1; s < i; s++) {
    const n = h[s], r = h[s + 1];
    t.push(n);
    const o = r.x - n.x, a = r.y - n.y, l = Math.sqrt(o * o + a * a), c = Math.ceil(l / e);
    for (let u = 1; u < c; u++) {
      const d = u / c;
      t.push({
        x: w.lerp(n.x, r.x, d),
        y: w.lerp(n.y, r.y, d)
      });
    }
  }
  return t.push(h[h.length - 1]), t;
}
function $o(h, e, t, s, i, n, r = []) {
  const o = 0.0783927971443699, a = 1 / 64, l = i.getTileBounds(e, t, s, !0, !1), [c, u, d, p] = l, { flipY: m } = i, f = i.getTileBounds(e, t, s, !1, !1);
  for (const g in h.layers) {
    const y = h.layers[g], x = y.extent, _ = x * a, b = [];
    for (let T = 0; T < y.length; T++) {
      const v = y.feature(T);
      if (v.type !== 2 || !n(g, v.properties, v.type))
        continue;
      const S = `${g}:${v.properties.name || v.id}`, M = v.loadGeometry();
      for (const P of M)
        b.push({
          key: S,
          id: S,
          properties: v.properties,
          points: P
        });
    }
    for (const T of b) {
      const v = jo(T.points, _), S = new ye();
      S.id = T.id, S.layer = g, S.properties = T.properties, S.lodLevel = s, S.range = f;
      for (const M of v) {
        const P = w.lerp(c, d, M.x / x), E = M.y / x, F = m ? w.lerp(p, u, E) : w.lerp(u, p, E), [B, W] = i.toCartographicPoint(P, F);
        S.lon.push(B), S.lat.push(W), S.positions.push(new C());
      }
      S.generateAnchors(o * (f[2] - f[0])), r.push(S);
    }
  }
  return r;
}
const Qo = 1e-10, Ko = 1, Zo = 16, Ae = /* @__PURE__ */ new fn(), Lt = /* @__PURE__ */ new C();
function Xi(h, e) {
  const { ray: t } = h, { planes: s } = e;
  let i = 0, n = h.far;
  for (let r = 0; r < 6; r++) {
    const o = s[r], a = o.normal.dot(t.direction);
    if (Math.abs(a) < Qo) {
      if (o.distanceToPoint(t.origin) < 0)
        return !1;
    } else {
      const l = t.distanceToPlane(o);
      if (a > 0)
        l !== null && l > i && (i = l);
      else {
        if (l === null)
          return !1;
        l < n && (n = l);
      }
      if (i > n)
        return !1;
    }
  }
  return !0;
}
class Jo {
  get hasPendingWork() {
    return this._queue.size > 0;
  }
  constructor() {
    this.tiles = null, this.occupancy = null, this.camera = null, this.maxSettleTimeMs = 1, this._queue = /* @__PURE__ */ new Set(), this._items = /* @__PURE__ */ new Set(), this.needsUpdate = !1, this._task = null, this._deadline = 0;
  }
  register(e) {
    this._items.add(e), this._queue.add(e);
  }
  unregister(e) {
    this._items.delete(e), this._queue.delete(e);
  }
  update() {
    if (this.needsUpdate) {
      this.needsUpdate = !1;
      for (const e of this._items.values())
        this._queue.add(e);
    }
    this._task === null && (this._task = this._settleGenerator()), this._task.next();
  }
  // deadline
  _deadlineExpired() {
    return performance.now() >= this._deadline;
  }
  _resetDeadline() {
    this._deadline = performance.now() + this.maxSettleTimeMs;
  }
  _getSettlingRay(e, t, s) {
    const { tiles: i } = this, { origin: n, direction: r } = s.ray;
    i.ellipsoid.getCartographicToPosition(e, t, 1e8, n), i.ellipsoid.getCartographicToPosition(e, t, 0, r), r.sub(n).normalize(), s.far = 2 * 1e8, s.firstHitOnly = !0;
  }
  _settleSample(e, t, s, i) {
    const { tiles: n } = this, { origin: r, direction: o } = Ae.ray;
    this._getSettlingRay(e, t, Ae), r.applyMatrix4(n.group.matrixWorld), o.transformDirection(n.group.matrixWorld);
    const a = Ae.intersectObject(n.group);
    a.length > 0 ? Lt.copy(a[0].point).applyMatrix4(n.group.matrixWorldInverse) : n.ellipsoid.getCartographicToPosition(e, t, 0, Lt), Lt.distanceTo(s) > i && s.copy(Lt);
  }
  *_settleGenerator() {
    const e = new Y(), t = new xr(), s = /* @__PURE__ */ new Set(), i = [[], [], [], []];
    for (this._resetDeadline(); ; ) {
      const { _queue: n, _items: r, tiles: o, camera: a, occupancy: l } = this;
      if (a !== null) {
        e.copy(o.group.matrixWorld).premultiply(a.matrixWorldInverse).premultiply(a.projectionMatrix), t.setFromProjectionMatrix(e);
        for (const c of n)
          if (!l.visible.has(c)) {
            if (c instanceof ye) {
              const { anchorPositions: u } = c, d = u[u.length >> 1], { lat: p, lon: m } = d;
              if (this._getSettlingRay(p, m, Ae), Xi(Ae, t)) {
                s.add(c);
                continue;
              }
            } else
              this._getSettlingRay(c.lat, c.lon, Ae), Xi(Ae, t) && s.add(c);
            this._deadlineExpired() && (yield, this._resetDeadline());
          }
      }
      for (const c of n) {
        const u = s.has(c);
        let d = 0;
        !c.ready && u ? d = 3 : l.visible.has(c) ? d = 2 : u && (d = 1), i[d].push(c), this._deadlineExpired() && (yield, this._resetDeadline());
      }
      for (let c = i.length - 1; c >= 0; c--) {
        const u = i[c];
        for (; u.length > 0; ) {
          const d = u.pop();
          if (n.delete(d), !!r.has(d)) {
            if (!d.enabled) {
              d.ready = !1;
              continue;
            }
            yield* this._settleItem(d), this._deadlineExpired() && (yield, this._resetDeadline());
          }
        }
      }
      s.clear(), i.forEach((c) => c.length = 0), yield, this._resetDeadline();
    }
  }
  *_settleItem(e) {
    const t = Ko * 2 ** (Zo - e.lodLevel);
    if (e instanceof ye) {
      const { _items: s } = this, { lat: i, lon: n, positions: r } = e;
      for (let o = 0, a = i.length; o < a; o++)
        if (this._settleSample(i[o], n[o], r[o], t), this._deadlineExpired() && (yield, this._resetDeadline(), !s.has(e)))
          return;
      e.needsUpdate = !0;
    } else
      this._settleSample(e.lat, e.lon, e.position, t);
    e.ready = !0;
  }
}
const ea = 40, ta = Math.PI / 2, sa = Math.cos(ta), ia = 0.8, xs = [], _s = [], se = /* @__PURE__ */ new C(), Ve = /* @__PURE__ */ new k(), Ts = /* @__PURE__ */ new k(), bs = /* @__PURE__ */ new k(), ji = /* @__PURE__ */ new k(), vs = /* @__PURE__ */ new k(), ws = /* @__PURE__ */ new k(), $i = /* @__PURE__ */ new k();
let na = 0;
class zn extends js {
  get lat() {
    return this.getActiveReference().lat;
  }
  get lon() {
    return this.getActiveReference().lon;
  }
  get ready() {
    return this.getActiveReference().line.ready;
  }
  set ready(e) {
  }
  get properties() {
    return this.getActiveReference().line.properties;
  }
  set properties(e) {
  }
  get enabled() {
    return this.getActiveReference().line.enabled;
  }
  set enabled(e) {
  }
  get text() {
    return this.getActiveReference().line.text;
  }
  constructor(e) {
    super(), this.id = `${e}_${na++}`, this.displayed = !1, this.referencePaths = [], this._activeReference = null, this._snapped = null, this._flippedTextDir = !1, this.characterPositions = [], this.characterAngles = [];
  }
  // overrides
  // "force" places the characters at the current projection even when they don't fit,
  // used to keep a fading-out label laid out (see ScreenOccupationManager.refreshLayout)
  evaluate(e, t = !1) {
    const { text: s } = this;
    if (!s)
      return !1;
    const { line: i } = this.getActiveReference(), { cumulativeLen: n } = i;
    return !i.ready || n.length < 2 || (this._flippedTextDir = this._getTextDirection(), xs.length = s.length, _s.length = s.length, this._layoutCharacters(e, xs, _s, t), !this.valid && !t) ? !1 : (this._placeCharacters(e, xs, _s), !0);
  }
  // determine the reading direction based on the positioning of the end points
  _getTextDirection() {
    const { line: e, i0: t, i1: s, alpha: i } = this.getActiveReference(), { cumulativeLen: n, screenPositions: r, totalTextWidth: o } = e, a = w.lerp(n[t], n[s], i), l = o * 0.5, c = a - l, u = a + l;
    let d = 0, p = 0, m = n.length - 2, f = 1;
    for (let x = 0, _ = n.length - 2; x < _; x++) {
      const b = x + 1, T = n[x], v = n[b];
      c >= T && c <= v && (d = x, p = w.mapLinear(c, T, v, 0, 1)), u >= T && u <= v && (m = x, f = w.mapLinear(u, T, v, 0, 1));
    }
    const g = se.lerpVectors(r[d], r[d + 1], p).x;
    return se.lerpVectors(r[m], r[m + 1], f).x < g;
  }
  // march the characters out from the anchor in both directions, centered, measuring and testing
  // each one so a string that doesn't fit leaves no marks behind. records per-character segment
  // index / alpha into the module scratch. Sets the "valid" field indicating whether the current
  // characters can be displayed or not.
  // TODO: also reject foreshortened paths (tiny screen-space segments)
  _layoutCharacters(e, t, s, i = !1) {
    const { line: n, i0: r, i1: o, alpha: a } = this.getActiveReference(), { cumulativeLen: l, screenPositions: c, totalTextWidth: u, characterWidths: d, characterRadius: p, text: m } = n, f = w.lerp(l[r], l[o], a), g = this._flippedTextDir;
    this.valid = !0;
    const y = c.length, x = l[l.length - 1], _ = m.length;
    let b = 0, T = 0, v = 0;
    for (let S = 0; S < _; S++) {
      const M = g ? _ - 1 - S : S, P = d[M], E = T + P * 0.5 - u * 0.5;
      T += P;
      const F = f + E;
      if ((F < 0 || F > x) && (this.valid = !1, !i))
        break;
      for (; b < y - 2 && l[b + 1] < F; )
        b++;
      const B = b + 1, W = l[B] - l[b], q = W > 0 ? (F - l[b]) / W : 0, K = c[b], A = c[B];
      if (se.lerpVectors(K, A, q), (se.z < 0 || se.z > 1 || e.test(se.x, se.y, p)) && (this.valid = !1, !i))
        break;
      if (S > 0) {
        const L = se.x - Ve.x, D = se.y - Ve.y, R = L * L + D * D, I = (P + v) * 0.5 * ia;
        if (R < I * I && (this.valid = !1, !i))
          break;
      }
      if (S >= 2) {
        vs.subVectors(Ve, Ts), ws.subVectors(se, Ts), $i.subVectors(se, Ve);
        const L = Math.abs(vs.cross(ws)), D = vs.length() * $i.length() * ws.length();
        if ((D > 0 ? 2 * L / D : 0) > 1 / ea && (this.valid = !1, !i))
          break;
      }
      if (bs.subVectors(A, K).normalize(), S > 0 && bs.dot(ji) < sa && (this.valid = !1, !i))
        break;
      ji.copy(bs), v = P, Ts.copy(Ve), Ve.copy(se), t[M] = b, s[M] = q;
    }
  }
  // commit a successful layout: mark occupancy and record a world-space position + baseline
  // angle per character, applying the reading-direction flip
  _placeCharacters(e, t, s) {
    const { characterPositions: i, characterAngles: n, text: r } = this, { line: o } = this.getActiveReference(), { screenPositions: a, positions: l, characterRadius: c } = o, u = this._flippedTextDir, d = r.length;
    for (; i.length < d; )
      i.push(new C());
    i.length = d, n.length = d;
    for (let p = 0; p < d; p++) {
      const m = t[p], f = s[p], g = a[m], y = a[m + 1];
      e.mark(g.x + (y.x - g.x) * f, g.y + (y.y - g.y) * f, c), i[p].lerpVectors(l[m], l[m + 1], f);
      const x = (y.x - g.x) * (u ? -1 : 1), _ = (y.y - g.y) * (u ? -1 : 1);
      n[p] = Math.atan2(_, x);
    }
  }
  updateTransform(e, t, s) {
    this.updateActiveReference(), this.getActiveReference().line.updateTransform(e, t, s);
  }
  // anchor functions
  isEmpty() {
    return this.referencePaths.length === 0;
  }
  hasLoD(e) {
    return this.referencePaths.find((t) => t.line.lodLevel === e);
  }
  getPosition(e) {
    const { line: t, i0: s, i1: i, alpha: n } = this.getActiveReference();
    return e.lerpVectors(t.positions[s], t.positions[i], n);
  }
  // the highest-LoD entry whose path is settled, used for placement - return the "snapped" or
  // active line reference
  getActiveReference() {
    return this._snapped ?? this._activeReference;
  }
  updateActiveReference() {
    const { referencePaths: e, _activeReference: t, displayed: s } = this;
    let i;
    const n = e[0] ?? null;
    if (n && n.line.ready ? i = n : t && t.line.ready && (e.includes(t) || this.displayed) ? i = t : i = n ?? t, i && t && i !== t)
      if (s) {
        const { lat: r, lon: o } = this._snapped ?? t;
        this._snapped = this._snapToLine(i.line, r, o);
      } else
        this._snapped = null;
    return this._activeReference = i, i;
  }
  // find the nearest point on the given line in cartographic lat / lon  to the supplied
  // position, returning a line-reference used to keep a displayed label coherent
  // when the active LoD swaps.
  _snapToLine(e, t, s) {
    const { lat: i, lon: n } = e;
    if (i.length < 2)
      return null;
    let r = 1 / 0, o = 0, a = 1, l = 0, c = i[0], u = n[0];
    for (let d = 0, p = i.length - 1; d < p; d++) {
      const m = i[d], f = n[d], g = i[d + 1] - m, y = n[d + 1] - f, x = g * g + y * y, _ = x > 0 ? w.clamp(((t - m) * g + (s - f) * y) / x, 0, 1) : 0, b = m + g * _, T = f + y * _, v = t - b, S = s - T, M = v * v + S * S;
      M < r && (r = M, o = d, a = d + 1, l = _, c = b, u = T);
    }
    return {
      line: e,
      i0: o,
      i1: a,
      alpha: l,
      lat: c,
      lon: u
    };
  }
  // clear the transient snapped slot when a fresh display begins so the label re-derives
  // from its evenly-spaced associated anchor. Deferred to the next appearance (rather than at
  // hide) so the snap survives the glyph fade-out and doesn't reflow the fading label.
  onShown() {
    this.displayed = !0, this._snapped = null;
  }
  onHidden() {
    this.displayed = !1;
  }
  // add a reference to the given line, associating this anchor with the provided anchor
  // position index
  addLine(e, t) {
    const s = e.anchorPositions[t], { referencePaths: i } = this;
    i.push({
      line: e,
      i0: s.i0,
      i1: s.i1,
      alpha: s.alpha,
      lat: s.lat,
      lon: s.lon
    }), i.sort((n, r) => r.line.lodLevel - n.line.lodLevel), this.updateActiveReference();
  }
  removeLine(e) {
    const { referencePaths: t } = this;
    for (let s = 0; s < t.length; s++)
      t[s].line === e && (t.splice(s, 1), s--);
    this.updateActiveReference();
  }
}
class ra {
  constructor() {
    this.added = /* @__PURE__ */ new Set(), this.removed = /* @__PURE__ */ new Set(), this._anchorsById = /* @__PURE__ */ new Map(), this._linesById = /* @__PURE__ */ new Map(), this.lines = /* @__PURE__ */ new Set(), this.anchors = /* @__PURE__ */ new Set();
  }
  reset() {
    this.added.clear(), this.removed.clear();
  }
  update() {
    const { _anchorsById: e, removed: t } = this;
    e.forEach((s, i) => {
      s.forEach((n) => {
        n.isEmpty() && (s.delete(n), this.anchors.delete(n), t.add(n));
      }), s.size === 0 && e.delete(i);
    });
  }
  // add a set of lines
  // NOTE: This is is designed to be called with all lines from a single tile at once
  addLines(e) {
    const { _anchorsById: t, _linesById: s, added: i } = this, n = /* @__PURE__ */ new Map();
    e.forEach((r) => {
      n.has(r.id) || n.set(r.id, []), n.get(r.id).push(r);
    }), n.forEach((r, o) => {
      t.has(o) || t.set(o, /* @__PURE__ */ new Set()), s.has(o) || s.set(o, /* @__PURE__ */ new Set());
      const a = r[0], l = t.get(o);
      l.forEach((c) => {
        let u = 1 / 0, d = null, p = -1;
        !a.hasCoverage(c.lat, c.lon) || c.hasLoD(a.lodLevel) || (r.forEach((m) => {
          m.anchorPositions.forEach((f, g) => {
            if (f.ref === null) {
              const y = c.lat - f.lat, x = c.lon - f.lon, _ = y * y + x * x;
              _ < u && (u = _, d = m, p = g);
            }
          });
        }), d && (c.addLine(d, p), d.anchorPositions[p].ref = c));
      }), r.forEach((c) => {
        c.anchorPositions.forEach((u, d) => {
          if (u.ref === null) {
            const p = new zn(o);
            p.addLine(c, d), c.hasCoverage(p.lat, p.lon) && (u.ref = p, l.add(p), this.anchors.add(p), i.add(p));
          }
        });
      });
    }), n.forEach((r, o) => {
      const a = s.get(o);
      r.forEach((l) => {
        a.add(l), this.lines.add(l);
      });
    });
  }
  deleteLines(e) {
    e.forEach((t) => this.deleteLine(t));
  }
  // remove a path; anchors left with no associated paths are dropped
  deleteLine(e) {
    const { _anchorsById: t, _linesById: s } = this, i = e.id;
    s.get(i).delete(e), this.lines.delete(e), s.get(i).size === 0 && s.delete(i);
    const n = t.get(i);
    n && n.forEach((r) => {
      r.removeLine(e);
    });
  }
}
class oa {
  constructor(e) {
    this.enabled = !1, this.canvas = null, this.occupancyManager = e;
  }
  update() {
    const { occupancyManager: e, enabled: t } = this;
    if (!t) {
      this.dispose();
      return;
    }
    if (this.canvas === null) {
      const f = document.createElement("canvas");
      f.style.cssText = "position:fixed;top:0;left:0;pointer-events:none;opacity:0.5;", document.body.appendChild(f), this.canvas = f;
    }
    if (e.working)
      return;
    const { canvas: s } = this, { cells: i, size: n, resolution: r, buffer: o } = e, a = window.devicePixelRatio, l = r.width * o, c = r.height * o, u = Math.ceil((r.width + 2 * l) / n), d = Math.ceil((r.height + 2 * c) / n);
    s.width = Math.round(a * (r.width + 2 * l)), s.height = Math.round(a * (r.height + 2 * c)), s.style.width = `${r.width + 2 * l}px`, s.style.height = `${r.height + 2 * c}px`, s.style.left = `${-l}px`, s.style.top = `${-c}px`;
    const p = n * a, m = s.getContext("2d");
    m.clearRect(0, 0, s.width, s.height);
    for (let f = 0; f < d; f++)
      for (let g = 0; g < u; g++) {
        const y = i[f * u + g] !== 0;
        m.fillStyle = y ? "rgba( 255, 80, 80, 0.6 )" : "rgba( 80, 255, 80, 0.15 )", m.fillRect(g * p + 0.5, f * p + 0.5, p - 1, p - 1), m.strokeStyle = y ? "rgba( 255, 80, 80, 1 )" : "rgba( 80, 255, 80, 0.25 )", m.lineWidth = 1, m.strokeRect(g * p + 0.5, f * p + 0.5, p - 1, p - 1);
      }
  }
  dispose() {
    this.canvas !== null && (this.canvas.remove(), this.canvas = null);
  }
}
const Ne = new class {
  constructor() {
    this._cache = {};
  }
  getColor(...h) {
    const e = h.pop(), t = h.join("_"), { _cache: s } = this;
    return t in s || (e.setHSL(Math.random(), 1, 0.5), s[t] = e.getHex()), e.set(s[t]);
  }
}(), ke = {
  NONE: 0,
  ID: 1,
  LEVEL: 2,
  TILE: 3,
  NAME: 4
}, he = /* @__PURE__ */ new C(), Et = /* @__PURE__ */ new C(), Ze = /* @__PURE__ */ new Vs();
function aa() {
  const t = new zt(new Uint8Array(4096), 32, 32);
  for (let s = 0; s < 32; s++)
    for (let i = 0; i < 32; i++) {
      const n = (s - 16) / 16, r = (i - 16) / 16, o = Math.sqrt(n * n + r * r), a = i * 32 + s;
      t.image.data[4 * a + 0] = 255, t.image.data[4 * a + 1] = 255, t.image.data[4 * a + 2] = 255, t.image.data[4 * a + 3] = o < 1 ? 255 : 0;
    }
  return t.needsUpdate = !0, t;
}
class la {
  get ColorMode() {
    return ke;
  }
  constructor(e) {
    this.enabled = !1, this.colorMode = ke.NONE, this.displayLines = !0, this.displayAnchors = !0, this.camera = null, this.anchorManager = e, this.group = null, this._lines = null, this._points = null;
  }
  update() {
    const { enabled: e, group: t, camera: s, anchorManager: i, displayAnchors: n, displayLines: r } = this;
    if (!e) {
      this.dispose();
      return;
    }
    if (this._lines === null) {
      const y = new ks();
      y.material.transparent = !0, y.material.depthTest = !1, y.material.depthWrite = !1, y.material.vertexColors = !0, y.frustumCulled = !1, y.raycast = () => {
      };
      const x = new As();
      x.material.transparent = !0, x.material.depthTest = !1, x.material.depthWrite = !1, x.material.map = aa(), x.material.size = 6, x.material.sizeAttenuation = !1, x.material.vertexColors = !0, x.frustumCulled = !1, x.raycast = () => {
      }, t.add(y, x), this._lines = y, this._points = x;
    }
    const { _lines: o, _points: a } = this;
    s !== null ? (he.setFromMatrixPosition(s.matrixWorld), t.worldToLocal(he)) : he.set(0, 0, 0);
    const l = Array.from(i.lines).filter((y) => y instanceof ye && y.ready);
    let c = 0;
    for (const y of l)
      c += y.count - 1;
    const u = new G(new Float32Array(c * 2 * 3), 3), d = new G(new Float32Array(c * 2 * 3), 3);
    let p = 0;
    for (const y of l) {
      this._getColor(y, Ze);
      const x = y.positions;
      for (let _ = 0, b = x.length - 1; _ < b; _++)
        u.setXYZ(p + 0, ...Et.copy(x[_]).sub(he)), u.setXYZ(p + 1, ...Et.copy(x[_ + 1]).sub(he)), d.setXYZ(p + 0, ...Ze), d.setXYZ(p + 1, ...Ze), p += 2;
    }
    const m = Array.from(i.anchors).filter((y) => y.ready), f = new G(new Float32Array(m.length * 3), 3), g = new G(new Float32Array(m.length * 2 * 3), 3);
    p = 0;
    for (const y of m)
      y.getPosition(Et).sub(he), f.setXYZ(p, ...Et), this._getColor(y.getActiveReference().line, Ze), g.setXYZ(p, ...Ze), p++;
    o.geometry.dispose(), o.geometry.setAttribute("position", u), o.geometry.setAttribute("color", d), o.position.copy(he), o.updateMatrixWorld(), o.visible = r, a.geometry.dispose(), a.geometry.setAttribute("position", f), a.geometry.setAttribute("color", g), a.position.copy(he), a.updateMatrixWorld(), a.visible = n;
  }
  dispose() {
    this._lines !== null && (this._lines.removeFromParent(), this._lines.geometry.dispose(), this._lines.material.dispose(), this._lines = null), this._points !== null && (this._points.removeFromParent(), this._points.geometry.dispose(), this._points.material.dispose(), this._points.material.map.dispose(), this._points = null);
  }
  // retrieve the color for the given line
  _getColor(e, t) {
    switch (this.colorMode) {
      case ke.ID:
        Ne.getColor(e.id, t);
        break;
      case ke.LEVEL:
        Ne.getColor(e.lodLevel, t);
        break;
      case ke.NAME:
        Ne.getColor(e.properties.name, t);
        break;
      case ke.TILE:
        Ne.getColor(...e.range, t);
        break;
      default:
        t.set(16777215);
        break;
    }
  }
}
const Qi = /* @__PURE__ */ new C(), ca = Math.acos(0.1);
class ha extends js {
  constructor() {
    super(), this.position = new C(), this.lat = 0, this.lon = 0, this.radius = 28, this.screenPos = new C(), this._facingAngle = 0;
  }
  updateTransform(e, t, s) {
    const { position: i, screenPos: n } = this;
    n.copy(i).applyMatrix4(e), n.x = (n.x * 0.5 + 0.5) * t.width, n.y = (-n.y * 0.5 + 0.5) * t.height, n.z = n.z < -1 || n.z > 1 ? 1 : 0, s !== null ? (Qi.subVectors(s, i), this._facingAngle = i.lengthSq() > 0 ? i.angleTo(Qi) : 0) : this._facingAngle = 0;
  }
  evaluate(e) {
    const { screenPos: t, radius: s, _facingAngle: i } = this;
    return !this.ready || t.z !== 0 || i > ca || e.test(t.x, t.y, s) ? !1 : (e.mark(t.x, t.y, s), !0);
  }
}
function ua(h, e, t, s, i, n, r = []) {
  const [o, a, l, c] = i.getTileBounds(e, t, s, !0, !1);
  for (const u in h.layers) {
    const d = h.layers[u], p = d.extent;
    for (let m = 0; m < d.length; m++) {
      const f = d.feature(m);
      if (f.type !== 1 || !n(u, f.properties, f.type))
        continue;
      const g = f.loadGeometry();
      for (const [y] of g) {
        const x = w.lerp(o, l, y.x / p), _ = y.y / p, b = i.flipY ? w.lerp(c, a, _) : w.lerp(a, c, _), [T, v] = i.toCartographicPoint(x, b), S = new ha();
        S.id = `${u}:${f.id}`, S.layer = u, S.properties = f.properties, S.lat = v, S.lon = T, S.lodLevel = s, r.push(S);
      }
    }
  }
  return r;
}
const Je = {
  NONE: 0,
  LEVEL: 1,
  TILE: 2
};
class da {
  get ColorMode() {
    return Je;
  }
  constructor() {
    this.enabled = !1, this._wasEnabled = !1, this.hierarchy = null, this.tiles = null, this.tiling = null, this.colorMode = Je.NONE, this._regions = {}, this._onToggleCallback = ({ x: e, y: t, level: s, visible: i }) => {
      const n = `${e}_${t}_${s}`;
      if (i) {
        const { ellipsoid: r, group: o } = this.tiles, [a, l, c, u] = this.tiling.getTileBounds(e, t, s, !1, !1), d = new Fs(...r.radius, l, u, a, c, 600, 700), p = new Rn(d);
        p.material.depthWrite = !1, p.material.depthTest = !1, p.material.transparent = !0;
        const m = new Dn(d);
        m.material.transparent = !0, m.material.opacity = 0.1, m.material.depthWrite = !1;
        const f = new Le();
        f.add(p, m), o.add(f), f.updateMatrixWorld(!0), this._regions[n] = {
          helper: f,
          x: e,
          y: t,
          level: s
        };
      } else {
        const { helper: r } = this._regions[n];
        r.children.forEach((o) => o.dispose()), r.removeFromParent(), delete this._regions[n];
      }
    };
  }
  update() {
    const { enabled: e, hierarchy: t, _regions: s } = this;
    if (e !== this._wasEnabled && (this._wasEnabled = e, e ? (t.getVisibleTiles().forEach((i) => {
      this._onToggleCallback(i);
    }), t.addEventListener("toggle", this._onToggleCallback)) : this.dispose()), e)
      for (const i in s) {
        const { x: n, y: r, level: o, helper: a } = s[i];
        a.children.forEach((l) => {
          const { color: c } = l.material;
          switch (this.colorMode) {
            case Je.NONE:
              c.set(16777215);
              break;
            case Je.LEVEL:
              Ne.getColor(o, c);
              break;
            case Je.TILE:
              Ne.getColor(n, r, o, c);
              break;
          }
        });
      }
  }
  dispose() {
    const { hierarchy: e } = this;
    e.getVisibleTiles().forEach((t) => {
      this._onToggleCallback({ ...t, visible: !1 });
    }), e.removeEventListener("toggle", this._onToggleCallback);
  }
}
class fa {
  constructor() {
    this.added = /* @__PURE__ */ new Set(), this.removed = /* @__PURE__ */ new Set(), this.points = /* @__PURE__ */ new Set(), this._annotationsById = /* @__PURE__ */ new Map();
  }
  add(e) {
    const { _annotationsById: t, points: s, added: i } = this, { id: n } = e;
    if (!t.has(n))
      t.set(n, { annotation: e, ref: 0 }), s.add(e), i.add(e);
    else {
      const r = t.get(n).annotation;
      e.lodLevel > r.lodLevel && (r.lodLevel = e.lodLevel, r.lat = e.lat, r.lon = e.lon);
    }
    t.get(n).ref++;
  }
  delete(e) {
    const { _annotationsById: t } = this, { id: s } = e, i = t.get(s);
    i.ref--;
  }
  update() {
    const { removed: e, points: t, _annotationsById: s } = this;
    s.forEach((i, n) => {
      i.ref === 0 && (e.add(i.annotation), t.delete(i.annotation), s.delete(n));
    });
  }
  reset() {
    this.added.clear(), this.removed.clear();
  }
}
class pa extends ht {
  /**
   * Returns true when all slots are allocated.
   * @type {boolean}
   **/
  get isFull() {
    return this._freeList.length === 0 && this._nextIndex >= this._capacity;
  }
  /**
   * Returns the total number of icons that can be added to the atlas.
   * @type {number}
   **/
  get capacity() {
    return this._capacity;
  }
  /**
   * Returns the number of icons currently used.
   * @type {number}
   **/
  get count() {
    return this._slots.size;
  }
  /**
   * @param {number} slotCount - Maximum number of slots in the atlas.
   * @param {number} slotSize - Width and height of each slot in pixels.
   */
  constructor(e = 32, t = 64) {
    super(null), this.generateMipmaps = !1, this.slotSize = 0, this._columns = -1, this._capacity = -1, this._slots = /* @__PURE__ */ new Map(), this._freeList = [], this._nextIndex = 0, this._capacity = 0, this._columns = 0, this._uvs = /* @__PURE__ */ new Map(), this.resize(e, t), this.colorSpace = ct;
  }
  /**
   * Returns the keys associated with all glyphs.
   */
  keys() {
    return this._slots.keys();
  }
  /**
   * Returns true if key has an allocated slot.
   * @param {string} key
   * @returns {boolean}
   */
  has(e) {
    return this._slots.has(e);
  }
  /**
   * Returns the slot bounds `{ x, y, w, h }` for key, or null if not allocated.
   * @param {string} key
   * @returns {{ x: number, y: number, w: number, h: number } | null}
   */
  get(e) {
    const { _slots: t } = this;
    return t.has(e) ? this._indexToSlot(t.get(e)) : null;
  }
  /**
   * Returns the UV bounds of a slot for key in GPU texture space (flipY applied),
   * or null if not allocated.
   * @param {Vector2} target
   * @returns {Vector2}
   */
  getSlotSize(e) {
    const { slotSize: t, image: s } = this;
    return e.set(t / s.width, t / s.height);
  }
  /**
   * Returns the UV bounds of the slot for key in GPU texture space (flipY applied),
   * or null if not allocated. x/y is the top-left corner; w/h is the slot size in UV units.
   * @param {string} key
   * @returns {{ x: number, y: number, w: number, h: number } | null}
   */
  getUV(e) {
    const { _slots: t, _uvs: s } = this, i = t.get(e);
    return s.get(i);
  }
  /**
   * Renders a single character in the slot, centered on its text metrics bounding box.
   * @param {string} key
   * @param {string} char - The character to draw.
   * @param {Object} [styles={}]
   * @param {string} [styles.font=''] CSS font string (e.g. `'bold 48px sans-serif'`).
   * @param {string} [styles.color='white'] CSS fill color.
   * @param {string|null} [styles.strokeStyle=null] CSS stroke color drawn under the fill, or
   * null to skip the stroke.
   * @param {number} [styles.strokeWidth=1] Stroke width in atlas pixels.
   * @returns {{ x: number, y: number, w: number, h: number }} The allocated slot.
   * @throws If the atlas is full.
   */
  drawChar(e, t, s = {}) {
    const {
      font: i = "",
      color: n = "white",
      strokeStyle: r = null,
      strokeWidth: o = 1
    } = s;
    return this._draw(e, (a, l, c, u, d) => {
      const p = l + u / 2, m = c + d / 2, f = this.measureChar(t), g = p - (f.actualBoundingBoxRight + f.actualBoundingBoxLeft) / 2, y = m + d / 4;
      r !== null && (a.font = i, a.lineJoin = "round", a.lineWidth = o * 2, a.strokeStyle = r, a.strokeText(t, g, y)), a.font = i, a.fillStyle = n, a.fillText(t, g, y);
    });
  }
  /**
   * Function that returns a text metrics object for the given character rendered with
   * the provided set of styles.
   * @param {string} char
   * @param {string} font
   * @returns {TextMetrics}
   */
  measureChar(e, t) {
    const { ctx: s } = this;
    return s.font = t, s.measureText(e);
  }
  /**
   * Draws a `CanvasImageSource` into the slot, scaled to fit.
   * @param {string} key
   * @param {HTMLImageElement|HTMLCanvasElement|ImageBitmap} image
   * @returns {{ x: number, y: number, w: number, h: number }} The allocated slot.
   * @throws If the atlas is full.
   */
  drawImage(e, t) {
    return this._draw(e, (s, i, n, r, o) => {
      s.drawImage(t, i, n, r, o);
    });
  }
  /**
   * Renders a `Path2D` into the slot. Path coordinates are slot-local (origin at top-left).
   * @param {string} key
   * @param {Path2D} path2D
   * @param {Object} [styles={}]
   * @param {string|null} [styles.fillStyle=null] CSS fill color, or null to skip fill.
   * @param {string|null} [styles.strokeStyle=null] CSS stroke color, or null to skip stroke.
   * @param {number} [styles.lineWidth=1] Stroke width in pixels.
   * @returns {{ x: number, y: number, w: number, h: number }} The allocated slot.
   * @throws If the atlas is full.
   */
  drawPath(e, t, s = {}) {
    const {
      fillStyle: i = null,
      strokeStyle: n = null,
      lineWidth: r = 1
    } = s;
    return this._draw(e, (o, a, l) => {
      o.save(), o.translate(a, l), i !== null && (o.fillStyle = i, o.fill(t)), n !== null && (o.strokeStyle = n, o.lineWidth = r, o.stroke(t)), o.restore();
    });
  }
  /**
   * Parses an SVG string and renders its paths into a slot, scaled to fit.
   * @param {string} key
   * @param {string} svgText
   * @param {Object} [styles={}]
   * @param {string|null} [styles.fillStyle='white'] CSS fill color, or null to skip fill.
   * @param {string|null} [styles.strokeStyle=null] CSS stroke color, or null to skip stroke.
   * @param {number} [styles.strokeWidth=1] Stroke width in SVG user units before scaling.
   * @param {number} [styles.iconScale=1] Fraction of the slot size the icon occupies (0–1).
   * @returns {{ x: number, y: number, w: number, h: number }} The allocated slot.
   * @throws If the atlas is full.
   */
  drawSVG(e, t, s = {}) {
    const {
      fillStyle: i = "white",
      strokeStyle: n = null,
      strokeWidth: r = 1,
      iconScale: o = 1
    } = s, l = new DOMParser().parseFromString(t, "image/svg+xml").documentElement, c = (l.getAttribute("viewBox") ?? "0 0 15 15").trim().split(/[\s,]+/), u = parseFloat(c[2]), d = parseFloat(c[3]), p = [...l.querySelectorAll("path")].map((m) => m.getAttribute("d")).filter(Boolean).map((m) => new Path2D(m));
    return this._draw(e, (m, f, g, y, x) => {
      const _ = y * o, b = x * o, T = Math.min(_ / u, b / d), v = f + (y - u * T) / 2, S = g + (x - d * T) / 2;
      if (m.save(), m.translate(v, S), m.scale(T, T), m.lineJoin = "round", m.lineCap = "round", n !== null) {
        m.lineWidth = r / T, m.strokeStyle = n;
        for (const M of p)
          m.stroke(M);
      }
      if (i !== null) {
        m.fillStyle = i;
        for (const M of p)
          m.fill(M);
      }
      m.restore();
    });
  }
  /**
   * Frees the slot for key, returning it to the pool for reuse.
   * @param {string} key
   */
  release(e) {
    const { _slots: t, _freeList: s } = this;
    if (!t.has(e))
      return;
    const i = t.get(e);
    s.push(i), t.delete(e);
  }
  /**
   * Resizes the atlas, copying existing slot content to their new positions.
   * @param {number} slotCount - New maximum slot count.
   * @param {number} [slotSize] - New slot size in pixels. Defaults to current size.
   */
  resize(e, t = this.slotSize) {
    const s = this.image, i = this._columns, n = this.slotSize, r = Math.ceil(Math.sqrt(e)), o = document.createElement("canvas");
    o.width = r * t, o.height = r * t;
    const a = o.getContext("2d");
    for (const l of this._slots.values()) {
      const c = l % i * n, u = Math.floor(l / i) * n, d = l % r * t, p = Math.floor(l / r) * t;
      a.drawImage(
        s,
        c,
        u,
        n,
        n,
        d,
        p,
        t,
        t
      );
    }
    this.dispose(), this.image = o, this.ctx = a, this.slotSize = t, this._columns = r, this._capacity = e, this.needsUpdate = !0;
  }
  /**
   * Clears all slots and resets the atlas to empty.
   */
  clear() {
    this._slots.clear(), this._freeList.length = 0, this._nextIndex = 0, this.ctx.clearRect(0, 0, this.image.width, this.image.height), this.needsUpdate = !0;
  }
  // calls the callback to draw into the calculated slot for the given key
  _draw(e, t) {
    const {
      ctx: s,
      image: i,
      _freeList: n,
      _capacity: r,
      _slots: o,
      _uvs: a
    } = this;
    let l;
    if (o.has(e))
      l = o.get(e);
    else {
      if (n.length > 0)
        l = n.pop();
      else if (this._nextIndex < r)
        l = this._nextIndex++;
      else
        throw new Error("MVTGlyphAtlasTexture: atlas is full. Call resize() to increase capacity.");
      o.set(e, l);
    }
    const c = this._indexToSlot(l);
    s.save(), s.beginPath(), s.rect(c.x, c.y, c.w, c.h), s.clip(), s.clearRect(c.x, c.y, c.w, c.h), t(s, c.x, c.y, c.w, c.h), s.restore();
    const { width: u, height: d, slotSize: p } = i;
    return a.set(l, {
      x: c.x / u,
      y: (d - c.y) / d,
      w: p / u,
      h: p / d
    }), this.needsUpdate = !0, c;
  }
  // calculates the section of the canvas for the given index
  _indexToSlot(e) {
    const { _columns: t, slotSize: s } = this;
    return {
      x: e % t * s,
      y: Math.floor(e / t) * s,
      w: s,
      h: s
    };
  }
}
const Ss = /* @__PURE__ */ new be();
class Ki extends mn {
  /**
   * The glyph atlas sampled by this material.
   * @type {MVTGlyphAtlasTexture}
   */
  get glyphAtlas() {
    return this._glyphAtlas;
  }
  set glyphAtlas(e) {
    this._glyphAtlas = e, e !== null && e.getSlotSize(this._glyphCellSize), this._uniforms && (this._uniforms.glyphAtlas.value = e);
  }
  /**
   * A single atlas slot's size in UV units.
   * @type {Vector2}
   */
  get glyphCellSize() {
    return this._glyphCellSize;
  }
  /**
   * @param {Object} [parameters] - `PointsMaterial` parameters, plus the overrides below.
   * @param {number} [parameters.size=25] - Point size in pixels.
   * @param {boolean} [parameters.sizeAttenuation=false] - Whether point size shrinks with distance.
   */
  constructor(e = {}) {
    const {
      size: t = 25,
      sizeAttenuation: s = !1,
      ...i
    } = e;
    super({ size: t, sizeAttenuation: s, ...i }), this.transparent = !0, this.depthTest = !1, this.depthWrite = !1, this.resolution = new k(), this._glyphCellSize = new k(), this._glyphAtlas = new pa(), this._uniforms = null, this.onBeforeCompile = (n) => {
      n.uniforms.glyphAtlas = { value: this._glyphAtlas }, n.uniforms.glyphCellSize = { value: this._glyphCellSize }, this._uniforms = n.uniforms, n.vertexShader = n.vertexShader.replace(
        "#include <color_pars_vertex>",
        /* glsl */
        `
					#include <color_pars_vertex>
					attribute vec2 glyphUV;
					attribute float alpha;
					attribute float angle;
					varying vec2 vGlyphUV;
					varying float vAlpha;
					varying float vAngle;
				`
      ), n.vertexShader = n.vertexShader.replace(
        "#include <color_vertex>",
        /* glsl */
        `
					#include <color_vertex>
					vGlyphUV = glyphUV;
					vAlpha = alpha;
					vAngle = angle;
				`
      ), n.fragmentShader = /* glsl */
      `

					uniform sampler2D glyphAtlas;
					uniform vec2 glyphCellSize;
					uniform float opacity;
					varying vec2 vGlyphUV;
					varying float vAlpha;
					varying float vAngle;

					void main() {

						vec4 diffuseColor = vec4( 0.0 );
						if ( vGlyphUV.x >= 0.0 ) {

							// rotate the point-sprite lookup around its center so the glyph follows
							// the path direction; clamp keeps the rotated corners inside the slot
							vec2 pc = gl_PointCoord - 0.5;
							float c = cos( vAngle );
							float s = sin( vAngle );
							pc = vec2( c * pc.x + s * pc.y, - s * pc.x + c * pc.y ) + 0.5;
							pc = clamp( pc, 0.0, 1.0 );

							vec4 glyph = texture2D( glyphAtlas, vGlyphUV + pc * glyphCellSize * vec2( 1.0, - 1.0 ) );
							diffuseColor = glyph;

						}

						diffuseColor.a *= vAlpha * opacity;
						gl_FragColor = diffuseColor;

						#include <tonemapping_fragment>
						#include <colorspace_fragment>
						#include <premultiplied_alpha_fragment>


					}


			`;
    };
  }
  onBeforeRender(e) {
    this._glyphAtlas.getSlotSize(this._glyphCellSize), e.getViewport(Ss), this.resolution.set(Ss.z, Ss.w);
  }
}
const et = /* @__PURE__ */ new Y(), ne = /* @__PURE__ */ new be(), ue = /* @__PURE__ */ new be(), Zi = /* @__PURE__ */ new k(), Ji = /* @__PURE__ */ new k(), Ms = /* @__PURE__ */ new C(), tt = /* @__PURE__ */ Object.freeze({
  OBSCURED: 0,
  DRAW_THROUGH: 1,
  OVERLAY: 2
});
class Gn extends Le {
  /**
   * The draw modes assignable to `drawMode`.
   * @type {MVTDrawModeEnum}
   */
  static get DrawMode() {
    return tt;
  }
  /**
   * Glyph size in pixels.
   * @type {number}
   */
  get size() {
    return this._opaque.material.size;
  }
  set size(e) {
    this._opaque.material.size = e, this._drawThrough.material.size = e;
  }
  /**
   * The texture atlas used for rendering glyphs.
   * @type {MVTGlyphAtlasTexture}
   */
  get glyphAtlas() {
    return this._opaque.material.glyphAtlas;
  }
  /**
   * How glyphs interact with the depth buffer; one of `MVTGlyphs.DrawMode`.
   * @type {number}
   */
  get drawMode() {
    return this._drawMode;
  }
  set drawMode(e) {
    this._drawMode = e, this._applyDrawMode();
  }
  get geometry() {
    return this._opaque.geometry;
  }
  constructor(e) {
    super(), this.frustumCulled = !1, this.fadeInDuration = 0.3, this.fadeOutDuration = 0.3, this.drawThroughOpacity = 0.5, this._entryMap = /* @__PURE__ */ new Map(), this._orderedEntries = [], this._lastUpdateTime = -1, this._lastCamera = null;
    const t = new Fe(), s = new As(t, new Ki());
    s.frustumCulled = !1, s.renderOrder = 1e3, s.onAfterRender = (n, r, o) => {
      this._lastCamera = o;
    };
    const i = new As(t, new Ki());
    i.frustumCulled = !1, i.material.glyphAtlas = s.material.glyphAtlas, i.renderOrder = 1001, i.onAfterRender = (n, r, o) => {
      this._lastCamera = o;
    }, this.add(i, s), this._opaque = s, this._drawThrough = i, this.drawMode = tt.OVERLAY;
  }
  /**
   * Disposes the glyph atlas, geometry, and materials.
   * @returns {void}
   */
  dispose() {
    this.glyphAtlas.dispose(), this.geometry.dispose(), this._opaque.material.dispose(), this._drawThrough.material.dispose();
  }
  /**
   * Updates the rendered glyphs from a frame's visibility changes and advances the fades. Call
   * once per frame.
   * @private
   * @param {Iterable<Object>} added - Items that became visible, each with a stable `id`.
   * @param {Iterable<Object>} removed - Items that became hidden.
   * @returns {void}
   */
  update(e, t) {
    const s = performance.now() / 1e3, i = this._lastUpdateTime < 0 ? 0 : Math.min(s - this._lastUpdateTime, 0.1);
    this._lastUpdateTime = s;
    const { _entryMap: n, _orderedEntries: r, fadeInDuration: o, fadeOutDuration: a } = this;
    for (const c of e) {
      const u = n.get(c.id);
      if (u)
        u.item = c, u.state === "out" && (u.state = "in");
      else {
        const d = { item: c, fade: 0, state: "in" };
        n.set(c.id, d), r.push(d);
      }
    }
    for (const c of t) {
      const u = n.get(c.id);
      u && u.state !== "out" && (u.state = "out");
    }
    let l = !1;
    for (const [c, u] of n)
      u.state === "in" ? (u.fade = Math.min(1, u.fade + i / o), u.fade >= 1 && (u.state = "visible")) : u.state === "out" && (u.fade = Math.max(0, u.fade - i / a), u.fade <= 0 && (n.delete(c), l = !0));
    l && (this._orderedEntries = r.filter((c) => n.has(c.item.id))), this._recenter(), this._updateGeometry();
  }
  raycast(e, t) {
    const s = e.camera;
    if (!s) return;
    const { geometry: i, matrixWorld: n } = this, { material: r } = this._opaque, { resolution: o } = r, a = i.getAttribute("position");
    if (!a || a.count === 0) return;
    const l = r.size / 2, c = -s.near;
    e.ray.at(1, ue), ue.w = 1, ue.applyMatrix4(s.matrixWorldInverse), ue.applyMatrix4(s.projectionMatrix), ue.multiplyScalar(1 / ue.w), Zi.set(ue.x * o.x / 2, ue.y * o.y / 2), et.multiplyMatrices(s.matrixWorldInverse, n);
    for (let u = 0, d = i.drawRange.count; u < d; u++) {
      if (ne.fromBufferAttribute(a, u), ne.w = 1, ne.applyMatrix4(et), ne.z > c || (ne.applyMatrix4(s.projectionMatrix), ne.multiplyScalar(1 / ne.w), ne.z < -1 || ne.z > 1) || (Ji.set(ne.x * o.x / 2, ne.y * o.y / 2), Zi.distanceTo(Ji) > l)) continue;
      Ms.fromBufferAttribute(a, u).applyMatrix4(n);
      const p = this._orderedEntries[u];
      t.push({
        distance: e.ray.origin.distanceTo(Ms),
        point: Ms.clone(),
        index: u,
        face: null,
        faceIndex: null,
        object: this,
        layer: (p == null ? void 0 : p.item.layer) ?? null,
        properties: (p == null ? void 0 : p.item.properties) ?? null
      });
    }
    return !1;
  }
  // configure the two child draws for the current draw mode
  _applyDrawMode() {
    const { _opaque: e, _drawThrough: t, drawThroughOpacity: s, _drawMode: i } = this;
    switch (i) {
      case tt.OVERLAY:
        e.visible = !0, e.material.depthTest = !1, t.visible = !1;
        break;
      case tt.DRAW_THROUGH:
        e.visible = !0, e.material.depthTest = !0, t.visible = !0, t.material.opacity = s, t.material.depthFunc = _r;
        break;
      case tt.OBSCURED:
      default:
        e.visible = !0, e.material.depthTest = !0, t.visible = !1;
        break;
    }
  }
  // keep the root near the camera to avoid gpu jitter at globe scale
  _recenter() {
    const { parent: e, _lastCamera: t } = this;
    t || (this.position.set(0, 0, 0), this.updateMatrixWorld(!0)), e ? et.copy(e.matrixWorld).invert() : et.identity(), this.position.setFromMatrixPosition(t.matrixWorld).applyMatrix4(et), this.updateMatrixWorld(!0);
  }
  // subclasses build their geometry from here
  _updateGeometry() {
  }
  // resize the shared per-glyph attribute buffers to hold `count` glyphs if necessary and set the draw
  // range
  _resizeGeometry(e) {
    const { geometry: t } = this, s = t.getAttribute("position");
    (!s || s.count < e) && (t.dispose(), t.setAttribute("position", new G(new Float32Array(e * 3), 3)), t.setAttribute("glyphUV", new G(new Float32Array(e * 2), 2)), t.setAttribute("alpha", new G(new Float32Array(e), 1)), t.setAttribute("angle", new G(new Float32Array(e), 1))), t.setDrawRange(0, e);
  }
  // write a single glyph's attributes; position is stored relative to this.position ( the
  // camera-local origin ) and `key` looks up the atlas slot, or -1 when it isn't present
  _writeGlyph(e, t, s, i, n = 0) {
    const { geometry: r, glyphAtlas: o } = this, a = this.position, {
      position: l,
      glyphUV: c,
      alpha: u,
      angle: d
    } = r.attributes;
    if (l.setXYZ(e, t.x - a.x, t.y - a.y, t.z - a.z), s !== null && o.has(s)) {
      const p = o.getUV(s);
      c.setXY(e, p.x, p.y);
    } else
      c.setXY(e, -1, -1);
    u.setX(e, i), d.setX(e, n);
  }
  // flag the per-glyph attributes for upload
  _markNeedsUpdate() {
    const { geometry: e } = this;
    e.getAttribute("position").needsUpdate = !0, e.getAttribute("glyphUV").needsUpdate = !0, e.getAttribute("alpha").needsUpdate = !0, e.getAttribute("angle").needsUpdate = !0;
  }
}
class ma extends Gn {
  /**
   * @param {Object} [options]
   * @param {MVTGetKindCallback} [options.getKind] - Chooses the atlas key to draw for each point.
   * @param {string|null} [options.fallback=null] - Atlas key drawn when `getKind`'s result is
   * missing from the atlas; null draws nothing.
   * @param {number} [options.size=18] - Glyph size in pixels.
   * @param {number} [options.glyphSize] - Atlas slot size in pixels (defaults to `18 * devicePixelRatio`).
   * @param {number} [options.slotCount=64] - Initial atlas slot capacity.
   */
  constructor(e = {}) {
    const {
      getKind: t = () => null,
      fallback: s = null,
      size: i = 18,
      glyphSize: n = 18 * window.devicePixelRatio,
      slotCount: r = 64
    } = e;
    super(), this.getKind = t, this.fallback = s, this.size = i, this.glyphAtlas.resize(r, n);
  }
  _updateGeometry() {
    const { _orderedEntries: e, getKind: t, glyphAtlas: s, fallback: i } = this, n = e.length;
    this._resizeGeometry(n);
    for (let r = 0; r < n; r++) {
      const { item: o, fade: a } = e[r];
      let l = t(o.layer, o.properties);
      (l === null || !s.has(l)) && (l = i), this._writeGlyph(r, o.position, l, a);
    }
    this._markNeedsUpdate();
  }
}
const st = /* @__PURE__ */ new Set();
class ga extends Gn {
  /**
   * @param {Object} [options]
   * @param {number} [options.size=16] - Glyph size in pixels.
   * @param {number} [options.glyphSize] - Atlas slot size in pixels (defaults to `16 * devicePixelRatio`).
   * @param {number} [options.slotCount=64] - Initial atlas slot capacity ( grows as needed ).
   * @param {string|null} [options.font=null] - Explicit CSS font string; overrides `fontFamily`.
   * @param {string} [options.fontFamily='sans-serif'] - Font family used to build the CSS font when
   * `font` isn't given.
   * @param {string} [options.strokeStyle='black'] - Outline color drawn under each glyph.
   * @param {number} [options.strokeWidth=0] - Outline width in atlas pixels ( 0 disables the outline ).
   */
  constructor(e = {}) {
    const {
      size: t = 16,
      glyphSize: s = 16 * window.devicePixelRatio,
      slotCount: i = 64,
      font: n = null,
      fontFamily: r = "sans-serif",
      strokeStyle: o = "black",
      strokeWidth: a = 0
    } = e;
    super();
    const l = Math.round(s * 0.7);
    this._font = n ?? `400 ${l}px ${r}`, this._advanceCache = /* @__PURE__ */ new Map(), this._strokeStyle = o, this._strokeWidth = a, this.glyphAtlas.resize(i, s), this.size = t;
  }
  /**
   * Resets the cached glyphs content. Used when changing fonts or styles.
   */
  reset() {
    this._advanceCache.clear(), this.glyphAtlas.clear();
  }
  /**
   * Advance width of `char` in the label's size units, cached per character.
   * @param {string} char - The character to measure.
   * @returns {number} The advance width.
   */
  measureChar(e) {
    const { _advanceCache: t, glyphAtlas: s, _font: i } = this;
    if (!t.has(e)) {
      const n = this.size / s.slotSize, o = s.measureChar(e, i).width + 2;
      t.set(e, o * n);
    }
    return t.get(e);
  }
  // rasterize a character into the atlas, evicting a glyph that isn't needed this frame ( or
  // growing the atlas if every rasterized glyph is still in use )
  _drawChar(e, t) {
    const { glyphAtlas: s } = this;
    if (s.capacity === s.count) {
      let i = null;
      for (const n of s.keys())
        if (!t.has(n)) {
          i = n;
          break;
        }
      i !== null ? s.release(i) : s.resize(s.capacity * 2);
    }
    s.drawChar(e, e, {
      font: this._font,
      color: "white",
      strokeStyle: this._strokeStyle,
      strokeWidth: this._strokeWidth
    });
  }
  _updateGeometry() {
    const { _orderedEntries: e, glyphAtlas: t } = this;
    st.clear();
    let s = 0;
    for (const n of e) {
      const { text: r, characterPositions: o } = n.item;
      s += o.length;
      for (let a = 0, l = r.length; a < l; a++)
        st.add(r[a]);
    }
    for (const n of st)
      t.has(n) || this._drawChar(n, st);
    this._resizeGeometry(s);
    let i = 0;
    for (const n of e) {
      const r = n.item, { fade: o } = n, a = r.characterPositions, l = r.characterAngles, c = r.text;
      for (let u = 0, d = a.length; u < d; u++)
        this._writeGlyph(i++, a[u], c[u], o, l[u]);
    }
    this._markNeedsUpdate(), st.clear();
  }
}
const Cs = /* @__PURE__ */ new Y();
function ya(h) {
  const e = [];
  return h.traverse((t) => {
    t.isMesh && e.push(t);
  }), e;
}
class xa {
  /**
   * Set to "true" when the filters or settings have changed to trigger an
   * update to the annotations in the plugin.
   * @type {boolean}
   */
  set needsUpdate(e) {
    e && this.version++;
  }
  constructor() {
    this.group = new Le(), this.version = 0;
  }
  /**
   * Whether an MVT feature should be included as an annotation.
   * @param {string} layer - The MVT layer name the feature belongs to.
   * @param {Object} properties - The feature's property map.
   * @param {number} type - The MVT geometry type: `1` = point, `2` = line.
   * @returns {boolean} True to include the feature as an annotation.
   */
  filterAnnotation(e, t, s) {
    return !1;
  }
  /**
   * Relative placement priority between two annotations, following the `Array.prototype.sort`
   * contract. Lower values sort first, are placed first, and win collisions.
   * @param {Object} a - The first annotation.
   * @param {Object} b - The second annotation.
   * @returns {number} Negative if `a` precedes `b`, positive if it follows, `0` if equal.
   */
  sortAnnotations(e, t) {
    const s = e.properties.rank ?? 1e10, i = t.properties.rank ?? 1e10;
    return s - i;
  }
  /**
   * Advance width of a single character, in pixels, used to space glyphs along text labels.
   * @param {string} char - The character to measure.
   * @param {layer} layer - The layer associated with the text.
   * @param {Object} properties - The properties associated with the text.
   * @returns {number} The advance width in pixels.
   */
  measureChar(e, t, s) {
    return 1;
  }
  /**
   * The string a line / road annotation should display for the given feature.
   * @param {Object} properties - The feature's property map.
   * @returns {string} The label text, or an empty string to render nothing.
   */
  getText(e) {
    return e.name ?? "";
  }
  /**
   * Whether a parsed annotation should currently be displayed. Unlike `filterAnnotation` which
   * decides what is parsed once.
   * @param {Object} properties - The feature's property map.
   * @param {number} type - The MVT geometry type: `1` = point, `2` = line.
   * @returns {boolean} True to display the annotation.
   */
  isAnnotationEnabled(e, t) {
    return !0;
  }
  /**
   * Called each frame with the point ( PoI ) annotations whose visibility changed, for the caller
   * to render.
   * @param {Object[]} added - Point annotations that became visible this frame.
   * @param {Object[]} removed - Point annotations that became hidden this frame.
   * @returns {void}
   */
  onPointsUpdate(e, t) {
  }
  /**
   * Called each frame with the line / label annotations whose visibility changed, for the caller
   * to render.
   * @param {Object[]} added - Label annotations that became visible this frame.
   * @param {Object[]} removed - Label annotations that became hidden this frame.
   * @returns {void}
   */
  onLabelsUpdate(e, t) {
  }
  /**
   * Releases any resources the driver created (geometries, materials, textures, etc.). Called by
   * the plugin from its own `dispose`.
   * @returns {void}
   */
  dispose() {
  }
}
function en(h) {
  const e = [], t = [];
  for (const s of h)
    s instanceof zn ? t.push(s) : e.push(s);
  return { points: e, labels: t };
}
class _a extends xa {
  constructor() {
    super();
    const e = window.devicePixelRatio, t = new ma({ fallback: "default" });
    t.glyphAtlas.drawChar("default", "●", {
      fillStyle: "white",
      strokeStyle: "black",
      strokeWidth: 3 * e,
      font: "30px sans-serif"
    });
    const s = new ga({
      fontFamily: "Arial",
      strokeStyle: "black",
      strokeWidth: 3 * e
    });
    this.group.add(t, s), this.icons = t, this.labels = s;
  }
  // include every feature
  filterAnnotation(e, t, s) {
    return !0;
  }
  measureChar(e, t, s) {
    return this.labels.measureChar(e);
  }
  onPointsUpdate(e, t) {
    this.icons.update(e, t);
  }
  onLabelsUpdate(e, t) {
    this.labels.update(e, t);
  }
  dispose() {
    this.icons.dispose(), this.labels.dispose();
  }
}
class vl {
  get contentCache() {
    return this.overlay.imageSource._contentCache;
  }
  constructor(e = {}) {
    this.priority = 1 / 0, this.name = "MVT_ANNOTATIONS_PLUGIN";
    const {
      overlay: t,
      camera: s = null,
      driver: i = new _a(),
      resolution: n = 50
    } = e;
    this.overlay = t, this.camera = s, this.driver = i, this.resolution = n, this._measureChar = (r) => this.driver.measureChar(r), this._filterAnnotation = (r, o, a) => this.driver.filterAnnotation(r, o, a), this._driverVersion = -1, this.hierarchy = new Ho(), this.occupancy = new Xo(), this.anchorManager = new ra(), this.pointManager = new fa(), this.settlingManager = new Jo(), this.tileLoadState = /* @__PURE__ */ new Map(), this.vectorTileInfo = /* @__PURE__ */ new Map(), this.debug = {
      occupancy: new oa(this.occupancy),
      paths: new la(this.anchorManager),
      hierarchy: new da()
    };
  }
  async init(e) {
    this.tiles = e, e.group.add(this.driver.group), this.driver.group.updateMatrixWorld();
    const {
      overlay: t,
      occupancy: s,
      debug: i,
      hierarchy: n,
      settlingManager: r,
      contentCache: o,
      pointManager: a,
      anchorManager: l
    } = this;
    i.paths.group = e.group, i.hierarchy.hierarchy = n, i.hierarchy.tiles = e, i.hierarchy.tiling = t.tiling, r.occupancy = s, r.tiles = e, n.contentCache = o, t.init(), t.isReady || await t.whenReady(), s.sortCallback = (c, u) => {
      const d = s.visible.has(c), p = s.visible.has(u);
      if (d !== p)
        return d ? -1 : 1;
      const m = this.driver.sortAnnotations(c, u);
      if (m !== 0)
        return m;
      if (c.lodLevel !== u.lodLevel)
        return u.lodLevel - c.lodLevel;
      const f = c.visibleDuration < 5e3 || u.visibleDuration < 5e3;
      return d && f && c.visibleTime !== u.visibleTime ? c.visibleTime < u.visibleTime ? -1 : 1 : u.screenPos.y !== c.screenPos.y ? u.screenPos.y - c.screenPos.y : c.id > u.id ? 1 : -1;
    }, this._onVisibilityChange = ({ scene: c, tile: u, visible: d }) => {
      r.needsUpdate = !0, this._markVectorTile(u, d);
    }, this._onUpdateAfter = () => {
      const { driver: c, camera: u, _measureChar: d } = this, p = c.version !== this._driverVersion;
      if (this._driverVersion = c.version, p) {
        for (const g of a.points)
          g.enabled = c.isAnnotationEnabled(g.layer, g.properties, 1);
        for (const g of l.lines)
          g.enabled = c.isAnnotationEnabled(g.layer, g.properties, 2), g.text = c.getText(g.properties), g.updateCharacterWidthCache(d);
        r.needsUpdate = !0, s.needsUpdate = !0;
      }
      u !== null && (e.getResolution(u, s.resolution), s.matrix.copy(e.group.matrixWorld)), n.update(), a.update(), a.added.forEach((g) => {
        s.register(g), r.register(g);
      }), a.removed.forEach((g) => {
        s.unregister(g), r.unregister(g);
      }), a.reset(), l.update(), l.added.forEach((g) => {
        s.register(g);
      }), l.removed.forEach((g) => {
        s.unregister(g);
      }), l.reset(), s.needsUpdate = s.needsUpdate || r.hasPendingWork, r.camera = u, r.update(), s.camera = u, s.update(), p && (s.flush(), s.finishAnimations());
      const m = en(s.added), f = en(s.removed);
      this.driver.onPointsUpdate(m.points, f.points), this.driver.onLabelsUpdate(m.labels, f.labels), (s.added.size > 0 || s.removed.size > 0) && e.dispatchEvent({ type: "needs-render" }), (s.hasPendingWork || r.hasPendingWork) && e.dispatchEvent({ type: "needs-update" }), i.paths.camera = this.camera, i.occupancy.update(), i.paths.update(), i.hierarchy.update();
    }, this._onVectorTileToggle = ({ x: c, y: u, level: d, visible: p }) => {
      e.dispatchEvent({ type: "needs-update" });
      const {
        contentCache: m,
        driver: f,
        vectorTileInfo: g,
        settlingManager: y,
        anchorManager: x,
        pointManager: _,
        _filterAnnotation: b,
        _measureChar: T
      } = this, v = `${c}_${u}_${d}`;
      if (p) {
        const { tiling: S } = t, M = m.get(c, u, d);
        if (!M) {
          g.set(v, { annotations: [] });
          return;
        }
        const P = [];
        ua(M, c, u, d, S, b, P), $o(M, c, u, d, S, b, P), g.set(v, { annotations: P });
        for (const E of P)
          E instanceof ye ? (y.register(E), E.enabled = f.isAnnotationEnabled(E.layer, E.properties, 2), E.text = f.getText(E.properties), E.updateCharacterWidthCache(T)) : (_.add(E), E.enabled = f.isAnnotationEnabled(E.layer, E.properties, 1));
        x.addLines(P.filter((E) => E instanceof ye));
      } else {
        const { annotations: S } = g.get(v);
        g.delete(v);
        for (const M of S)
          M instanceof ye ? y.unregister(M) : _.delete(M);
        x.deleteLines(S.filter((M) => M instanceof ye));
      }
    }, this._onDisposeModel = ({ tile: c }) => {
      this.tileLoadState.delete(c);
    }, n.addEventListener("toggle", this._onVectorTileToggle), e.addEventListener("update-after", this._onUpdateAfter), e.addEventListener("tile-visibility-change", this._onVisibilityChange), e.addEventListener("dispose-model", this._onDisposeModel), e.forEachLoadedModel((c, u) => {
      this.processTileModel(c, u), e.visibleTiles.has(u) && this._markVectorTile(u, !0);
    });
  }
  dispose() {
    const { debug: e, tiles: t, hierarchy: s, tileLoadState: i } = this;
    e.occupancy.dispose(), e.paths.dispose(), t.group.remove(this.driver.group), this.driver.dispose(), s.removeEventListener("toggle", this._onVectorTileToggle), t.removeEventListener("update-after", this._onUpdateAfter), t.removeEventListener("tile-visibility-change", this._onVisibilityChange), t.removeEventListener("dispose-model", this._onDisposeModel), i.forEach((n, r) => {
      t.visibleTiles.has(r) && this._markVectorTile(r, !1);
    });
  }
  processTileModel(e, t) {
    const { tiles: s, overlay: i } = this;
    Cs.identity(), e.parent !== null && Cs.copy(s.group.matrixWorldInverse), e.updateMatrixWorld();
    const n = ya(e), { range: r } = Ls(n, s.ellipsoid, Cs, i.projection);
    this.tileLoadState.set(t, r);
  }
  //
  _markVectorTile(e, t) {
    const s = this.tileLoadState.get(e);
    this._forEachTileInBounds(s, (i, n, r) => {
      this.hierarchy.setTargetState(i, n, r, t);
    });
  }
  _forEachTileInBounds(e, t) {
    const { overlay: s, resolution: i } = this, { tiling: n } = s, r = s.calculateLevel(e, i);
    if (!s.isReady)
      throw new Error("MVTAnnotationsPlugin: overlay is not ready.");
    le(e, r, n, t);
  }
}
let Ta = null;
function ba() {
  return Ta ?? (Ta = Promise.all([
    import("@mapbox/vector-tile"),
    import("pbf")
  ]).then(([{ VectorTile: h }, { default: e }]) => ({ VectorTile: h, Protobuf: e })));
}
const va = {
  earth: { fill: "#e2dfda", order: 0 },
  water: { fill: "#80deea", order: 1 },
  landcover: { fill: "#c4e7d2", order: 2 },
  landuse: { fill: "#cfddd5", order: 3 },
  natural: { fill: "#e2e0d7", order: 4 },
  buildings: { fill: "#cccccc", order: 5 },
  roads: { stroke: "#ebebeb", order: 6 },
  transit: { stroke: "#a7b1b3", order: 7 },
  boundaries: { stroke: "#adadad", order: 8 },
  places: { fill: "#5c5c5c", order: 9 },
  pois: { fill: "#1a8cbd", radius: 3, order: 10 }
}, wa = (h, e) => va[h] ?? null;
class Wn extends Gs {
  constructor(e = {}) {
    super();
    const {
      url: t = null,
      levels: s = 20,
      projection: i = "EPSG:3857"
    } = e;
    this.url = t, this.levels = s, this.projectionId = i, this.tiling = new Gt(), this.fetchData = (...n) => fetch(...n), this.fetchOptions = {};
  }
  init() {
    const { tiling: e, levels: t, url: s, projectionId: i } = this;
    e.flipY = !/{\s*reverseY|-\s*y\s*}/g.test(s), e.setProjection(new ee(i)), e.setContentBounds(...e.projection.getBounds());
    const n = 512;
    return Array.isArray(t) ? t.forEach((r, o) => {
      r !== null && e.setLevel(o, {
        tilePixelWidth: n,
        tilePixelHeight: n,
        ...r
      });
    }) : e.generateLevels(t, e.projection.tileCountX, e.projection.tileCountY, {
      tilePixelWidth: n,
      tilePixelHeight: n
    }), Promise.resolve();
  }
  async fetchItem([e, t, s], i) {
    const n = this.getUrl(e, t, s), o = await (await this.fetchData(n, { ...this.fetchOptions, signal: i })).arrayBuffer();
    return this._parseVectorTile(o);
  }
  async _parseVectorTile(e) {
    if (!e || e.byteLength === 0)
      return null;
    const { VectorTile: t, Protobuf: s } = await ba();
    return new t(new s(e));
  }
  // Parsed JS objects — nothing to dispose
  disposeItem() {
  }
  getUrl(e, t, s) {
    return this.url.replace(/{\s*z\s*}/gi, s).replace(/{\s*x\s*}/gi, e).replace(/{\s*(y|reverseY|-\s*y)\s*}/gi, t);
  }
}
class Rs extends Ht {
  get tiling() {
    return this._contentCache.tiling;
  }
  get fetchData() {
    return this._contentCache.fetchData;
  }
  set fetchData(e) {
    this._contentCache.fetchData = e;
  }
  get fetchOptions() {
    return this._contentCache.fetchOptions;
  }
  set fetchOptions(e) {
    this._contentCache.fetchOptions = e;
  }
  constructor(e = {}) {
    const {
      resolution: t = 512,
      getStyle: s = null,
      contentCache: i,
      ...n
    } = e;
    super(), this.resolution = t, this.getStyle = s, this._canvasRenderer = new Rt({ tileExtent: 4096 }), this._contentCache = i ?? new Wn(n);
  }
  init() {
    return this._contentCache.init();
  }
  hasContent(e, t, s, i, n) {
    let r = 0;
    return le([e, t, s, i], n, this._contentCache.tiling, () => r++), r > 0;
  }
  async fetchItem([e, t, s, i, n], r) {
    const { resolution: o, _contentCache: a } = this, l = document.createElement("canvas");
    l.width = o, l.height = o;
    const c = [e, t, s, i], u = [];
    le(c, n, a.tiling, (p, m, f) => {
      u.push(a.lock(p, m, f));
    }), await Promise.all(u), r == null || r.throwIfAborted(), this._drawToCanvas(l, c, n);
    const d = new ht(l);
    return d.colorSpace = ct, d.generateMipmaps = !1, d.needsUpdate = !0, d;
  }
  disposeItem(e, [t, s, i, n, r]) {
    le([t, s, i, n], r, this._contentCache.tiling, (o, a, l) => {
      this._contentCache.release(o, a, l);
    }), e && e.dispose();
  }
  redraw(...e) {
    const [t, s, i, n, r] = e, o = this.get(t, s, i, n, r);
    o && (this._drawToCanvas(o.image, [t, s, i, n], r), o.needsUpdate = !0);
  }
  dispose() {
    super.dispose(), this._contentCache.dispose();
  }
  _drawToCanvas(e, t, s) {
    const { _contentCache: i, _canvasRenderer: n } = this, r = e.getContext("2d");
    le(t, s, i.tiling, (o, a, l) => {
      const c = i.tiling.getTileBounds(o, a, l, !0, !1);
      n.setFrame(r, c, t);
      const u = i.get(o, a, l);
      u && this._renderVectorTile(u);
    });
  }
  _renderVectorTile(e) {
    const { _canvasRenderer: t } = this, s = this.getStyle || wa, i = [...Object.keys(e.layers)].sort((n, r) => {
      var l, c;
      const o = ((l = s(n, null)) == null ? void 0 : l.order) ?? Rt.DEFAULT_STYLE.order, a = ((c = s(r, null)) == null ? void 0 : c.order) ?? Rt.DEFAULT_STYLE.order;
      return o !== a ? o - a : n.localeCompare(r);
    });
    for (const n of i) {
      const r = e.layers[n];
      for (let o = 0; o < r.length; o++) {
        const a = r.feature(o), { properties: l, type: c } = a, u = s(n, l);
        t.setStyle(u);
        const d = a.loadGeometry();
        c === 1 ? t._renderPoints(d) : c === 2 ? t._renderLines(d) : c === 3 && t._renderPolygons(d);
      }
    }
  }
}
const It = Math.PI / 180;
let Sa = null;
function Ma() {
  return Sa ?? (Sa = import("pmtiles").then((h) => h.PMTiles));
}
class Ca extends Ge {
  constructor(e, t) {
    super(), this.instance = e, this.tiling = t;
  }
  async fetchItem([e, t, s], i) {
    const n = await this.instance.getZxy(s, e, t, i);
    return !n || !n.data || n.data.byteLength === 0 ? null : this.processBufferToTexture(n.data);
  }
}
class Aa extends Wn {
  constructor(e = {}) {
    super(e), this.instance = null, this.tileType = 1;
  }
  async init() {
    const { tiling: e } = this, t = await Ma();
    this.instance = new t({
      getKey: () => this.url,
      getBytes: async (n, r, o) => {
        o && o.throwIfAborted();
        const { fetchOptions: a, url: l } = this, c = await this.fetchData(l, {
          ...a,
          signal: o,
          headers: {
            ...a.headers,
            range: `bytes=${n}-${n + r - 1}`
          }
        });
        if (!c.ok)
          throw new Error(`PMTilesImageSource: Bad response code: ${c.status}`);
        if (c.status !== 206)
          throw new Error("PMTilesImageSource: Server does not support HTTP Byte Serving.");
        return {
          data: await c.arrayBuffer(),
          etag: c.headers.get("ETag"),
          cacheControl: c.headers.get("Cache-Control"),
          expires: c.headers.get("Expires")
        };
      }
    });
    const s = await this.instance.getHeader();
    this.tileType = s.tileType;
    const i = new ee("EPSG:3857");
    e.flipY = !0, e.setProjection(i), e.setContentBounds(
      It * s.minLon,
      It * s.minLat,
      It * s.maxLon,
      It * s.maxLat
    ), e.generateLevels(s.maxZoom + 1, i.tileCountX, i.tileCountY, {
      tilePixelWidth: 512,
      tilePixelHeight: 512,
      minLevel: s.minZoom
    });
  }
  async fetchItem([e, t, s], i) {
    const n = await this.instance.getZxy(s, e, t, i);
    return this._parseVectorTile(n ? n.data : null);
  }
}
class La extends Ht {
  get tiling() {
    return this._contentCache.tiling;
  }
  get fetchData() {
    return this._contentCache.fetchData;
  }
  set fetchData(e) {
    this._contentCache.fetchData = e;
  }
  get resolution() {
    return this._resolution;
  }
  set resolution(e) {
    this._resolution = e, this._deferredSource && (this._deferredSource.resolution = e);
  }
  get fetchOptions() {
    return this._contentCache.fetchOptions;
  }
  set fetchOptions(e) {
    this._contentCache.fetchOptions = e;
  }
  constructor(e = {}) {
    super();
    const {
      resolution: t = 512,
      getStyle: s = null
    } = e;
    this._resolution = t, this._getStyle = s, this._contentCache = new Aa(e), this._deferredSource = null, this.isVectorTile = !1;
  }
  async init() {
    await this._contentCache.init();
    const { _contentCache: e } = this;
    if (this.isVectorTile = e.tileType === 1, this.isVectorTile)
      this._deferredSource = new Rs({
        resolution: this._resolution,
        getStyle: this._getStyle,
        contentCache: e
      });
    else {
      const t = new Ca(e.instance, e.tiling);
      this._deferredSource = new wn(t), this._deferredSource.resolution = this._resolution;
    }
  }
  hasContent(e, t, s, i, n) {
    return this._deferredSource.hasContent(e, t, s, i, n);
  }
  lock(...e) {
    return this._deferredSource.lock(...e);
  }
  release(...e) {
    this._deferredSource.release(...e);
  }
  get(...e) {
    return this._deferredSource.get(...e);
  }
  redraw(...e) {
    this._deferredSource instanceof Rs && this._deferredSource.redraw(...e);
  }
  forEachItem(...e) {
    return this._deferredSource.forEachItem(...e);
  }
  dispose() {
    super.dispose(), this._contentCache.dispose(), this._deferredSource && this._deferredSource.dispose();
  }
}
class Ea extends Hs {
  get tiling() {
    return this.imageSource.tiling;
  }
  get projection() {
    return this.tiling.projection;
  }
  get aspectRatio() {
    return this.tiling && this.isReady ? this.tiling.aspectRatio : 1;
  }
  get fetchOptions() {
    return this.imageSource.fetchOptions;
  }
  set fetchOptions(e) {
    this.imageSource.fetchOptions = e;
  }
  get resolution() {
    return this.imageSource.resolution;
  }
  constructor(e = {}) {
    super(e), this.imageSource = e.imageSource ?? new Rs(e), this._redrawQueue = new zs(), this._redrawQueue.maxJobs = 4, this._redrawQueue.priorityCallback = () => 0;
  }
  _init() {
    return this.imageSource.fetchData = (...e) => this.fetch(...e), this.imageSource.init();
  }
  // the MVTOverlay provides an optional resolution argument so that
  // MVTAnnotationsPlugin can adjust it to prevent large amounts of
  // annotations from loading.
  calculateLevel(e, t = this.resolution) {
    const [s, i, n, r] = e, o = n - s, a = r - i, l = this.tiling.maxLevel;
    let c = 0;
    for (; c < l; c++) {
      const u = this.tiling.getLevel(c);
      if (u == null)
        continue;
      const { pixelWidth: d, pixelHeight: p } = u;
      if (d >= t / o || p >= t / a)
        break;
    }
    return c;
  }
  hasContent(e, t = this.calculateLevel(e)) {
    return this.imageSource.hasContent(...e, t);
  }
  getTexture(e, t = this.calculateLevel(e)) {
    return this.imageSource.get(...e, t);
  }
  lockTexture(e, t = this.calculateLevel(e)) {
    return this.imageSource.lock(...e, t);
  }
  releaseTexture(e, t = this.calculateLevel(e)) {
    this.imageSource.release(...e, t);
  }
  setResolution(e) {
    this.imageSource.resolution = e;
  }
  shouldSplit(e) {
    return !0;
  }
  setRegionVisible(e, t) {
    if (super.setRegionVisible(e, t), t) {
      const { _redrawQueue: s } = this, i = e.join("_") + "_" + this.calculateLevel(e);
      s.has(i) && s.flush(i);
    }
  }
  redraw() {
    const {
      imageSource: e,
      _redrawQueue: t,
      _visibleRegionCounts: s
    } = this;
    for (const { range: i } of s.values())
      e.redraw(...i, this.calculateLevel(i));
    e.forEachItem((i, n) => {
      const r = n.join("_");
      !s.has(r) && !t.has(r) && t.add(r, () => {
        e.redraw(...n);
      });
    });
  }
}
class wl extends Ea {
  constructor(e = {}) {
    super({ ...e, imageSource: new La(e) });
  }
  shouldSplit(e) {
    return this.imageSource.isVectorTile ? !0 : this.tiling.maxLevel > this.calculateLevel(e);
  }
}
const Vt = xn * Math.PI * 2, tn = /* @__PURE__ */ new ee("EPSG:3857");
function Ia(h) {
  return /:4326$/i.test(h);
}
function Hn(h) {
  return /:3857$/i.test(h);
}
function Ds(h) {
  return h.trim().split(/\s+/).map((e) => parseFloat(e));
}
function Bs(h, e) {
  Ia(e) && ([h[1], h[0]] = [h[0], h[1]]);
}
function kt(h, e) {
  if (Hn(e))
    return h[0] = tn.convertNormalizedToLongitude(0.5 + h[0] / Vt), h[1] = tn.convertNormalizedToLatitude(0.5 + h[1] / Vt), h[0] *= w.RAD2DEG, h[1] *= w.RAD2DEG, h;
}
function Nt(h) {
  h[0] *= w.DEG2RAD, h[1] *= w.DEG2RAD;
}
class Sl extends _n {
  parse(e) {
    const t = new TextDecoder("utf-8").decode(new Uint8Array(e)), s = new DOMParser().parseFromString(t, "text/xml"), i = s.querySelector("Contents"), n = me(i, "TileMatrixSet").map((a) => Oa(a)), r = me(i, "Layer").map((a) => Ra(a)), o = Pa(s.querySelector("ServiceIdentification"));
    return r.forEach((a) => {
      a.tileMatrixSets = a.tileMatrixSetLinks.map((l) => n.find((c) => c.identifier === l));
    }), {
      serviceIdentification: o,
      tileMatrixSets: n,
      layers: r
    };
  }
}
function Pa(h) {
  var n;
  const e = h.querySelector("Title").textContent, t = ((n = h.querySelector("Abstract")) == null ? void 0 : n.textContent) || "", s = h.querySelector("ServiceType").textContent, i = h.querySelector("ServiceTypeVersion").textContent;
  return {
    title: e,
    abstract: t,
    serviceType: s,
    serviceTypeVersion: i
  };
}
function Ra(h) {
  const e = h.querySelector("Title").textContent, t = h.querySelector("Identifier").textContent, s = h.querySelector("Format").textContent, i = me(h, "ResourceURL").map((l) => Da(l)), n = me(h, "TileMatrixSetLink").map((l) => me(l, "TileMatrixSet")[0].textContent), r = me(h, "Style").map((l) => Ua(l)), o = me(h, "Dimension").map((l) => Ba(l));
  let a = sn(h.querySelector("WGS84BoundingBox"));
  return a || (a = sn(h.querySelector("BoundingBox"))), {
    title: e,
    identifier: t,
    format: s,
    dimensions: o,
    tileMatrixSetLinks: n,
    styles: r,
    boundingBox: a,
    resourceUrls: i
  };
}
function Da(h) {
  const e = h.getAttribute("template"), t = h.getAttribute("format"), s = h.getAttribute("resourceType");
  return {
    template: e,
    format: t,
    resourceType: s
  };
}
function Ba(h) {
  var r, o;
  const e = h.querySelector("Identifier").textContent, t = ((r = h.querySelector("UOM")) == null ? void 0 : r.textContent) || "", s = h.querySelector("Default").textContent, i = ((o = h.querySelector("Current")) == null ? void 0 : o.textContent) === "true", n = me(h, "Value").map((a) => a.textContent);
  return {
    identifier: e,
    uom: t,
    defaultValue: s,
    current: i,
    values: n
  };
}
function sn(h) {
  if (!h)
    return null;
  const e = h.nodeName.endsWith("WGS84BoundingBox") ? "urn:ogc:def:crs:CRS::84" : h.getAttribute("crs"), t = Ds(h.querySelector("LowerCorner").textContent), s = Ds(h.querySelector("UpperCorner").textContent);
  return Bs(t, e), Bs(s, e), kt(t, e), kt(s, e), Nt(t), Nt(s), {
    crs: e,
    lowerCorner: t,
    upperCorner: s,
    bounds: [...t, ...s]
  };
}
function Ua(h) {
  var i;
  const e = ((i = h.querySelector("Title")) == null ? void 0 : i.textContent) || null, t = h.querySelector("Identifier").textContent, s = h.getAttribute("isDefault") === "true";
  return {
    title: e,
    identifier: t,
    isDefault: s
  };
}
function Oa(h) {
  var r, o;
  const e = h.querySelector("SupportedCRS").textContent, t = ((r = h.querySelector("Title")) == null ? void 0 : r.textContent) || "", s = h.querySelector("Identifier").textContent, i = ((o = h.querySelector("Abstract")) == null ? void 0 : o.textContent) || "", n = [];
  return h.querySelectorAll("TileMatrix").forEach((a, l) => {
    const c = Va(a), u = 28e-5 * c.scaleDenominator, d = c.tileWidth * c.matrixWidth * u, p = c.tileHeight * c.matrixHeight * u;
    let m;
    Bs(c.topLeftCorner, e), Hn(e) ? m = [
      c.topLeftCorner[0] + d,
      c.topLeftCorner[1] - p
    ] : m = [
      c.topLeftCorner[0] + 360 * d / Vt,
      c.topLeftCorner[1] - 360 * p / Vt
    ], kt(m, e), kt(c.topLeftCorner, e), Nt(m), Nt(c.topLeftCorner), c.bounds = [...c.topLeftCorner, ...m], [c.bounds[1], c.bounds[3]] = [c.bounds[3], c.bounds[1]], n.push(c);
  }), {
    title: t,
    identifier: s,
    abstract: i,
    supportedCRS: e,
    tileMatrices: n
  };
}
function Va(h) {
  const e = h.querySelector("Identifier").textContent, t = parseFloat(h.querySelector("TileWidth").textContent), s = parseFloat(h.querySelector("TileHeight").textContent), i = parseFloat(h.querySelector("MatrixWidth").textContent), n = parseFloat(h.querySelector("MatrixHeight").textContent), r = parseFloat(h.querySelector("ScaleDenominator").textContent), o = Ds(h.querySelector("TopLeftCorner").textContent);
  return {
    identifier: e,
    tileWidth: t,
    tileHeight: s,
    matrixWidth: i,
    matrixHeight: n,
    scaleDenominator: r,
    topLeftCorner: o,
    bounds: null
  };
}
function me(h, e) {
  return [...h.children].filter((t) => t.tagName === e);
}
const nn = xn * Math.PI * 2, rn = /* @__PURE__ */ new ee("EPSG:3857");
function ka(h) {
  return /:4326$/i.test(h);
}
function Na(h) {
  return /:3857$/i.test(h);
}
function on(h, e) {
  return Na(e) && (h[0] = rn.convertNormalizedToLongitude(0.5 + h[0] / (Math.PI * 2 * nn)), h[1] = rn.convertNormalizedToLatitude(0.5 + h[1] / (Math.PI * 2 * nn)), h[0] *= w.RAD2DEG, h[1] *= w.RAD2DEG), h;
}
function an(h, e, t) {
  const [s, i] = t.split(".").map((r) => parseInt(r)), n = s === 1 && i < 3 || s < 1;
  ka(e) && n && ([h[0], h[1]] = [h[1], h[0]]);
}
function ze(h) {
  h[0] *= w.DEG2RAD, h[1] *= w.DEG2RAD;
}
function Fa(h, e) {
  if (!h)
    return null;
  const t = h.getAttribute("CRS") || h.getAttribute("crs") || h.getAttribute("SRS") || "", s = parseFloat(h.getAttribute("minx")), i = parseFloat(h.getAttribute("miny")), n = parseFloat(h.getAttribute("maxx")), r = parseFloat(h.getAttribute("maxy")), o = [s, i], a = [n, r];
  return an(o, t, e), an(a, t, e), on(o, t), on(a, t), ze(o), ze(a), { crs: t, bounds: [...o, ...a] };
}
function za(h) {
  const e = parseFloat(h.querySelector("westBoundLongitude").textContent), t = parseFloat(h.querySelector("eastBoundLongitude").textContent), s = parseFloat(h.querySelector("southBoundLatitude").textContent), i = parseFloat(h.querySelector("northBoundLatitude").textContent), n = [e, s], r = [t, i];
  return ze(n), ze(r), [...n, ...r];
}
function Ga(h) {
  const e = parseFloat(h.getAttribute("minx").textContent), t = parseFloat(h.getAttribute("maxx").textContent), s = parseFloat(h.getAttribute("miny").textContent), i = parseFloat(h.getAttribute("maxy").textContent), n = [e, s], r = [t, i];
  return ze(n), ze(r), [...n, ...r];
}
function Wa(h) {
  const e = h.querySelector("Name").textContent, t = h.querySelector("Title").textContent, s = [...h.querySelectorAll("LegendURL")].map((i) => {
    const n = parseInt(i.getAttribute("width")), r = parseInt(i.getAttribute("height")), o = i.querySelector("Format").textContent, a = i.querySelector("OnlineResource"), l = Us(a);
    return {
      width: n,
      height: r,
      format: o,
      url: l
    };
  });
  return {
    name: e,
    title: t,
    legends: s
  };
}
function Yn(h, e, t = {}) {
  var f, g, y;
  let {
    styles: s = [],
    crs: i = [],
    contentBoundingBox: n = null,
    queryable: r = !1,
    opaque: o = !1
  } = t;
  const a = ((f = h.querySelector(":scope > Name")) == null ? void 0 : f.textContent) || null, l = ((g = h.querySelector(":scope > Title")) == null ? void 0 : g.textContent) || "", c = ((y = h.querySelector(":scope > Abstract")) == null ? void 0 : y.textContent) || "", u = [...h.querySelectorAll(":scope > Keyword")].map((x) => x.textContent), p = [...h.querySelectorAll(":scope > BoundingBox")].map((x) => Fa(x, e));
  i = [
    ...i,
    ...Array.from(h.querySelectorAll("CRS")).map((x) => x.textContent)
  ], s = [
    ...s,
    ...Array.from(h.querySelectorAll(":scope > Style")).map((x) => Wa(x))
  ], h.hasAttribute("queryable") && (r = h.getAttribute("queryable") === "1"), h.hasAttribute("opaque") && (o = h.getAttribute("opaque") === "1"), h.querySelector("EX_GeographicBoundingBox") ? n = za(h.querySelector("EX_GeographicBoundingBox")) : h.querySelector("LatLonBoundingBox") && (n = Ga(h.querySelector("LatLonBoundingBox")));
  const m = Array.from(h.querySelectorAll(":scope > Layer")).map((x) => Yn(x, e, {
    // add
    styles: s,
    crs: i,
    // replace
    contentBoundingBox: n,
    queryable: r,
    opaque: o
  }));
  return {
    name: a,
    title: l,
    abstract: c,
    queryable: r,
    opaque: o,
    keywords: u,
    crs: i,
    boundingBoxes: p,
    contentBoundingBox: n,
    styles: s,
    subLayers: m
  };
}
function Ha(h) {
  var e, t, s;
  return {
    name: ((e = h.querySelector("Name")) == null ? void 0 : e.textContent) || "",
    title: ((t = h.querySelector("Title")) == null ? void 0 : t.textContent) || "",
    abstract: ((s = h.querySelector("Abstract")) == null ? void 0 : s.textContent) || "",
    keywords: Array.from(h.querySelectorAll("Keyword")).map((i) => i.textContent),
    maxWidth: parseFloat(h.querySelector("MaxWidth")) || null,
    maxHeight: parseFloat(h.querySelector("MaxHeight")) || null,
    layerLimit: parseFloat(h.querySelector("LayerLimit")) || null
  };
}
function Us(h) {
  return h ? (h.getAttribute("xlink:href") || h.getAttributeNS("http://www.w3.org/1999/xlink", "href") || "").trim() : "";
}
function Ya(h) {
  const e = Array.from(h.querySelectorAll("Format")).map((s) => s.textContent.trim()), t = Array.from(h.querySelectorAll("DCPType")).map((s) => {
    const i = s.querySelector("HTTP"), n = i.querySelector("Get OnlineResource") || i.querySelector("Get > OnlineResource") || i.querySelector("Get"), r = i.querySelector("Post OnlineResource") || i.querySelector("Post > OnlineResource") || i.querySelector("Post"), o = Us(n), a = Us(r);
    return { type: "HTTP", get: o, post: a };
  });
  return { formats: e, dcp: t, href: t[0].get };
}
function qa(h) {
  const e = {};
  return Array.from(h.querySelectorAll(":scope > *")).forEach((t) => {
    const s = t.localName;
    e[s] = Ya(t);
  }), e;
}
function qn(h, e = []) {
  return h.forEach((t) => {
    t.name !== null && e.push(t), qn(t.subLayers, e);
  }), e;
}
class Ml extends _n {
  parse(e) {
    const t = new TextDecoder("utf-8").decode(new Uint8Array(e)), s = new DOMParser().parseFromString(t, "text/xml"), n = (s.querySelector("WMS_Capabilities") || s.querySelector("WMT_MS_Capabilities")).getAttribute("version"), r = s.querySelector("Capability"), o = Ha(s.querySelector(":scope > Service")), a = qa(r.querySelector(":scope > Request")), l = Array.from(r.querySelectorAll(":scope > Layer")).map((u) => Yn(u, n)), c = qn(l);
    return { version: n, service: o, layers: c, request: a };
  }
}
export {
  Ee as A,
  Xs as B,
  ll as C,
  bl as D,
  pl as E,
  cl as F,
  Co as G,
  nl as H,
  Hs as I,
  Sl as J,
  rl as K,
  yl as L,
  xa as M,
  Tl as O,
  wl as P,
  no as Q,
  _l as R,
  xl as S,
  ve as T,
  fl as U,
  Ml as W,
  tl as X,
  ml as a,
  ol as b,
  sl as c,
  _a as d,
  ul as e,
  Mo as f,
  vo as g,
  Rr as h,
  il as i,
  al as j,
  el as k,
  vl as l,
  pa as m,
  Ki as n,
  Gn as o,
  ma as p,
  ga as q,
  Ea as r,
  So as s,
  dl as t,
  Mi as u,
  Pe as v,
  Re as w,
  $r as x,
  hl as y,
  gl as z
};
//# sourceMappingURL=WMSCapabilitiesLoader-BAEVskb_.js.map
