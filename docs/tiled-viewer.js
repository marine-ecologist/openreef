import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { TilesRenderer } from '3d-tiles-renderer';

const viewer = document.querySelector('[data-tileset]');

if (viewer) {
  const tilesetUrl = viewer.dataset.tileset;
  const modelTitle = viewer.dataset.title || 'Reef model';
  const modelSource = viewer.dataset.source || 'Spatial 3D tiles';
  const tileCount = Number(viewer.dataset.tiles || 0);
  const viewDirection = (viewer.dataset.viewDirection || '0.8,-1.2,0.65')
    .split(',')
    .map(Number);
  const viewDistance = Number(viewer.dataset.viewDistance || 1.08);
  const viewTarget = (viewer.dataset.viewTarget || '0,0,0')
    .split(',')
    .map(Number);
  const viewUp = (viewer.dataset.viewUp || '0,0,1')
    .split(',')
    .map(Number);

  viewer.innerHTML = `
    <div class="reef-viewport" aria-label="Interactive 3D model of ${modelTitle}"></div>
    <div class="reef-vignette" aria-hidden="true"></div>
    <section class="reef-information" aria-label="Model information">
      <span class="badge text-bg-success">Streaming 3D tiles</span>
      <h1>${modelTitle}</h1>
      <p>${modelSource}</p>
    </section>
    <div class="reef-status" aria-live="polite">
      <span class="reef-spinner" aria-hidden="true"></span>
      <span class="reef-status-copy">Loading tileset</span>
      <strong class="reef-transfer">0% transferred</strong>
    </div>
    <aside class="reef-controls card text-bg-dark border-secondary" aria-label="Viewer controls">
      <div class="card-header border-secondary">
        <span>Viewer controls</span>
        <span aria-hidden="true">3D</span>
      </div>
      <div class="card-body">
        <button class="reef-reset btn btn-secondary w-100 mb-3" type="button">Reset view</button>
        <label class="form-label" for="reef-detail">Streaming detail</label>
        <select class="reef-detail form-select mb-3" id="reef-detail">
          <option value="16">Fast preview</option>
          <option value="8" selected>Balanced</option>
          <option value="3">Fine</option>
        </select>
        <div class="d-grid gap-2 d-sm-flex">
          <button class="reef-shot btn btn-secondary flex-fill" type="button">Screenshot</button>
          <button class="reef-fullscreen btn btn-secondary flex-fill" type="button">Full screen</button>
        </div>
      </div>
    </aside>
    <div class="reef-progress-wrap" style="left:50%;top:50%;bottom:auto;transform:translate(-50%,-50%)" role="progressbar" aria-label="Visible tile transfer" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
      <div class="progress">
        <div class="reef-progress progress-bar bg-success" style="width: 0%"></div>
      </div>
    </div>
    <div class="reef-help" aria-label="How to move around the model">
      <span><strong>Rotate</strong> left- or right-drag</span>
      <span><strong>Pan</strong> middle-drag or two fingers</span>
      <span><strong>Zoom</strong> wheel or pinch</span>
    </div>
  `;

  const viewport = viewer.querySelector('.reef-viewport');
  const status = viewer.querySelector('.reef-status');
  const statusCopy = viewer.querySelector('.reef-status-copy');
  const transfer = viewer.querySelector('.reef-transfer');
  const progressWrap = viewer.querySelector('.reef-progress-wrap');
  const progressBar = viewer.querySelector('.reef-progress');

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x222222);
  scene.fog = new THREE.FogExp2(0x222222, 0.00012);

  const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 1_000_000_000);
  camera.up.set(...viewUp).normalize();

  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    preserveDrawingBuffer: true,
    powerPreference: 'high-performance',
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  viewport.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.screenSpacePanning = true;
  controls.mouseButtons.LEFT = THREE.MOUSE.ROTATE;
  controls.mouseButtons.MIDDLE = THREE.MOUSE.PAN;
  controls.mouseButtons.RIGHT = THREE.MOUSE.ROTATE;
  renderer.domElement.addEventListener('contextmenu', (event) => event.preventDefault());

  const remappedPointerEvents = new WeakSet();
  renderer.domElement.addEventListener('pointerdown', (event) => {
    if (remappedPointerEvents.has(event) || event.button !== 0 || !event.ctrlKey) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const mappedButton = event.shiftKey ? 1 : 2;
    const mappedEvent = new PointerEvent('pointerdown', {
      bubbles: true,
      cancelable: true,
      composed: true,
      pointerId: event.pointerId,
      pointerType: event.pointerType,
      isPrimary: event.isPrimary,
      clientX: event.clientX,
      clientY: event.clientY,
      screenX: event.screenX,
      screenY: event.screenY,
      button: mappedButton,
      buttons: mappedButton === 1 ? 4 : 2,
    });
    remappedPointerEvents.add(mappedEvent);
    renderer.domElement.dispatchEvent(mappedEvent);
  }, true);

  const panFromTrackpad = (deltaX, deltaY) => {
    camera.updateMatrix();
    const offset = camera.position.clone().sub(controls.target);
    const visibleHeight = 2 * offset.length()
      * Math.tan(THREE.MathUtils.degToRad(camera.fov * 0.5));
    const unitsPerPixel = visibleHeight / Math.max(renderer.domElement.clientHeight, 1);
    const right = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(camera.matrix, 1);
    const movement = right.multiplyScalar(-deltaX * unitsPerPixel * 0.45)
      .add(up.multiplyScalar(deltaY * unitsPerPixel * 0.45));
    camera.position.add(movement);
    controls.target.add(movement);
    controls.update();
  };

  const orbitFromTrackpad = (deltaX, deltaY) => {
    const offset = camera.position.clone().sub(controls.target);
    const spherical = new THREE.Spherical().setFromVector3(offset);
    spherical.theta -= deltaX * 0.003;
    spherical.phi -= deltaY * 0.003;
    spherical.phi = THREE.MathUtils.clamp(spherical.phi, 0.01, Math.PI - 0.01);
    offset.setFromSpherical(spherical);
    camera.position.copy(controls.target).add(offset);
    camera.lookAt(controls.target);
    controls.update();
  };

  renderer.domElement.addEventListener('wheel', (event) => {
    if (event.ctrlKey) return;
    const trackpad = event.deltaMode === WheelEvent.DOM_DELTA_PIXEL
      && (Math.abs(event.deltaX) > 0 || Math.abs(event.deltaY) < 50);
    if (!trackpad) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (event.shiftKey) orbitFromTrackpad(event.deltaX, event.deltaY);
    else panFromTrackpad(event.deltaX, event.deltaY);
  }, { capture: true, passive: false });

  scene.add(new THREE.HemisphereLight(0xffffff, 0x303030, 2.2));
  const sun = new THREE.DirectionalLight(0xffffff, 2.5);
  sun.position.set(4, -3, 8);
  scene.add(sun);

  const tiles = new TilesRenderer(tilesetUrl);
  tiles.setCamera(camera);
  tiles.setResolutionFromRenderer(camera, renderer);
  tiles.errorTarget = 8;
  scene.add(tiles.group);

  let rootReady = false;
  let loadedTiles = 0;
  let fittedSphere = null;

  const recordView = () => {
    if (!fittedSphere) return;
    const offset = camera.position.clone().sub(controls.target);
    const baseDistance = fittedSphere.radius / Math.sin(THREE.MathUtils.degToRad(camera.fov * 0.5));
    viewer.dataset.currentViewDirection = offset.normalize().toArray().map(value => value.toFixed(4)).join(',');
    viewer.dataset.currentViewDistance = (camera.position.distanceTo(controls.target) / baseDistance).toFixed(4);
    viewer.dataset.currentViewTarget = controls.target.clone().sub(fittedSphere.center)
      .divideScalar(fittedSphere.radius).toArray().map(value => value.toFixed(4)).join(',');
  };
  controls.addEventListener('end', recordView);

  const setNavbarHeight = () => {
    const header = document.querySelector('#quarto-header') || document.querySelector('.navbar');
    const bottom = header ? Math.max(0, header.getBoundingClientRect().bottom) : 0;
    document.documentElement.style.setProperty('--reef-navbar-height', `${bottom}px`);
  };

  const resize = () => {
    setNavbarHeight();
    const width = viewport.clientWidth;
    const height = viewport.clientHeight;
    renderer.setSize(width, height, false);
    camera.aspect = width / Math.max(height, 1);
    camera.updateProjectionMatrix();
    tiles.setResolutionFromRenderer(camera, renderer);
  };

  const fit = () => {
    const sphere = new THREE.Sphere();
    if (!rootReady || !tiles.getBoundingSphere(sphere) || sphere.radius <= 0) return;
    tiles.group.updateMatrixWorld(true);
    sphere.applyMatrix4(tiles.group.matrixWorld);
    fittedSphere = sphere.clone();
    const direction = new THREE.Vector3(...viewDirection).normalize();
    const target = sphere.center.clone().add(
      new THREE.Vector3(...viewTarget).multiplyScalar(sphere.radius),
    );
    const distance = sphere.radius / Math.sin(THREE.MathUtils.degToRad(camera.fov * 0.5));
    camera.position.copy(target).add(direction.multiplyScalar(distance * viewDistance));
    camera.near = Math.max(distance / 1000, 0.0001);
    camera.far = Math.max(distance * 1000, 1000);
    camera.updateProjectionMatrix();
    controls.target.copy(target);
    controls.update();
    recordView();
    scene.fog = new THREE.FogExp2(0x222222, 0.16 / Math.max(sphere.radius, 1));
  };

  tiles.addEventListener('load-root-tileset', () => {
    rootReady = true;
    fit();
    statusCopy.textContent = `${tileCount.toLocaleString()} spatial tiles ready`;
    transfer.textContent = 'Streaming';
    status.querySelector('.reef-spinner')?.remove();
  });
  tiles.addEventListener('load-model', () => { loadedTiles += 1; });
  tiles.addEventListener('dispose-model', () => { loadedTiles = Math.max(0, loadedTiles - 1); });
  tiles.addEventListener('tiles-load-start', () => {
    progressWrap.hidden = false;
    statusCopy.textContent = 'Loading visible detail';
  });
  tiles.addEventListener('tiles-load-end', () => {
    progressWrap.hidden = true;
    statusCopy.textContent = `${loadedTiles} tiles loaded`;
    transfer.textContent = 'Move closer for detail';
  });
  tiles.addEventListener('load-error', (event) => {
    console.error(event.error || event);
    statusCopy.textContent = 'Tiles could not be loaded';
    transfer.textContent = 'Load failed';
  });

  viewer.querySelector('.reef-reset').addEventListener('click', fit);
  viewer.querySelector('.reef-detail').addEventListener('change', (event) => {
    tiles.errorTarget = Number(event.target.value);
  });
  viewer.querySelector('.reef-fullscreen').addEventListener('click', () => {
    viewer.requestFullscreen();
  });
  viewer.querySelector('.reef-shot').addEventListener('click', () => {
    renderer.render(scene, camera);
    const link = document.createElement('a');
    link.download = `openreef-${modelTitle.toLowerCase().replaceAll(' ', '-')}.png`;
    link.href = renderer.domElement.toDataURL('image/png');
    link.click();
  });
  window.addEventListener('keydown', (event) => {
    if (event.key.toLowerCase() !== 'f' || event.ctrlKey || event.metaKey || event.altKey) return;
    event.preventDefault();
    fit();
  });
  window.addEventListener('resize', resize);
  resize();

  renderer.setAnimationLoop(() => {
    controls.update();
    camera.updateMatrixWorld();
    tiles.update();
    if (!progressWrap.hidden) {
      const percentage = Math.round(tiles.loadProgress * 100);
      progressBar.style.width = `${percentage}%`;
      progressWrap.setAttribute('aria-valuenow', String(percentage));
      transfer.textContent = `${percentage}% transferred`;
    }
    renderer.render(scene, camera);
  });
}
