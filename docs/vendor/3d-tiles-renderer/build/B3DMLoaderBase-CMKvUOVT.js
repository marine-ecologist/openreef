import { b as w, L, r as A } from "./LoaderBase-CU5shB7w.js";
function I(h, e, t, a, n, r) {
  let s;
  switch (a) {
    case "SCALAR":
      s = 1;
      break;
    case "VEC2":
      s = 2;
      break;
    case "VEC3":
      s = 3;
      break;
    case "VEC4":
      s = 4;
      break;
    default:
      throw new Error(`FeatureTable : Feature type not provided for "${r}".`);
  }
  let c;
  const o = t * s;
  switch (n) {
    case "BYTE":
      c = new Int8Array(h, e, o);
      break;
    case "UNSIGNED_BYTE":
      c = new Uint8Array(h, e, o);
      break;
    case "SHORT":
      c = new Int16Array(h, e, o);
      break;
    case "UNSIGNED_SHORT":
      c = new Uint16Array(h, e, o);
      break;
    case "INT":
      c = new Int32Array(h, e, o);
      break;
    case "UNSIGNED_INT":
      c = new Uint32Array(h, e, o);
      break;
    case "FLOAT":
      c = new Float32Array(h, e, o);
      break;
    case "DOUBLE":
      c = new Float64Array(h, e, o);
      break;
    default:
      throw new Error(`FeatureTable : Feature component type not provided for "${r}".`);
  }
  return c;
}
class T {
  /**
   * @param {ArrayBuffer} buffer
   * @param {number} start - Byte offset of the feature table within the buffer
   * @param {number} headerLength - Byte length of the JSON header
   * @param {number} binLength - Byte length of the binary body
   */
  constructor(e, t, a, n) {
    this.buffer = e, this.binOffset = t + a, this.binLength = n;
    let r = null;
    if (a !== 0) {
      const s = new Uint8Array(e, t, a);
      r = JSON.parse(w(s));
    } else
      r = {};
    this.header = r;
  }
  /**
   * Returns all property key names defined in the feature table header, excluding `extensions`.
   * @returns {Array<string>}
   */
  getKeys() {
    return Object.keys(this.header).filter((e) => e !== "extensions");
  }
  /**
   * Returns the value for the given property key. For binary properties, reads typed array data
   * from the binary body using the provided count, component type, and vector type.
   * @param {string} key
   * @param {number} count - Number of elements to read for binary properties
   * @param {string | null} [defaultComponentType] - Fallback component type (e.g. `'FLOAT'`, `'UNSIGNED_SHORT'`)
   * @param {string | null} [defaultType] - Fallback vector type (e.g. `'SCALAR'`, `'VEC3'`)
   * @returns {number | string | ArrayBufferView | null}
   */
  getData(e, t, a = null, n = null) {
    const r = this.header;
    if (!(e in r))
      return null;
    const s = r[e];
    if (s instanceof Object) {
      if (Array.isArray(s))
        return s;
      {
        const { buffer: c, binOffset: o, binLength: i } = this, l = s.byteOffset || 0, f = s.type || n, b = s.componentType || a;
        if ("type" in s && n && s.type !== n)
          throw new Error("FeatureTable: Specified type does not match expected type.");
        const u = o + l, d = I(c, u, t, f, b, e);
        if (u + d.byteLength > o + i)
          throw new Error("FeatureTable: Feature data read outside binary body length.");
        return d;
      }
    } else return s;
  }
  /**
   * Returns a slice of the binary body at the given offset and length.
   * @param {number} byteOffset
   * @param {number} byteLength
   * @returns {ArrayBuffer}
   */
  getBuffer(e, t) {
    const { buffer: a, binOffset: n } = this;
    return a.slice(n + e, n + e + t);
  }
}
class B {
  constructor(e) {
    this.batchTable = e;
    const t = e.header.extensions["3DTILES_batch_table_hierarchy"];
    this.classes = t.classes;
    for (const n of this.classes) {
      const r = n.instances;
      for (const s in r)
        n.instances[s] = this._parseProperty(r[s], n.length, s);
    }
    if (this.instancesLength = t.instancesLength, this.classIds = this._parseProperty(t.classIds, this.instancesLength, "classIds"), t.parentCounts ? this.parentCounts = this._parseProperty(t.parentCounts, this.instancesLength, "parentCounts") : this.parentCounts = new Array(this.instancesLength).fill(1), t.parentIds) {
      const n = this.parentCounts.reduce((r, s) => r + s, 0);
      this.parentIds = this._parseProperty(t.parentIds, n, "parentIds");
    } else
      this.parentIds = null;
    this.instancesIds = [];
    const a = {};
    for (const n of this.classIds)
      a[n] = a[n] ?? 0, this.instancesIds.push(a[n]), a[n]++;
  }
  _parseProperty(e, t, a) {
    if (Array.isArray(e))
      return e;
    {
      const { buffer: n, binOffset: r } = this.batchTable, s = e.byteOffset, c = e.componentType || "UNSIGNED_SHORT", o = r + s;
      return I(n, o, t, "SCALAR", c, a);
    }
  }
  getDataFromId(e, t = {}) {
    const a = this.parentCounts[e];
    if (this.parentIds && a > 0) {
      let o = 0;
      for (let i = 0; i < e; i++)
        o += this.parentCounts[i];
      for (let i = 0; i < a; i++) {
        const l = this.parentIds[o + i];
        l !== e && this.getDataFromId(l, t);
      }
    }
    const n = this.classIds[e], r = this.classes[n].instances, s = this.classes[n].name, c = this.instancesIds[e];
    for (const o in r)
      t[s] = t[s] || {}, t[s][o] = r[o][c];
    return t;
  }
}
class E extends T {
  /**
   * @param {ArrayBuffer} buffer
   * @param {number} count - Number of features in the batch
   * @param {number} start - Byte offset of the batch table within the buffer
   * @param {number} headerLength - Byte length of the JSON header
   * @param {number} binLength - Byte length of the binary body
   */
  constructor(e, t, a, n, r) {
    super(e, a, n, r), this.count = t, this.extensions = {};
    const s = this.header.extensions;
    s && s["3DTILES_batch_table_hierarchy"] && (this.extensions["3DTILES_batch_table_hierarchy"] = new B(this));
  }
  /**
   * Returns an object with all properties of the batch table and its extensions for the
   * given feature id. A `target` object can be specified to store the result. Throws if
   * `id` is out of bounds.
   * @param {number} id - Feature index (0 to count - 1)
   * @param {Object} [target={}] - Optional object to write properties into
   * @returns {Object}
   */
  getDataFromId(e, t = {}) {
    if (e < 0 || e >= this.count)
      throw new Error(`BatchTable: id value "${e}" out of bounds for "${this.count}" features number.`);
    for (const a of this.getKeys())
      t[a] = super.getData(a, this.count)[e];
    for (const a in this.extensions) {
      const n = this.extensions[a];
      n.getDataFromId instanceof Function && (t[a] = t[a] || {}, n.getDataFromId(e, t[a]));
    }
    return t;
  }
  /**
   * Returns the array of values for the given property key across all features. Returns
   * `null` if the key is not in the table.
   * @param {string} key
   * @returns {Array | TypedArray | null}
   */
  getPropertyArray(e) {
    return super.getData(e, this.count);
  }
}
class _ extends L {
  /**
   * Parses a B3DM buffer and returns the raw tile data.
   * @param {ArrayBuffer} buffer
   * @returns {{ version: string, featureTable: FeatureTable, batchTable: BatchTable, glbBytes: Uint8Array }}
   */
  parse(e) {
    const t = new DataView(e), a = A(t);
    console.assert(a === "b3dm");
    const n = t.getUint32(4, !0);
    console.assert(n === 1);
    const r = t.getUint32(8, !0);
    console.assert(r === e.byteLength);
    const s = t.getUint32(12, !0), c = t.getUint32(16, !0), o = t.getUint32(20, !0), i = t.getUint32(24, !0), l = 28, f = e.slice(
      l,
      l + s + c
    ), b = new T(
      f,
      0,
      s,
      c
    ), u = l + s + c, d = e.slice(
      u,
      u + o + i
    ), p = new E(
      d,
      b.getData("BATCH_LENGTH"),
      0,
      o,
      i
    ), y = u + o + i, g = new Uint8Array(e, y, r - y);
    return {
      version: n,
      featureTable: b,
      batchTable: p,
      glbBytes: g
    };
  }
}
export {
  _ as B,
  T as F,
  E as a,
  I as p
};
//# sourceMappingURL=B3DMLoaderBase-CMKvUOVT.js.map
