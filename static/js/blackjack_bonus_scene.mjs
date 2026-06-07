import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { TrackChipFactory } from 'ar-track-chip-factory';
import { createZastavkiChipLayout, stacksToDenomArray } from 'ar-zastavki-chip-layout';

/** Номиналы только для BJ Bonus: Pair (2.5 вместо 2, без 0.5). */
const BJ_BONUS_CHIP_VALUES_DESC = [5000, 1000, 500, 100, 25, 5, 2.5, 1];

function bonusAmountToChipStacks(amount) {
	let remaining = Number(amount);
	if (!Number.isFinite(remaining) || remaining < 0) return [];
	remaining = Math.round(remaining * 100) / 100;
	const stacks = [];
	for (const d of BJ_BONUS_CHIP_VALUES_DESC) {
		const count = Math.floor((remaining + 1e-9) / d);
		if (count > 0) {
			stacks.push({ denomination: d, count });
			remaining = Math.round((remaining - count * d) * 100) / 100;
		}
	}
	return stacks;
}

const FELT_COLOR = 0x243d6b;
const FELT_DEEP = 0x1a2f4f;
const GOLD = 0xd4af37;
const RAIL_COLOR = 0x3d2817;

/** +Y — к дилеру. Сверху прямоугольник, посередине P/S/D, снизу карты. */
const TABLE_LAYOUT = {
	MAIN_BET: { x: 0, y: 6.2, w: 3.65, h: 4.25 },
	BONUS: { y: 2.15, sy: 1.55, r: 0.82, px: -1.9, sx: 0, dx: 1.9 },
	PLAYER_Y: -2.35,
	CARD_H: 3.0,
};

const CHIP_SCALE = 0.58;
const DEFAULT_CAMERA_STORAGE_KEY = 'bj_bonus_camera';

function getCameraStorageKey(config) {
	return config?.cameraStorageKey || DEFAULT_CAMERA_STORAGE_KEY;
}

function makeLetterLabelTexture(letter) {
	const canvas = document.createElement('canvas');
	canvas.width = 256;
	canvas.height = 256;
	const ctx = canvas.getContext('2d');
	ctx.fillStyle = '#d4af37';
	ctx.textAlign = 'center';
	ctx.textBaseline = 'middle';
	ctx.font = 'bold 140px sans-serif';
	ctx.fillText(String(letter).toUpperCase(), 128, 128);
	const tex = new THREE.CanvasTexture(canvas);
	tex.colorSpace = THREE.SRGBColorSpace;
	tex.needsUpdate = true;
	return tex;
}

function addGoldRectFrame(group, cx, cy, w, h, z, thickness) {
	const mat = new THREE.MeshBasicMaterial({ color: GOLD });
	const hw = w / 2;
	const hh = h / 2;
	const t = thickness;
	for (const [pw, ph, px, py] of [
		[w, t, cx, cy + hh - t / 2],
		[w, t, cx, cy - hh + t / 2],
		[t, h, cx - hw + t / 2, cy],
		[t, h, cx + hw - t / 2, cy],
	]) {
		const mesh = new THREE.Mesh(new THREE.BoxGeometry(pw, ph, 0.08), mat);
		mesh.position.set(px, py, z);
		group.add(mesh);
	}
}

function addGoldCircleFrame(group, cx, cy, r, z, thickness) {
	const ring = new THREE.Mesh(
		new THREE.RingGeometry(r - thickness, r, 64),
		new THREE.MeshBasicMaterial({ color: GOLD, side: THREE.DoubleSide })
	);
	ring.position.set(cx, cy, z);
	group.add(ring);
}

function addCircleLabel(group, letter, cx, cy, r, z) {
	const plane = new THREE.Mesh(
		new THREE.CircleGeometry(r * 0.55, 32),
		new THREE.MeshBasicMaterial({
			map: makeLetterLabelTexture(letter),
			transparent: true,
			depthWrite: false,
		})
	);
	plane.position.set(cx, cy, z);
	group.add(plane);
}

function buildTable(scene) {
	const tableGroup = new THREE.Group();
	const feltW = 14;
	const feltH = 18;

	const felt = new THREE.Mesh(
		new THREE.PlaneGeometry(feltW, feltH),
		new THREE.MeshStandardMaterial({ color: FELT_COLOR, roughness: 0.92, metalness: 0.05 })
	);
	felt.receiveShadow = true;
	tableGroup.add(felt);

	const railPad = 0.55;
	const rail = new THREE.Mesh(
		new THREE.BoxGeometry(feltW + railPad * 2, feltH + railPad * 2, 0.35),
		new THREE.MeshStandardMaterial({ color: RAIL_COLOR, roughness: 0.85, metalness: 0.08 })
	);
	rail.position.z = -0.2;
	tableGroup.add(rail);

	const inset = new THREE.Mesh(
		new THREE.PlaneGeometry(feltW - 0.25, feltH - 0.25),
		new THREE.MeshStandardMaterial({ color: FELT_DEEP, roughness: 0.95, metalness: 0.02 })
	);
	inset.position.z = 0.005;
	tableGroup.add(inset);

	scene.add(tableGroup);
	return tableGroup;
}

function buildBettingZones(group) {
	const zones = new THREE.Group();
	const zLine = 0.04;
	const zLabel = 0.06;
	const lineT = 0.07;
	const { MAIN_BET, BONUS } = TABLE_LAYOUT;

	addGoldRectFrame(zones, MAIN_BET.x, MAIN_BET.y, MAIN_BET.w, MAIN_BET.h, zLine, lineT);

	addGoldCircleFrame(zones, BONUS.px, BONUS.y, BONUS.r, zLine, lineT);
	addCircleLabel(zones, 'P', BONUS.px, BONUS.y, BONUS.r, zLabel);

	addGoldCircleFrame(zones, BONUS.sx, BONUS.sy ?? BONUS.y, BONUS.r, zLine, lineT);
	addCircleLabel(zones, 'S', BONUS.sx, BONUS.sy ?? BONUS.y, BONUS.r, zLabel);

	addGoldCircleFrame(zones, BONUS.dx, BONUS.y, BONUS.r, zLine, lineT);
	addCircleLabel(zones, 'D', BONUS.dx, BONUS.y, BONUS.r, zLabel);

	group.add(zones);
}

function addChipAt(chipsGroup, factory, denom, x, y, z, rotZ) {
	const mesh = factory.createMesh(denom);
	const holder = new THREE.Group();
	holder.position.set(x, y, z);
	if (rotZ !== undefined) holder.rotation.z = rotZ;
	holder.add(mesh);
	chipsGroup.add(holder);
}

function buildChipsAt(group, amount, bx, by) {
	const bet = Math.max(0, Number(amount) || 0);
	if (bet <= 0) return;

	const factory = new TrackChipFactory(CHIP_SCALE);
	const layout = createZastavkiChipLayout(CHIP_SCALE);
	const chipsGroup = new THREE.Group();
	const addChip = (denom, x, y, z, rotZ) => addChipAt(chipsGroup, factory, denom, x, y, z, rotZ);
	layout.drawPositionDenomCaches(
		stacksToDenomArray(bonusAmountToChipStacks(bet)),
		bx,
		by,
		addChip
	);
	group.add(chipsGroup);
}

function buildAllChips(group, config) {
	const { BONUS } = TABLE_LAYOUT;
	const chipZone = (config.chipZone || 'P').toUpperCase();
	let bx;
	let by;
	let amount = 0;
	if (chipZone === 'S') {
		bx = BONUS.sx;
		by = BONUS.sy ?? BONUS.y;
		amount = config.sBet;
	} else if (chipZone === 'D') {
		bx = BONUS.dx;
		by = BONUS.y;
		amount = config.dBet;
	} else {
		bx = BONUS.px;
		by = BONUS.y;
		amount = config.ppBet;
	}
	try {
		if (amount > 0) buildChipsAt(group, amount, bx, by);
	} catch (err) {
		console.error('BJ bonus chips failed:', err);
	}
}

function isCameraPoseValid(position, target) {
	if (!position || !target) return false;
	const nums = [position.x, position.y, position.z, target.x, target.y, target.z];
	if (nums.some((v) => !Number.isFinite(v))) return false;
	const dx = position.x - target.x;
	const dy = position.y - target.y;
	const dz = position.z - target.z;
	const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
	return dist >= 5 && dist <= 30;
}

function clearSavedCamera(storageKey) {
	try {
		sessionStorage.removeItem(storageKey);
	} catch (_) {}
}

function loadCardTextures(cards, cardsBaseUrl, maxAnisotropy) {
	const loader = new THREE.TextureLoader();
	return Promise.all(
		cards.map((card) => {
			const url = card.img.startsWith('http') || card.img.startsWith('/')
				? card.img
				: cardsBaseUrl + card.img;
			return new Promise((resolve, reject) => {
				loader.load(
					url,
					(tex) => {
						tex.colorSpace = THREE.SRGBColorSpace;
						tex.anisotropy = maxAnisotropy;
						tex.minFilter = THREE.LinearMipmapLinearFilter;
						tex.magFilter = THREE.LinearFilter;
						resolve({ card, tex });
					},
					undefined,
					reject
				);
			});
		})
	);
}

function addCardMesh(cardsGroup, card, tex, x, y, z, cardH) {
	const img = tex.image;
	const aspect = img && img.width && img.height ? img.width / img.height : 75 / 110;
	const cardW = cardH * aspect;
	const cardGroup = new THREE.Group();
	cardGroup.position.set(x, y, z);

	const border = 0.05;
	const back = new THREE.Mesh(
		new THREE.PlaneGeometry(cardW + border, cardH + border),
		new THREE.MeshBasicMaterial({ color: 0xf5f5f5 })
	);
	back.position.z = -0.01;
	cardGroup.add(back);

	const mesh = new THREE.Mesh(
		new THREE.PlaneGeometry(cardW, cardH),
		new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: true })
	);
	cardGroup.add(mesh);
	cardsGroup.add(cardGroup);
	return cardW;
}

function buildCards(group, config, renderer) {
	const cardsGroup = new THREE.Group();
	cardsGroup.name = 'cards';
	group.add(cardsGroup);

	const cardH = TABLE_LAYOUT.CARD_H;
	const maxAnisotropy = renderer?.capabilities?.getMaxAnisotropy?.() || 8;
	const playerHand = config.playerHand || [];
	if (playerHand.length !== 2) return Promise.resolve();

	return loadCardTextures(playerHand, config.cardsBaseUrl || '/static/cards/', maxAnisotropy).then((loaded) => {
		const texMap = new Map(loaded.map(({ card, tex }) => [`${card.rank}_${card.suit}_${card.img}`, tex]));

		const p0 = playerHand[0];
		const p1 = playerHand[1];
		const p0Tex = texMap.get(`${p0.rank}_${p0.suit}_${p0.img}`);
		const p1Tex = texMap.get(`${p1.rank}_${p1.suit}_${p1.img}`);
		if (p0Tex && p1Tex) {
			const offsetY = 0.52;
			const offsetX = 0.42;
			const cx = 0;
			addCardMesh(cardsGroup, p0, p0Tex, cx, TABLE_LAYOUT.PLAYER_Y + offsetY * 0.45, 0.15, cardH);
			addCardMesh(cardsGroup, p1, p1Tex, cx - offsetX * 1.55, TABLE_LAYOUT.PLAYER_Y - offsetY * 1.35, 0.18, cardH);
		}
	});
}

export function initBlackjackBonusScene(canvas, config) {
	if (!canvas) throw new Error('canvas not found');
	const cameraStorageKey = getCameraStorageKey(config);

	let containerW = canvas.parentElement ? canvas.parentElement.clientWidth : 0;
	let containerH = canvas.parentElement ? canvas.parentElement.clientHeight : 0;
	if (!containerW || containerW < 100) containerW = 640;
	if (!containerH || containerH < 100) containerH = 360;

	const scene = new THREE.Scene();
	scene.background = new THREE.Color(0x1a1a1a);

	const aspect = containerW / containerH;
	const camera = new THREE.PerspectiveCamera(48, aspect, 0.1, 200);
	const cameraHomePos = { x: 0, y: -11.8, z: 9.8 };
	const cameraHomeTarget = { x: 0, y: 1.2, z: 0 };
	camera.position.set(cameraHomePos.x, cameraHomePos.y, cameraHomePos.z);
	camera.lookAt(cameraHomeTarget.x, cameraHomeTarget.y, cameraHomeTarget.z);

	const controls = new OrbitControls(camera, canvas);
	controls.target.set(cameraHomeTarget.x, cameraHomeTarget.y, cameraHomeTarget.z);
	controls.enableDamping = true;
	controls.dampingFactor = 0.05;
	controls.enablePan = false;
	controls.maxPolarAngle = Math.PI * 0.95;
	controls.minPolarAngle = Math.PI / 2 - 0.4;
	controls.minAzimuthAngle = -Math.PI / 2;
	controls.maxAzimuthAngle = Math.PI / 2;
	controls.minDistance = 6;
	controls.maxDistance = 28;

	const rotateHint = document.querySelector('.ar-rotate-hint');
	function hideRotateHint() {
		if (rotateHint && !rotateHint.classList.contains('ar-rotate-hint--hidden')) {
			rotateHint.classList.add('ar-rotate-hint--hidden');
		}
	}
	controls.addEventListener('start', hideRotateHint);

	function tryApplySavedCamera() {
		try {
			const raw = sessionStorage.getItem(cameraStorageKey);
			if (!raw) return;
			const o = JSON.parse(raw);
			if (o?.position && o?.target && isCameraPoseValid(o.position, o.target)) {
				camera.position.set(o.position.x, o.position.y, o.position.z);
				controls.target.set(cameraHomeTarget.x, cameraHomeTarget.y, cameraHomeTarget.z);
				controls.update();
			} else {
				clearSavedCamera(cameraStorageKey);
			}
		} catch (_) {
			clearSavedCamera(cameraStorageKey);
		}
	}

	function saveCamera() {
		try {
			sessionStorage.setItem(
				cameraStorageKey,
				JSON.stringify({
					position: { x: camera.position.x, y: camera.position.y, z: camera.position.z },
					target: { x: controls.target.x, y: controls.target.y, z: controls.target.z },
				})
			);
		} catch (_) {}
	}

	controls.addEventListener('end', saveCamera);

	const payoutForm = canvas.closest('form');
	if (payoutForm) payoutForm.addEventListener('submit', saveCamera);

	const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
	if (!renderer.getContext()) {
		canvas.parentElement?.insertAdjacentHTML(
			'beforeend',
			'<p style="color:#e11;padding:16px;margin:0;">WebGL не доступен.</p>'
		);
		return null;
	}
	renderer.setSize(containerW, containerH);
	renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

	scene.add(new THREE.AmbientLight(0xffffff, 0.62));
	const dir = new THREE.DirectionalLight(0xffffff, 0.88);
	dir.position.set(4, -6, 14);
	scene.add(dir);
	const fill = new THREE.DirectionalLight(0xffffff, 0.35);
	fill.position.set(-6, 8, 6);
	scene.add(fill);

	const tableRoot = buildTable(scene);
	buildBettingZones(tableRoot);

	function animate() {
		requestAnimationFrame(animate);
		controls.update();
		renderer.render(scene, camera);
	}
	animate();

	buildAllChips(tableRoot, config);
	buildCards(tableRoot, config, renderer)
		.catch((err) => console.error('BJ bonus cards failed:', err))
		.finally(() => tryApplySavedCamera());

	let resizeRaf = 0;
	function onResize(force) {
		cancelAnimationFrame(resizeRaf);
		resizeRaf = requestAnimationFrame(() => {
			const nextW = canvas.parentElement?.clientWidth || 640;
			const nextH = canvas.parentElement?.clientHeight || Math.min(480, Math.floor(nextW * 0.66));
			if (!force && nextW === containerW && nextH === containerH) return;
			containerW = nextW;
			containerH = nextH;
			camera.aspect = containerW / containerH;
			camera.updateProjectionMatrix();
			renderer.setSize(containerW, containerH);
		});
	}
	window.addEventListener('resize', onResize);
	if (typeof ResizeObserver !== 'undefined' && canvas.parentElement) {
		const ro = new ResizeObserver(onResize);
		ro.observe(canvas.parentElement);
	}

	const resetBtn = document.getElementById('bjBonusCameraReset');
	if (resetBtn) {
		resetBtn.addEventListener('click', () => {
			clearSavedCamera(cameraStorageKey);
			camera.position.set(cameraHomePos.x, cameraHomePos.y, cameraHomePos.z);
			controls.target.set(cameraHomeTarget.x, cameraHomeTarget.y, cameraHomeTarget.z);
			controls.update();
		});
	}

	onResize(true);
	requestAnimationFrame(() => onResize(true));

	return { scene, camera, controls, renderer };
}
