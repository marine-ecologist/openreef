import { e as ot, d as Tt } from "./TilesRendererBase-BGxy2Uih.js";
import { MathUtils as D, Spherical as mt, Vector3 as u, Matrix4 as R, Sphere as Et, Ray as yt, Euler as St, Box3 as dt, Plane as wt, TextureUtils as _t } from "three";
import { estimateBytesUsed as zt } from "three/addons/utils/BufferGeometryUtils.js";
const F = /* @__PURE__ */ new mt(), et = /* @__PURE__ */ new u(), Ct = {};
function xt(c) {
  const { x: t, y: i, z: o } = c;
  c.x = o, c.y = t, c.z = i;
}
function Ft(c) {
  const { x: t, y: i, z: o } = c;
  c.z = t, c.x = i, c.y = o;
}
function gt(c) {
  return -(c - Math.PI / 2);
}
function J(c) {
  return -c + Math.PI / 2;
}
function Rt(c, t, i = {}) {
  return F.theta = t, F.phi = J(c), et.setFromSpherical(F), F.setFromVector3(et), i.lat = gt(F.phi), i.lon = F.theta, i;
}
function st(c, t = "E", i = "W") {
  const o = c < 0 ? i : t;
  c = Math.abs(c);
  const s = ~~c, e = (c - s) * 60, r = ~~e, l = ~~((e - r) * 60);
  return `${s}° ${r}' ${l}" ${o}`;
}
function bt(c, t, i = !1) {
  const o = Rt(c, t, Ct);
  let s, e;
  return i ? (s = `${(D.RAD2DEG * o.lat).toFixed(4)}°`, e = `${(D.RAD2DEG * o.lon).toFixed(4)}°`) : (s = st(D.RAD2DEG * o.lat, "N", "S"), e = st(D.RAD2DEG * o.lon, "E", "W")), `${s} ${e}`;
}
const Ot = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  latitudeToSphericalPhi: J,
  sphericalPhiToLatitude: gt,
  swapToGeoFrame: xt,
  swapToThreeFrame: Ft,
  toLatLonString: bt
}, Symbol.toStringTag, { value: "Module" })), nt = /* @__PURE__ */ new mt(), _ = /* @__PURE__ */ new u(), y = /* @__PURE__ */ new u(), Y = /* @__PURE__ */ new u(), P = /* @__PURE__ */ new R(), S = /* @__PURE__ */ new R(), V = /* @__PURE__ */ new Et(), g = /* @__PURE__ */ new St(), rt = /* @__PURE__ */ new u(), at = /* @__PURE__ */ new u(), ct = /* @__PURE__ */ new u(), A = /* @__PURE__ */ new u(), q = /* @__PURE__ */ new yt(), vt = 1e-12, Nt = 0.1, At = 0, lt = 1, L = 2;
class ft {
  constructor(t = 1, i = 1, o = 1) {
    this.name = "", this.radius = new u(t, i, o);
  }
  /**
   * Returns the point where the given ray intersects the ellipsoid surface, or null if no
   * intersection exists. Writes the result into `target`.
   * @param {Ray} ray
   * @param {Vector3} target
   * @returns {Vector3|null}
   */
  intersectRay(t, i) {
    return P.makeScale(...this.radius).invert(), V.center.set(0, 0, 0), V.radius = 1, q.copy(t).applyMatrix4(P), q.intersectSphere(V, i) ? (P.makeScale(...this.radius), i.applyMatrix4(P), i) : null;
  }
  /**
   * Returns a Matrix4 representing the East-North-Up (ENU) frame at the given geographic
   * position: X points east, Y points north, Z points up. Writes the result into `target`.
   * @param {number} lat Latitude in radians.
   * @param {number} lon Longitude in radians.
   * @param {number} height Height above the ellipsoid surface in meters.
   * @param {Matrix4} target
   * @returns {Matrix4}
   */
  getEastNorthUpFrame(t, i, o, s) {
    return o.isMatrix4 && (s = o, o = 0, console.warn('Ellipsoid: The signature for "getEastNorthUpFrame" has changed.')), this.getEastNorthUpAxes(t, i, rt, at, ct), this.getCartographicToPosition(t, i, o, A), s.makeBasis(rt, at, ct).setPosition(A);
  }
  /**
   * Returns a Matrix4 representing the ENU frame at the given position, rotated by the given
   * azimuth, elevation, and roll. Equivalent to `getObjectFrame` with `ENU_FRAME`.
   * @param {number} lat Latitude in radians.
   * @param {number} lon Longitude in radians.
   * @param {number} height Height above the ellipsoid surface in meters.
   * @param {number} az Azimuth in radians, measured from true north towards east.
   * @param {number} el Elevation in radians, measured from the horizon upward.
   * @param {number} roll Roll in radians around the north axis.
   * @param {Matrix4} target
   * @returns {Matrix4}
   */
  getOrientedEastNorthUpFrame(t, i, o, s, e, r, a) {
    return this.getObjectFrame(t, i, o, s, e, r, a, At);
  }
  /**
   * Returns a Matrix4 representing a frame at the given geographic position, rotated by the
   * given azimuth, elevation, and roll, and adjusted to match the three.js `frame` convention.
   * `OBJECT_FRAME` orients with "+Y" up and "+Z" forward; `CAMERA_FRAME` orients with "+Y" up
   * and "-Z" forward; `ENU_FRAME` returns the raw ENU-relative rotation.
   * @param {number} lat Latitude in radians.
   * @param {number} lon Longitude in radians.
   * @param {number} height Height above the ellipsoid surface in meters.
   * @param {number} az Azimuth in radians, measured from true north towards east.
   * @param {number} el Elevation in radians, measured from the horizon upward.
   * @param {number} roll Roll in radians around the north axis.
   * @param {Matrix4} target
   * @param {Frames} [frame=OBJECT_FRAME]
   * @returns {Matrix4}
   */
  getObjectFrame(t, i, o, s, e, r, a, l = L) {
    return this.getEastNorthUpFrame(t, i, o, P), g.set(e, r, -s, "ZXY"), a.makeRotationFromEuler(g).premultiply(P), l === lt ? (g.set(Math.PI / 2, 0, 0, "XYZ"), S.makeRotationFromEuler(g), a.multiply(S)) : l === L && (g.set(-Math.PI / 2, 0, Math.PI, "XYZ"), S.makeRotationFromEuler(g), a.multiply(S)), a;
  }
  /**
   * Extracts geographic position and orientation (lat, lon, height, azimuth, elevation, roll)
   * from the given object/camera frame matrix. The inverse of `getObjectFrame`. Writes the
   * result into `target` and returns it.
   * @param {Matrix4} matrix
   * @param {Object} target
   * @param {Frames} [frame=OBJECT_FRAME]
   * @returns {{ lat: number, lon: number, height: number, azimuth: number, elevation: number, roll: number }}
   */
  getCartographicFromObjectFrame(t, i, o = L) {
    return o === lt ? (g.set(-Math.PI / 2, 0, 0, "XYZ"), S.makeRotationFromEuler(g).premultiply(t)) : o === L ? (g.set(-Math.PI / 2, 0, Math.PI, "XYZ"), S.makeRotationFromEuler(g).premultiply(t)) : S.copy(t), A.setFromMatrixPosition(S), this.getPositionToCartographic(A, i), this.getEastNorthUpFrame(i.lat, i.lon, 0, P).invert(), S.premultiply(P), g.setFromRotationMatrix(S, "ZXY"), i.azimuth = -g.z, i.elevation = g.x, i.roll = g.y, i;
  }
  /**
   * Fills in the east, north, and up unit vectors for the ENU frame at the given latitude and
   * longitude. Optionally writes the surface position into `point`.
   * @param {number} lat Latitude in radians.
   * @param {number} lon Longitude in radians.
   * @param {Vector3} vecEast
   * @param {Vector3} vecNorth
   * @param {Vector3} vecUp
   * @param {Vector3} [point]
   */
  getEastNorthUpAxes(t, i, o, s, e, r = A) {
    this.getCartographicToPosition(t, i, 0, r), this.getCartographicToNormal(t, i, e), o.set(-r.y, r.x, 0).normalize(), s.crossVectors(e, o).normalize();
  }
  /**
   * Converts geographic coordinates to a 3D Cartesian position on the ellipsoid surface
   * (plus the given height offset). Writes the result into `target` and returns it.
   * @param {number} lat Latitude in radians.
   * @param {number} lon Longitude in radians.
   * @param {number} height Height above the ellipsoid surface in meters.
   * @param {Vector3} target
   * @returns {Vector3}
   */
  getCartographicToPosition(t, i, o, s) {
    this.getCartographicToNormal(t, i, _);
    const e = this.radius;
    y.copy(_), y.x *= e.x ** 2, y.y *= e.y ** 2, y.z *= e.z ** 2;
    const r = Math.sqrt(_.dot(y));
    return y.divideScalar(r), s.copy(y).addScaledVector(_, o);
  }
  /**
   * Converts a 3D Cartesian position to geographic coordinates (lat, lon, height). Writes the
   * result into `target` and returns it.
   * @param {Vector3} pos
   * @param {Object} target
   * @returns {{ lat: number, lon: number, height: number }}
   */
  getPositionToCartographic(t, i) {
    this.getPositionToSurfacePoint(t, y), this.getPositionToNormal(y, _);
    const o = Y.subVectors(t, y);
    return i.lon = Math.atan2(_.y, _.x), i.lat = Math.asin(_.z), i.height = Math.sign(o.dot(t)) * o.length(), i;
  }
  /**
   * Returns the surface normal of the ellipsoid at the given latitude and longitude. Writes the
   * result into `target` and returns it.
   * @param {number} lat Latitude in radians.
   * @param {number} lon Longitude in radians.
   * @param {Vector3} target
   * @returns {Vector3}
   */
  getCartographicToNormal(t, i, o) {
    return nt.set(1, J(t), i), o.setFromSpherical(nt).normalize(), xt(o), o;
  }
  /**
   * Returns the surface normal of the ellipsoid at the given 3D Cartesian position. Writes the
   * result into `target` and returns it.
   * @param {Vector3} pos
   * @param {Vector3} target
   * @returns {Vector3}
   */
  getPositionToNormal(t, i) {
    const o = this.radius;
    return i.copy(t), i.x /= o.x ** 2, i.y /= o.y ** 2, i.z /= o.z ** 2, i.normalize(), i;
  }
  /**
   * Projects the given 3D position onto the ellipsoid surface along the geodetic normal.
   * Returns null if the position is at or near the center. Writes the result into `target`.
   * @param {Vector3} pos
   * @param {Vector3} target
   * @returns {Vector3|null}
   */
  getPositionToSurfacePoint(t, i) {
    const o = this.radius, s = 1 / o.x ** 2, e = 1 / o.y ** 2, r = 1 / o.z ** 2, a = t.x * t.x * s, l = t.y * t.y * e, h = t.z * t.z * r, p = a + l + h, w = Math.sqrt(1 / p), M = y.copy(t).multiplyScalar(w);
    if (p < Nt)
      return isFinite(w) ? i.copy(M) : null;
    const E = Y.set(
      M.x * s * 2,
      M.y * e * 2,
      M.z * r * 2
    );
    let m = (1 - w) * t.length() / (0.5 * E.length()), x = 0, $, K, b, v, N, k, j, X, Q, tt, it;
    do {
      m -= x, b = 1 / (1 + m * s), v = 1 / (1 + m * e), N = 1 / (1 + m * r), k = b * b, j = v * v, X = N * N, Q = k * b, tt = j * v, it = X * N, $ = a * k + l * j + h * X - 1, K = a * Q * s + l * tt * e + h * it * r;
      const Pt = -2 * K;
      x = $ / Pt;
    } while (Math.abs($) > vt);
    return i.set(
      t.x * b,
      t.y * v,
      t.z * N
    );
  }
  /**
   * Returns the geometric distance to the horizon from the given latitude and elevation above
   * the ellipsoid surface.
   * @param {number} latitude Latitude in degrees.
   * @param {number} elevation Height above the ellipsoid surface in meters.
   * @returns {number}
   */
  calculateHorizonDistance(t, i) {
    const o = this.calculateEffectiveRadius(t);
    return Math.sqrt(2 * o * i + i ** 2);
  }
  /**
   * Returns the prime vertical radius of curvature (distance from the center of the ellipsoid
   * to the surface along the normal) at the given latitude.
   * @param {number} latitude Latitude in degrees.
   * @returns {number}
   */
  calculateEffectiveRadius(t) {
    const i = this.radius.x, s = 1 - this.radius.z ** 2 / i ** 2, e = t * D.DEG2RAD, r = Math.sin(e) ** 2;
    return i / Math.sqrt(1 - s * r);
  }
  /**
   * Returns the height of the given 3D position above (or below) the ellipsoid surface.
   * @param {Vector3} pos
   * @returns {number}
   */
  getPositionElevation(t) {
    this.getPositionToSurfacePoint(t, y);
    const i = Y.subVectors(t, y);
    return Math.sign(i.dot(t)) * i.length();
  }
  /**
   * Returns an estimate of the closest point on the ellipsoid surface to the given ray.
   * Returns the exact surface intersection point if the ray intersects the ellipsoid.
   * @param {Ray} ray
   * @param {Vector3} target
   * @returns {Vector3}
   */
  closestPointToRayEstimate(t, i) {
    return this.intersectRay(t, i) ? i : (P.makeScale(...this.radius).invert(), q.copy(t).applyMatrix4(P), y.set(0, 0, 0), q.closestPointToPoint(y, i).normalize(), P.makeScale(...this.radius), i.applyMatrix4(P));
  }
  /**
   * Copies the radius from the given ellipsoid into this one.
   * @param {Ellipsoid} source
   * @returns {this}
   */
  copy(t) {
    return this.radius.copy(t.radius), this;
  }
  /**
   * Returns a new Ellipsoid with the same radius as this one.
   * @returns {Ellipsoid}
   */
  clone() {
    return new this.constructor().copy(this);
  }
}
const Bt = new ft(ot, ot, Tt);
Bt.name = "WGS84 Earth";
const U = /* @__PURE__ */ new u(), O = /* @__PURE__ */ new u(), f = /* @__PURE__ */ new u(), G = /* @__PURE__ */ new yt();
class Gt {
  constructor(t = new dt(), i = new R()) {
    this.box = t.clone(), this.transform = i.clone(), this.inverseTransform = new R(), this.points = new Array(8).fill().map(() => new u()), this.planes = new Array(6).fill().map(() => new wt());
  }
  copy(t) {
    return this.box.copy(t.box), this.transform.copy(t.transform), this.update(), this;
  }
  clone() {
    return new this.constructor().copy(this);
  }
  /**
   * Clamps the given point within the bounds of this OBB
   * @param {Vector3} point
   * @param {Vector3} result
   * @returns {Vector3}
   */
  clampPoint(t, i) {
    return i.copy(t).applyMatrix4(this.inverseTransform).clamp(this.box.min, this.box.max).applyMatrix4(this.transform);
  }
  /**
   * Returns the distance from any edge of this OBB to the specified point.
   * If the point lies inside of this box, the distance will be 0.
   * @param {Vector3} point
   * @returns {number}
   */
  distanceToPoint(t) {
    return this.clampPoint(t, f).distanceTo(t);
  }
  containsPoint(t) {
    return f.copy(t).applyMatrix4(this.inverseTransform), this.box.containsPoint(f);
  }
  // returns boolean indicating whether the ray has intersected the obb
  intersectsRay(t) {
    return G.copy(t).applyMatrix4(this.inverseTransform), G.intersectsBox(this.box);
  }
  // Sets "target" equal to the intersection point.
  // Returns "null" if no intersection found.
  intersectRay(t, i) {
    return G.copy(t).applyMatrix4(this.inverseTransform), G.intersectBox(this.box, i) ? (i.applyMatrix4(this.transform), i) : null;
  }
  update() {
    const { points: t, inverseTransform: i, transform: o, box: s } = this;
    i.copy(o).invert();
    const { min: e, max: r } = s;
    let a = 0;
    for (let l = -1; l <= 1; l += 2)
      for (let h = -1; h <= 1; h += 2)
        for (let p = -1; p <= 1; p += 2)
          t[a].set(
            l < 0 ? e.x : r.x,
            h < 0 ? e.y : r.y,
            p < 0 ? e.z : r.z
          ).applyMatrix4(o), a++;
    this.updatePlanes();
  }
  updatePlanes() {
    U.copy(this.box.min).applyMatrix4(this.transform), O.copy(this.box.max).applyMatrix4(this.transform), f.set(0, 0, 1).transformDirection(this.transform), this.planes[0].setFromNormalAndCoplanarPoint(f, U), this.planes[1].setFromNormalAndCoplanarPoint(f, O).negate(), f.set(0, 1, 0).transformDirection(this.transform), this.planes[2].setFromNormalAndCoplanarPoint(f, U), this.planes[3].setFromNormalAndCoplanarPoint(f, O).negate(), f.set(1, 0, 0).transformDirection(this.transform), this.planes[4].setFromNormalAndCoplanarPoint(f, U), this.planes[5].setFromNormalAndCoplanarPoint(f, O).negate();
  }
  intersectsSphere(t) {
    return this.clampPoint(t.center, f), f.distanceToSquared(t.center) <= t.radius * t.radius;
  }
  intersectsFrustum(t) {
    return this._intersectsPlaneShape(t.planes, t.points);
  }
  intersectsOBB(t) {
    return this._intersectsPlaneShape(t.planes, t.points);
  }
  // takes a series of 6 planes that define and enclosed shape and the 8 points that lie at the corners
  // of that shape to determine whether the OBB is intersected with.
  _intersectsPlaneShape(t, i) {
    const o = this.points, s = this.planes;
    for (let e = 0; e < 6; e++) {
      const r = t[e];
      let a = -1 / 0;
      for (let l = 0; l < 8; l++) {
        const h = o[l], p = r.distanceToPoint(h);
        a = a < p ? p : a;
      }
      if (a < 0)
        return !1;
    }
    for (let e = 0; e < 6; e++) {
      const r = s[e];
      let a = -1 / 0;
      for (let l = 0; l < 8; l++) {
        const h = i[l], p = r.distanceToPoint(h);
        a = a < p ? p : a;
      }
      if (a < 0)
        return !1;
    }
    return !0;
  }
}
const W = 1e-13, I = Math.PI, Z = I / 2, B = /* @__PURE__ */ new u(), C = /* @__PURE__ */ new u(), T = /* @__PURE__ */ new u(), n = /* @__PURE__ */ new u(), d = /* @__PURE__ */ new R(), Dt = /* @__PURE__ */ new dt(), ht = /* @__PURE__ */ new R();
function z(c, t) {
  t.radius = Math.max(t.radius, c.distanceToSquared(t.center));
}
function pt(c) {
  return c.x !== c.y;
}
class $t extends ft {
  constructor(t = 1, i = 1, o = 1, s = -Z, e = Z, r = 0, a = 2 * I, l = 0, h = 0) {
    super(t, i, o), this.latStart = s, this.latEnd = e, this.lonStart = r, this.lonEnd = a, this.heightStart = l, this.heightEnd = h;
  }
  /**
   * Computes an oriented bounding box for this region. Writes the box extents into `box` and
   * the orientation frame into `matrix`.
   * @param {Box3} box
   * @param {Matrix4} matrix
   */
  getBoundingBox(t, i) {
    pt(this.radius) && console.warn("EllipsoidRegion: Triaxial ellipsoids are not supported.");
    const {
      latStart: o,
      latEnd: s,
      lonStart: e,
      lonEnd: r,
      heightStart: a,
      heightEnd: l
    } = this, h = (o + s) * 0.5, p = (e + r) * 0.5, w = o > 0, M = s < 0;
    let E;
    w ? E = o : M ? E = s : E = 0;
    const { min: m, max: x } = t;
    m.setScalar(1 / 0), x.setScalar(-1 / 0), r - e <= I ? (this.getCartographicToNormal(h, p, T), C.set(0, 0, 1), B.crossVectors(C, T).normalize(), C.crossVectors(T, B).normalize(), i.makeBasis(B, C, T), d.copy(i).invert(), this.getCartographicToPosition(E, e, l, n).applyMatrix4(d), x.x = Math.abs(n.x), m.x = -x.x, this.getCartographicToPosition(s, e, l, n).applyMatrix4(d), x.y = n.y, this.getCartographicToPosition(s, p, l, n).applyMatrix4(d), x.y = Math.max(n.y, x.y), this.getCartographicToPosition(o, e, l, n).applyMatrix4(d), m.y = n.y, this.getCartographicToPosition(o, p, l, n).applyMatrix4(d), m.y = Math.min(n.y, m.y), this.getCartographicToPosition(h, p, l, n).applyMatrix4(d), x.z = n.z, this.getCartographicToPosition(o, e, a, n).applyMatrix4(d), m.z = n.z, this.getCartographicToPosition(s, e, a, n).applyMatrix4(d), m.z = Math.min(n.z, m.z)) : (this.getCartographicToPosition(E, p, l, T), T.z = 0, T.length() < 1e-10 ? T.set(1, 0, 0) : T.normalize(), C.set(0, 0, 1), B.crossVectors(T, C).normalize(), i.makeBasis(B, C, T), d.copy(i).invert(), this.getCartographicToPosition(E, p + Z, l, n).applyMatrix4(d), x.x = Math.abs(n.x), m.x = -x.x, this.getCartographicToPosition(s, 0, M ? a : l, n).applyMatrix4(d), x.y = n.y, this.getCartographicToPosition(o, 0, w ? a : l, n).applyMatrix4(d), m.y = n.y, this.getCartographicToPosition(E, p, l, n).applyMatrix4(d), x.z = n.z, this.getCartographicToPosition(E, r, l, n).applyMatrix4(d), m.z = n.z), t.getCenter(n), t.min.sub(n).multiplyScalar(1 + W), t.max.sub(n).multiplyScalar(1 + W), n.applyMatrix4(i), i.setPosition(n);
  }
  /**
   * Computes a bounding sphere for this region. Writes the result into `sphere`.
   * @param {Sphere} sphere
   */
  getBoundingSphere(t) {
    pt(this.radius) && console.warn("EllipsoidRegion: Triaxial ellipsoids are not supported."), this.getBoundingBox(Dt, ht), t.center.setFromMatrixPosition(ht), t.radius = 0;
    const {
      latStart: i,
      latEnd: o,
      lonStart: s,
      lonEnd: e,
      heightStart: r,
      heightEnd: a
    } = this, l = (i + o) * 0.5, h = (s + e) * 0.5, p = i > 0, w = o < 0;
    let M;
    p ? M = i : w ? M = o : M = 0, this.getCartographicToPosition(M, s, a, n), z(n, t), this.getCartographicToPosition(o, s, a, n), z(n, t), this.getCartographicToPosition(o, h, a, n), z(n, t), this.getCartographicToPosition(i, s, a, n), z(n, t), this.getCartographicToPosition(i, h, a, n), z(n, t), this.getCartographicToPosition(l, h, a, n), z(n, t), this.getCartographicToPosition(i, s, r, n), z(n, t), e - s > I && (this.getCartographicToPosition(M, h + I, a, n), z(n, t)), t.radius = Math.sqrt(t.radius) * (1 + W);
  }
}
const H = 0;
function ut(c, t, i, o) {
  try {
    return _t.getByteLength(c, t, i, o);
  } catch {
    return H;
  }
}
function Mt(c) {
  var r, a;
  if (!c)
    return 0;
  if (c.isExternalTexture)
    return ((r = c.userData) == null ? void 0 : r.byteLength) ?? H;
  const { format: t, type: i, image: o, mipmaps: s } = c;
  if (c.isCompressedTexture && Array.isArray(s) && s.length > 0) {
    let l = 0;
    for (const h of s)
      (a = h == null ? void 0 : h.data) != null && a.byteLength ? l += h.data.byteLength : l += ut(h.width, h.height, t, i);
    return l;
  }
  if (!o)
    return H;
  let e = ut(o.width, o.height, t, i);
  return e *= c.generateMipmaps ? 4 / 3 : 1, e;
}
function It(c) {
  const t = /* @__PURE__ */ new Set();
  let i = 0;
  return c.traverse((o) => {
    if (o.geometry && !t.has(o.geometry) && (i += zt(o.geometry), t.add(o.geometry)), o.material) {
      const s = o.material;
      for (const e in s) {
        const r = s[e];
        r && r.isTexture && !t.has(r) && (i += Mt(r), t.add(r));
      }
    }
  }), i;
}
const kt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  estimateBytesUsed: It,
  getTextureByteLength: Mt
}, Symbol.toStringTag, { value: "Module" }));
export {
  lt as C,
  At as E,
  Ot as G,
  kt as M,
  Gt as O,
  Bt as W,
  ft as a,
  $t as b,
  L as c,
  It as e,
  Mt as g
};
//# sourceMappingURL=MemoryUtils-ZzXvtRjr.js.map
