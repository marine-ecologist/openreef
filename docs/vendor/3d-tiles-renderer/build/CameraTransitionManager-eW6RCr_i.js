import { T as Ie } from "./TilesRendererBase-BGxy2Uih.js";
import { g as Re, r as ze } from "./LoaderBase-CU5shB7w.js";
import { B as Ae } from "./B3DMLoaderBase-CMKvUOVT.js";
import { DefaultLoadingManager as kt, Matrix4 as z, Vector3 as y, Vector2 as L, MathUtils as v, PointsMaterial as Fe, BufferGeometry as We, BufferAttribute as nt, Color as Le, Points as Ve, InstancedMesh as ke, Quaternion as st, Group as Dt, Ray as Nt, Sphere as Ne, Frustum as Ue, Matrix3 as Be, LoadingManager as je, EventDispatcher as yt, Mesh as He, PlaneGeometry as Ge, ShaderMaterial as Ze, Plane as De, Raycaster as qe, PerspectiveCamera as ee, OrthographicCamera as ve, Clock as Qe } from "three";
import { GLTFLoader as Jt } from "three/addons/loaders/GLTFLoader.js";
import { PNTSLoaderBase as $e, I3DMLoaderBase as Ye, CMPTLoaderBase as Xe } from "./index.core.js";
import { W as vt, O as ie, b as Ke, e as Je, a as ti } from "./MemoryUtils-ZzXvtRjr.js";
class we extends Ae {
  constructor(t = kt) {
    super(), this.manager = t, this.adjustmentTransform = new z();
  }
  /**
   * Parses a b3dm buffer and resolves to a GLTF result object extended with legacy
   * tile metadata. Both `model` and `model.scene` receive the extra fields.
   * @param {ArrayBuffer} buffer
   * @returns {Promise<{ scene: Group, scenes: Array, batchTable: BatchTable, featureTable: FeatureTable }>}
   */
  parse(t) {
    const e = super.parse(t), i = e.glbBytes.slice().buffer;
    return new Promise((s, o) => {
      const n = this.manager, r = this.fetchOptions, a = n.getHandler("path.gltf") || new Jt(n);
      r.credentials === "include" && r.mode === "cors" && a.setCrossOrigin("use-credentials"), "credentials" in r && a.setWithCredentials(r.credentials === "include"), r.headers && a.setRequestHeader(r.headers);
      let c = this.workingPath;
      !/[\\/]$/.test(c) && c.length && (c += "/");
      const p = this.adjustmentTransform;
      a.parse(i, c, (l) => {
        const { batchTable: m, featureTable: d } = e, { scene: h } = l, u = d.getData("RTC_CENTER", 1, "FLOAT", "VEC3");
        u && (h.position.x += u[0], h.position.y += u[1], h.position.z += u[2]), l.scene.updateMatrix(), l.scene.matrix.multiply(p), l.scene.matrix.decompose(l.scene.position, l.scene.quaternion, l.scene.scale), l.batchTable = m, l.featureTable = d, h.batchTable = m, h.featureTable = d, s(l);
      }, o);
    });
  }
}
function ei(g) {
  const t = g >> 11, e = g >> 5 & 63, i = g & 31, s = Math.round(t / 31 * 255), o = Math.round(e / 63 * 255), n = Math.round(i / 31 * 255);
  return [s, o, n];
}
const bt = /* @__PURE__ */ new L();
function ii(g, t, e = new y()) {
  bt.set(g, t).divideScalar(256).multiplyScalar(2).subScalar(1), e.set(bt.x, bt.y, 1 - Math.abs(bt.x) - Math.abs(bt.y));
  const i = v.clamp(-e.z, 0, 1);
  return e.x >= 0 ? e.setX(e.x - i) : e.setX(e.x + i), e.y >= 0 ? e.setY(e.y - i) : e.setY(e.y + i), e.normalize(), e;
}
const se = {
  RGB: "color",
  POSITION: "position"
};
class Te extends $e {
  constructor(t = kt) {
    super(), this.manager = t;
  }
  /**
   * Parses a pnts buffer and resolves to a result object containing a constructed
   * three.js `Points` scene with metadata attached.
   * @param {ArrayBuffer} buffer
   * @returns {Promise<{ scene: Points, batchTable: BatchTable, featureTable: FeatureTable }>}
   */
  parse(t) {
    return super.parse(t).then(async (e) => {
      const { featureTable: i, batchTable: s } = e, o = new Fe(), n = i.header.extensions, r = new y();
      let a;
      if (n && n["3DTILES_draco_point_compression"]) {
        const { byteOffset: l, byteLength: m, properties: d } = n["3DTILES_draco_point_compression"], h = this.manager.getHandler("draco.drc");
        if (h == null)
          throw new Error("PNTSLoader: dracoLoader not available.");
        const u = {};
        for (const M in d)
          if (M in se && M in d) {
            const P = se[M];
            u[P] = d[M];
          }
        const b = {
          attributeIDs: u,
          attributeTypes: {
            position: "Float32Array",
            color: "Uint8Array"
          },
          useUniqueIDs: !0
        }, I = i.getBuffer(l, m);
        a = await h.decodeGeometry(I, b), a.attributes.color && (o.vertexColors = !0);
      } else {
        const l = i.getData("POINTS_LENGTH"), m = i.getData("POSITION", l, "FLOAT", "VEC3"), d = i.getData("NORMAL", l, "FLOAT", "VEC3"), h = i.getData("NORMAL", l, "UNSIGNED_BYTE", "VEC2"), u = i.getData("RGB", l, "UNSIGNED_BYTE", "VEC3"), b = i.getData("RGBA", l, "UNSIGNED_BYTE", "VEC4"), I = i.getData("RGB565", l, "UNSIGNED_SHORT", "SCALAR"), M = i.getData("CONSTANT_RGBA", l, "UNSIGNED_BYTE", "VEC4"), P = i.getData("POSITION_QUANTIZED", l, "UNSIGNED_SHORT", "VEC3"), f = i.getData("QUANTIZED_VOLUME_SCALE", l, "FLOAT", "VEC3"), O = i.getData("QUANTIZED_VOLUME_OFFSET", l, "FLOAT", "VEC3");
        if (a = new We(), P) {
          const T = new Float32Array(l * 3);
          for (let w = 0; w < l; w++)
            for (let C = 0; C < 3; C++) {
              const A = 3 * w + C;
              T[A] = P[A] / 65535 * f[C];
            }
          r.x = O[0], r.y = O[1], r.z = O[2], a.setAttribute("position", new nt(T, 3, !1));
        } else
          a.setAttribute("position", new nt(m, 3, !1));
        if (d !== null)
          a.setAttribute("normal", new nt(d, 3, !1));
        else if (h !== null) {
          const T = new Float32Array(l * 3), w = new y();
          for (let C = 0; C < l; C++) {
            const A = h[C * 2], ot = h[C * 2 + 1], F = ii(A, ot, w);
            T[C * 3] = F.x, T[C * 3 + 1] = F.y, T[C * 3 + 2] = F.z;
          }
          a.setAttribute("normal", new nt(T, 3, !1));
        }
        if (b !== null)
          a.setAttribute("color", new nt(b, 4, !0)), o.vertexColors = !0, o.transparent = !0, o.depthWrite = !1;
        else if (u !== null)
          a.setAttribute("color", new nt(u, 3, !0)), o.vertexColors = !0;
        else if (I !== null) {
          const T = new Uint8Array(l * 3);
          for (let w = 0; w < l; w++) {
            const C = ei(I[w]);
            for (let A = 0; A < 3; A++) {
              const ot = 3 * w + A;
              T[ot] = C[A];
            }
          }
          a.setAttribute("color", new nt(T, 3, !0)), o.vertexColors = !0;
        } else if (M !== null) {
          const T = new Le(M[0], M[1], M[2]);
          o.color = T;
          const w = M[3] / 255;
          w < 1 && (o.opacity = w, o.transparent = !0, o.depthWrite = !1);
        }
      }
      const c = new Ve(a, o);
      c.position.copy(r), e.scene = c, e.scene.featureTable = i, e.scene.batchTable = s;
      const p = i.getData("RTC_CENTER", 1, "FLOAT", "VEC3");
      return p && (e.scene.position.x += p[0], e.scene.position.y += p[1], e.scene.position.z += p[2]), e;
    });
  }
}
const Tt = /* @__PURE__ */ new y(), ht = /* @__PURE__ */ new y(), pt = /* @__PURE__ */ new y(), Bt = /* @__PURE__ */ new y(), Ct = /* @__PURE__ */ new st(), St = /* @__PURE__ */ new y(), dt = /* @__PURE__ */ new z(), oe = /* @__PURE__ */ new z(), ne = /* @__PURE__ */ new y(), re = /* @__PURE__ */ new z(), jt = /* @__PURE__ */ new st(), Ht = {};
function ae(g, t, e, i) {
  if (g = g / e * 2 - 1, t = t / e * 2 - 1, i.x = g, i.y = t, i.z = 1 - Math.abs(g) - Math.abs(t), i.z < 0) {
    const s = i.x;
    i.x = (1 - Math.abs(i.y)) * (s >= 0 ? 1 : -1), i.y = (1 - Math.abs(s)) * (i.y >= 0 ? 1 : -1);
  }
  return i.normalize(), i;
}
class Ce extends Ye {
  constructor(t = kt) {
    super(), this.manager = t, this.adjustmentTransform = new z(), this.ellipsoid = vt.clone();
  }
  resolveExternalURL(t) {
    return this.manager.resolveURL(super.resolveExternalURL(t));
  }
  /**
   * Parses an i3dm buffer and resolves to a GLTF result object where the scene's
   * meshes have been replaced with `InstancedMesh` objects (one per GLTF mesh), with
   * metadata attached to both `model` and `model.scene`.
   * @param {ArrayBuffer} buffer
   * @returns {Promise<{ scene: Group, batchTable: BatchTable, featureTable: FeatureTable }>}
   */
  parse(t) {
    return super.parse(t).then((e) => {
      const { featureTable: i, batchTable: s } = e, o = e.glbBytes.slice().buffer;
      return new Promise((n, r) => {
        const a = this.fetchOptions, c = this.manager, p = c.getHandler("path.gltf") || new Jt(c);
        a.credentials === "include" && a.mode === "cors" && p.setCrossOrigin("use-credentials"), "credentials" in a && p.setWithCredentials(a.credentials === "include"), a.headers && p.setRequestHeader(a.headers);
        let l = e.gltfWorkingPath ?? this.workingPath;
        /[\\/]$/.test(l) || (l += "/");
        const m = this.adjustmentTransform;
        p.parse(o, l, (d) => {
          const h = i.getData("INSTANCES_LENGTH");
          let u = i.getData("POSITION", h, "FLOAT", "VEC3");
          const b = i.getData("POSITION_QUANTIZED", h, "UNSIGNED_SHORT", "VEC3"), I = i.getData("QUANTIZED_VOLUME_OFFSET", 1, "FLOAT", "VEC3"), M = i.getData("QUANTIZED_VOLUME_SCALE", 1, "FLOAT", "VEC3"), P = i.getData("NORMAL_UP", h, "FLOAT", "VEC3"), f = i.getData("NORMAL_RIGHT", h, "FLOAT", "VEC3"), O = i.getData("NORMAL_UP_OCT32P", h, "UNSIGNED_SHORT", "VEC2"), T = i.getData("NORMAL_RIGHT_OCT32P", h, "UNSIGNED_SHORT", "VEC2"), w = i.getData("SCALE_NON_UNIFORM", h, "FLOAT", "VEC3"), C = i.getData("SCALE", h, "FLOAT", "SCALAR"), A = i.getData("RTC_CENTER", 1, "FLOAT", "VEC3"), ot = i.getData("EAST_NORTH_UP");
          if (!u && b) {
            u = new Float32Array(h * 3);
            for (let x = 0; x < h; x++)
              u[x * 3 + 0] = I[0] + b[x * 3 + 0] / 65535 * M[0], u[x * 3 + 1] = I[1] + b[x * 3 + 1] / 65535 * M[1], u[x * 3 + 2] = I[2] + b[x * 3 + 2] / 65535 * M[2];
          }
          const F = new y();
          for (let x = 0; x < h; x++)
            F.x += u[x * 3 + 0] / h, F.y += u[x * 3 + 1] / h, F.z += u[x * 3 + 2] / h;
          const wt = [], te = [];
          d.scene.updateMatrixWorld(), d.scene.traverse((x) => {
            if (x.isMesh) {
              te.push(x);
              const { geometry: lt, material: Ut } = x, Q = new ke(lt, Ut, h);
              Q.position.copy(F), A && (Q.position.x += A[0], Q.position.y += A[1], Q.position.z += A[2]), wt.push(Q);
            }
          });
          for (let x = 0; x < h; x++) {
            Bt.set(
              u[x * 3 + 0] - F.x,
              u[x * 3 + 1] - F.y,
              u[x * 3 + 2] - F.z
            ), Ct.identity(), P && f ? (ht.set(
              P[x * 3 + 0],
              P[x * 3 + 1],
              P[x * 3 + 2]
            ), pt.set(
              f[x * 3 + 0],
              f[x * 3 + 1],
              f[x * 3 + 2]
            ), Tt.crossVectors(pt, ht).normalize(), dt.makeBasis(
              pt,
              ht,
              Tt
            ), Ct.setFromRotationMatrix(dt)) : O && T && (ae(
              O[x * 2 + 0],
              O[x * 2 + 1],
              65535,
              ht
            ), ae(
              T[x * 2 + 0],
              T[x * 2 + 1],
              65535,
              pt
            ), Tt.crossVectors(pt, ht).normalize(), dt.makeBasis(
              pt,
              ht,
              Tt
            ), Ct.setFromRotationMatrix(dt)), St.set(1, 1, 1), w && St.set(
              w[x * 3 + 0],
              w[x * 3 + 1],
              w[x * 3 + 2]
            ), C && St.multiplyScalar(C[x]);
            for (let lt = 0, Ut = wt.length; lt < Ut; lt++) {
              const Q = wt[lt];
              jt.copy(Ct), ot && (Q.updateMatrixWorld(), ne.copy(Bt).applyMatrix4(Q.matrixWorld), this.ellipsoid.getPositionToCartographic(ne, Ht), this.ellipsoid.getEastNorthUpFrame(Ht.lat, Ht.lon, re), jt.setFromRotationMatrix(re)), dt.compose(Bt, jt, St).multiply(m);
              const Oe = te[lt];
              oe.multiplyMatrices(dt, Oe.matrixWorld), Q.setMatrixAt(x, oe);
            }
          }
          d.scene.clear(), d.scene.add(...wt), d.batchTable = s, d.featureTable = i, d.scene.batchTable = s, d.scene.featureTable = i, n(d);
        }, r);
      });
    });
  }
}
class si extends Xe {
  constructor(t = kt) {
    super(), this.manager = t, this.adjustmentTransform = new z(), this.ellipsoid = vt.clone();
  }
  /**
   * Parses a cmpt buffer and resolves to an object containing a `Group` with all
   * sub-tile scenes added as children, and the individual sub-tile results.
   * @param {ArrayBuffer} buffer
   * @returns {Promise<{ scene: Group, tiles: Array }>}
   */
  parse(t) {
    const e = super.parse(t), { manager: i, ellipsoid: s, adjustmentTransform: o } = this, n = [];
    for (const r in e.tiles) {
      const { type: a, buffer: c } = e.tiles[r];
      switch (a) {
        case "b3dm": {
          const p = c.slice(), l = new we(i);
          l.workingPath = this.workingPath, l.fetchOptions = this.fetchOptions, l.adjustmentTransform.copy(o);
          const m = l.parse(p.buffer);
          n.push(m);
          break;
        }
        case "pnts": {
          const p = c.slice(), l = new Te(i);
          l.workingPath = this.workingPath, l.fetchOptions = this.fetchOptions;
          const m = l.parse(p.buffer);
          n.push(m);
          break;
        }
        case "i3dm": {
          const p = c.slice(), l = new Ce(i);
          l.workingPath = this.workingPath, l.fetchOptions = this.fetchOptions, l.ellipsoid.copy(s), l.adjustmentTransform.copy(o);
          const m = l.parse(p.buffer);
          n.push(m);
          break;
        }
      }
    }
    return Promise.all(n).then((r) => {
      const a = new Dt();
      return r.forEach((c) => {
        a.add(c.scene);
      }), {
        tiles: r,
        scene: a
      };
    });
  }
}
const _t = /* @__PURE__ */ new z();
class oi extends Dt {
  constructor(t) {
    super(), this.isTilesGroup = !0, this.name = "TilesRenderer.TilesGroup", this.tilesRenderer = t, this.matrixWorldInverse = new z();
  }
  raycast(t, e) {
    return this.tilesRenderer.raycast(t, e), !1;
  }
  updateMatrixWorld(t) {
    if (this.matrixAutoUpdate && this.updateMatrix(), this.matrixWorldNeedsUpdate || t) {
      this.parent === null ? _t.copy(this.matrix) : _t.multiplyMatrices(this.parent.matrixWorld, this.matrix), this.matrixWorldNeedsUpdate = !1;
      const e = _t.elements, i = this.matrixWorld.elements;
      let s = !1;
      for (let o = 0; o < 16; o++) {
        const n = e[o], r = i[o];
        if (Math.abs(n - r) > Number.EPSILON) {
          s = !0;
          break;
        }
      }
      if (s) {
        this.matrixWorld.copy(_t), this.matrixWorldInverse.copy(_t).invert();
        const o = this.children;
        for (let c = 0, p = o.length; c < p; c++)
          o[c].updateMatrixWorld();
        const { tilesRenderer: n } = this, { activeTiles: r, visibleTiles: a } = n;
        r.forEach((c) => {
          if (!a.has(c)) {
            const { scene: p } = c.engineData;
            p.traverse((l) => {
              l.updateMatrix(), l.matrixWorld.copy(l.matrix), l.parent ? l.matrixWorld.premultiply(l.parent.matrixWorld) : l.matrixWorld.premultiply(this.matrixWorld);
            });
          }
        });
      }
    }
  }
  updateWorldMatrix(t, e) {
    this.parent && t && this.parent.updateWorldMatrix(t, !1), this.updateMatrixWorld(!0);
  }
}
const ni = /* @__PURE__ */ new Nt();
function ri(g, t, e, i) {
  const { scene: s } = g.engineData;
  e.invokeOnePlugin((n) => n.raycastTile && n.raycastTile(g, s, t, i)) || t.intersectObject(s, !0, i);
}
function ai(g) {
  return "traversal" in g;
}
function Se(g, t, e, i, s = null) {
  if (!ai(t))
    return;
  const { group: o, activeTiles: n } = g, { boundingVolume: r } = t.engineData;
  if (s === null && (s = ni, s.copy(e.ray).applyMatrix4(o.matrixWorldInverse)), !t.traversal.used || !r.intersectsRay(s))
    return;
  n.has(t) && ri(t, e, g, i);
  const a = t.children;
  for (let c = 0, p = a.length; c < p; c++)
    Se(g, a[c], e, i, s);
}
const $ = /* @__PURE__ */ new y(), Y = /* @__PURE__ */ new y(), X = /* @__PURE__ */ new y(), ce = /* @__PURE__ */ new y(), le = /* @__PURE__ */ new y();
class ci {
  constructor() {
    this.sphere = null, this.obb = null, this.region = null, this.regionObb = null;
  }
  intersectsRay(t) {
    const e = this.sphere, i = this.obb || this.regionObb;
    return !(e && !t.intersectsSphere(e) || i && !i.intersectsRay(t));
  }
  intersectRay(t, e = null) {
    const i = this.sphere, s = this.obb || this.regionObb;
    let o = -1 / 0, n = -1 / 0;
    i && t.intersectSphere(i, ce) && (o = i.containsPoint(t.origin) ? 0 : t.origin.distanceToSquared(ce)), s && s.intersectRay(t, le) && (n = s.containsPoint(t.origin) ? 0 : t.origin.distanceToSquared(le));
    const r = Math.max(o, n);
    return r === -1 / 0 ? null : (t.at(Math.sqrt(r), e), e);
  }
  distanceToPoint(t) {
    const e = this.sphere, i = this.obb || this.regionObb;
    let s = -1 / 0, o = -1 / 0;
    return e && (s = Math.max(e.distanceToPoint(t), 0)), i && (o = i.distanceToPoint(t)), s > o ? s : o;
  }
  intersectsFrustum(t) {
    const e = this.obb || this.regionObb, i = this.sphere;
    return i && !t.intersectsSphere(i) || e && !e.intersectsFrustum(t) ? !1 : !!(i || e);
  }
  intersectsSphere(t) {
    const e = this.obb || this.regionObb, i = this.sphere;
    return i && !i.intersectsSphere(t) || e && !e.intersectsSphere(t) ? !1 : !!(i || e);
  }
  intersectsOBB(t) {
    const e = this.obb || this.regionObb, i = this.sphere;
    return i && !t.intersectsSphere(i) || e && !e.intersectsOBB(t) ? !1 : !!(i || e);
  }
  getOBB(t, e) {
    const i = this.obb || this.regionObb;
    i ? (t.copy(i.box), e.copy(i.transform)) : (this.getAABB(t), e.identity());
  }
  getAABB(t) {
    if (this.sphere)
      this.sphere.getBoundingBox(t);
    else {
      const e = this.obb || this.regionObb;
      t.copy(e.box).applyMatrix4(e.transform);
    }
  }
  getSphere(t) {
    if (this.sphere)
      t.copy(this.sphere);
    else if (this.region)
      this.region.getBoundingSphere(t);
    else {
      const e = this.obb || this.regionObb;
      e.box.getBoundingSphere(t), t.applyMatrix4(e.transform);
    }
  }
  setObbData(t, e) {
    const i = new ie();
    $.set(t[3], t[4], t[5]), Y.set(t[6], t[7], t[8]), X.set(t[9], t[10], t[11]);
    const s = $.length(), o = Y.length(), n = X.length();
    $.normalize(), Y.normalize(), X.normalize(), s === 0 && $.crossVectors(Y, X), o === 0 && Y.crossVectors($, X), n === 0 && X.crossVectors($, Y), i.transform.set(
      $.x,
      Y.x,
      X.x,
      t[0],
      $.y,
      Y.y,
      X.y,
      t[1],
      $.z,
      Y.z,
      X.z,
      t[2],
      0,
      0,
      0,
      1
    ).premultiply(e), i.box.min.set(-s, -o, -n), i.box.max.set(s, o, n), i.update(), this.obb = i;
  }
  setSphereData(t, e, i, s, o) {
    const n = new Ne();
    n.center.set(t, e, i), n.radius = s, n.applyMatrix4(o), this.sphere = n;
  }
  setRegionData(t, e, i, s, o, n, r) {
    const a = new Ke(
      ...t.radius,
      i,
      o,
      e,
      s,
      n,
      r
    ), c = new ie();
    a.getBoundingBox(c.box, c.transform), c.update(), this.region = a, this.regionObb = c;
  }
}
const li = /* @__PURE__ */ new Be();
function hi(g, t, e, i) {
  const s = li.set(
    g.normal.x,
    g.normal.y,
    g.normal.z,
    t.normal.x,
    t.normal.y,
    t.normal.z,
    e.normal.x,
    e.normal.y,
    e.normal.z
  );
  return i.set(-g.constant, -t.constant, -e.constant), i.applyMatrix3(s.invert()), i;
}
class pi extends Ue {
  constructor() {
    super(), this.points = Array(8).fill().map(() => new y());
  }
  setFromProjectionMatrix(...t) {
    return super.setFromProjectionMatrix(...t), this.calculateFrustumPoints(), this;
  }
  calculateFrustumPoints() {
    const { planes: t, points: e } = this;
    [
      [t[0], t[3], t[4]],
      // Near top left
      [t[1], t[3], t[4]],
      // Near top right
      [t[0], t[2], t[4]],
      // Near bottom left
      [t[1], t[2], t[4]],
      // Near bottom right
      [t[0], t[3], t[5]],
      // Far top left
      [t[1], t[3], t[5]],
      // Far top right
      [t[0], t[2], t[5]],
      // Far bottom left
      [t[1], t[2], t[5]]
      // Far bottom right
    ].forEach((s, o) => {
      hi(s[0], s[1], s[2], e[o]);
    });
  }
}
const Ee = Symbol("INITIAL_FRUSTUM_CULLED"), Et = /* @__PURE__ */ new z(), Mt = /* @__PURE__ */ new y(), Gt = /* @__PURE__ */ new L(), di = /* @__PURE__ */ new y(1, 0, 0), ui = /* @__PURE__ */ new y(0, 1, 0);
function he(g, t) {
  g.traverse((e) => {
    e.frustumCulled = e[Ee] && t;
  });
}
class Ri extends Ie {
  /**
   * If `true`, all tile meshes automatically have `frustumCulled` set to `false` since the
   * tiles renderer performs its own frustum culling. If `displayActiveTiles` is `true` or
   * multiple cameras are being used, consider setting this to `false`.
   * @type {boolean}
   * @default true
   */
  get autoDisableRendererCulling() {
    return this._autoDisableRendererCulling;
  }
  set autoDisableRendererCulling(t) {
    this._autoDisableRendererCulling !== t && (super._autoDisableRendererCulling = t, this.forEachLoadedModel((e) => {
      he(e, !t);
    }));
  }
  constructor(...t) {
    super(...t), this.accelerateRaycast = !0, this.group = new oi(this), this.ellipsoid = vt.clone(), this.cameras = [], this.cameraMap = /* @__PURE__ */ new Map(), this.cameraInfo = [], this._upRotationMatrix = new z(), this._bytesUsed = /* @__PURE__ */ new WeakMap(), this._autoDisableRendererCulling = !0, this.manager = new je(), this._listeners = {};
  }
  addEventListener(t, e) {
    yt.prototype.addEventListener.call(this, t, e);
  }
  hasEventListener(t, e) {
    return yt.prototype.hasEventListener.call(this, t, e);
  }
  removeEventListener(t, e) {
    yt.prototype.removeEventListener.call(this, t, e);
  }
  dispatchEvent(t) {
    yt.prototype.dispatchEvent.call(this, t);
  }
  /* Public API */
  /**
   * Returns the axis-aligned bounding box of the root tile in the group's local space.
   * @param {Box3} target - Target box to write into.
   * @returns {boolean} Whether the tileset is loaded and a bounding box is available.
   */
  getBoundingBox(t) {
    if (!this.root)
      return !1;
    const e = this.root.engineData.boundingVolume;
    return e ? (e.getAABB(t), !0) : !1;
  }
  /**
   * Returns the oriented bounding box and transform of the root tile.
   * @param {Box3} targetBox - Target box to write into (in local OBB space).
   * @param {Matrix4} targetMatrix - Transform from OBB local space to group local space.
   * @returns {boolean} Whether the tileset is loaded and an OBB is available.
   */
  getOrientedBoundingBox(t, e) {
    if (!this.root)
      return !1;
    const i = this.root.engineData.boundingVolume;
    return i ? (i.getOBB(t, e), !0) : !1;
  }
  /**
   * Returns the bounding sphere of the root tile in the group's local space.
   * @param {Sphere} target - Target sphere to write into.
   * @returns {boolean} Whether the tileset is loaded and a bounding sphere is available.
   */
  getBoundingSphere(t) {
    if (!this.root)
      return !1;
    const e = this.root.engineData.boundingVolume;
    return e ? (e.getSphere(t), !0) : !1;
  }
  /**
   * Iterates over all currently loaded tile scenes.
   * @param {Function} callback - Called with `( scene: Object3D, tile: object )` for each loaded tile.
   */
  forEachLoadedModel(t) {
    this.traverse((e) => {
      const i = e.engineData && e.engineData.scene;
      i && t(i, e);
    }, null, !1);
  }
  /**
   * Performs a raycast against all loaded tile scenes. Compatible with Three.js raycasting.
   * Supports `raycaster.firstHitOnly` for early termination.
   * @param {Raycaster} raycaster
   * @param {Array} intersects - Array to push intersection results into.
   */
  raycast(t, e) {
    if (this.root)
      if (this.accelerateRaycast)
        Se(this, this.root, t, e);
      else {
        const i = t.firstHitOnly ? [] : e;
        for (const s of this.activeTiles) {
          const { scene: o } = s.engineData;
          this.invokeOnePlugin((n) => n.raycastTile && n.raycastTile(s, o, t, i)) || t.intersectObject(o, !0, i);
        }
        t.firstHitOnly && i.length > 0 && (i.sort((s, o) => s.distance - o.distance), e.push(i[0]));
      }
  }
  /**
   * Returns whether the given camera is registered with this renderer.
   * @param {Camera} camera
   * @returns {boolean}
   */
  hasCamera(t) {
    return this.cameraMap.has(t);
  }
  /**
   * Registers a camera with the renderer so it is used for tile selection and screen-space error
   * calculation. Use `setResolution` or `setResolutionFromRenderer` to provide the camera's resolution.
   * @param {Camera} camera
   * @returns {boolean} Whether the camera was newly added.
   */
  setCamera(t) {
    const e = this.cameras, i = this.cameraMap;
    return i.has(t) ? !1 : (i.set(t, new L()), e.push(t), this.dispatchEvent({ type: "add-camera", camera: t }), !0);
  }
  /**
   * Sets the render resolution for a registered camera, used for screen-space error calculation.
   * @param {Camera} camera - A previously registered camera.
   * @param {number|Vector2} xOrVec - Render width in pixels, or a Vector2 containing width and height.
   * @param {number} [y] - Render height in pixels when `xOrVec` is a number.
   * @returns {boolean} Whether the camera is registered and the resolution was updated.
   */
  setResolution(t, e, i) {
    const s = this.cameraMap;
    if (!s.has(t))
      return !1;
    const o = e.isVector2 ? e.x : e, n = e.isVector2 ? e.y : i, r = s.get(t);
    return (r.width !== o || r.height !== n) && (r.set(o, n), this.dispatchEvent({ type: "camera-resolution-change" })), !0;
  }
  /**
   * Returns the render resolution previously set for a registered camera.
   * @param {Camera} camera - A previously registered camera.
   * @param {Vector2} target - Vector2 to write the result into.
   * @returns {Vector2|null} The target with width/height filled in, or null if the camera is not registered.
   */
  getResolution(t, e) {
    const i = this.cameraMap.get(t);
    return i ? e.copy(i) : null;
  }
  /**
   * Sets the render resolution for a camera by reading the current size from a WebGLRenderer.
   * @param {Camera} camera - A previously registered camera.
   * @param {WebGLRenderer} renderer
   * @returns {boolean} Whether the camera is registered and the resolution was updated.
   */
  setResolutionFromRenderer(t, e) {
    return e.getSize(Gt), this.setResolution(t, Gt.x, Gt.y);
  }
  /**
   * Unregisters a camera from the renderer.
   * @param {Camera} camera
   * @returns {boolean} Whether the camera was found and removed.
   */
  deleteCamera(t) {
    const e = this.cameras, i = this.cameraMap;
    if (i.has(t)) {
      const s = e.indexOf(t);
      return e.splice(s, 1), i.delete(t), this.dispatchEvent({ type: "delete-camera", camera: t }), !0;
    }
    return !1;
  }
  /* Overriden */
  loadRootTileset(...t) {
    return super.loadRootTileset(...t).then((e) => {
      const { asset: i, extensions: s = {} } = e;
      switch ((i && i.gltfUpAxis || "y").toLowerCase()) {
        case "x":
          this._upRotationMatrix.makeRotationAxis(ui, -Math.PI / 2);
          break;
        case "y":
          this._upRotationMatrix.makeRotationAxis(di, Math.PI / 2);
          break;
      }
      if ("3DTILES_ellipsoid" in s) {
        const n = s["3DTILES_ellipsoid"], { ellipsoid: r } = this;
        r.name = n.body, n.radii ? r.radius.set(...n.radii) : r.radius.set(1, 1, 1);
      }
      return e;
    });
  }
  prepareForTraversal() {
    const t = this.group, e = this.cameras, i = this.cameraMap, s = this.cameraInfo;
    for (; s.length > e.length; )
      s.pop();
    for (; s.length < e.length; )
      s.push({
        frustum: new pi(),
        isOrthographic: !1,
        sseDenominator: -1,
        // used if isOrthographic:false
        position: new y(),
        invScale: -1,
        pixelSize: 0
        // used if isOrthographic:true
      });
    Mt.setFromMatrixScale(t.matrixWorldInverse), Math.abs(Math.max(Mt.x - Mt.y, Mt.x - Mt.z)) > 1e-6 && console.warn("ThreeTilesRenderer : Non uniform scale used for tile which may cause issues when calculating screen space error.");
    for (let o = 0, n = s.length; o < n; o++) {
      const r = e[o], a = s[o], c = a.frustum, p = a.position, l = i.get(r);
      (l.width === 0 || l.height === 0) && console.warn("TilesRenderer: resolution for camera error calculation is not set.");
      const m = r.projectionMatrix.elements;
      if (a.isOrthographic = m[15] === 1, a.isOrthographic) {
        const d = 2 / m[0], h = 2 / m[5];
        a.pixelSize = Math.max(h / l.height, d / l.width);
      } else
        a.sseDenominator = 2 / m[5] / l.height;
      Et.copy(t.matrixWorld), Et.premultiply(r.matrixWorldInverse), Et.premultiply(r.projectionMatrix), c.setFromProjectionMatrix(Et, r.coordinateSystem, r.reversedDepth), p.set(0, 0, 0), p.applyMatrix4(r.matrixWorld), p.applyMatrix4(t.matrixWorldInverse);
    }
  }
  update() {
    if (super.update(), this.cameras.length === 0 && this.root) {
      let t = !1;
      this.invokeAllPlugins((e) => t = t || !!(e !== this && e.calculateTileViewError)), t === !1 && console.warn("TilesRenderer: no cameras defined. Cannot update 3d tiles.");
    }
  }
  preprocessNode(t, e, i = null) {
    super.preprocessNode(t, e, i);
    const s = new z();
    if (t.transform) {
      const r = t.transform;
      for (let a = 0; a < 16; a++)
        s.elements[a] = r[a];
    }
    i && s.premultiply(i.engineData.transform);
    const o = new z().copy(s).invert(), n = new ci();
    "sphere" in t.boundingVolume && n.setSphereData(...t.boundingVolume.sphere, s), "box" in t.boundingVolume && n.setObbData(t.boundingVolume.box, s), "region" in t.boundingVolume && n.setRegionData(this.ellipsoid, ...t.boundingVolume.region), t.engineData.transform = s, t.engineData.transformInverse = o, t.engineData.boundingVolume = n, t.engineData.geometry = null, t.engineData.materials = null, t.engineData.textures = null;
  }
  async parseTile(t, e, i, s, o) {
    const n = e.engineData, r = Re(s), a = this.fetchOptions, c = this.manager;
    let p = null;
    const l = n.transform, m = this._upRotationMatrix, d = (ze(t) || i).toLowerCase();
    switch (d) {
      case "b3dm": {
        const f = new we(c);
        f.workingPath = r, f.fetchOptions = a, f.adjustmentTransform.copy(m), p = f.parse(t);
        break;
      }
      case "pnts": {
        const f = new Te(c);
        f.workingPath = r, f.fetchOptions = a, p = f.parse(t);
        break;
      }
      case "i3dm": {
        const f = new Ce(c);
        f.workingPath = r, f.fetchOptions = a, f.adjustmentTransform.copy(m), f.ellipsoid.copy(this.ellipsoid), p = f.parse(t);
        break;
      }
      case "cmpt": {
        const f = new si(c);
        f.workingPath = r, f.fetchOptions = a, f.adjustmentTransform.copy(m), f.ellipsoid.copy(this.ellipsoid), p = f.parse(t).then((O) => O.scene);
        break;
      }
      // 3DTILES_content_gltf
      case "gltf":
      case "glb": {
        const f = c.getHandler("path.gltf") || c.getHandler("path.glb") || new Jt(c);
        f.setWithCredentials(a.credentials === "include"), f.setRequestHeader(a.headers || {}), a.credentials === "include" && a.mode === "cors" && f.setCrossOrigin("use-credentials");
        let O = f.resourcePath || f.path || r;
        !/[\\/]$/.test(O) && O.length && (O += "/"), p = f.parseAsync(t, O).then((T) => {
          T.scene = T.scene || new Dt();
          const { scene: w } = T;
          return w.updateMatrix(), w.matrix.multiply(m).decompose(w.position, w.quaternion, w.scale), T;
        });
        break;
      }
      default: {
        p = this.invokeOnePlugin((f) => f.parseToMesh && f.parseToMesh(t, e, i, s, o));
        break;
      }
    }
    const h = await p;
    if (h === null)
      throw new Error(`TilesRenderer: Content type "${d}" not supported.`);
    let u, b;
    h.isObject3D ? (u = h, b = null) : (u = h.scene, b = h), u.updateMatrix(), u.matrix.premultiply(l), u.matrix.decompose(u.position, u.quaternion, u.scale), await this.invokeAllPlugins((f) => f.processTileModel && f.processTileModel(u, e)), u.traverse((f) => {
      f[Ee] = f.frustumCulled;
    }), he(u, !this.autoDisableRendererCulling);
    const I = [], M = [], P = [];
    if (u.traverse((f) => {
      if (f.geometry && M.push(f.geometry), f.material) {
        const O = f.material;
        I.push(f.material);
        for (const T in O) {
          const w = O[T];
          w && w.isTexture && P.push(w);
        }
      }
    }), o.aborted) {
      for (let f = 0, O = P.length; f < O; f++) {
        const T = P[f];
        T.image instanceof ImageBitmap && T.image.close(), T.dispose();
      }
      return;
    }
    n.materials = I, n.geometry = M, n.textures = P, n.scene = u, n.metadata = b;
  }
  disposeTile(t) {
    super.disposeTile(t);
    const e = t.engineData;
    if (e.scene) {
      const i = e.materials, s = e.geometry, o = e.textures, n = e.scene.parent;
      e.scene.traverse((r) => {
        r.userData.meshFeatures && r.userData.meshFeatures.dispose(), r.userData.structuralMetadata && r.userData.structuralMetadata.dispose();
      });
      for (let r = 0, a = s.length; r < a; r++)
        s[r].dispose();
      for (let r = 0, a = i.length; r < a; r++)
        i[r].dispose();
      for (let r = 0, a = o.length; r < a; r++) {
        const c = o[r];
        c.image instanceof ImageBitmap && c.image.close(), c.dispose();
      }
      n && n.remove(e.scene), e.scene = null, e.materials = null, e.textures = null, e.geometry = null, e.metadata = null;
    }
  }
  setTileActive(t, e) {
    const i = t.engineData.scene, s = this.group;
    i && i.traverse((o) => {
      o.updateMatrix(), o.matrixWorld.copy(o.matrix), o.parent ? o.matrixWorld.premultiply(o.parent.matrixWorld) : o.matrixWorld.premultiply(s.matrixWorld);
    }), super.setTileActive(t, e);
  }
  setTileVisible(t, e) {
    const i = t.engineData.scene, s = this.group;
    e ? i && s.add(i) : i && s.remove(i), super.setTileVisible(t, e);
  }
  calculateBytesUsed(t, e) {
    const i = this._bytesUsed;
    return !i.has(t) && e && i.set(t, Je(e)), i.get(t) ?? null;
  }
  calculateTileViewError(t, e) {
    const i = t.engineData, s = this.cameras, o = this.cameraInfo, n = i.boundingVolume;
    let r = !1, a = 0, c = 1 / 0, p = 0, l = 1 / 0;
    for (let m = 0, d = s.length; m < d; m++) {
      const h = o[m];
      let u, b;
      if (h.isOrthographic) {
        const M = h.pixelSize;
        u = t.geometricError / M, b = 1 / 0;
      } else {
        const M = h.sseDenominator;
        b = n.distanceToPoint(h.position), u = b === 0 ? 1 / 0 : t.geometricError / (b * M);
      }
      const I = o[m].frustum;
      n.intersectsFrustum(I) && (r = !0, a = Math.max(a, u), c = Math.min(c, b)), p = Math.max(p, u), l = Math.min(l, b);
    }
    r ? (e.inView = !0, e.error = a, e.distanceFromCamera = c) : (e.inView = !1, e.error = p, e.distanceFromCamera = l);
  }
  dispose() {
    super.dispose(), this.group.removeFromParent();
  }
}
class mi extends He {
  constructor() {
    super(new Ge(0, 0), new fi()), this.renderOrder = 1 / 0;
  }
  onBeforeRender(t) {
    const e = this.material.uniforms;
    t.getSize(e.resolution.value);
  }
  updateMatrixWorld() {
    this.matrixWorld.makeTranslation(this.position);
  }
  dispose() {
    this.geometry.dispose(), this.material.dispose();
  }
}
class fi extends Ze {
  constructor() {
    super({
      depthWrite: !1,
      depthTest: !1,
      transparent: !0,
      uniforms: {
        resolution: { value: new L() },
        size: { value: 15 },
        thickness: { value: 2 },
        opacity: { value: 1 }
      },
      vertexShader: (
        /* glsl */
        `

				uniform float size;
				uniform float thickness;
				uniform vec2 resolution;
				varying vec2 vUv;

				void main() {

					vUv = uv;

					float aspect = resolution.x / resolution.y;
					vec2 offset = uv * 2.0 - vec2( 1.0 );
					offset.y *= aspect;

					vec4 screenPoint = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
					screenPoint.xy += offset * ( size + thickness ) * screenPoint.w / resolution.x;

					gl_Position = screenPoint;

				}
			`
      ),
      fragmentShader: (
        /* glsl */
        `

				uniform float size;
				uniform float thickness;
				uniform float opacity;

				varying vec2 vUv;
				void main() {

					float ht = 0.5 * thickness;
					float planeDim = size + thickness;
					float offset = ( planeDim - ht - 2.0 ) / planeDim;
					float texelThickness = ht / planeDim;

					vec2 vec = vUv * 2.0 - vec2( 1.0 );
					float dist = abs( length( vec ) - offset );
					float fw = fwidth( dist ) * 0.5;
					float a = smoothstep( texelThickness - fw, texelThickness + fw, dist );

					gl_FragColor = vec4( 1, 1, 1, opacity * ( 1.0 - a ) );

				}
			`
      )
    });
  }
}
const pe = /* @__PURE__ */ new L(), de = /* @__PURE__ */ new L();
class gi {
  constructor() {
    this.domElement = null, this.buttons = 0, this.pointerType = null, this.pointerOrder = [], this.previousPositions = {}, this.pointerPositions = {}, this.startPositions = {}, this.pointerSetThisFrame = {}, this.hoverPosition = new L(), this.hoverSet = !1;
  }
  reset() {
    this.buttons = 0, this.pointerType = null, this.pointerOrder = [], this.previousPositions = {}, this.pointerPositions = {}, this.startPositions = {}, this.pointerSetThisFrame = {}, this.hoverPosition = new L(), this.hoverSet = !1;
  }
  // The pointers can be set multiple times per frame so track whether the pointer has
  // been set this frame or not so we don't overwrite the previous position and lose information
  // about pointer movement
  updateFrame() {
    const { previousPositions: t, pointerPositions: e } = this;
    for (const i in e)
      t[i].copy(e[i]);
  }
  setHoverEvent(t) {
    (t.pointerType === "mouse" || t.type === "wheel") && (this.getAdjustedPointer(t, this.hoverPosition), this.hoverSet = !0);
  }
  getLatestPoint(t) {
    return this.pointerType !== null ? (this.getCenterPoint(t), t) : this.hoverSet ? (t.copy(this.hoverPosition), t) : null;
  }
  // get the pointer position in the coordinate system of the target element
  getAdjustedPointer(t, e) {
    const s = (this.domElement ? this.domElement : t.target).getBoundingClientRect(), o = t.clientX - s.left, n = t.clientY - s.top;
    e.set(o, n);
  }
  addPointer(t) {
    const e = t.pointerId, i = new L();
    this.getAdjustedPointer(t, i), this.pointerOrder.push(e), this.pointerPositions[e] = i, this.previousPositions[e] = i.clone(), this.startPositions[e] = i.clone(), this.getPointerCount() === 1 && (this.pointerType = t.pointerType, this.buttons = t.buttons);
  }
  updatePointer(t) {
    const e = t.pointerId;
    return e in this.pointerPositions ? (this.getAdjustedPointer(t, this.pointerPositions[e]), !0) : !1;
  }
  deletePointer(t) {
    const e = t.pointerId, i = this.pointerOrder;
    i.splice(i.indexOf(e), 1), delete this.pointerPositions[e], delete this.previousPositions[e], delete this.startPositions[e], this.getPointerCount() === 0 && (this.buttons = 0, this.pointerType = null);
  }
  getPointerCount() {
    return this.pointerOrder.length;
  }
  getCenterPoint(t, e = this.pointerPositions) {
    const i = this.pointerOrder;
    if (this.getPointerCount() === 1 || this.getPointerType() === "mouse") {
      const s = i[0];
      return t.copy(e[s]), t;
    } else if (this.getPointerCount() === 2) {
      const s = this.pointerOrder[0], o = this.pointerOrder[1], n = e[s], r = e[o];
      return t.addVectors(n, r).multiplyScalar(0.5), t;
    }
    return null;
  }
  getPreviousCenterPoint(t) {
    return this.getCenterPoint(t, this.previousPositions);
  }
  getStartCenterPoint(t) {
    return this.getCenterPoint(t, this.startPositions);
  }
  getMoveDistance() {
    return this.getCenterPoint(pe), this.getPreviousCenterPoint(de), pe.sub(de).length();
  }
  getTouchPointerDistance(t = this.pointerPositions) {
    if (this.getPointerCount() <= 1 || this.getPointerType() === "mouse")
      return 0;
    const { pointerOrder: e } = this, i = e[0], s = e[1], o = t[i], n = t[s];
    return o.distanceTo(n);
  }
  getPreviousTouchPointerDistance() {
    return this.getTouchPointerDistance(this.previousPositions);
  }
  getStartTouchPointerDistance() {
    return this.getTouchPointerDistance(this.startPositions);
  }
  getPointerType() {
    return this.pointerType;
  }
  isPointerTouch() {
    return this.getPointerType() === "touch";
  }
  getPointerButtons() {
    return this.buttons;
  }
  isLeftClicked() {
    return !!(this.buttons & 1);
  }
  isRightClicked() {
    return !!(this.buttons & 2);
  }
}
const Ot = /* @__PURE__ */ new z();
function xt(g, t, e) {
  return e.makeTranslation(-g.x, -g.y, -g.z), Ot.makeRotationFromQuaternion(t), e.premultiply(Ot), Ot.makeTranslation(g.x, g.y, g.z), e.premultiply(Ot), e;
}
function ft(g, t, e) {
  e.x = g.x / t.clientWidth * 2 - 1, e.y = -(g.y / t.clientHeight) * 2 + 1, e.isVector3 && (e.z = 0);
}
function H(g, t, e) {
  const i = g instanceof Nt ? g : g.ray, { origin: s, direction: o } = i;
  s.set(t.x, t.y, -1).unproject(e), o.set(t.x, t.y, 1).unproject(e).sub(s), g.isRay || (g.near = 0, g.far = o.length(), g.camera = e), o.normalize();
}
const Z = 0, it = 1, K = 2, gt = 3, Zt = 4, q = 5, qt = 0.05, Qt = 0.025, et = /* @__PURE__ */ new z(), It = /* @__PURE__ */ new z(), N = /* @__PURE__ */ new y(), _ = /* @__PURE__ */ new y(), Rt = /* @__PURE__ */ new y(), zt = /* @__PURE__ */ new y(), W = /* @__PURE__ */ new y(), j = /* @__PURE__ */ new y(), $t = /* @__PURE__ */ new y(), At = /* @__PURE__ */ new y(), G = /* @__PURE__ */ new st(), ue = /* @__PURE__ */ new De(), R = /* @__PURE__ */ new y(), Ft = /* @__PURE__ */ new y(), Yt = /* @__PURE__ */ new y(), yi = /* @__PURE__ */ new st(), S = /* @__PURE__ */ new Nt(), Wt = /* @__PURE__ */ new y(), Lt = /* @__PURE__ */ new L(), k = /* @__PURE__ */ new L(), me = /* @__PURE__ */ new L(), Pt = /* @__PURE__ */ new L(), Xt = /* @__PURE__ */ new L(), fe = /* @__PURE__ */ new L(), Kt = { type: "change" }, ge = { type: "start" }, ye = { type: "end" };
class xi extends yt {
  /**
   * Whether the controls are active. When set to false, all input is ignored
   * and inertia is cleared.
   * @type {boolean}
   * @default true
   */
  get enabled() {
    return this._enabled;
  }
  set enabled(t) {
    t !== this.enabled && (this._enabled = t, this.resetState(), this.pointerTracker.reset(), this.enabled || (this.dragInertia.set(0, 0, 0), this.rotationInertia.set(0, 0)));
  }
  constructor(t = null, e = null, i = null) {
    super(), this.isEnvironmentControls = !0, this.domElement = null, this.camera = null, this.scene = null, this.tilesRenderer = null, this._enabled = !0, this.cameraRadius = 5, this.rotationSpeed = 1, this.minAltitude = 0, this.maxAltitude = 0.45 * Math.PI, this.minDistance = 10, this.maxDistance = 1 / 0, this.minZoom = 0, this.maxZoom = 1 / 0, this.zoomSpeed = 1, this.adjustHeight = !0, this.enableDamping = !1, this.dampingFactor = 0.15, this.fallbackPlane = new De(new y(0, 1, 0), 0), this.useFallbackPlane = !0, this.enableFlight = !1, this.flightSpeed = 10, this.flightSpeedMultiplier = 4, this.scaleZoomOrientationAtEdges = !1, this.autoAdjustCameraRotation = !0, this.state = Z, this.pointerTracker = new gi(), this.needsUpdate = !1, this.actionHeightOffset = 0, this.pivotPoint = new y(), this.zoomDirectionSet = !1, this.zoomPointSet = !1, this.zoomDirection = new y(), this.zoomPoint = new y(), this.zoomDelta = 0, this.rotationInertiaPivot = new y(), this.rotationInertia = new L(), this.dragInertia = new y(), this.inertiaTargetDistance = 1 / 0, this.inertiaStableFrames = 0, this.pivotMesh = new mi(), this.pivotMesh.raycast = () => {
    }, this.pivotMesh.scale.setScalar(0.25), this.raycaster = new qe(), this.raycaster.firstHitOnly = !0, this.up = new y(0, 1, 0), this._lastTime = performance.now(), this._keysDown = /* @__PURE__ */ new Set(), this._detachCallback = null, this._upInitialized = !1, this._lastUsedState = Z, this._zoomPointWasSet = !1, this._tilesOnChangeCallback = () => this.zoomPointSet = !1, i && this.attach(i), e && this.setCamera(e), t && this.setScene(t);
  }
  _getDeltaTime() {
    const t = performance.now(), e = t - this._lastTime;
    return this._lastTime = t, e * 1e-3;
  }
  /**
   * Sets the scene to raycast against for surface-based interaction.
   * @param {Object3D} scene
   */
  setScene(t) {
    this.scene = t;
  }
  /**
   * Sets the camera to control.
   * @param {Camera} camera
   */
  setCamera(t) {
    this.camera = t, this._upInitialized = !1, this.zoomDirectionSet = !1, this.zoomPointSet = !1, this.needsUpdate = !0, this.raycaster.camera = t, this.resetState();
  }
  /**
   * Attaches the controls to a DOM element, registering all pointer and keyboard event listeners.
   * @param {HTMLElement} domElement
   */
  attach(t) {
    if (this.domElement)
      throw new Error("EnvironmentControls: Controls already attached to element");
    this.domElement = t, this.pointerTracker.domElement = t, t.style.touchAction = "none", t.hasAttribute("tabindex") || (t.tabIndex = -1);
    const e = (d) => {
      this.enabled && d.preventDefault();
    }, i = (d) => {
      const {
        camera: h,
        raycaster: u,
        domElement: b,
        up: I,
        pivotMesh: M,
        pointerTracker: P,
        scene: f,
        pivotPoint: O,
        enabled: T,
        enableFlight: w,
        _keysDown: C
      } = this;
      if (!this.enabled)
        return;
      if (d.preventDefault(), b.focus(), P.addPointer(d), this.needsUpdate = !0, P.isPointerTouch()) {
        if (M.visible = !1, P.getPointerCount() === 0)
          b.setPointerCapture(d.pointerId);
        else if (P.getPointerCount() > 2) {
          this.resetState();
          return;
        }
      }
      P.getCenterPoint(k), ft(k, b, k), H(u, k, h);
      const A = Math.abs(u.ray.direction.dot(I));
      if (A < qt || A < Qt)
        return;
      const ot = C.has("w") || C.has("s") || C.has("a") || C.has("d") || C.has("q") || C.has("e") || C.has("arrowup") || C.has("arrowdown") || C.has("arrowleft") || C.has("arrowright") || C.has("shift");
      if (w && ot && !P.isPointerTouch() && (P.isRightClicked() || P.isLeftClicked())) {
        O.copy(h.position), this.setState(q);
        return;
      }
      const F = this._raycast(u);
      F && (P.getPointerCount() === 2 || P.isRightClicked() || P.isLeftClicked() && d.shiftKey ? (O.copy(F.point), M.position.copy(F.point), M.visible = P.isPointerTouch() ? !1 : T, M.updateMatrixWorld(), f.add(M), this.setState(P.isPointerTouch() ? Zt : K)) : P.isLeftClicked() && (O.copy(F.point), M.position.copy(F.point), M.updateMatrixWorld(), f.add(M), this.setState(it)));
    };
    let s = !1;
    const o = (d) => {
      const { pointerTracker: h } = this;
      if (!this.enabled)
        return;
      d.preventDefault();
      const {
        pivotMesh: u,
        enabled: b
      } = this;
      this.zoomDirectionSet = !1, this.zoomPointSet = !1, this.state !== Z && (this.needsUpdate = !0), h.setHoverEvent(d), h.updatePointer(d) && (h.isPointerTouch() && h.getPointerCount() === 2 && (s || (s = !0, queueMicrotask(() => {
        s = !1, h.getCenterPoint(Xt);
        const I = h.getStartTouchPointerDistance(), M = h.getTouchPointerDistance(), P = M - I;
        if (this.state === Z || this.state === Zt) {
          h.getCenterPoint(Xt), h.getStartCenterPoint(fe);
          const f = 2 * window.devicePixelRatio, O = Xt.distanceTo(fe);
          (Math.abs(P) > f || O > f) && (Math.abs(P) > O ? (this.setState(gt), this.zoomDirectionSet = !1) : this.setState(K));
        }
        if (this.state === gt) {
          const f = h.getPreviousTouchPointerDistance();
          this.zoomDelta += M - f, u.visible = !1;
        } else this.state === K && (u.visible = b);
      }))), this.dispatchEvent(Kt));
    }, n = (d) => {
      const { pointerTracker: h } = this;
      !this.enabled || h.getPointerCount() === 0 || (h.deletePointer(d), h.getPointerType() === "touch" && h.getPointerCount() === 0 && t.releasePointerCapture(d.pointerId), this.resetState(), this.needsUpdate = !0);
    }, r = (d) => {
      if (!this.enabled)
        return;
      d.preventDefault();
      const { pointerTracker: h } = this;
      h.setHoverEvent(d), h.updatePointer(d), this.dispatchEvent(ge);
      let u;
      switch (d.deltaMode) {
        case 2:
          u = d.deltaY * 800;
          break;
        case 1:
          u = d.deltaY * 40;
          break;
        case 0:
          u = d.deltaY;
          break;
      }
      const b = Math.sign(u), I = Math.abs(u);
      this.zoomDelta -= 0.25 * b * I, this.needsUpdate = !0, this._lastUsedState = gt, this.dispatchEvent(ye);
    }, a = (d) => {
      this.enabled && this.resetState();
    };
    t.addEventListener("contextmenu", e), t.addEventListener("pointerdown", i), t.addEventListener("wheel", r, { passive: !1 });
    const c = t.getRootNode();
    c.addEventListener("pointermove", o), c.addEventListener("pointerup", n), c.addEventListener("pointerleave", a);
    const p = (d) => {
      const { _keysDown: h, state: u } = this;
      h.add(d.key.toLowerCase()), (h.has("w") || h.has("s") || h.has("a") || h.has("d") || h.has("q") || h.has("e") || h.has("arrowup") || h.has("arrowdown") || h.has("arrowleft") || h.has("arrowright")) && u !== q && this.resetState();
    }, l = (d) => {
      this._keysDown.delete(d.key.toLowerCase());
    }, m = () => {
      this._keysDown.clear();
    };
    t.addEventListener("keydown", p), window.addEventListener("keyup", l), window.addEventListener("blur", m), this._detachCallback = () => {
      t.removeEventListener("contextmenu", e), t.removeEventListener("pointerdown", i), t.removeEventListener("wheel", r), c.removeEventListener("pointermove", o), c.removeEventListener("pointerup", n), c.removeEventListener("pointerleave", a), t.removeEventListener("keydown", p), window.removeEventListener("keyup", l), window.removeEventListener("blur", m);
    };
  }
  /**
   * Detaches the controls from the DOM element, removing all event listeners.
   */
  detach() {
    this.domElement = null, this._detachCallback && (this._detachCallback(), this._detachCallback = null, this.pointerTracker.reset());
  }
  /**
   * Returns the local up direction at a world-space point. Override to provide terrain-aware
   * up vectors (e.g. ellipsoid normals). Default returns the controls' `up` vector.
   * @param {Vector3} point - World-space point to query.
   * @param {Vector3} target - Target vector to write the result into.
   */
  getUpDirection(t, e) {
    e.copy(this.up);
  }
  /**
   * Returns the local up direction at the camera's current position.
   * @param {Vector3} target - Target vector to write the result into.
   */
  getCameraUpDirection(t) {
    this.getUpDirection(this.camera.position, t);
  }
  /**
   * Returns the current drag or rotation pivot point in world space.
   * @param {Vector3} target - Target vector to write the result into.
   * @returns {Vector3|null} The target vector, or null if no pivot is active.
   */
  getPivotPoint(t) {
    let e = null;
    this._lastUsedState === gt ? this._zoomPointWasSet && (e = t.copy(this.zoomPoint)) : (this._lastUsedState === K || this._lastUsedState === it) && (e = t.copy(this.pivotPoint));
    const { camera: i, raycaster: s } = this;
    e !== null && (_.copy(e).project(i), (_.x < -1 || _.x > 1 || _.y < -1 || _.y > 1) && (e = null)), H(s, { x: 0, y: 0 }, i);
    const o = this._raycast(s);
    return o && (e === null || o.distance < e.distanceTo(s.ray.origin)) && (e = t.copy(o.point)), e;
  }
  /**
   * Clears the current interaction state, cancelling any active drag, rotate, or zoom.
   */
  resetState() {
    this.state !== Z && this.dispatchEvent(ye), this.state = Z, this.pivotMesh.removeFromParent(), this.pivotMesh.visible = this.enabled, this.actionHeightOffset = 0, this.pointerTracker.reset();
  }
  /**
   * Sets the current control state (e.g. `NONE`, `DRAG`, `ROTATE`, `ZOOM`).
   * @param {number} [state] - One of the exported state constants. Defaults to current state.
   * @param {boolean} [fireEvent=true] - Whether to dispatch `'start'` and `'end'` events.
   */
  setState(t = this.state, e = !0) {
    this.state !== t && (this.state === Z && e && this.dispatchEvent(ge), this.pivotMesh.visible = this.enabled, this.dragInertia.set(0, 0, 0), this.rotationInertia.set(0, 0), this.inertiaStableFrames = 0, this.state = t, t !== Z && t !== Zt && (this._lastUsedState = t));
  }
  /**
   * Applies pending input and inertia to the camera. Must be called each frame.
   * @param {number} [deltaTime] - Time in seconds since the last frame. Defaults to the clock delta, capped at 64ms.
   */
  update(t = Math.min(this._getDeltaTime(), 64 / 1e3)) {
    if (!this.enabled || !this.camera || t === 0)
      return;
    const {
      camera: e,
      cameraRadius: i,
      pivotPoint: s,
      up: o,
      state: n,
      adjustHeight: r,
      autoAdjustCameraRotation: a
    } = this;
    e.updateMatrixWorld(), this.getCameraUpDirection(R), this._upInitialized || (this._upInitialized = !0, this.up.copy(R)), this.zoomPointSet = !1;
    const c = this._inertiaNeedsUpdate(), p = this.needsUpdate || c;
    if (this.needsUpdate || c) {
      const d = this.zoomDelta;
      this._updateZoom(), this._updatePosition(t), this._updateRotation(t), n === it || n === K || n === q ? (W.set(0, 0, -1).transformDirection(e.matrixWorld), this.inertiaTargetDistance = _.copy(s).sub(e.position).dot(W)) : n === Z && this._updateInertia(t), (n !== Z || d !== 0 || c) && this.dispatchEvent(Kt), this.needsUpdate = !1;
    }
    const l = this._updateFlight(t);
    l && (this.dragInertia.set(0, 0, 0), this.rotationInertia.set(0, 0, 0), this.dispatchEvent(Kt));
    const m = e.isOrthographicCamera ? null : r && !l && this._getPointBelowCamera() || null;
    if (this.getCameraUpDirection(R), this._setFrame(R), (this.state === it || this.state === K || this.state === q) && this.actionHeightOffset !== 0) {
      const { actionHeightOffset: d } = this;
      e.position.addScaledVector(o, -d), s.addScaledVector(o, -d), m && (m.distance -= d);
    }
    if (this.actionHeightOffset = 0, m) {
      const d = m.distance;
      if (d < i) {
        const h = i - d;
        e.position.addScaledVector(o, h), s.addScaledVector(o, h), this.actionHeightOffset = h;
      }
    }
    this.pointerTracker.updateFrame(), (p && a || l) && (this.getCameraUpDirection(R), this._alignCameraUp(R, 1), this.getCameraUpDirection(R), this._clampRotation(R));
  }
  /**
   * Adjusts the camera to satisfy altitude and distance constraints. Called automatically by `update`.
   * Override in subclasses to add custom camera adjustment behaviour (e.g. near/far plane updates).
   * @param {Camera} camera
   */
  adjustCamera(t) {
    const { adjustHeight: e, cameraRadius: i } = this;
    if (t.isPerspectiveCamera) {
      this.getUpDirection(t.position, R);
      const s = e && this._getPointBelowCamera(t.position, R) || null;
      if (s) {
        const o = s.distance;
        o < i && t.position.addScaledVector(R, i - o);
      }
    }
  }
  /**
   * Disposes of event listeners and internal resources. Calls `detach` if currently attached.
   */
  dispose() {
    this.detach();
  }
  // private
  _updateInertia(t) {
    const {
      rotationInertia: e,
      pivotPoint: i,
      dragInertia: s,
      enableDamping: o,
      dampingFactor: n,
      camera: r,
      cameraRadius: a,
      minDistance: c,
      inertiaTargetDistance: p
    } = this;
    if (!this.enableDamping || this.inertiaStableFrames > 1) {
      s.set(0, 0, 0), e.set(0, 0, 0);
      return;
    }
    const l = Math.pow(2, -t / n), m = Math.max(r.near, a, c, p), u = 0.25 * (2 / (2 * 1e3));
    if (e.lengthSq() > 0) {
      H(S, _.set(0, 0, -1), r), S.applyMatrix4(r.matrixWorldInverse), S.direction.normalize(), S.recast(-S.direction.dot(S.origin)).at(m / S.direction.z, _), _.applyMatrix4(r.matrixWorld), H(S, N.set(u, u, -1), r), S.applyMatrix4(r.matrixWorldInverse), S.direction.normalize(), S.recast(-S.direction.dot(S.origin)).at(m / S.direction.z, N), N.applyMatrix4(r.matrixWorld), _.sub(i).normalize(), N.sub(i).normalize();
      const b = _.angleTo(N) / t;
      e.multiplyScalar(l), (e.lengthSq() < b ** 2 || !o) && e.set(0, 0);
    }
    if (s.lengthSq() > 0) {
      H(S, _.set(0, 0, -1), r), S.applyMatrix4(r.matrixWorldInverse), S.direction.normalize(), S.recast(-S.direction.dot(S.origin)).at(m / S.direction.z, _), _.applyMatrix4(r.matrixWorld), H(S, N.set(u, u, -1), r), S.applyMatrix4(r.matrixWorldInverse), S.direction.normalize(), S.recast(-S.direction.dot(S.origin)).at(m / S.direction.z, N), N.applyMatrix4(r.matrixWorld);
      const b = _.distanceTo(N) / t;
      s.multiplyScalar(l), (s.lengthSq() < b ** 2 || !o) && s.set(0, 0, 0);
    }
    e.lengthSq() > 0 && this._applyRotation(e.x * t, e.y * t, i), s.lengthSq() > 0 && (r.position.addScaledVector(s, t), r.updateMatrixWorld());
  }
  _inertiaNeedsUpdate() {
    const { rotationInertia: t, dragInertia: e } = this;
    return t.lengthSq() !== 0 || e.lengthSq() !== 0;
  }
  _getFlightSpeedScale() {
    return 1;
  }
  _updateFlight(t) {
    const {
      camera: e,
      enableFlight: i,
      flightSpeed: s,
      flightSpeedMultiplier: o,
      _keysDown: n
    } = this;
    if (!i || e.isOrthographicCamera)
      return !1;
    const r = n.has("w") || n.has("arrowup"), a = n.has("s") || n.has("arrowdown"), c = n.has("a") || n.has("arrowleft"), p = n.has("d") || n.has("arrowright"), l = n.has("q"), m = n.has("e"), h = (n.has("shift") ? o : 1) * s * this._getFlightSpeedScale() * t;
    return Wt.set(
      (p ? 1 : 0) - (c ? 1 : 0),
      (l ? 1 : 0) - (m ? 1 : 0),
      (a ? 1 : 0) - (r ? 1 : 0)
    ), Wt.lengthSq() === 0 ? !1 : (Wt.normalize().transformDirection(e.matrixWorld), e.position.addScaledVector(Wt, h), e.updateMatrixWorld(), !0);
  }
  _updateZoom() {
    const {
      zoomPoint: t,
      zoomDirection: e,
      camera: i,
      minDistance: s,
      maxDistance: o,
      pointerTracker: n,
      domElement: r,
      minZoom: a,
      maxZoom: c,
      zoomSpeed: p,
      state: l
    } = this;
    let m = this.zoomDelta;
    if (this.zoomDelta = 0, !(!n.getLatestPoint(k) || m === 0 && l !== gt))
      if (this.rotationInertia.set(0, 0), this.dragInertia.set(0, 0, 0), i.isOrthographicCamera) {
        this._updateZoomDirection();
        const d = this.zoomPointSet || this._updateZoomPoint();
        Ft.unproject(i);
        const h = Math.pow(0.95, Math.abs(m * 0.05));
        let u = m > 0 ? 1 / Math.abs(h) : h;
        u *= p, u > 1 ? c < i.zoom * u && (u = 1) : a > i.zoom * u && (u = 1), i.zoom *= u, i.updateProjectionMatrix(), d && (ft(k, r, Yt), Yt.unproject(i), i.position.sub(Yt).add(Ft), i.updateMatrixWorld());
      } else {
        this._updateZoomDirection();
        const d = _.copy(e);
        if (this.zoomPointSet || this._updateZoomPoint()) {
          const h = t.distanceTo(i.position);
          if (m < 0) {
            const u = Math.min(0, h - o);
            m = m * h * p * 25e-4, m = Math.max(m, u);
          } else {
            const u = Math.max(0, h - s);
            m = m * Math.max(h - s, 0) * p * 25e-4, m = Math.min(m, u);
          }
          i.position.addScaledVector(e, m), i.updateMatrixWorld();
        } else {
          const h = this._getPointBelowCamera();
          if (h) {
            const u = h.distance;
            d.set(0, 0, -1).transformDirection(i.matrixWorld), i.position.addScaledVector(d, m * u * 0.01), i.updateMatrixWorld();
          } else
            i.position.addScaledVector(e, m), i.updateMatrixWorld();
        }
      }
  }
  _updateZoomDirection() {
    if (this.zoomDirectionSet)
      return;
    const { domElement: t, raycaster: e, camera: i, zoomDirection: s, pointerTracker: o } = this;
    o.getLatestPoint(k), ft(k, t, Ft), H(e, Ft, i), s.copy(e.ray.direction).normalize(), this.zoomDirectionSet = !0;
  }
  // update the point being zoomed in to based on the zoom direction
  _updateZoomPoint() {
    const {
      camera: t,
      zoomDirectionSet: e,
      zoomDirection: i,
      raycaster: s,
      zoomPoint: o,
      pointerTracker: n,
      domElement: r
    } = this;
    if (this._zoomPointWasSet = !1, !e)
      return !1;
    t.isOrthographicCamera && n.getLatestPoint(Lt) ? (ft(Lt, r, Lt), H(s, Lt, t)) : (s.ray.origin.copy(t.position), s.ray.direction.copy(i), s.near = 0, s.far = 1 / 0);
    const a = this._raycast(s);
    return a ? (o.copy(a.point), this.zoomPointSet = !0, this._zoomPointWasSet = !0, !0) : !1;
  }
  // returns the point below the camera
  _getPointBelowCamera(t = this.camera.position, e = this.up) {
    const { raycaster: i } = this;
    i.ray.direction.copy(e).multiplyScalar(-1), i.ray.origin.copy(t).addScaledVector(e, 1e5), i.near = 0, i.far = 1 / 0;
    const s = this._raycast(i);
    return s && (s.distance -= 1e5), s;
  }
  // update the drag action
  _updatePosition(t) {
    const {
      raycaster: e,
      camera: i,
      pivotPoint: s,
      up: o,
      pointerTracker: n,
      domElement: r,
      state: a,
      dragInertia: c
    } = this;
    if (a === it) {
      if (n.getCenterPoint(k), ft(k, r, k), ue.setFromNormalAndCoplanarPoint(o, s), H(e, k, i), Math.abs(e.ray.direction.dot(o)) < qt) {
        const p = Math.acos(qt);
        At.crossVectors(e.ray.direction, o).normalize(), e.ray.direction.copy(o).applyAxisAngle(At, p).multiplyScalar(-1);
      }
      if (this.getUpDirection(s, R), Math.abs(e.ray.direction.dot(R)) < Qt) {
        const p = Math.acos(Qt);
        At.crossVectors(e.ray.direction, R).normalize(), e.ray.direction.copy(R).applyAxisAngle(At, p).multiplyScalar(-1);
      }
      e.ray.intersectPlane(ue, _) && (N.subVectors(s, _), i.position.add(N), i.updateMatrixWorld(), N.multiplyScalar(1 / t), n.getMoveDistance() / t < 2 * window.devicePixelRatio ? this.inertiaStableFrames++ : (c.copy(N), this.inertiaStableFrames = 0));
    }
  }
  _updateRotation(t) {
    const {
      pivotPoint: e,
      pointerTracker: i,
      domElement: s,
      state: o,
      rotationInertia: n
    } = this;
    (o === K || o === q) && (o === q && e.copy(this.camera.position), i.getCenterPoint(k), i.getPreviousCenterPoint(me), Pt.subVectors(k, me).multiplyScalar(2 * Math.PI / s.clientHeight), this._applyRotation(Pt.x, Pt.y, e), Pt.multiplyScalar(1 / t), i.getMoveDistance() / t < 2 * window.devicePixelRatio ? this.inertiaStableFrames++ : (n.copy(Pt), this.inertiaStableFrames = 0));
  }
  _applyRotation(t, e, i) {
    if (t === 0 && e === 0)
      return;
    const {
      camera: s,
      minAltitude: o,
      maxAltitude: n,
      rotationSpeed: r
    } = this, a = -t * r;
    let c = e * r;
    W.set(0, 0, 1).transformDirection(s.matrixWorld), j.set(1, 0, 0).transformDirection(s.matrixWorld), this.getUpDirection(i, R);
    let p;
    R.dot(W) > 1 - 1e-10 ? p = 0 : (_.crossVectors(R, W).normalize(), p = Math.sign(_.dot(j)) * R.angleTo(W)), c > 0 ? (c = Math.min(p - o, c), c = Math.max(0, c)) : (c = Math.max(p - n, c), c = Math.min(0, c)), G.setFromAxisAngle(R, a), xt(i, G, et), s.matrixWorld.premultiply(et), j.set(1, 0, 0).transformDirection(s.matrixWorld), G.setFromAxisAngle(j, -c), xt(i, G, et), s.matrixWorld.premultiply(et), s.matrixWorld.decompose(s.position, s.quaternion, _);
  }
  // sets the "up" axis for the current surface of the tileset
  _setFrame(t) {
    const {
      up: e,
      camera: i,
      zoomPoint: s,
      zoomDirectionSet: o,
      zoomPointSet: n,
      scaleZoomOrientationAtEdges: r
    } = this;
    if (o && (n || this._updateZoomPoint())) {
      if (G.setFromUnitVectors(e, t), r) {
        this.getUpDirection(s, _);
        let a = Math.max(_.dot(e) - 0.6, 0) / 0.4;
        a = v.mapLinear(a, 0, 0.5, 0, 1), a = Math.min(a, 1), i.isOrthographicCamera && (a *= 0.1), G.slerp(yi, 1 - a);
      }
      xt(s, G, et), i.updateMatrixWorld(), i.matrixWorld.premultiply(et), i.matrixWorld.decompose(i.position, i.quaternion, _), this.zoomDirectionSet = !1, this._updateZoomDirection();
    }
    e.copy(t), i.updateMatrixWorld();
  }
  _raycast(t) {
    const { scene: e, useFallbackPlane: i, fallbackPlane: s } = this, o = t.intersectObject(e)[0] || null;
    if (o)
      return o;
    if (i) {
      const n = s;
      if (t.ray.intersectPlane(n, _))
        return {
          point: _.clone(),
          distance: t.ray.origin.distanceTo(_)
        };
    }
    return null;
  }
  // tilt the camera to align with the provided "up" value
  _alignCameraUp(t, e = 1) {
    const { camera: i, state: s, pivotPoint: o, zoomPoint: n, zoomPointSet: r } = this;
    i.updateMatrixWorld(), W.set(0, 0, -1).transformDirection(i.matrixWorld), j.set(-1, 0, 0).transformDirection(i.matrixWorld);
    let a = v.mapLinear(1 - Math.abs(W.dot(t)), 0, 0.2, 0, 1);
    a = v.clamp(a, 0, 1), e *= a, $t.crossVectors(t, W), $t.lerp(j, 1 - e).normalize(), G.setFromUnitVectors(j, $t), i.quaternion.premultiply(G);
    let c = null;
    s === it || s === K || s === q ? c = Rt.copy(o) : r && (c = Rt.copy(n)), c && (It.copy(i.matrixWorld).invert(), _.copy(c).applyMatrix4(It), i.updateMatrixWorld(), _.applyMatrix4(i.matrixWorld), zt.subVectors(c, _), i.position.add(zt)), i.updateMatrixWorld();
  }
  // clamp rotation to the given "up" vector
  _clampRotation(t) {
    const { camera: e, minAltitude: i, maxAltitude: s, state: o, pivotPoint: n, zoomPoint: r, zoomPointSet: a } = this;
    e.updateMatrixWorld(), W.set(0, 0, 1).transformDirection(e.matrixWorld), j.set(1, 0, 0).transformDirection(e.matrixWorld);
    let c;
    t.dot(W) > 1 - 1e-10 ? c = 0 : (_.crossVectors(t, W), c = Math.sign(_.dot(j)) * t.angleTo(W));
    let p;
    if (c > s)
      p = s;
    else if (c < i)
      p = i;
    else
      return;
    W.copy(t), G.setFromAxisAngle(j, p), W.applyQuaternion(G).normalize(), _.crossVectors(W, j).normalize(), et.makeBasis(j, _, W), e.quaternion.setFromRotationMatrix(et);
    let l = null;
    o === it || o === K || o === q ? l = Rt.copy(n) : a && (l = Rt.copy(r)), l && (It.copy(e.matrixWorld).invert(), _.copy(l).applyMatrix4(It), e.updateMatrixWorld(), _.applyMatrix4(e.matrixWorld), zt.subVectors(l, _), e.position.add(zt)), e.updateMatrixWorld();
  }
}
const xe = /* @__PURE__ */ new z(), ut = /* @__PURE__ */ new z(), U = /* @__PURE__ */ new y(), D = /* @__PURE__ */ new y(), J = /* @__PURE__ */ new y(), B = /* @__PURE__ */ new y(), bi = /* @__PURE__ */ new y(), mt = /* @__PURE__ */ new y(), tt = /* @__PURE__ */ new st(), be = /* @__PURE__ */ new y(), rt = /* @__PURE__ */ new y(), E = /* @__PURE__ */ new Nt(), _e = /* @__PURE__ */ new ti(), Vt = /* @__PURE__ */ new L(), Me = {}, _i = 2550;
class zi extends xi {
  /**
   * The world matrix of `ellipsoidGroup`, representing the ellipsoid's coordinate frame.
   * @type {Matrix4}
   * @readonly
   */
  get ellipsoidFrame() {
    return this.ellipsoidGroup.matrixWorld;
  }
  /**
   * The inverse of `ellipsoidFrame`.
   * @type {Matrix4}
   * @readonly
   */
  get ellipsoidFrameInverse() {
    const { ellipsoidGroup: t, ellipsoidFrame: e, _ellipsoidFrameInverse: i } = this;
    return t.matrixWorldInverse ? t.matrixWorldInverse : i.copy(e).invert();
  }
  constructor(t = null, e = null, i = null) {
    super(t, e, i), this.isGlobeControls = !0, this._dragMode = 0, this._rotationMode = 0, this.maxZoom = 0.01, this.nearMargin = 0.25, this.farMargin = 0, this.useFallbackPlane = !1, this.autoAdjustCameraRotation = !1, this.globeInertia = new st(), this.globeInertiaFactor = 0, this.ellipsoid = vt.clone(), this.ellipsoidGroup = new Dt(), this._ellipsoidFrameInverse = new z();
  }
  /**
   * Sets the ellipsoid model and its scene group for globe-aware interaction.
   * @param {Ellipsoid} [ellipsoid] - Ellipsoid to use. Defaults to a WGS84 clone.
   * @param {Group} [ellipsoidGroup] - Group whose world matrix defines the ellipsoid frame.
   */
  setEllipsoid(t, e) {
    this.ellipsoid = t || vt.clone(), this.ellipsoidGroup = e || new Dt();
  }
  getPivotPoint(t) {
    const { camera: e, ellipsoidFrame: i, ellipsoidFrameInverse: s, ellipsoid: o } = this;
    return B.set(0, 0, -1).transformDirection(e.matrixWorld), E.origin.copy(e.position), E.direction.copy(B), E.applyMatrix4(s), o.closestPointToRayEstimate(E, D).applyMatrix4(i), (super.getPivotPoint(t) === null || U.subVectors(t, E.origin).dot(E.direction) > U.subVectors(D, E.origin).dot(E.direction)) && t.copy(D), t;
  }
  /**
   * Returns the vector from the camera to the center of the ellipsoid in world space.
   * @param {Vector3} target
   * @returns {Vector3}
   */
  getVectorToCenter(t) {
    const { ellipsoidFrame: e, camera: i } = this;
    return t.setFromMatrixPosition(e).sub(i.position);
  }
  /**
   * Returns the distance from the camera to the center of the ellipsoid.
   * @returns {number}
   */
  getDistanceToCenter() {
    return this.getVectorToCenter(D).length();
  }
  getUpDirection(t, e) {
    const { ellipsoidFrame: i, ellipsoidFrameInverse: s, ellipsoid: o } = this;
    D.copy(t).applyMatrix4(s), o.getPositionToNormal(D, e), e.transformDirection(i);
  }
  getCameraUpDirection(t) {
    const { ellipsoidFrame: e, ellipsoidFrameInverse: i, ellipsoid: s, camera: o } = this;
    o.isOrthographicCamera ? (this._getVirtualOrthoCameraPosition(D), D.applyMatrix4(i), s.getPositionToNormal(D, t), t.transformDirection(e)) : this.getUpDirection(o.position, t);
  }
  update(t = Math.min(this._getDeltaTime(), 64 / 1e3)) {
    if (!this.enabled || !this.camera || t === 0)
      return;
    const { camera: e, pivotMesh: i } = this;
    this._isNearControls() ? this.scaleZoomOrientationAtEdges = this.zoomDelta < 0 : (this.state !== Z && this._dragMode !== 1 && this._rotationMode !== 1 && (i.visible = !1), this.scaleZoomOrientationAtEdges = !1);
    const s = this.needsUpdate || this._inertiaNeedsUpdate();
    super.update(t), this.adjustCamera(e), s && (this._isNearControls() || this.state === q) && (this.getCameraUpDirection(mt), this._alignCameraUp(mt, 1), this.getCameraUpDirection(mt), this._clampRotation(mt));
  }
  // Updates the passed camera near and far clip planes to encapsulate the ellipsoid from the
  // current position in addition to adjusting the height.
  adjustCamera(t) {
    super.adjustCamera(t);
    const { ellipsoidFrame: e, ellipsoidFrameInverse: i, ellipsoid: s, nearMargin: o, farMargin: n } = this, r = this._getMaxWorldRadius();
    if (t.isPerspectiveCamera) {
      const a = D.setFromMatrixPosition(e).sub(t.position).length(), c = o * r, p = v.clamp((a - r) / c, 0, 1), l = v.lerp(1, 1e3, p);
      t.near = Math.max(l, a - r - c), U.copy(t.position).applyMatrix4(i), s.getPositionToCartographic(U, Me);
      const m = Math.max(s.getPositionElevation(U), _i), d = s.calculateHorizonDistance(Me.lat, m);
      t.far = d + 0.1 + r * n, t.updateProjectionMatrix();
    } else {
      this._getVirtualOrthoCameraPosition(t.position, t), t.updateMatrixWorld(), xe.copy(t.matrixWorld).invert(), D.setFromMatrixPosition(e).applyMatrix4(xe);
      const a = -D.z;
      t.near = a - r * (1 + o), t.far = a + 0.1 + r * n, t.position.addScaledVector(B, t.near), t.far -= t.near, t.near = 0, t.updateProjectionMatrix(), t.updateMatrixWorld();
    }
  }
  // resets the "stuck" drag modes
  setState(...t) {
    super.setState(...t), this._dragMode = 0, this._rotationMode = 0;
  }
  _updateInertia(t) {
    super._updateInertia(t);
    const {
      globeInertia: e,
      enableDamping: i,
      dampingFactor: s,
      camera: o,
      cameraRadius: n,
      minDistance: r,
      inertiaTargetDistance: a,
      ellipsoidFrame: c
    } = this;
    if (!this.enableDamping || this.inertiaStableFrames > 1) {
      this.globeInertiaFactor = 0, this.globeInertia.identity();
      return;
    }
    const p = Math.pow(2, -t / s), l = Math.max(o.near, n, r, a), h = 0.25 * (2 / (2 * 1e3));
    if (J.setFromMatrixPosition(c), this.globeInertiaFactor !== 0) {
      H(E, D.set(0, 0, -1), o), E.applyMatrix4(o.matrixWorldInverse), E.direction.normalize(), E.recast(-E.direction.dot(E.origin)).at(l / E.direction.z, D), D.applyMatrix4(o.matrixWorld), H(E, U.set(h, h, -1), o), E.applyMatrix4(o.matrixWorldInverse), E.direction.normalize(), E.recast(-E.direction.dot(E.origin)).at(l / E.direction.z, U), U.applyMatrix4(o.matrixWorld), D.sub(J).normalize(), U.sub(J).normalize(), this.globeInertiaFactor *= p;
      const u = D.angleTo(U) / t;
      (2 * Math.acos(e.w) * this.globeInertiaFactor < u || !i) && (this.globeInertiaFactor = 0, e.identity());
    }
    this.globeInertiaFactor !== 0 && (e.w === 1 && (e.x !== 0 || e.y !== 0 || e.z !== 0) && (e.w = Math.min(e.w, 1 - 1e-9)), J.setFromMatrixPosition(c), tt.identity().slerp(e, this.globeInertiaFactor * t), xt(J, tt, ut), o.matrixWorld.premultiply(ut), o.matrixWorld.decompose(o.position, o.quaternion, D));
  }
  _inertiaNeedsUpdate() {
    return super._inertiaNeedsUpdate() || this.globeInertiaFactor !== 0;
  }
  _getFlightSpeedScale() {
    const t = this.getDistanceToCenter() - this._getMaxWorldRadius();
    return 2 * Math.max(t, 1e3);
  }
  _updateFlight(t) {
    const { camera: e } = this, i = super._updateFlight(t);
    if (i) {
      const s = this._getMaxPerspectiveDistance(), o = this.getDistanceToCenter();
      if (o > s && (this.getVectorToCenter(D).normalize(), e.position.addScaledVector(D, o - s), e.updateMatrixWorld()), !this._isNearControls()) {
        const n = v.clamp(
          v.mapLinear(this.getDistanceToCenter(), this._getPerspectiveTransitionDistance(), s, 0, 1),
          0,
          1
        );
        this._tiltTowardsCenter(0.02 * n), this._alignCameraUpToNorth(0.01 * n);
      }
    }
    return i;
  }
  _updatePosition(t) {
    if (this.state === it) {
      this._dragMode === 0 && (this._dragMode = this._isNearControls() ? 1 : -1);
      const {
        raycaster: e,
        camera: i,
        pivotPoint: s,
        pointerTracker: o,
        domElement: n,
        ellipsoidFrame: r,
        ellipsoidFrameInverse: a
      } = this, c = U, p = bi;
      o.getCenterPoint(Vt), ft(Vt, n, Vt), H(e, Vt, i), e.ray.applyMatrix4(a);
      const l = D.copy(s).applyMatrix4(a).length();
      if (_e.radius.setScalar(l), !_e.intersectRay(e.ray, D)) {
        this.resetState(), this._updateInertia(t);
        return;
      }
      D.applyMatrix4(r), J.setFromMatrixPosition(r), c.subVectors(s, J).normalize(), p.subVectors(D, J).normalize(), tt.setFromUnitVectors(p, c), xt(J, tt, ut), i.matrixWorld.premultiply(ut), i.matrixWorld.decompose(i.position, i.quaternion, D), o.getMoveDistance() / t < 2 * window.devicePixelRatio ? this.inertiaStableFrames++ : (this.globeInertia.copy(tt), this.globeInertiaFactor = 1 / t, this.inertiaStableFrames = 0);
    }
  }
  // disable rotation once we're outside the control transition
  _updateRotation(...t) {
    if (this.state === q) {
      super._updateRotation(...t);
      return;
    }
    this._rotationMode === 1 || this._isNearControls() ? (this._rotationMode = 1, super._updateRotation(...t)) : (this.pivotMesh.visible = !1, this._rotationMode = -1);
  }
  _updateZoom() {
    const { zoomDelta: t, zoomSpeed: e, zoomPoint: i, camera: s, maxZoom: o, state: n } = this;
    if (n !== gt && t === 0)
      return;
    this.rotationInertia.set(0, 0), this.dragInertia.set(0, 0, 0), this.globeInertia.identity(), this.globeInertiaFactor = 0;
    const r = v.clamp(v.mapLinear(Math.abs(t), 0, 20, 0, 1), 0, 1);
    if (this._isNearControls() || t > 0) {
      if (this._updateZoomDirection(), t < 0 && (this.zoomPointSet || this._updateZoomPoint())) {
        B.set(0, 0, -1).transformDirection(s.matrixWorld).normalize(), rt.copy(this.up).multiplyScalar(-1), this.getUpDirection(i, be);
        const a = v.clamp(v.mapLinear(-be.dot(rt), 1, 0.95, 0, 1), 0, 1), c = 1 - B.dot(rt), p = s.isOrthographicCamera ? 0.05 : 1, l = v.clamp(r * 3, 0, 1), m = Math.min(a * c * p * l, 0.1);
        rt.lerpVectors(B, rt, m).normalize(), tt.setFromUnitVectors(B, rt), xt(i, tt, ut), s.matrixWorld.premultiply(ut), s.matrixWorld.decompose(s.position, s.quaternion, rt), this.zoomDirection.subVectors(i, s.position).normalize();
      }
      super._updateZoom();
    } else if (s.isPerspectiveCamera) {
      const a = this._getPerspectiveTransitionDistance(), c = this._getMaxPerspectiveDistance(), p = v.mapLinear(this.getDistanceToCenter(), a, c, 0, 1);
      this._tiltTowardsCenter(v.lerp(0, 0.4, p * r)), this._alignCameraUpToNorth(v.lerp(0, 0.2, p * r));
      const l = this.getDistanceToCenter() - this._getMaxWorldRadius(), m = t * l * e * 25e-4, d = Math.max(m, Math.min(this.getDistanceToCenter() - c, 0));
      this.getVectorToCenter(D).normalize(), this.camera.position.addScaledVector(D, d), this.camera.updateMatrixWorld(), this.zoomDelta = 0;
    } else {
      const a = this._getOrthographicTransitionZoom(), c = this._getMinOrthographicZoom(), p = v.mapLinear(s.zoom, a, c, 0, 1);
      this._tiltTowardsCenter(v.lerp(0, 0.4, p * r)), this._alignCameraUpToNorth(v.lerp(0, 0.2, p * r));
      const l = this.zoomDelta, m = Math.pow(0.95, Math.abs(l * 0.05)), d = l > 0 ? 1 / Math.abs(m) : m, h = c / s.zoom, u = Math.max(d * e, Math.min(h, 1));
      s.zoom = Math.min(o, s.zoom * u), s.updateProjectionMatrix(), this.zoomDelta = 0, this.zoomDirectionSet = !1;
    }
  }
  // tilt the camera to align with north
  _alignCameraUpToNorth(t) {
    const { ellipsoidFrame: e } = this;
    mt.set(0, 0, 1).transformDirection(e), this._alignCameraUp(mt, t);
  }
  // tilt the camera to look at the center of the globe
  _tiltTowardsCenter(t) {
    const {
      camera: e,
      ellipsoidFrame: i
    } = this;
    B.set(0, 0, -1).transformDirection(e.matrixWorld).normalize(), D.setFromMatrixPosition(i).sub(e.position).normalize(), D.lerp(B, 1 - t).normalize(), tt.setFromUnitVectors(B, D), e.quaternion.premultiply(tt), e.updateMatrixWorld();
  }
  // returns the perspective camera transition distance can move to based on globe size and fov
  _getPerspectiveTransitionDistance() {
    const { camera: t } = this;
    if (!t.isPerspectiveCamera)
      throw new Error();
    const e = this._getMaxWorldRadius(), i = 2 * Math.atan(Math.tan(v.DEG2RAD * t.fov * 0.5) * t.aspect), s = e / Math.tan(v.DEG2RAD * t.fov * 0.5), o = e / Math.tan(i * 0.5);
    return Math.max(s, o);
  }
  // returns the max distance the perspective camera can move to based on globe size and fov
  _getMaxPerspectiveDistance() {
    const { camera: t } = this;
    if (!t.isPerspectiveCamera)
      throw new Error();
    const e = this._getMaxWorldRadius(), i = 2 * Math.atan(Math.tan(v.DEG2RAD * t.fov * 0.5) * t.aspect), s = e / Math.tan(v.DEG2RAD * t.fov * 0.5), o = e / Math.tan(i * 0.5);
    return 2 * Math.max(s, o);
  }
  // returns the transition threshold for orthographic zoom based on the globe size and camera settings
  _getOrthographicTransitionZoom() {
    const { camera: t } = this;
    if (!t.isOrthographicCamera)
      throw new Error();
    const e = t.top - t.bottom, i = t.right - t.left, s = Math.max(e, i), n = 2 * this._getMaxWorldRadius();
    return 2 * s / n;
  }
  // returns the minimum allowed orthographic zoom based on the globe size and camera settings
  _getMinOrthographicZoom() {
    const { camera: t } = this;
    if (!t.isOrthographicCamera)
      throw new Error();
    const e = t.top - t.bottom, i = t.right - t.left, s = Math.min(e, i), n = 2 * this._getMaxWorldRadius();
    return 0.7 * s / n;
  }
  // returns the "virtual position" of the orthographic based on where it is and
  // where it's looking primarily so we can reasonably position the camera object
  // in space and derive a reasonable "up" value.
  _getVirtualOrthoCameraPosition(t, e = this.camera) {
    const { ellipsoidFrame: i, ellipsoidFrameInverse: s, ellipsoid: o } = this;
    if (!e.isOrthographicCamera)
      throw new Error();
    E.origin.copy(e.position), E.direction.set(0, 0, -1).transformDirection(e.matrixWorld), E.applyMatrix4(s), o.closestPointToRayEstimate(E, U).applyMatrix4(i);
    const n = e.top - e.bottom, r = e.right - e.left, a = Math.max(n, r) / e.zoom;
    B.set(0, 0, -1).transformDirection(e.matrixWorld);
    const c = U.sub(e.position).dot(B);
    t.copy(e.position).addScaledVector(B, c - a * 4);
  }
  _isNearControls() {
    const { camera: t } = this;
    return t.isPerspectiveCamera ? this.getDistanceToCenter() < this._getPerspectiveTransitionDistance() : t.zoom > this._getOrthographicTransitionZoom();
  }
  _raycast(t) {
    const e = super._raycast(t);
    if (e === null) {
      const { ellipsoid: i, ellipsoidFrame: s, ellipsoidFrameInverse: o } = this;
      E.copy(t.ray).applyMatrix4(o);
      const n = i.intersectRay(E, D);
      return n !== null ? (n.applyMatrix4(s), {
        point: n.clone(),
        distance: n.distanceTo(t.ray.origin)
      }) : null;
    } else
      return e;
  }
  _getMaxWorldRadius() {
    const { ellipsoid: t, ellipsoidFrame: e } = this;
    return Math.max(...t.radius) * e.getMaxScaleOnAxis();
  }
}
const V = /* @__PURE__ */ new y(), at = /* @__PURE__ */ new y(), ct = /* @__PURE__ */ new ve(), Mi = /* @__PURE__ */ new y(), Pi = /* @__PURE__ */ new y(), Di = /* @__PURE__ */ new y(), Pe = /* @__PURE__ */ new st(), vi = /* @__PURE__ */ new st();
class Ai extends yt {
  /**
   * Whether a transition animation is currently in progress.
   * @type {boolean}
   * @readonly
   */
  get animating() {
    return this._alpha !== 0 && this._alpha !== 1;
  }
  /**
   * Transition progress from 0 (at perspective) to 1 (at orthographic).
   * @type {number}
   * @readonly
   */
  get alpha() {
    return this._target === 0 ? 1 - this._alpha : this._alpha;
  }
  /**
   * The currently active camera. Returns `perspectiveCamera`, `orthographicCamera`, or the
   * blended `transitionCamera` depending on the current transition state.
   * @type {Camera}
   * @readonly
   */
  get camera() {
    return this._alpha === 0 ? this.perspectiveCamera : this._alpha === 1 ? this.orthographicCamera : this.transitionCamera;
  }
  /**
   * The target camera mode. Set to `'perspective'` or `'orthographic'` to jump instantly without
   * animation. Use `toggle()` to animate the transition.
   * @type {string}
   */
  get mode() {
    return this._target === 0 ? "perspective" : "orthographic";
  }
  set mode(t) {
    if (t === this.mode)
      return;
    const e = this.camera;
    t === "perspective" ? (this._target = 0, this._alpha = 0) : (this._target = 1, this._alpha = 1), this.dispatchEvent({ type: "camera-change", camera: this.camera, prevCamera: e });
  }
  constructor(t = new ee(), e = new ve()) {
    super(), this.perspectiveCamera = t, this.orthographicCamera = e, this.transitionCamera = new ee(), this.orthographicPositionalZoom = !0, this.orthographicOffset = 50, this.fixedPoint = new y(), this.duration = 200, this.autoSync = !0, this.easeFunction = (i) => i, this._target = 0, this._alpha = 0, this._clock = new Qe();
  }
  /**
   * Begins an animated transition to the opposite camera mode. Dispatches a `'toggle'` event.
   */
  toggle() {
    this._target = this._target === 1 ? 0 : 1, this._clock.getDelta(), this.dispatchEvent({ type: "toggle" });
  }
  /**
   * Advances the transition animation and updates the active camera. Must be called each frame.
   * @param {number} [deltaTime] - Time in seconds since the last frame. Defaults to the clock delta, capped at 64ms.
   */
  update(t = Math.min(this._clock.getDelta(), 64 / 1e3)) {
    this.autoSync && this.syncCameras();
    const { perspectiveCamera: e, orthographicCamera: i, transitionCamera: s, camera: o } = this, n = t * 1e3;
    if (this._alpha !== this._target) {
      const p = Math.sign(this._target - this._alpha) * n / this.duration;
      this._alpha = v.clamp(this._alpha + p, 0, 1), this.dispatchEvent({ type: "change", alpha: this.alpha });
    }
    const r = o;
    let a = null;
    this._alpha === 0 ? a = e : this._alpha === 1 ? a = i : (a = s, this._updateTransitionCamera()), r !== a && (a === s && this.dispatchEvent({ type: "transition-start" }), this.dispatchEvent({ type: "camera-change", camera: a, prevCamera: r }), r === s && this.dispatchEvent({ type: "transition-end" }));
  }
  /**
   * Synchronises the non-active camera so that both cameras represent the same viewpoint.
   * Called automatically by `update` when `autoSync` is true.
   */
  syncCameras() {
    const t = this._getFromCamera(), { perspectiveCamera: e, orthographicCamera: i, transitionCamera: s, fixedPoint: o } = this;
    if (V.set(0, 0, -1).transformDirection(t.matrixWorld).normalize(), t.isPerspectiveCamera) {
      if (this.orthographicPositionalZoom)
        i.position.copy(e.position).addScaledVector(V, -this.orthographicOffset), i.rotation.copy(e.rotation), i.updateMatrixWorld();
      else {
        const c = at.subVectors(o, i.position).dot(V), p = at.subVectors(o, e.position).dot(V);
        at.copy(e.position).addScaledVector(V, p), i.rotation.copy(e.rotation), i.position.copy(at).addScaledVector(V, -c), i.updateMatrixWorld();
      }
      const n = Math.abs(at.subVectors(e.position, o).dot(V)), r = 2 * Math.tan(v.DEG2RAD * e.fov * 0.5) * n, a = i.top - i.bottom;
      i.zoom = a / r, i.updateProjectionMatrix();
    } else {
      const n = Math.abs(at.subVectors(i.position, o).dot(V)), a = (i.top - i.bottom) / i.zoom * 0.5 / Math.tan(v.DEG2RAD * e.fov * 0.5);
      e.rotation.copy(i.rotation), e.position.copy(i.position).addScaledVector(V, n).addScaledVector(V, -a), e.updateMatrixWorld(), this.orthographicPositionalZoom && (i.position.copy(e.position).addScaledVector(V, -this.orthographicOffset), i.updateMatrixWorld());
    }
    s.position.copy(e.position), s.rotation.copy(e.rotation);
  }
  _getTransitionDirection() {
    return Math.sign(this._target - this._alpha);
  }
  _getToCamera() {
    const t = this._getTransitionDirection();
    return t === 0 ? this._target === 0 ? this.perspectiveCamera : this.orthographicCamera : t > 0 ? this.orthographicCamera : this.perspectiveCamera;
  }
  _getFromCamera() {
    const t = this._getTransitionDirection();
    return t === 0 ? this._target === 0 ? this.perspectiveCamera : this.orthographicCamera : t > 0 ? this.perspectiveCamera : this.orthographicCamera;
  }
  _updateTransitionCamera() {
    const { perspectiveCamera: t, orthographicCamera: e, transitionCamera: i, fixedPoint: s } = this, o = this.easeFunction(this._alpha);
    V.set(0, 0, -1).transformDirection(e.matrixWorld).normalize(), ct.copy(e), ct.position.addScaledVector(V, e.near), e.far -= e.near, e.near = 0, V.set(0, 0, -1).transformDirection(t.matrixWorld).normalize();
    const n = Math.abs(at.subVectors(t.position, s).dot(V)), r = 2 * Math.tan(v.DEG2RAD * t.fov * 0.5) * n, a = vi.slerpQuaternions(t.quaternion, ct.quaternion, o), c = v.lerp(t.fov, 1, o), p = r * 0.5 / Math.tan(v.DEG2RAD * c * 0.5), l = Di.copy(ct.position).sub(s).applyQuaternion(Pe.copy(ct.quaternion).invert()), m = Pi.copy(t.position).sub(s).applyQuaternion(Pe.copy(t.quaternion).invert()), d = Mi.lerpVectors(m, l, o);
    d.z -= Math.abs(d.z) - p;
    const h = -(m.z - d.z), u = -(l.z - d.z), b = v.lerp(h + t.near, u + ct.near, o), I = v.lerp(h + t.far, u + ct.far, o), M = Math.max(I, 0) - Math.max(b, 0);
    i.aspect = t.aspect, i.fov = c, i.near = Math.max(b, M * 1e-5), i.far = I, i.position.copy(d).applyQuaternion(a).add(s), i.quaternion.copy(a), i.updateProjectionMatrix(), i.updateMatrixWorld();
  }
}
export {
  we as B,
  si as C,
  xi as E,
  zi as G,
  Ce as I,
  Te as P,
  Ri as T,
  Ai as a
};
//# sourceMappingURL=CameraTransitionManager-eW6RCr_i.js.map
