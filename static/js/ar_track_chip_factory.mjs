import * as THREE from 'three';

/** Цвета по номиналу. 2 — золотая (заставки). 2.5 — фиолетовая (BJ Bonus: Pair). */
export const CHIP_COLORS = {
	2: 0xd4af37,
	2.5: 0x9333ea,
	1: 0x9ca3af,
	5: 0xc41e3a,
	25: 0x15803d,
	100: 0x1c1c1c,
	500: 0xe879a0,
	1000: 0xf0f0f0,
	5000: 0xa855f7
};

const CHIP_LARGE_FROM = 500;
const CHIP_LARGE_SCALE = 1.12;

function chipDenomIsLarge(denomination) {
	return denomination >= CHIP_LARGE_FROM;
}

function chipColorIntToCss(colorInt) {
	return `#${(colorInt >>> 0).toString(16).padStart(6, '0')}`;
}

function makeChipSideStripeTexture(baseColorCss, stripeColorCss) {
	const w = 2048;
	const h = 256;
	const cnv = document.createElement('canvas');
	cnv.width = w;
	cnv.height = h;
	const ctx = cnv.getContext('2d');
	ctx.fillStyle = baseColorCss;
	ctx.fillRect(0, 0, w, h);
	const stripeRatio = 0.03;
	const stripeW = Math.max(10, Math.round(w * stripeRatio));
	const cardinals = [0, 0.25, 0.5, 0.75];
	ctx.fillStyle = stripeColorCss;
	for (const t of cardinals) {
		const x = Math.round(t * w);
		ctx.fillRect((x - stripeW / 2 + w) % w, 0, stripeW, h);
		if (x - stripeW / 2 < 0) {
			ctx.fillRect(w + (x - stripeW / 2), 0, stripeW, h);
		}
	}
	const tex = new THREE.CanvasTexture(cnv);
	tex.colorSpace = THREE.SRGBColorSpace;
	tex.wrapS = THREE.RepeatWrapping;
	tex.wrapT = THREE.ClampToEdgeWrapping;
	tex.generateMipmaps = false;
	tex.minFilter = THREE.LinearFilter;
	tex.magFilter = THREE.NearestFilter;
	tex.anisotropy = 8;
	tex.needsUpdate = true;
	return tex;
}

function makeChipCapStripeTexture(baseColorCss, stripeColorCss) {
	const size = 1024;
	const cnv = document.createElement('canvas');
	cnv.width = size;
	cnv.height = size;
	const ctx = cnv.getContext('2d');
	const cx = size / 2;
	const cy = size / 2;
	ctx.fillStyle = baseColorCss;
	ctx.fillRect(0, 0, size, size);
	ctx.fillStyle = stripeColorCss;
	const stripeRatio = 0.03;
	const lineLen = Math.round(size * 0.2);
	const r = Math.round(size * 0.41);
	const lineW = Math.max(10, Math.round(r * 2 * Math.PI * stripeRatio));
	ctx.fillRect(cx - lineW / 2, cy - r - lineLen, lineW, lineLen);
	ctx.fillRect(cx - lineW / 2, cy + r, lineW, lineLen);
	ctx.fillRect(cx - r - lineLen, cy - lineW / 2, lineLen, lineW);
	ctx.fillRect(cx + r, cy - lineW / 2, lineLen, lineW);
	const rimLen = Math.round(size * 0.11);
	const rOuter = Math.round(size * 0.48);
	ctx.fillRect(cx - lineW / 2, cy - rOuter, lineW, rimLen);
	ctx.fillRect(cx - lineW / 2, cy + rOuter - rimLen, lineW, rimLen);
	ctx.fillRect(cx - rOuter, cy - lineW / 2, rimLen, lineW);
	ctx.fillRect(cx + rOuter - rimLen, cy - lineW / 2, rimLen, lineW);
	const tex = new THREE.CanvasTexture(cnv);
	tex.colorSpace = THREE.SRGBColorSpace;
	tex.generateMipmaps = false;
	tex.minFilter = THREE.LinearFilter;
	tex.magFilter = THREE.NearestFilter;
	tex.anisotropy = 8;
	tex.needsUpdate = true;
	return tex;
}

function badgeTextColor(label) {
	if (String(label) === '100' || String(label) === '25' || String(label) === '5' || String(label) === '2') {
		return '#000000';
	}
	if (String(label) === '1000') {
		return '#ffffff';
	}
	if (String(label) === '2.5') {
		return '#000000';
	}
	return '#000000';
}

function makeChipTopFaceBadgeTexture(label, baseColorCss) {
	const size = 1024;
	const cnv = document.createElement('canvas');
	cnv.width = size;
	cnv.height = size;
	const ctx = cnv.getContext('2d');
	const cx = size / 2;
	const cy = size / 2;
	ctx.fillStyle = baseColorCss;
	ctx.fillRect(0, 0, size, size);
	const stripeRatio = 0.03;
	const lineW = Math.max(10, Math.round(Math.round(size * 0.41) * 2 * Math.PI * stripeRatio));
	const lineLen = Math.round(size * 0.18);
	const r = Math.round(size * 0.41);
	ctx.fillStyle = String(label) === '1000' ? '#000000' : '#ffffff';
	ctx.fillRect(cx - lineW / 2, cy - r - lineLen, lineW, lineLen);
	ctx.fillRect(cx - lineW / 2, cy + r, lineW, lineLen);
	ctx.fillRect(cx - r - lineLen, cy - lineW / 2, lineLen, lineW);
	ctx.fillRect(cx + r, cy - lineW / 2, lineLen, lineW);
	const rBadge = Math.round(size * 0.34);
	ctx.beginPath();
	ctx.arc(cx, cy, rBadge, 0, Math.PI * 2);
	ctx.closePath();
	ctx.fillStyle = String(label) === '1000' ? '#000000' : '#ffffff';
	ctx.fill();
	ctx.lineWidth = Math.max(2, Math.round(size * 0.008));
	ctx.strokeStyle = 'rgba(0,0,0,0.35)';
	ctx.stroke();
	ctx.fillStyle = badgeTextColor(label);
	const isThreeDigits = String(label).length >= 3;
	const fs = isThreeDigits ? Math.round(size * 0.28) : Math.round(size * 0.34);
	ctx.font = `800 ${fs}px system-ui, -apple-system, "Segoe UI", sans-serif`;
	ctx.textAlign = 'center';
	ctx.textBaseline = 'middle';
	ctx.save();
	ctx.translate(cx, cy);
	ctx.rotate(Math.PI / 2);
	ctx.fillText(String(label), 0, 0);
	ctx.restore();
	const tex = new THREE.CanvasTexture(cnv);
	tex.colorSpace = THREE.SRGBColorSpace;
	tex.generateMipmaps = false;
	tex.minFilter = THREE.LinearFilter;
	tex.magFilter = THREE.NearestFilter;
	tex.anisotropy = 8;
	tex.needsUpdate = true;
	return tex;
}

const STRIPED_DENOMS = new Set([1, 2, 2.5, 5, 25, 100, 500, 1000, 5000]);

export class TrackChipFactory {
	constructor(chipScaleK) {
		const r0 = 1.5 * chipScaleK;
		const h0 = 0.35 * chipScaleK;
		this.hSmall = h0;
		this.hLarge = h0 * CHIP_LARGE_SCALE;
		this.geomSmall = new THREE.CylinderGeometry(r0, r0, h0, 32);
		this.geomLarge = new THREE.CylinderGeometry(
			r0 * CHIP_LARGE_SCALE,
			r0 * CHIP_LARGE_SCALE,
			h0 * CHIP_LARGE_SCALE,
			32
		);
		this._materials = new Map();
		this._materialTriples = new Map();
		this._baseMat = {
			metalness: 0.12,
			roughness: 0.48,
			polygonOffset: true,
			polygonOffsetFactor: -1,
			polygonOffsetUnits: -1
		};
	}

	getMaterial(denomination) {
		if (!(denomination in CHIP_COLORS)) {
			throw new Error(`Unknown chip denomination: ${denomination}`);
		}
		if (!this._materials.has(denomination)) {
			const rough = denomination === 1000 ? 0.55 : this._baseMat.roughness;
			const mat = new THREE.MeshStandardMaterial({
				...this._baseMat,
				color: CHIP_COLORS[denomination],
				roughness: rough
			});
			this._materials.set(denomination, mat);
		}
		return this._materials.get(denomination);
	}

	setDenomTexture(denomination, texture) {
		if (texture) texture.colorSpace = THREE.SRGBColorSpace;
		const m = this.getMaterial(denomination);
		m.map = texture;
		m.needsUpdate = true;
	}

	chipHeight(denomination) {
		return chipDenomIsLarge(denomination) ? this.hLarge : this.hSmall;
	}

	spawnZ(denomination, labelZ) {
		return labelZ + this.chipHeight(denomination) / 2 + 0.008;
	}

	createMesh(denomination) {
		const geom = chipDenomIsLarge(denomination) ? this.geomLarge : this.geomSmall;
		let material = this.getMaterial(denomination);
		if (STRIPED_DENOMS.has(denomination)) {
			if (!this._materialTriples.has(denomination)) {
				const isWhiteStripe =
					denomination === 1 ||
					denomination === 100 ||
					denomination === 25 ||
					denomination === 5 ||
					denomination === 2;
				const stripeColorCss = isWhiteStripe ? '#ffffff' : '#0a0a0a';
				const emissiveColor = isWhiteStripe ? 0xffffff : 0x000000;
				const capEmissiveIntensity = isWhiteStripe ? 0.45 : 0.0;
				const sideEmissiveIntensity = isWhiteStripe ? 0.55 : 0.0;
				const baseCss = chipColorIntToCss(CHIP_COLORS[denomination]);
				const sideTex = makeChipSideStripeTexture(baseCss, stripeColorCss);
				const capTex = makeChipCapStripeTexture(baseCss, stripeColorCss);
				const topTex = makeChipTopFaceBadgeTexture(denomination, baseCss);
				const bottomTex = topTex;
				const capEmissiveMap = denomination === 100 ? null : capTex;
				const capEmissive = denomination === 100 ? 0x000000 : emissiveColor;
				const capEmissivePower = denomination === 100 ? 0.0 : capEmissiveIntensity;
				const top = new THREE.MeshStandardMaterial({
					...this._baseMat,
					color: 0xffffff,
					roughness: 0.58,
					map: topTex,
					emissive: 0x000000,
					emissiveMap: null,
					emissiveIntensity: 0.0
				});
				const bottom = new THREE.MeshStandardMaterial({
					...this._baseMat,
					color: 0xffffff,
					roughness: 0.58,
					map: bottomTex,
					emissive: 0x000000,
					emissiveMap: null,
					emissiveIntensity: 0.0
				});
				const side = new THREE.MeshStandardMaterial({
					...this._baseMat,
					color: CHIP_COLORS[denomination],
					roughness: 0.52,
					map: sideTex,
					emissive: emissiveColor,
					emissiveMap: sideTex,
					emissiveIntensity: sideEmissiveIntensity
				});
				this._materialTriples.set(denomination, [side, top, bottom]);
			}
			material = this._materialTriples.get(denomination);
		}
		const mesh = new THREE.Mesh(geom, material);
		mesh.rotation.x = -Math.PI / 2;
		mesh.userData.denomination = denomination;
		mesh.renderOrder = 3;
		mesh.name = `track-chip-${denomination}`;
		return mesh;
	}
}
