var he = Object.defineProperty;
var ue = (t, e, n) => e in t ? he(t, e, { enumerable: !0, configurable: !0, writable: !0, value: n }) : t[e] = n;
var M = (t, e, n) => ue(t, typeof e != "symbol" ? e + "" : e, n);
import { t as fe } from "./LoaderBase-CU5shB7w.js";
function W(t) {
  if (!t)
    return null;
  let e = t.length;
  const n = t.indexOf("?"), s = t.indexOf("#");
  n !== -1 && (e = Math.min(e, n)), s !== -1 && (e = Math.min(e, s));
  const a = t.lastIndexOf(".", e), r = t.lastIndexOf("/", e), i = t.indexOf("://");
  return i !== -1 && i + 2 === r || a === -1 || a < r ? null : t.substring(a + 1, e) || null;
}
class F {
  /**
   * Sets the active "XRSession" value to use to scheduling rAF callbacks.
   * @param {XRSession} session
   */
  static setXRSession(e) {
    e !== this.session && (this.flushPending(), this.session = e);
  }
  /**
   * Request animation frame (defer to XR session if set)
   * @param {Function} cb
   * @returns {number}
   */
  static requestAnimationFrame(e) {
    const { session: n, pending: s } = this;
    let a;
    const r = () => {
      s.delete(a), e();
    };
    return n ? a = n.requestAnimationFrame(r) : a = requestAnimationFrame(r), s.set(a, e), a;
  }
  /**
   * Cancel animation frame via handle (defer to XR session if set)
   * @param {number} handle
   */
  static cancelAnimationFrame(e) {
    const { pending: n, session: s } = this;
    n.delete(e), s ? s.cancelAnimationFrame(e) : cancelAnimationFrame(e);
  }
  /**
   * Flush and complete pending AFs (defer to XR session if set)
   */
  static flushPending() {
    this.pending.forEach((e, n) => {
      e(), this.cancelAnimationFrame(n);
    });
  }
}
M(F, "pending", /* @__PURE__ */ new Map()), M(F, "session", null);
const $ = 2 ** 30;
class ve {
  /**
   * Comparator used to determine eviction order. Items that sort last are evicted first.
   * When `null`, eviction order is by last-used time.
   * @type {UnloadPriorityCallback|null}
   * @default null
   */
  get unloadPriorityCallback() {
    return this._unloadPriorityCallback;
  }
  set unloadPriorityCallback(e) {
    e.length === 1 ? (console.warn('LRUCache: "unloadPriorityCallback" function has been changed to take two arguments.'), this._unloadPriorityCallback = (n, s) => {
      const a = e(n), r = e(s);
      return a < r ? -1 : a > r ? 1 : 0;
    }) : this._unloadPriorityCallback = e;
  }
  constructor() {
    this.minSize = 6e3, this.maxSize = 8e3, this.minBytesSize = 0.3 * $, this.maxBytesSize = 0.4 * $, this.unloadPercent = 0.05, this.autoMarkUnused = !0, this.itemSet = /* @__PURE__ */ new Map(), this.itemList = [], this.usedSet = /* @__PURE__ */ new Set(), this.callbacks = /* @__PURE__ */ new Map(), this.unloadingHandle = -1, this.cachedBytes = 0, this.bytesMap = /* @__PURE__ */ new Map(), this.loadedSet = /* @__PURE__ */ new Set(), this._unloadPriorityCallback = null;
    const e = this.itemSet;
    this.defaultPriorityCallback = (n) => e.get(n);
  }
  /**
   * Returns whether the cache has reached its maximum item count or byte size.
   * @returns {boolean}
   */
  isFull() {
    return this.itemSet.size >= this.maxSize || this.cachedBytes >= this.maxBytesSize;
  }
  /**
   * Returns the byte size registered for the given item, or 0 if not tracked.
   * @param {any} item
   * @returns {number}
   */
  getMemoryUsage(e) {
    return this.bytesMap.get(e) || 0;
  }
  /**
   * Sets the byte size for the given item, updating the total `cachedBytes` count.
   * @param {any} item
   * @param {number} bytes
   */
  setMemoryUsage(e, n) {
    const { bytesMap: s, itemSet: a } = this;
    a.has(e) && (this.cachedBytes -= s.get(e) || 0, s.set(e, n), this.cachedBytes += n);
  }
  /**
   * Adds an item to the cache. Returns false if the item already exists or the cache is full.
   * @param {any} item
   * @param {RemoveCallback} removeCb - Called with the item when it is evicted
   * @returns {boolean}
   */
  add(e, n) {
    const s = this.itemSet;
    if (s.has(e) || this.isFull())
      return !1;
    const a = this.usedSet, r = this.itemList, i = this.callbacks;
    return r.push(e), a.add(e), s.set(e, Date.now()), i.set(e, n), !0;
  }
  /**
   * Returns whether the given item is in the cache.
   * @param {any} item
   * @returns {boolean}
   */
  has(e) {
    return this.itemSet.has(e);
  }
  /**
   * Removes an item from the cache immediately, invoking its removal callback.
   * Returns false if the item was not in the cache.
   * @param {any} item
   * @returns {boolean}
   */
  remove(e) {
    const n = this.usedSet, s = this.itemSet, a = this.itemList, r = this.bytesMap, i = this.callbacks, l = this.loadedSet;
    if (s.has(e)) {
      this.cachedBytes -= r.get(e) || 0, r.delete(e), i.get(e)(e);
      const o = a.indexOf(e);
      return a.splice(o, 1), n.delete(e), s.delete(e), i.delete(e), l.delete(e), !0;
    }
    return !1;
  }
  /**
   * Marks whether an item has finished loading. Unloaded items may be evicted early
   * when the cache is over its max size limits, even if they are marked as used.
   * @param {any} item
   * @param {boolean} value
   */
  setLoaded(e, n) {
    const { itemSet: s, loadedSet: a } = this;
    s.has(e) && (n === !0 ? a.add(e) : a.delete(e));
  }
  /**
   * Marks an item as used in the current frame, preventing it from being evicted.
   * @param {any} item
   */
  markUsed(e) {
    const n = this.itemSet, s = this.usedSet;
    n.has(e) && !s.has(e) && (n.set(e, Date.now()), s.add(e));
  }
  /**
   * Marks an item as unused, making it eligible for eviction.
   * @param {any} item
   */
  markUnused(e) {
    this.usedSet.delete(e);
  }
  /**
   * Marks all items in the cache as unused.
   */
  markAllUnused() {
    this.usedSet.clear();
  }
  /**
   * Returns whether the given item is currently marked as used.
   * @param {any} item
   * @returns {boolean}
   */
  isUsed(e) {
    return this.usedSet.has(e);
  }
  /**
   * Evicts unused items until the cache is within its min size and byte limits.
   * Items are sorted by `unloadPriorityCallback` before eviction.
   */
  // TODO: this should be renamed because it's not necessarily unloading all unused content
  // Maybe call it "cleanup" or "unloadToMinSize"
  unloadUnusedContent() {
    const {
      unloadPercent: e,
      minSize: n,
      maxSize: s,
      itemList: a,
      itemSet: r,
      usedSet: i,
      loadedSet: l,
      callbacks: o,
      bytesMap: u,
      minBytesSize: v,
      maxBytesSize: c
    } = this, h = a.length - i.size, k = a.length - l.size, d = Math.max(Math.min(a.length - n, h), 0), p = this.cachedBytes - v, P = this.unloadPriorityCallback || this.defaultPriorityCallback;
    let L = !1;
    const re = d > 0 && h > 0 || k && a.length > s;
    if (h && this.cachedBytes > v || k && this.cachedBytes > c || re) {
      a.sort((f, g) => {
        const G = i.has(f), de = i.has(g);
        if (G === de) {
          const H = l.has(f), ce = l.has(g);
          return H === ce ? -P(f, g) : H ? 1 : -1;
        } else
          return G ? 1 : -1;
      });
      const ie = Math.max(n * e, d * e), j = Math.ceil(Math.min(ie, h, d)), le = Math.max(e * p, e * v), oe = Math.min(le, p);
      let m = 0, U = 0;
      for (; this.cachedBytes - U > c || a.length - m > s; ) {
        const f = a[m], g = u.get(f) || 0;
        if (i.has(f) && l.has(f) || this.cachedBytes - U - g < c && a.length - m <= s)
          break;
        U += g, m++;
      }
      for (; U < oe || m < j; ) {
        const f = a[m], g = u.get(f) || 0;
        if (i.has(f) || this.cachedBytes - U - g < v && m >= j)
          break;
        U += g, m++;
      }
      a.splice(0, m).forEach((f) => {
        this.cachedBytes -= u.get(f) || 0, o.get(f)(f), u.delete(f), r.delete(f), o.delete(f), l.delete(f), i.delete(f);
      }), L = m < d || U < p && m < h, L = L && m > 0;
    }
    L && (this.unloadingHandle = F.requestAnimationFrame(() => this.scheduleUnload()));
  }
  /**
   * Schedules `unloadUnusedContent` to run asynchronously via microtask.
   */
  scheduleUnload() {
    F.cancelAnimationFrame(this.unloadingHandle), this.scheduled || (this.scheduled = !0, queueMicrotask(() => {
      this.scheduled = !1, this.unloadUnusedContent();
    }));
  }
}
class me extends DOMException {
  constructor() {
    super("PriorityQueue: Item removed", "AbortError");
  }
}
class q {
  /**
   * returns whether tasks are queued or actively running
   * @readonly
   * @type {boolean}
   */
  get running() {
    return this.items.length !== 0 || this.currJobs !== 0;
  }
  constructor() {
    this.maxJobs = 6, this.items = [], this.callbacks = /* @__PURE__ */ new Map(), this.currJobs = 0, this.scheduled = !1, this.autoUpdate = !0, this.priorityCallback = null, this._schedulingCallback = (e) => {
      F.requestAnimationFrame(e);
    }, this._runjobs = () => {
      this.scheduled = !1, this.tryRunJobs();
    };
  }
  /**
   * Sorts the pending item list using `priorityCallback`, if set.
   */
  sort() {
    const e = this.priorityCallback, n = this.items;
    e !== null && n.sort(e);
  }
  /**
   * Returns whether the given item is currently queued.
   * @param {any} item
   * @returns {boolean}
   */
  has(e) {
    return this.callbacks.has(e);
  }
  /**
   * Adds an item to the queue and returns a Promise that resolves when the item's
   * callback completes, or rejects if the item is removed before running.
   * @param {any} item
   * @param {ItemCallback} callback - Invoked with `item` when it is dequeued; may return a Promise
   * @returns {Promise<any>}
   */
  add(e, n) {
    const s = {
      callback: n,
      reject: null,
      resolve: null,
      promise: null
    };
    return s.promise = new Promise((a, r) => {
      const i = this.items, l = this.callbacks;
      s.resolve = a, s.reject = r, i.unshift(e), l.set(e, s), this.autoUpdate && this.scheduleJobRun();
    }), s.promise;
  }
  /**
   * Removes an item from the queue, rejecting its promise with an `AbortError` DOMException.
   * @param {any} item
   */
  remove(e) {
    const n = this.items, s = this.callbacks, a = n.indexOf(e);
    if (a !== -1) {
      const r = s.get(e);
      r.promise.catch((i) => {
        if (i.name !== "AbortError")
          throw i;
      }), r.reject(new me()), n.splice(a, 1), s.delete(e);
    }
  }
  /**
   * Removes all queued items for which `filter` returns true.
   * @param {FilterCallback} filter - Called with each item; return true to remove
   */
  removeByFilter(e) {
    const { items: n } = this;
    for (let s = 0; s < n.length; s++) {
      const a = n[s];
      e(a) && (this.remove(a), s--);
    }
  }
  /**
   * Immediately attempts to dequeue and run pending jobs up to `maxJobs` concurrency.
   */
  tryRunJobs() {
    this.sort();
    const e = this.items, n = this.callbacks, s = this.maxJobs;
    let a = 0;
    const r = () => {
      this.currJobs--, this.autoUpdate && this.scheduleJobRun();
    };
    for (; s > this.currJobs && e.length > 0 && a < s; ) {
      this.currJobs++, a++;
      const i = e.pop(), { callback: l, resolve: o, reject: u } = n.get(i);
      n.delete(i);
      let v;
      try {
        v = l(i);
      } catch (c) {
        u(c), r();
      }
      v instanceof Promise ? v.then(o).catch(u).finally(r) : (o(v), r());
    }
  }
  /**
   * Immediately runs the callback for the given item, removing it from the queue.
   * Does nothing if the item is not queued.
   * @param {any} item
   * @returns {Promise<any>|any}
   */
  flush(e) {
    const { items: n, callbacks: s } = this, a = n.indexOf(e);
    if (!s.has(e))
      return;
    const { callback: r, resolve: i, reject: l } = s.get(e);
    s.delete(e), n.splice(a, 1);
    let o;
    try {
      o = r(e);
    } catch (u) {
      l(u);
      return;
    }
    return o instanceof Promise ? o.then(i).catch(l) : i(o), o;
  }
  /**
   * Schedules a deferred call to `tryRunJobs` via `schedulingCallback`.
   */
  scheduleJobRun() {
    this.scheduled || (this._schedulingCallback(this._runjobs), this.scheduled = !0);
  }
}
const R = -1, C = 0, A = 1, x = 2, O = 3, S = 4, ke = 6378137, Fe = 1 / 298.257223563, Re = 6356752314245179e-9, B = {
  inView: !1,
  error: 1 / 0,
  distanceFromCamera: 1 / 0
};
function V(t) {
  return t === S || t === R;
}
function y(t, e) {
  return I(t) && t.traversal.lastFrameVisited === e && t.traversal.used;
}
function I(t) {
  return !!t.traversal;
}
function E(t) {
  const { children: e } = t, n = e.length === 0 || I(e[e.length - 1]), s = !t.internal.hasUnrenderableContent || V(t.internal.loadingState);
  return n && s;
}
function T(t) {
  return t.traversal.unconditionallyRefine;
}
function w(t, e) {
  if (I(t) && (e.ensureChildrenArePreprocessed(t), t.traversal.lastFrameVisited !== e.frameCount && (t.traversal.wasInFrustum = t.traversal.inFrustum, t.traversal.wasSetActive = t.traversal.active, t.traversal.wasSetVisible = t.traversal.visible, t.traversal.usedLastFrame = t.traversal.used, t.traversal.lastFrameVisited = e.frameCount, t.traversal.used = !1, t.traversal.inFrustum = !1, t.traversal.isLeaf = !1, t.traversal.visible = !1, t.traversal.active = !1, t.traversal.error = 1 / 0, t.traversal.distanceFromCamera = 1 / 0, t.traversal.allChildrenReady = !1, t.traversal.allChildrenLoaded = !1, t.traversal.kicked = !1, t.traversal.allUsedChildrenProcessed = !1, e.calculateTileViewErrorWithPlugin(t, B), t.traversal.inFrustum = B.inView, t.traversal.error = B.error, t.traversal.distanceFromCamera = B.distanceFromCamera, t.traversal.unconditionallyRefine = t.internal.hasUnrenderableContent, !t.traversal.unconditionallyRefine))) {
    let n = t.parent;
    for (; n && n.traversal.unconditionallyRefine; )
      n = n.parent;
    n && n.geometricError <= t.geometricError && (t.traversal.unconditionallyRefine = !0);
  }
}
function N(t, e, n = !1) {
  if (w(t, e), n ? e.markTileUsed(t) : D(t), T(t) && E(t)) {
    const s = t.children;
    for (let a = 0, r = s.length; a < r; a++)
      N(s[a], e, n);
  }
}
function K(t, e) {
  if (w(t, e), t.traversal.usedLastFrame && (D(t), t.traversal.wasSetActive && (t.traversal.active = !0), (!t.traversal.active || T(t)) && E(t))) {
    const n = t.children;
    for (let s = 0, a = n.length; s < a; s++)
      K(n[s], e);
  }
}
function D(t) {
  t.traversal.used = !0;
}
function pe(t, e) {
  return !(t.traversal.error <= e.errorTarget && !T(t) || e.maxDepth > 0 && t.internal.depth + 1 >= e.maxDepth || !E(t));
}
function Z(t, e) {
  const { frameCount: n } = e, { children: s } = t;
  for (let a = 0, r = s.length; a < r; a++) {
    const i = s[a];
    y(i, n) && (i.traversal.active && (i.traversal.kicked = !0, i.traversal.active = !1), Z(i, e));
  }
}
function Y(t) {
  return !T(t) && (!t.internal.hasContent || V(t.internal.loadingState));
}
function ee(t, e) {
  if (w(t, e), !t.traversal.inFrustum)
    return;
  if (!pe(t, e)) {
    D(t);
    return;
  }
  let n = !1, s = !1;
  const a = t.children;
  for (let r = 0, i = a.length; r < i; r++) {
    const l = a[r];
    ee(l, e), n = n || y(l, e.frameCount), s = s || l.traversal.inFrustum;
  }
  if (t.refine === "REPLACE" && !s && a.length !== 0) {
    t.traversal.inFrustum = !1, e.markTileUsed(t);
    for (let r = 0, i = a.length; r < i; r++)
      N(a[r], e, !0);
    return;
  }
  if (D(t), t.refine === "REPLACE" && n && (e.loadSiblings || e.loadAncestors))
    for (let r = 0, i = a.length; r < i; r++)
      N(a[r], e);
}
function te(t, e) {
  const n = e.frameCount;
  if (!y(t, n))
    return;
  const s = t.children;
  let a = !1;
  for (let i = 0, l = s.length; i < l; i++) {
    const o = s[i];
    a = a || y(o, n);
  }
  if (!a)
    t.traversal.isLeaf = !0;
  else {
    for (let l = 0, o = s.length; l < o; l++)
      te(s[l], e);
    let i = !0;
    for (let l = 0, o = s.length; l < o; l++) {
      const u = s[l];
      if (y(u, n)) {
        const v = !T(u), c = !u.internal.hasContent || V(u.internal.loadingState);
        v && c || u.traversal.allChildrenLoaded || (i = !1);
      }
    }
    t.traversal.allChildrenLoaded = i;
  }
  let r = !0;
  for (let i = 0, l = s.length; i < l; i++) {
    const o = s[i];
    y(o, e.frameCount) && !o.traversal.allUsedChildrenProcessed && (r = !1);
  }
  t.traversal.allUsedChildrenProcessed = r && E(t);
}
function se(t, e) {
  if (!y(t, e.frameCount))
    return;
  const n = t.children;
  if (e.loadAncestors && !t.traversal.allChildrenLoaded && !T(t) && (t.traversal.isLeaf = !0), t.traversal.isLeaf) {
    if (!T(t) && (t.traversal.active = !0, E(t) && t.internal.hasContent && !V(t.internal.loadingState)))
      for (let a = 0, r = n.length; a < r; a++)
        K(n[a], e);
    return;
  }
  let s = n.length > 0;
  for (let a = 0, r = n.length; a < r; a++) {
    const i = n[a];
    se(i, e), y(i, e.frameCount) && !(i.traversal.active && Y(i)) && !i.traversal.allChildrenReady && (s = !1);
  }
  t.traversal.allChildrenReady = s, !s && t.traversal.wasSetActive && Y(t) && (t.traversal.active = !0, Z(t, e));
}
function ne(t, e) {
  w(t, e);
  const n = y(t, e.frameCount);
  if (n && (t.internal.hasUnrenderableContent && (e.markTileUsed(t), e.queueTileForDownload(t)), t.internal.hasRenderableContent && t.refine === "ADD" && (t.traversal.active = !0), (t.traversal.active || t.traversal.kicked) && t.internal.hasContent && (e.markTileUsed(t), t.traversal.allUsedChildrenProcessed && e.queueTileForDownload(t), t.internal.loadingState !== S && (t.traversal.active = !1)), e.loadAncestors && t.internal.hasContent && (e.markTileUsed(t), e.queueTileForDownload(t)), t.internal.virtualChildCount > 0 && t.internal.hasContent && e.markTileUsed(t), t.traversal.visible = t.internal.hasRenderableContent && t.traversal.active && t.traversal.inFrustum && t.internal.loadingState === S, e.stats.used++, t.traversal.inFrustum && e.stats.inFrustum++), n || I(t) && t.traversal.usedLastFrame) {
    let s = !1, a = !1;
    n ? (s = t.traversal.active, e.displayActiveTiles ? a = t.traversal.active || t.traversal.visible : a = t.traversal.visible) : w(t, e), t.internal.hasRenderableContent && t.internal.loadingState === S ? (s && e.stats.active++, a && e.stats.visible++, t.traversal.wasSetActive !== s && e.invokeOnePlugin((i) => i.setTileActive && i.setTileActive(t, s)), t.traversal.wasSetVisible !== a && e.invokeOnePlugin((i) => i.setTileVisible && i.setTileVisible(t, a))) : t.internal.hasRenderableContent || (a = t.traversal.isLeaf, t.traversal.wasSetVisible !== a && e.invokeOnePlugin((i) => i.setEmptyTileVisible && i.setEmptyTileVisible(t, a))), t.traversal.visible = a, t.traversal.active = s;
    const r = t.children;
    for (let i = 0, l = r.length; i < l; i++) {
      const o = r[i];
      ne(o, e);
    }
  }
}
function ge(t, e) {
  ee(t, e), te(t, e), se(t, e), ne(t, e);
}
function ye(t) {
  let e = null;
  return () => {
    e === null && (e = F.requestAnimationFrame(() => {
      e = null, t();
    }));
  };
}
const X = Symbol("PLUGIN_REGISTERED"), b = {
  inView: !0,
  error: 0,
  distance: 1 / 0
}, Ce = (t, e) => {
  const n = t.priority || 0, s = e.priority || 0;
  return n !== s ? n > s ? 1 : -1 : !t.traversal || !e.traversal ? 0 : t.traversal.used !== e.traversal.used ? t.traversal.used ? 1 : -1 : t.traversal.error !== e.traversal.error ? t.traversal.error > e.traversal.error ? 1 : -1 : t.traversal.distanceFromCamera !== e.traversal.distanceFromCamera ? t.traversal.distanceFromCamera > e.traversal.distanceFromCamera ? -1 : 1 : t.internal.depthFromRenderedParent !== e.internal.depthFromRenderedParent ? t.internal.depthFromRenderedParent > e.internal.depthFromRenderedParent ? -1 : 1 : 0;
}, be = (t, e) => t.traversal.used !== e.traversal.used ? t.traversal.used ? 1 : -1 : t.traversal.inFrustum !== e.traversal.inFrustum ? t.traversal.inFrustum ? 1 : -1 : t.internal.hasUnrenderableContent !== e.internal.hasUnrenderableContent ? t.internal.hasUnrenderableContent ? 1 : -1 : t.traversal.distanceFromCamera !== e.traversal.distanceFromCamera ? t.traversal.distanceFromCamera > e.traversal.distanceFromCamera ? -1 : 1 : t.internal.depthFromRenderedParent !== e.internal.depthFromRenderedParent ? t.internal.depthFromRenderedParent > e.internal.depthFromRenderedParent ? -1 : 1 : 0, Se = (t, e) => t.traversal.lastFrameVisited !== e.traversal.lastFrameVisited ? t.traversal.lastFrameVisited > e.traversal.lastFrameVisited ? -1 : 1 : t.internal.depthFromRenderedParent !== e.internal.depthFromRenderedParent ? t.internal.depthFromRenderedParent > e.internal.depthFromRenderedParent ? 1 : -1 : t.internal.loadingState !== e.internal.loadingState ? t.internal.loadingState > e.internal.loadingState ? -1 : 1 : t.internal.hasUnrenderableContent !== e.internal.hasUnrenderableContent ? t.internal.hasUnrenderableContent ? -1 : 1 : t.traversal.error !== e.traversal.error ? t.traversal.error > e.traversal.error ? -1 : 1 : 0, _ = (t, e) => {
  const n = t.priority ?? 1 / 0, s = e.priority ?? 1 / 0;
  if (n !== s)
    return n > s ? 1 : -1;
  if (!t.internal || !e.internal)
    return 0;
  const a = t.internal.renderer, r = e.internal.renderer, i = !a.loadAncestors, l = !r.loadAncestors;
  return i && l ? be(t, e) : Ce(t, e);
}, ae = new ve();
ae.unloadPriorityCallback = Se;
const Q = new q();
Q.maxJobs = 25;
Q.priorityCallback = _;
const J = new q();
J.maxJobs = 5;
J.priorityCallback = _;
const z = new q();
z.maxJobs = 25;
z.priorityCallback = (t, e) => {
  const n = t.parent, s = e.parent;
  return n === s ? 0 : n ? s ? _(n, s) : -1 : 1;
};
class we {
  /**
   * Root tile of the loaded root tileset, or null if not yet loaded.
   * @type {Tile|null}
   * @readonly
   */
  get root() {
    const e = this.rootTileset;
    return e ? e.root : null;
  }
  /**
   * Fraction of tiles loaded since the last idle state, from 0 (nothing loaded) to 1 (all loaded).
   * @type {number}
   * @readonly
   */
  get loadProgress() {
    const { stats: e, isLoading: n } = this, s = e.queued + e.downloading + e.parsing, a = e.inCacheSinceLoad + (n ? 1 : 0);
    return a === 0 ? 1 : 1 - s / a;
  }
  /**
   * @param {string} [url] - URL of the root tileset JSON to load.
   */
  constructor(e = null) {
    this.rootLoadingState = C, this.rootTileset = null, this.rootURL = e, this.fetchOptions = {}, this.plugins = [], this.queuedTiles = [], this.cachedSinceLoadComplete = /* @__PURE__ */ new Set(), this.isLoading = !1, this.processedTiles = /* @__PURE__ */ new WeakSet(), this.visibleTiles = /* @__PURE__ */ new Set(), this.activeTiles = /* @__PURE__ */ new Set(), this.usedSet = /* @__PURE__ */ new Set(), this.loadingTiles = /* @__PURE__ */ new Set(), this.lruCache = ae, this.downloadQueue = Q, this.parseQueue = J, this.processNodeQueue = z, this.stats = {
      inCacheSinceLoad: 0,
      inCache: 0,
      queued: 0,
      downloading: 0,
      parsing: 0,
      loaded: 0,
      failed: 0,
      inFrustum: 0,
      used: 0,
      active: 0,
      visible: 0,
      tilesProcessed: 0
    }, this.frameCount = 0, this._dispatchNeedsUpdateEvent = ye(() => {
      this.dispatchEvent({ type: "needs-update" });
    }), this.errorTarget = 16, this.displayActiveTiles = !1, this.maxDepth = 1 / 0, this.loadSiblings = !0, this.loadAncestors = !0, this.maxTilesProcessed = 250;
  }
  // Plugins
  /**
   * Registers a plugin with this renderer. Plugins are inserted in priority order and
   * receive lifecycle callbacks throughout the tile loading and rendering process.
   * A plugin instance may only be registered to one renderer at a time.
   * @param {Object} plugin
   */
  registerPlugin(e) {
    if (e[X] === !0)
      throw new Error("TilesRendererBase: A plugin can only be registered to a single tileset");
    const n = this.plugins, s = e.priority || 0;
    let a = n.length;
    for (let r = 0; r < n.length; r++)
      if ((n[r].priority || 0) > s) {
        a = r;
        break;
      }
    n.splice(a, 0, e), e[X] = !0, e.init && e.init(this);
  }
  /**
   * Removes a registered plugin. Calls `plugin.dispose()` if defined.
   * Accepts either the plugin instance or its string name.
   * Returns true if the plugin was found and removed.
   * @param {Object|string} plugin
   * @returns {boolean}
   */
  unregisterPlugin(e) {
    const n = this.plugins;
    if (typeof e == "string" && (e = this.getPluginByName(e)), n.includes(e)) {
      const s = n.indexOf(e);
      return n.splice(s, 1), e.dispose && e.dispose(), !0;
    }
    return !1;
  }
  /**
   * Returns the first registered plugin whose `name` property matches, or null.
   * @param {string} name
   * @returns {Object|null}
   */
  getPluginByName(e) {
    return this.plugins.find((n) => n.name === e) || null;
  }
  invokeOnePlugin(e) {
    const n = [...this.plugins, this];
    for (let s = 0; s < n.length; s++) {
      const a = e(n[s]);
      if (a)
        return a;
    }
    return null;
  }
  invokeAllPlugins(e) {
    const n = [...this.plugins, this], s = [];
    for (let a = 0; a < n.length; a++) {
      const r = e(n[a]);
      r && s.push(r);
    }
    return s.length === 0 ? null : Promise.all(s);
  }
  // Public API
  /**
   * Iterates over all tiles in the loaded hierarchy. `beforecb` is called before
   * descending into a tile's children; returning true from it skips the subtree.
   * `aftercb` is called after all children have been visited.
   * @param {TileBeforeCallback|null} [beforecb]
   * @param {TileAfterCallback|null} [aftercb]
   */
  traverse(e, n, s = !0) {
    this.root && fe(this.root, (a, ...r) => (s && this.ensureChildrenArePreprocessed(a, !0), e ? e(a, ...r) : !1), n);
  }
  /**
   * Collects attribution data from all registered plugins into `target` and returns it.
   * @param {Array<{type: string, value: any}>} [target]
   * @returns {Array<{type: string, value: any}>}
   */
  getAttributions(e = []) {
    return this.invokeAllPlugins((n) => n !== this && n.getAttributions && n.getAttributions(e)), e;
  }
  /**
   * Runs the tile traversal and update loop. Should be called once per frame after
   * camera matrices have been updated. Triggers tile loading, visibility updates,
   * and LRU cache eviction.
   */
  update() {
    const { lruCache: e, usedSet: n, stats: s, root: a, downloadQueue: r, parseQueue: i, processNodeQueue: l } = this;
    if (this.rootLoadingState === C && (this.rootLoadingState = x, this.invokeOnePlugin((c) => c.loadRootTileset && c.loadRootTileset()).then((c) => {
      let h = this.rootURL;
      h !== null && this.invokeAllPlugins((k) => h = k.preprocessURL ? k.preprocessURL(h, null) : h), this.rootLoadingState = S, this.rootTileset = c, this.dispatchEvent({ type: "needs-update" }), this.dispatchEvent({
        type: "load-tileset",
        tileset: c,
        url: h
      }), this.dispatchEvent({
        type: "load-root-tileset",
        tileset: c,
        url: h
      });
    }).catch((c) => {
      this.rootLoadingState = R, console.error(c), this.rootTileset = null, this.dispatchEvent({
        type: "load-error",
        tile: null,
        error: c,
        url: this.rootURL
      });
    })), !a)
      return;
    let o = null;
    if (this.invokeAllPlugins((c) => {
      if (c.doTilesNeedUpdate) {
        const h = c.doTilesNeedUpdate();
        o === null ? o = h : o = !!(o || h);
      }
    }), o === !1) {
      this.dispatchEvent({ type: "update-before" }), this.dispatchEvent({ type: "update-after" });
      return;
    }
    this.dispatchEvent({ type: "update-before" }), s.inFrustum = 0, s.used = 0, s.active = 0, s.visible = 0, s.tilesProcessed = 0, this.frameCount++, n.forEach((c) => e.markUnused(c)), n.clear(), this.prepareForTraversal(), ge(a, this), this.removeUnusedPendingTiles();
    const u = this.queuedTiles;
    u.sort(e.unloadPriorityCallback);
    for (let c = 0, h = u.length; c < h && !e.isFull(); c++)
      this.requestTileContents(u[c]);
    u.length = 0, e.scheduleUnload(), (r.running || i.running || l.running) === !1 && this.isLoading === !0 && (this.cachedSinceLoadComplete.clear(), s.inCacheSinceLoad = 0, this.dispatchEvent({ type: "tiles-load-end" }), this.isLoading = !1), this.dispatchEvent({ type: "update-after" });
  }
  /**
   * Resets any tiles that previously failed to load so they will be retried on the next `update`.
   */
  resetFailedTiles() {
    this.rootLoadingState === R && (this.rootLoadingState = C);
    const e = this.stats;
    e.failed !== 0 && (this.traverse((n) => {
      n.internal.loadingState === R && (n.internal.loadingState = C);
    }, null, !1), e.failed = 0);
  }
  calculateTileViewErrorWithPlugin(e, n) {
    this.calculateTileViewError(e, n);
    let s = null, a = 0, r = 1 / 0;
    this.invokeAllPlugins((i) => {
      i !== this && i.calculateTileViewError && (b.inView = !0, b.error = 0, b.distance = 1 / 0, i.calculateTileViewError(e, b) && (s === null && (s = !0), s = s && b.inView, b.inView && (r = Math.min(r, b.distance), a = Math.max(a, b.error))));
    }), n.inView && s !== !1 ? (n.error = Math.max(n.error, a), n.distanceFromCamera = Math.min(n.distanceFromCamera, r)) : s ? (n.inView = !0, n.error = a, n.distanceFromCamera = r) : n.inView = !1;
  }
  /**
   * Disposes all loaded tiles and unregisters all plugins. The renderer should not
   * be used after calling this.
   */
  dispose() {
    [...this.plugins].forEach((a) => {
      this.unregisterPlugin(a);
    });
    const n = this.lruCache, s = [];
    this.traverse((a) => (s.push(a), !1), null, !1);
    for (let a = 0, r = s.length; a < r; a++)
      n.remove(s[a]);
    this.stats = {
      queued: 0,
      parsing: 0,
      downloading: 0,
      failed: 0,
      inFrustum: 0,
      traversed: 0,
      used: 0,
      active: 0,
      visible: 0
    }, this.frameCount = 0, this.loadingTiles.clear();
  }
  // Overrideable
  calculateBytesUsed(e, n) {
    return 0;
  }
  /**
   * Dispatches an event to all registered listeners for the given event type.
   * @param {{ type: string }} e
   */
  dispatchEvent(e) {
  }
  /**
   * Registers a listener for the given event type.
   * @param {string} name
   * @param {EventCallback} callback
   */
  addEventListener(e, n) {
  }
  /**
   * Removes a previously registered event listener.
   * @param {string} name
   * @param {EventCallback} callback
   */
  removeEventListener(e, n) {
  }
  parseTile(e, n, s) {
    return null;
  }
  prepareForTraversal() {
  }
  disposeTile(e) {
    e.traversal.visible && (e.internal.hasRenderableContent ? this.invokeOnePlugin((s) => s.setTileVisible && s.setTileVisible(e, !1)) : this.invokeOnePlugin((s) => s.setEmptyTileVisible && s.setEmptyTileVisible(e, !1)), e.traversal.visible = !1), e.traversal.active && e.internal.hasRenderableContent && this.invokeOnePlugin((s) => s.setTileActive && s.setTileActive(e, !1)), e.traversal.active = !1;
    const { scene: n } = e.engineData;
    n && this.dispatchEvent({
      type: "dispose-model",
      scene: n,
      tile: e
    });
  }
  preprocessNode(e, n, s = null) {
    var a;
    if (this.processedTiles.add(e), this.stats.tilesProcessed++, e.content && (!("uri" in e.content) && "url" in e.content && (e.content.uri = e.content.url, delete e.content.url), e.content.boundingVolume && !("box" in e.content.boundingVolume || "sphere" in e.content.boundingVolume || "region" in e.content.boundingVolume) && delete e.content.boundingVolume), e.parent = s, e.children = e.children || [], e.internal = {
      hasContent: !1,
      hasRenderableContent: !1,
      hasUnrenderableContent: !1,
      loadingState: C,
      basePath: n,
      depth: -1,
      depthFromRenderedParent: -1,
      isVirtual: !1,
      virtualChildCount: 0,
      renderer: this,
      // preserve any pre-seeded fields
      ...e.internal
    }, (a = e.content) != null && a.uri) {
      const r = W(e.content.uri), i = !!(r && /json$/.test(r));
      e.internal.hasContent = !0, e.internal.hasUnrenderableContent = i, e.internal.hasRenderableContent = !i;
    } else
      e.internal.hasContent = !1, e.internal.hasUnrenderableContent = !1, e.internal.hasRenderableContent = !1;
    s ? (e.internal.depth = s.internal.depth + 1, e.internal.depthFromRenderedParent = s.internal.depthFromRenderedParent + (e.internal.hasRenderableContent ? 1 : 0)) : (e.internal.depth = 0, e.internal.depthFromRenderedParent = e.internal.hasRenderableContent ? 1 : 0), e.traversal = {
      distanceFromCamera: 1 / 0,
      error: 1 / 0,
      inFrustum: !1,
      wasInFrustum: !1,
      isLeaf: !1,
      used: !1,
      usedLastFrame: !1,
      visible: !1,
      wasSetVisible: !1,
      active: !1,
      wasSetActive: !1,
      allChildrenReady: !1,
      allChildrenLoaded: !1,
      kicked: !1,
      allUsedChildrenProcessed: !1,
      lastFrameVisited: -1
    }, s === null ? e.refine = e.refine || "REPLACE" : e.refine = e.refine || s.refine, e.engineData = {
      scene: null,
      metadata: null,
      boundingVolume: null
    }, Object.defineProperty(e, "cached", {
      get() {
        return console.warn('TilesRenderer: "tile.cached" field has been renamed to "tile.engineData".'), this.engineData;
      },
      enumerable: !1,
      configurable: !0
    }), this.invokeAllPlugins((r) => {
      r !== this && r.preprocessNode && r.preprocessNode(e, n, s);
    });
  }
  setTileActive(e, n) {
    n ? this.activeTiles.add(e) : this.activeTiles.delete(e);
  }
  setTileVisible(e, n) {
    n ? this.visibleTiles.add(e) : this.visibleTiles.delete(e), this.dispatchEvent({
      type: "tile-visibility-change",
      scene: e.engineData.scene,
      tile: e,
      visible: n
    });
  }
  calculateTileViewError(e, n) {
  }
  removeUnusedPendingTiles() {
    const { lruCache: e, loadingTiles: n } = this, s = [];
    for (const a of n)
      !e.isUsed(a) && a.internal.loadingState === A && s.push(a);
    for (let a = 0; a < s.length; a++)
      e.remove(s[a]);
  }
  // Private Functions
  queueTileForDownload(e) {
    e.internal.loadingState !== C || this.lruCache.isFull() || this.queuedTiles.push(e);
  }
  markTileUsed(e) {
    this.usedSet.add(e), this.lruCache.markUsed(e);
  }
  fetchData(e, n) {
    return fetch(e, n);
  }
  ensureChildrenArePreprocessed(e, n = this.stats.tilesProcessed < this.maxTilesProcessed) {
    const s = e.children;
    if (s.length === 0 || s[s.length - 1].traversal)
      return;
    const a = (r) => {
      for (let i = 0, l = r.length; i < l; i++) {
        const o = r[i];
        o && !o.traversal && this.preprocessNode(o, e.internal.basePath, e);
      }
    };
    n ? (this.processNodeQueue.remove(e), a(s)) : this.processNodeQueue.has(e) || this.processNodeQueue.add(e, (r) => {
      a(r.children), this._dispatchNeedsUpdateEvent();
    });
  }
  // returns the total bytes used for by the given tile as reported by all plugins
  getBytesUsed(e) {
    let n = 0;
    return this.invokeAllPlugins((s) => {
      s.calculateBytesUsed && (n += s.calculateBytesUsed(e, e.engineData.scene) || 0);
    }), n;
  }
  // force a recalculation of the tile or all tiles if no tile is provided
  recalculateBytesUsed(e = null) {
    const { lruCache: n, processedTiles: s } = this;
    e === null ? n.itemSet.forEach((a) => {
      s.has(a) && n.setMemoryUsage(a, this.getBytesUsed(a));
    }) : n.setMemoryUsage(e, this.getBytesUsed(e));
  }
  preprocessTileset(e, n, s = null) {
    const a = e.asset.version, [r, i] = a.split(".").map((o) => parseInt(o));
    console.assert(
      r <= 1,
      "TilesRenderer: asset.version is expected to be a 1.x or a compatible version."
    ), r === 1 && i > 0 && console.warn("TilesRenderer: tiles versions at 1.1 or higher have limited support. Some new extensions and features may not be supported.");
    let l = n.replace(/\/[^/]*$/, "");
    l = new URL(l, window.location.href).toString(), this.preprocessNode(e.root, l, s);
  }
  loadRootTileset() {
    let e = this.rootURL;
    return this.invokeAllPlugins((s) => e = s.preprocessURL ? s.preprocessURL(e, null) : e), this.invokeOnePlugin((s) => s.fetchData && s.fetchData(e, this.fetchOptions)).then((s) => {
      if (s instanceof Response) {
        if (s.ok)
          return s.json();
        throw new Error(`TilesRenderer: Failed to load tileset "${e}" with status ${s.status} : ${s.statusText}`);
      } else return s;
    }).then((s) => (this.preprocessTileset(s, e), s));
  }
  requestTileContents(e) {
    if (e.internal.loadingState !== C)
      return;
    let n = !1, s = null, a = new URL(e.content.uri, e.internal.basePath + "/").toString();
    this.invokeAllPlugins((d) => a = d.preprocessURL ? d.preprocessURL(a, e) : a);
    const r = this.stats, i = this.lruCache, l = this.downloadQueue, o = this.parseQueue, u = this.loadingTiles, v = W(a), c = new AbortController(), h = c.signal;
    if (i.add(e, (d) => {
      c.abort(), n ? d.children.length = 0 : this.invokeAllPlugins((p) => {
        p.disposeTile && p.disposeTile(d);
      }), r.inCache--, this.cachedSinceLoadComplete.has(e) && (this.cachedSinceLoadComplete.delete(e), r.inCacheSinceLoad--), d.internal.loadingState === A ? r.queued-- : d.internal.loadingState === x ? r.downloading-- : d.internal.loadingState === O ? r.parsing-- : d.internal.loadingState === S && r.loaded--, d.internal.loadingState = C, o.remove(d), l.remove(d), u.delete(d);
    }))
      return this.isLoading || (this.isLoading = !0, this.dispatchEvent({ type: "tiles-load-start" })), i.setMemoryUsage(e, this.getBytesUsed(e)), this.cachedSinceLoadComplete.add(e), r.inCacheSinceLoad++, r.inCache++, r.queued++, e.internal.loadingState = A, u.add(e), l.add(e, (d) => {
        if (h.aborted)
          return Promise.resolve();
        e.internal.loadingState = x, r.downloading++, r.queued--;
        const p = this.invokeOnePlugin((P) => P.fetchData && P.fetchData(a, { ...this.fetchOptions, signal: h }));
        return this.dispatchEvent({
          type: "tile-download-start",
          tile: e,
          url: a,
          get uri() {
            return console.warn('tile-download-start event: "uri" has been renamed to "url".'), this.url;
          }
        }), p;
      }).then((d) => {
        if (!h.aborted)
          if (d instanceof Response) {
            if (d.ok)
              return v === "json" ? d.json() : d.arrayBuffer();
            throw new Error(`Failed to load model with error code ${d.status}`);
          } else return d;
      }).then((d) => {
        if (!h.aborted)
          return r.downloading--, r.parsing++, e.internal.loadingState = O, o.add(e, (p) => h.aborted ? Promise.resolve() : v === "json" && d.root ? (this.preprocessTileset(d, a, e), e.children.push(d.root), s = d, n = !0, Promise.resolve()) : this.invokeOnePlugin((P) => P.parseTile && P.parseTile(d, p, v, a, h)));
      }).then(() => {
        if (h.aborted)
          return;
        r.parsing--, r.loaded++, e.internal.loadingState = S, u.delete(e), i.setLoaded(e, !0);
        const d = this.getBytesUsed(e);
        if (i.getMemoryUsage(e) === 0 && d > 0 && i.isFull()) {
          i.remove(e);
          return;
        }
        i.setMemoryUsage(e, d), this.dispatchEvent({ type: "needs-update" }), n && this.dispatchEvent({
          type: "load-tileset",
          tileset: s,
          url: a
        }), e.engineData.scene && this.dispatchEvent({
          type: "load-model",
          scene: e.engineData.scene,
          tile: e,
          url: a
        });
      }).catch((d) => {
        h.aborted || (d.name !== "AbortError" ? (o.remove(e), l.remove(e), e.internal.loadingState === A ? r.queued-- : e.internal.loadingState === x ? r.downloading-- : e.internal.loadingState === O ? r.parsing-- : e.internal.loadingState === S && r.loaded--, r.failed++, console.error(`TilesRenderer : Failed to load tile at url "${e.content.uri}".`), console.error(d), e.internal.loadingState = R, u.delete(e), i.setLoaded(e, !0), this.dispatchEvent({
          type: "load-error",
          tile: e,
          error: d,
          url: a
        })) : i.remove(e));
      });
  }
}
export {
  Q as D,
  R as F,
  S as L,
  O as P,
  A as Q,
  F as S,
  we as T,
  C as U,
  Fe as W,
  x as a,
  ve as b,
  q as c,
  Re as d,
  ke as e,
  _ as u
};
//# sourceMappingURL=TilesRendererBase-BGxy2Uih.js.map
