import { D as C, F, L as _, a as W, b as H, P as R, c as k, Q as J, S as Q, T as $, U as q, W as j, d as z, e as K, u as X } from "./TilesRendererBase-BGxy2Uih.js";
import { L as f, r as b, b as A, g as P } from "./LoaderBase-CU5shB7w.js";
import { a as Z, T as ee } from "./LoaderBase-CU5shB7w.js";
import { F as p, a as N } from "./B3DMLoaderBase-CMKvUOVT.js";
import { B as ae, p as se } from "./B3DMLoaderBase-CMKvUOVT.js";
class G extends f {
  /**
   * Parses an I3DM buffer and returns the raw tile data.
   * @param {ArrayBuffer} buffer
   * @returns {Promise<{ version: string, featureTable: FeatureTable, batchTable: BatchTable, glbBytes: Uint8Array, gltfWorkingPath: string }>}
   */
  parse(t) {
    const e = new DataView(t), L = b(e);
    console.assert(L === "i3dm");
    const i = e.getUint32(4, !0);
    console.assert(i === 1);
    const T = e.getUint32(8, !0);
    console.assert(T === t.byteLength);
    const n = e.getUint32(12, !0), a = e.getUint32(16, !0), s = e.getUint32(20, !0), r = e.getUint32(24, !0), o = e.getUint32(28, !0), l = 32, g = t.slice(
      l,
      l + n + a
    ), c = new p(
      g,
      0,
      n,
      a
    ), h = l + n + a, U = t.slice(
      h,
      h + s + r
    ), E = new N(
      U,
      c.getData("INSTANCES_LENGTH"),
      0,
      s,
      r
    ), D = h + s + r, S = new Uint8Array(t, D, T - D);
    let y = null, B = null, m = null;
    if (o)
      y = S, B = Promise.resolve();
    else {
      const d = this.resolveExternalURL(A(S));
      m = P(d), B = fetch(d, this.fetchOptions).then((u) => {
        if (!u.ok)
          throw new Error(`I3DMLoaderBase : Failed to load file "${d}" with status ${u.status} : ${u.statusText}`);
        return u.arrayBuffer();
      }).then((u) => {
        y = new Uint8Array(u);
      });
    }
    return B.then(() => ({
      version: i,
      featureTable: c,
      batchTable: E,
      glbBytes: y,
      gltfWorkingPath: m
    }));
  }
}
class I extends f {
  /**
   * Parses a PNTS buffer and returns the raw tile data.
   * @param {ArrayBuffer} buffer
   * @returns {Promise<{ version: string, featureTable: FeatureTable, batchTable: BatchTable }>}
   */
  parse(t) {
    const e = new DataView(t), L = b(e);
    console.assert(L === "pnts");
    const i = e.getUint32(4, !0);
    console.assert(i === 1);
    const T = e.getUint32(8, !0);
    console.assert(T === t.byteLength);
    const n = e.getUint32(12, !0), a = e.getUint32(16, !0), s = e.getUint32(20, !0), r = e.getUint32(24, !0), o = 28, l = t.slice(
      o,
      o + n + a
    ), g = new p(
      l,
      0,
      n,
      a
    ), c = o + n + a, h = t.slice(
      c,
      c + s + r
    ), U = new N(
      h,
      g.getData("BATCH_LENGTH") || g.getData("POINTS_LENGTH"),
      0,
      s,
      r
    );
    return Promise.resolve({
      version: i,
      featureTable: g,
      batchTable: U
    });
  }
}
class v extends f {
  /**
   * Parses a CMPT buffer and returns an object containing each inner tile's type and raw buffer.
   * @param {ArrayBuffer} buffer
   * @returns {{ version: string, tiles: Array<{ type: string, buffer: Uint8Array, version: number }> }}
   */
  parse(t) {
    const e = new DataView(t), L = b(e);
    console.assert(L === "cmpt", 'CMPTLoader: The magic bytes equal "cmpt".');
    const i = e.getUint32(4, !0);
    console.assert(i === 1, 'CMPTLoader: The version listed in the header is "1".');
    const T = e.getUint32(8, !0);
    console.assert(T === t.byteLength, "CMPTLoader: The contents buffer length listed in the header matches the file.");
    const n = e.getUint32(12, !0), a = [];
    let s = 16;
    for (let r = 0; r < n; r++) {
      const o = new DataView(t, s, 12), l = b(o), g = o.getUint32(4, !0), c = o.getUint32(8, !0), h = new Uint8Array(t, s, c);
      a.push({
        type: l,
        buffer: h,
        version: g
      }), s += c;
    }
    return {
      version: i,
      tiles: a
    };
  }
}
export {
  ae as B3DMLoaderBase,
  N as BatchTable,
  v as CMPTLoaderBase,
  C as DEFAULT_DOWNLOAD_QUEUE,
  F as FAILED,
  p as FeatureTable,
  G as I3DMLoaderBase,
  _ as LOADED,
  W as LOADING,
  H as LRUCache,
  f as LoaderBase,
  Z as LoaderUtils,
  R as PARSING,
  I as PNTSLoaderBase,
  k as PriorityQueue,
  J as QUEUED,
  Q as Scheduler,
  $ as TilesRendererBase,
  ee as TraversalUtils,
  q as UNLOADED,
  j as WGS84_FLATTENING,
  z as WGS84_HEIGHT,
  K as WGS84_RADIUS,
  se as parseBinArray,
  X as unifiedPriorityCallback
};
//# sourceMappingURL=index.core.js.map
