import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const viewer = document.querySelector('[data-model]');

if (viewer) {
  const modelUrl = viewer.dataset.model;
  const modelTitle = viewer.dataset.title || 'Reef model';
  const modelSource = viewer.dataset.source || 'Compact textured mesh';
  const declaredBytes = Number(viewer.dataset.bytes || 0);

  viewer.innerHTML = `
    <div class="reef-viewport" aria-label="Interactive 3D model of ${modelTitle}"></div>
    <div class="reef-vignette" aria-hidden="true"></div>
    <section class="reef-information" aria-label="Model information">
      <span class="badge text-bg-success">Textured mesh</span>
      <h1>${modelTitle}</h1>
      <p>${modelSource}</p>
    </section>
    <div class="reef-status" aria-live="polite">
      <span class="reef-spinner" aria-hidden="true"></span>
      <span class="reef-status-copy">Loading model</span>
      <strong class="reef-transfer">0% transferred</strong>
    </div>
    <aside class="reef-controls card text-bg-dark border-secondary" aria-label="Viewer controls">
      <div class="card-header border-secondary">
        <span>Viewer controls</span>
        <span aria-hidden="true">3D</span>
      </div>
      <div class="card-body">
        <button class="reef-reset btn btn-secondary w-100 mb-3" type="button">Reset view</button>
        <label class="form-label" for="reef-display">Display</label>
        <select class="reef-display form-select mb-3" id="reef-display">
          <option value="textured">Textured</option>
          <option value="wireframe">Wireframe</option>
          <option value="textured-wire">Textured + wire</option>
          <option value="points">Points</option>
        </select>
        <label class="reef-point-size form-label w-100 mb-3" hidden>
          Point size <output class="float-end">1 px</output>
          <input class="form-range" type="range" min="1" max="12" step="1" value="1">
        </label>
        <div class="d-grid gap-2 d-sm-flex">
          <button class="reef-shot btn btn-secondary flex-fill" type="button">Screenshot</button>
          <button class="reef-fullscreen btn btn-secondary flex-fill" type="button">Full screen</button>
        </div>
      </div>
    </aside>
    <div class="reef-progress-wrap" role="progressbar" aria-label="Model transfer" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
      <div class="progress">
        <div class="reef-progress progress-bar bg-success" style="width: 0%"></div>
      </div>
    </div>
    <div class="reef-help" aria-label="How to move around the model">
      <span><strong>Rotate</strong> left-drag</span>
      <span><strong>Pan</strong> right-drag</span>
      <span><strong>Zoom</strong> wheel or pinch</span>
    </div>
  `;

  const viewport = viewer.querySelector('.reef-viewport');
  const status = viewer.querySelector('.reef-status');
  const statusCopy = viewer.querySelector('.reef-status-copy');
  const transfer = viewer.querySelector('.reef-transfer');
  const progressWrap = viewer.querySelector('.reef-progress-wrap');
  const progressBar = viewer.querySelector('.reef-progress');
  const display = viewer.querySelector('.reef-display');
  const pointSizeRow = viewer.querySelector('.reef-point-size');
  const pointSize = pointSizeRow.querySelector('input');
  const pointSizeOutput = pointSizeRow.querySelector('output');

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x222222);
  scene.fog = new THREE.FogExp2(0x222222, 0.00012);

  const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 1_000_000);
  camera.up.set(0, 0, -1);

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
  controls.mouseButtons.MIDDLE = THREE.MOUSE.DOLLY;
  controls.mouseButtons.RIGHT = THREE.MOUSE.PAN;
  controls.touches.ONE = THREE.TOUCH.ROTATE;
  controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;

  scene.add(new THREE.HemisphereLight(0xffffff, 0x303030, 2.2));
  const sun = new THREE.DirectionalLight(0xffffff, 2.5);
  sun.position.set(4, -3, -8);
  scene.add(sun);

  const root = new THREE.Group();
  scene.add(root);
  let meshes = [];
  let generatedPoints = [];
  let edges = [];

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
  };

  const fit = () => {
    const box = new THREE.Box3().setFromObject(root);
    if (box.isEmpty()) return;
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const radius = Math.max(size.length() * 0.5, 0.001);
    const distance = radius / Math.sin(THREE.MathUtils.degToRad(camera.fov * 0.5));
    const direction = new THREE.Vector3(0.08, -1.5, -0.82).normalize();
    camera.position.copy(center).add(direction.multiplyScalar(distance));
    camera.near = Math.max(radius / 10_000, 0.0001);
    camera.far = Math.max(radius * 10_000, 1_000);
    camera.updateProjectionMatrix();
    controls.target.copy(center);
    controls.update();
    scene.fog = new THREE.FogExp2(0x222222, 0.16 / Math.max(radius, 1));
  };

  const clearEdges = () => {
    edges.forEach((edge) => {
      edge.parent?.remove(edge);
      edge.geometry.dispose();
      edge.material.dispose();
    });
    edges = [];
  };

  const applyDisplayMode = (mode) => {
    clearEdges();
    meshes.forEach((mesh) => {
      mesh.visible = mode !== 'points';
      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      materials.forEach((material) => {
        material.wireframe = mode === 'wireframe';
      });
      if (mode === 'textured-wire') {
        const edge = new THREE.LineSegments(
          new THREE.EdgesGeometry(mesh.geometry, 22),
          new THREE.LineBasicMaterial({ color: 0x222222, transparent: true, opacity: 0.62 }),
        );
        mesh.add(edge);
        edges.push(edge);
      }
    });
    generatedPoints.forEach((points) => {
      points.visible = mode === 'points';
    });
    pointSizeRow.hidden = mode !== 'points';
  };

  const updateProgress = (event) => {
    const total = event.total || declaredBytes;
    if (!total) return;
    const percentage = Math.min(99, Math.round((event.loaded / total) * 100));
    transfer.textContent = `${percentage}% transferred`;
    progressBar.style.width = `${percentage}%`;
    progressWrap.setAttribute('aria-valuenow', String(percentage));
  };

  const countVertices = () => meshes.reduce(
    (count, mesh) => count + (mesh.geometry?.attributes?.position?.count || 0),
    0,
  );

  new GLTFLoader().load(
    modelUrl,
    (gltf) => {
      root.add(gltf.scene);
      root.traverse((object) => {
        if (object.isMesh) meshes.push(object);
      });
      generatedPoints = meshes.map((mesh) => {
        const points = new THREE.Points(
          mesh.geometry,
          new THREE.PointsMaterial({ color: 0x3498db, size: 1, sizeAttenuation: false }),
        );
        points.position.copy(mesh.position);
        points.quaternion.copy(mesh.quaternion);
        points.scale.copy(mesh.scale);
        points.visible = false;
        mesh.parent.add(points);
        return points;
      });
      fit();
      const vertices = new Intl.NumberFormat().format(countVertices());
      statusCopy.textContent = `${vertices} vertices`;
      transfer.textContent = 'Loaded';
      status.querySelector('.reef-spinner')?.remove();
      progressWrap.remove();
    },
    updateProgress,
    (error) => {
      console.error(error);
      statusCopy.textContent = 'Model could not be loaded';
      transfer.textContent = 'Load failed';
      status.querySelector('.reef-spinner')?.remove();
      progressWrap.remove();
    },
  );

  display.addEventListener('change', () => applyDisplayMode(display.value));
  pointSize.addEventListener('input', () => {
    const size = Number(pointSize.value);
    generatedPoints.forEach((points) => {
      points.material.size = size;
    });
    pointSizeOutput.textContent = `${size} px`;
  });
  viewer.querySelector('.reef-reset').addEventListener('click', fit);
  viewer.querySelector('.reef-fullscreen').addEventListener('click', () => viewer.requestFullscreen());
  viewer.querySelector('.reef-shot').addEventListener('click', () => {
    renderer.render(scene, camera);
    const link = document.createElement('a');
    link.download = `openreef-${modelTitle.toLowerCase().replaceAll(' ', '-')}.png`;
    link.href = renderer.domElement.toDataURL('image/png');
    link.click();
  });

  window.addEventListener('resize', resize);
  resize();
  renderer.setAnimationLoop(() => {
    controls.update();
    renderer.render(scene, camera);
  });
}

