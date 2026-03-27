/**
 * Поле европейской рулетки через buildArRouletteTable (та же геометрия, что в ar_bets).
 * Камера и OrbitControls — как в заставке AR Bets, не как в ar_series (там без вращения).
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { buildArRouletteTable } from './ar_roulette_table.mjs';

/** Совпадает с ar_bets.html (начальная камера после загрузки). */
const CAMERA_HOME_POS = { x: 12.095, y: 2.566, z: 18.105 };
const CAMERA_HOME_TARGET = { x: 12.281, y: 17.126, z: 1.613 };

/**
 * @param {HTMLCanvasElement} canvas
 * @returns {{ dispose: () => void; resetCamera: () => void } | null}
 */
export function mountArRouletteField(canvas) {
	if (!canvas) return null;
	const wrap = canvas.closest('.ar-canvas-wrap');
	if (!wrap) return null;

	let containerW = wrap.clientWidth || 0;
	let containerH = wrap.clientHeight || 0;
	if (!containerW || containerW < 100) containerW = 640;
	if (!containerH || containerH < 100) containerH = Math.min(480, Math.floor(containerW * 0.75));
	let w = containerW;
	let h = containerH;

	const scene = new THREE.Scene();
	scene.background = new THREE.Color(0x1a1a1a);

	const aspect = h > 0 && w > 0 ? w / h : 16 / 9;
	const camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 1000);
	camera.position.set(CAMERA_HOME_POS.x, CAMERA_HOME_POS.y, CAMERA_HOME_POS.z);
	camera.lookAt(CAMERA_HOME_TARGET.x, CAMERA_HOME_TARGET.y, CAMERA_HOME_TARGET.z);

	const controls = new OrbitControls(camera, canvas);
	controls.target.set(CAMERA_HOME_TARGET.x, CAMERA_HOME_TARGET.y, CAMERA_HOME_TARGET.z);
	controls.enableDamping = true;
	controls.dampingFactor = 0.05;
	controls.maxPolarAngle = Math.PI * 0.95;
	controls.minAzimuthAngle = -Math.PI / 2;
	controls.maxAzimuthAngle = Math.PI / 2;

	const rotateHint = wrap.querySelector('.ar-rotate-hint');
	function hideRotateHint() {
		if (rotateHint && !rotateHint.classList.contains('ar-rotate-hint--hidden')) {
			rotateHint.classList.add('ar-rotate-hint--hidden');
		}
	}
	controls.addEventListener('start', hideRotateHint);

	const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
	if (!renderer.getContext()) {
		wrap.insertAdjacentHTML(
			'beforeend',
			'<p style="color:#e11;padding:16px;margin:0;">WebGL не доступен. Обновите браузер или включите аппаратное ускорение.</p>'
		);
		return null;
	}
	renderer.setSize(w, h);
	renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

	scene.add(new THREE.AmbientLight(0xffffff, 0.6));
	const dir = new THREE.DirectionalLight(0xffffff, 0.9);
	dir.position.set(20, 25, 20);
	scene.add(dir);

	buildArRouletteTable(THREE, scene, { visibleDozens: [1, 2, 3] });

	let raf = 0;
	function animate() {
		raf = requestAnimationFrame(animate);
		controls.update();
		renderer.render(scene, camera);
	}
	animate();

	function onResize() {
		containerW = wrap.clientWidth || 640;
		containerH = wrap.clientHeight || Math.min(480, Math.floor(containerW * 0.75));
		if (containerW < 100) containerW = 640;
		if (containerH < 100) containerH = 360;
		w = containerW;
		h = containerH;
		camera.aspect = h > 0 ? w / h : 16 / 9;
		camera.updateProjectionMatrix();
		renderer.setSize(w, h);
	}
	window.addEventListener('resize', onResize);

	function resetCamera() {
		camera.position.set(CAMERA_HOME_POS.x, CAMERA_HOME_POS.y, CAMERA_HOME_POS.z);
		controls.target.set(CAMERA_HOME_TARGET.x, CAMERA_HOME_TARGET.y, CAMERA_HOME_TARGET.z);
		controls.update();
	}

	return {
		resetCamera,
		dispose() {
			window.removeEventListener('resize', onResize);
			controls.removeEventListener('start', hideRotateHint);
			cancelAnimationFrame(raf);
			controls.dispose();
			renderer.dispose();
			scene.clear();
		},
	};
}
