import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { TrackChipFactory } from './ar_track_chip_factory.mjs';
import { amountToChipStacks } from './ar_chip_amount.mjs';

const FELT_COLOR = 0x243d6b;
const FELT_DEEP = 0x1a2f4f;
const GOLD = 0xd4af37;
const RAIL_COLOR = 0x3d2817;

/** Вертикальная раскладка сукна (+Y — к Bet). */
const TABLE_LAYOUT = {
	BET_Y: 5.65,
	ANTE_Y: 4.15,
	BONUS_Y: 2.05,
	BONUS_R: 1.0,
	CARDS_Y: -2.55,
	CARD_H: 2.45,
};

function cardRowHalfSpacing(cardH, gap = 0.14) {
	/** Центр верхнего/нижнего ряда: без наложения краёv карт. */
	return (cardH + gap) / 2;
}

const BONUS_CENTER = { x: 0, y: TABLE_LAYOUT.BONUS_Y };
const BONUS_CHIP_SCALE = 0.58;
const BONUS_CAMERA_STORAGE_KEY = 'poker_bonus_camera';

function makeZoneLabelTexture(label, amount) {
	const width = 512;
	const height = 256;
	const canvas = document.createElement('canvas');
	canvas.width = width;
	canvas.height = height;
	const ctx = canvas.getContext('2d');
	ctx.fillStyle = '#d4af37';
	ctx.textAlign = 'center';
	ctx.textBaseline = 'middle';
	const showAmount = amount !== null && amount !== undefined && amount !== '';
	if (showAmount) {
		ctx.font = 'bold 72px sans-serif';
		ctx.fillText(String(label).toUpperCase(), width / 2, height * 0.34);
		ctx.font = 'bold 108px sans-serif';
		ctx.fillText(String(amount), width / 2, height * 0.72);
	} else {
		ctx.font = 'bold 88px sans-serif';
		ctx.fillText(String(label).toUpperCase(), width / 2, height / 2);
	}
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
	const parts = [
		[w, t, cx, cy + hh - t / 2],
		[w, t, cx, cy - hh + t / 2],
		[t, h, cx - hw + t / 2, cy],
		[t, h, cx + hw - t / 2, cy],
	];
	for (const [pw, ph, px, py] of parts) {
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

function addZoneLabel(group, label, amount, cx, cy, w, h, z) {
	const plane = new THREE.Mesh(
		new THREE.PlaneGeometry(w, h),
		new THREE.MeshBasicMaterial({
			map: makeZoneLabelTexture(label, amount),
			transparent: true,
			side: THREE.DoubleSide,
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

function buildBettingZones(group, config) {
	const zones = new THREE.Group();
	const zLine = 0.04;
	const zLabel = 0.06;
	const lineT = 0.07;

	addGoldRectFrame(zones, 0, TABLE_LAYOUT.BET_Y, 5.2, 1.35, zLine, lineT);
	addZoneLabel(zones, 'Bet', null, 0, TABLE_LAYOUT.BET_Y, 4.6, 1.1, zLabel);

	addGoldRectFrame(zones, 0, TABLE_LAYOUT.ANTE_Y, 4.4, 1.15, zLine, lineT);
	addZoneLabel(zones, 'Ante', null, 0, TABLE_LAYOUT.ANTE_Y, 3.8, 0.95, zLabel);

	addGoldCircleFrame(zones, BONUS_CENTER.x, BONUS_CENTER.y, TABLE_LAYOUT.BONUS_R, zLine, lineT);
	addZoneLabel(zones, 'Bonus', null, BONUS_CENTER.x, BONUS_CENTER.y, 1.75, 1.75, zLabel);

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

function splitDenomGroups(denomArray) {
	const groups = [];
	for (let i = 0; i < denomArray.length; ) {
		const denom = denomArray[i];
		let j = i + 1;
		while (j < denomArray.length && denomArray[j] === denom) j++;
		groups.push({ denom, count: j - i });
		i = j;
	}
	return groups;
}

function stacksToDenomArray(stacks) {
	const arr = [];
	for (const stack of stacks) {
		for (let i = 0; i < stack.count; i++) arr.push(stack.denomination);
	}
	return arr;
}

/** Раскладка фишек как в AR «Заставки 2+», с масштабом под стол Bonus. */
function createBonusChipLayout(scale) {
	const chipStep = 0.35 * scale;
	const spawnZ = 0.175 * scale;
	const ladderStep = 0.3 * scale;
	const denomCacheGap = ladderStep * 2;
	const chip11OffsetX = 0.3 * scale;
	const firstLadderOffset = 0.6 * scale;
	const zastavkiRotMin = 0.24;
	const zastavkiRotRange = 0.56;
	const zastavkiRotZ = () => zastavkiRotMin + Math.random() * zastavkiRotRange;

	function buildCachePlacements(count, bx, by, ySign, xSign, zStart) {
		const placements = [];
		let lastX = bx;
		let lastY = by;
		let lastZ = zStart;
		let endDirY = ySign;
		if (count <= 0) {
			return { placements, lastX, lastY, lastZ, endDirY };
		}
		let zIdx = 0;
		function nextZ() {
			const z = zStart + chipStep * zIdx;
			zIdx += 1;
			return z;
		}
		function place(x, y, rotZ, fixedZ) {
			const z = fixedZ !== undefined ? fixedZ : nextZ();
			placements.push({ x, y, z, rotZ });
			lastX = x;
			lastY = y;
			lastZ = z;
		}
		const rz = () => zastavkiRotZ();
		const ladderYs = (d) => by + d;
		const ys = (d) => by + ySign * d;
		const n = count;
		const col1 = Math.min(n, 10);
		const isStack = col1 >= 5;
		const isLadder = col1 >= 2 && col1 <= 4;
		place(bx, by, rz());
		if (col1 >= 2 && (isStack || isLadder)) {
			if (isStack) place(bx, by, rz());
			else place(bx, ladderYs(ladderStep), rz());
		}
		if (col1 >= 3 && (isStack || isLadder)) {
			if (isStack) place(bx, by, rz());
			else place(bx, ladderYs(ladderStep * 2), rz());
		}
		if (col1 >= 4 && (isStack || isLadder)) {
			if (isStack) place(bx, by, rz());
			else place(bx, ladderYs(ladderStep * 3), rz());
		}
		if (col1 >= 5) place(bx, by, rz());
		if (col1 >= 6 && col1 < 10) place(bx, ladderYs(firstLadderOffset), rz());
		if (col1 >= 7 && col1 < 10) place(bx, ladderYs(firstLadderOffset + ladderStep), rz());
		if (col1 >= 8 && col1 < 10) place(bx, ladderYs(firstLadderOffset + ladderStep * 2), rz());
		if (col1 >= 9 && col1 < 10) place(bx, ladderYs(firstLadderOffset + ladderStep * 3), rz());
		if (col1 === 10) {
			const yTen = ladderYs(firstLadderOffset);
			for (let k = 0; k < 5; k++) place(bx, yTen, rz());
		}
		if (n >= 15) {
			const zStack = [spawnZ + chipStep * 10, spawnZ + chipStep * 11, spawnZ + chipStep * 12, spawnZ + chipStep * 13, spawnZ + chipStep * 14];
			for (let k = 0; k < 5; k++) place(bx, by, rz(), zStack[k]);
		} else {
			if (n >= 11) place(bx + xSign * chip11OffsetX, by, rz());
			if (n >= 12) place(bx + xSign * chip11OffsetX, ys(chipStep), rz());
			if (n >= 13) place(bx + xSign * chip11OffsetX, ys(chipStep * 2), rz());
			if (n >= 14) place(bx + xSign * chip11OffsetX, ys(chipStep * 3), rz());
		}
		if (n >= 16) {
			if (n === 20) {
				for (let j = 16; j <= 20; j++) place(bx, ladderYs(firstLadderOffset), rz());
			} else {
				for (let j = 16; j <= n; j++) {
					const rung = j <= 19 ? j - 16 : 3;
					const dy = firstLadderOffset + rung * ladderStep;
					place(bx, ladderYs(dy), rz());
				}
			}
		}
		if (isLadder || (col1 >= 6 && col1 <= 9) || col1 === 10 || n >= 16) {
			endDirY = 1;
		} else if (n >= 11 && n <= 14) {
			endDirY = ySign;
		} else if (col1 <= 5) {
			endDirY = ySign;
		}
		return { placements, lastX, lastY, lastZ, endDirY };
	}

	function resolveDenomCacheSigns(g, groups, lowerEndDirY) {
		if (g === 0) return { ySign: 1, xSign: 1 };
		const firstCount = groups[0].count;
		if (firstCount <= 5) {
			const away = g % 2 === 1;
			if (away) {
				return { ySign: 1, xSign: lowerEndDirY === -1 ? -1 : 1 };
			}
			return { ySign: -1, xSign: 1 };
		}
		if (g === 1) return { ySign: -1, xSign: 1 };
		if (lowerEndDirY === 1) return { ySign: -1, xSign: 1 };
		return { ySign: 1, xSign: -1 };
	}

	function drawPositionDenomCaches(denomArray, bx, by, addChip) {
		const groups = splitDenomGroups(denomArray);
		let anchorX = bx;
		let anchorY = by;
		let zBase = spawnZ;
		let lowerEndDirY = 1;
		for (let g = 0; g < groups.length; g++) {
			const signs = resolveDenomCacheSigns(g, groups, lowerEndDirY);
			const ySign = signs.ySign;
			const xSign = signs.xSign;
			if (g > 0) anchorY += ySign * denomCacheGap;
			const plan = buildCachePlacements(groups[g].count, anchorX, anchorY, ySign, xSign, zBase);
			for (const pl of plan.placements) {
				addChip(groups[g].denom, pl.x, pl.y, pl.z, pl.rotZ);
			}
			lowerEndDirY = plan.endDirY;
			anchorX = plan.lastX;
			anchorY = plan.lastY;
			zBase = plan.lastZ + chipStep;
		}
	}

	return { drawPositionDenomCaches, spawnZ };
}

function buildBonusChips(group, bonusBet) {
	const amount = Math.max(0, Math.round(Number(bonusBet) || 0));
	if (amount <= 0) return;

	const factory = new TrackChipFactory(BONUS_CHIP_SCALE);
	const layout = createBonusChipLayout(BONUS_CHIP_SCALE);
	const chipsGroup = new THREE.Group();
	chipsGroup.name = 'bonus-chips';

	const addChip = (denom, x, y, z, rotZ) => addChipAt(chipsGroup, factory, denom, x, y, z, rotZ);
	layout.drawPositionDenomCaches(
		stacksToDenomArray(amountToChipStacks(amount)),
		BONUS_CENTER.x,
		BONUS_CENTER.y,
		addChip
	);

	group.add(chipsGroup);
}

const RANKS_ASC = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
const WHEEL_RANKS = ['A', '2', '3', '4', '5'];

function rankIdx(rank) {
	const i = RANKS_ASC.indexOf(rank);
	return i >= 0 ? i : 0;
}

function isWheelStraight(cards) {
	const ranks = new Set(cards.map((c) => c.rank));
	return ranks.size === 5 && WHEEL_RANKS.every((r) => ranks.has(r));
}

/** Слева направо: 2…K, туз последний; wheel A-2-3-4-5 — туз первый. */
function sortStraightLine(cards) {
	if (isWheelStraight(cards)) {
		return [...cards].sort(
			(a, b) => WHEEL_RANKS.indexOf(a.rank) - WHEEL_RANKS.indexOf(b.rank)
		);
	}
	return [...cards].sort((a, b) => rankIdx(a.rank) - rankIdx(b.rank));
}

function sortAceLast(cards) {
	return [...cards].sort((a, b) => rankIdx(a.rank) - rankIdx(b.rank));
}

function countByRank(cards) {
	const counts = new Map();
	for (const card of cards) {
		counts.set(card.rank, (counts.get(card.rank) || 0) + 1);
	}
	return counts;
}

function orderHandForCombo(hand, combo) {
	const cards = hand.slice();
	switch (combo) {
		case 'Роял-флеш':
		case 'Стрит-флеш':
		case 'Стрит':
			return sortStraightLine(cards);
		case 'Флеш':
			return sortAceLast(cards);
		case 'Каре': {
			const counts = countByRank(cards);
			const quadRank = [...counts.entries()].find(([, n]) => n === 4)[0];
			const kicker = cards.find((c) => c.rank !== quadRank);
			return [...cards.filter((c) => c.rank === quadRank), kicker];
		}
		case 'Фул-хаус': {
			const counts = countByRank(cards);
			const tripRank = [...counts.entries()].find(([, n]) => n === 3)[0];
			const pairRank = [...counts.entries()].find(([, n]) => n === 2)[0];
			return [
				...cards.filter((c) => c.rank === tripRank),
				...cards.filter((c) => c.rank === pairRank),
			];
		}
		case 'Сет': {
			const counts = countByRank(cards);
			const setRank = [...counts.entries()].find(([, n]) => n === 3)[0];
			const kickers = sortAceLast(cards.filter((c) => c.rank !== setRank));
			return [...cards.filter((c) => c.rank === setRank), ...kickers];
		}
		case 'Две пары': {
			const counts = countByRank(cards);
			const pairRanks = [...counts.entries()]
				.filter(([, n]) => n === 2)
				.map(([rank]) => rank)
				.sort((a, b) => rankIdx(a) - rankIdx(b));
			const kicker = cards.find((c) => counts.get(c.rank) === 1);
			const ordered = [];
			for (const rank of pairRanks) {
				ordered.push(...cards.filter((c) => c.rank === rank));
			}
			ordered.push(kicker);
			return ordered;
		}
		default:
			return sortAceLast(cards);
	}
}

function cardKey(card) {
	return `${card.rank}_${card.suit}_${card.img}`;
}

function widthForCard(hand, card, cardWidths) {
	const idx = hand.findIndex(
		(c) => c.rank === card.rank && c.suit === card.suit && c.img === card.img
	);
	return idx >= 0 ? cardWidths[idx] : cardWidths[0];
}

function parseTwoPairs(hand) {
	const counts = countByRank(hand);
	const pairRanks = [...counts.entries()]
		.filter(([, n]) => n === 2)
		.map(([rank]) => rank)
		.sort((a, b) => rankIdx(a) - rankIdx(b));
	const lowPair = hand.filter((c) => c.rank === pairRanks[0]);
	const highPair = hand.filter((c) => c.rank === pairRanks[1]);
	const kicker = hand.find((c) => counts.get(c.rank) === 1);
	return { lowPair, highPair, kicker };
}

function parseSet(hand) {
	const counts = countByRank(hand);
	const setRank = [...counts.entries()].find(([, n]) => n === 3)[0];
	const setCards = hand.filter((c) => c.rank === setRank);
	const kickers = sortAceLast(hand.filter((c) => c.rank !== setRank));
	return { setCards, kickers };
}

function parseFullHouse(hand) {
	const counts = countByRank(hand);
	const tripRank = [...counts.entries()].find(([, n]) => n === 3)[0];
	const pairRank = [...counts.entries()].find(([, n]) => n === 2)[0];
	return {
		trips: hand.filter((c) => c.rank === tripRank),
		pair: hand.filter((c) => c.rank === pairRank),
	};
}

function parseQuads(hand) {
	const counts = countByRank(hand);
	const quadRank = [...counts.entries()].find(([, n]) => n === 4)[0];
	return {
		quads: hand.filter((c) => c.rank === quadRank),
		kicker: hand.find((c) => c.rank !== quadRank),
	};
}

function rowCardXs(cards, hand, cardWidths, hGap) {
	const widths = cards.map((c) => widthForCard(hand, c, cardWidths));
	const rowW = widths.reduce((sum, w) => sum + w, 0) + hGap * Math.max(0, cards.length - 1);
	let x = -rowW / 2;
	return cards.map((card, i) => {
		const cx = x + widths[i] / 2;
		x += widths[i] + (i < cards.length - 1 ? hGap : 0);
		return { card, x: cx, w: widths[i] };
	});
}

/**
 * @returns {{ card: object, x: number, y: number, z: number }[]}
 */
function computeCardPlacements(hand, combo, cardWidths, centerY, cardH) {
	const hGap = 0.16;
	const rowDy = cardRowHalfSpacing(cardH);
	const sideGap = 0.26;

	if (combo === 'Две пары') {
		const { lowPair, highPair, kicker } = parseTwoPairs(hand);
		const highRow = rowCardXs(highPair, hand, cardWidths, hGap);
		const lowRow = rowCardXs(lowPair, hand, cardWidths, hGap);
		const mainHalfW = Math.max(
			highRow[highRow.length - 1].x + highRow[highRow.length - 1].w / 2,
			lowRow[lowRow.length - 1].x + lowRow[lowRow.length - 1].w / 2
		);
		const kickerW = widthForCard(hand, kicker, cardWidths);
		const kickerX = mainHalfW + sideGap + kickerW / 2;
		return [
			...highRow.map((slot, i) => ({ card: slot.card, x: slot.x, y: centerY + rowDy, z: i })),
			...lowRow.map((slot, i) => ({ card: slot.card, x: slot.x, y: centerY - rowDy, z: i + 2 })),
			{ card: kicker, x: kickerX, y: centerY, z: 4 },
		];
	}

	if (combo === 'Сет') {
		const { setCards, kickers } = parseSet(hand);
		const topRow = rowCardXs(setCards, hand, cardWidths, hGap);
		const leftX = topRow[0].x;
		const rightX = topRow[2].x;
		const [lowKicker, highKicker] = kickers;
		return [
			...topRow.map((slot, i) => ({ card: slot.card, x: slot.x, y: centerY + rowDy, z: i })),
			{ card: lowKicker, x: leftX, y: centerY - rowDy, z: 3 },
			{ card: highKicker, x: rightX, y: centerY - rowDy, z: 4 },
		];
	}

	if (combo === 'Фул-хаус') {
		const { trips, pair } = parseFullHouse(hand);
		const topRow = rowCardXs(trips, hand, cardWidths, hGap);
		const bottomRow = rowCardXs(pair, hand, cardWidths, hGap);
		return [
			...topRow.map((slot, i) => ({ card: slot.card, x: slot.x, y: centerY + rowDy, z: i })),
			...bottomRow.map((slot, i) => ({ card: slot.card, x: slot.x, y: centerY - rowDy, z: i + 3 })),
		];
	}

	if (combo === 'Каре') {
		const { quads, kicker } = parseQuads(hand);
		const topRow = rowCardXs(quads, hand, cardWidths, hGap);
		return [
			...topRow.map((slot, i) => ({ card: slot.card, x: slot.x, y: centerY + rowDy, z: i })),
			{ card: kicker, x: 0, y: centerY - rowDy, z: 4 },
		];
	}

	const ordered = orderHandForCombo(hand, combo);
	const line = rowCardXs(ordered, hand, cardWidths, hGap);
	return line.map((slot, i) => ({ card: slot.card, x: slot.x, y: centerY, z: i }));
}

function loadCardTextures(hand, cardsBaseUrl, maxAnisotropy) {
	const loader = new THREE.TextureLoader();
	return Promise.all(
		hand.map((card) => {
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

function buildCards(group, hand, combo, cardsBaseUrl, renderer) {
	const cardsGroup = new THREE.Group();
	cardsGroup.name = 'cards';
	group.add(cardsGroup);

	const cardH = TABLE_LAYOUT.CARD_H;
	const centerY = TABLE_LAYOUT.CARDS_Y;
	const maxAnisotropy = renderer?.capabilities?.getMaxAnisotropy?.() || 8;

	return loadCardTextures(hand, cardsBaseUrl, maxAnisotropy).then((loaded) => {
		const cardWidths = loaded.map(({ tex }) => {
			const img = tex.image;
			const aspect = img && img.width && img.height ? img.width / img.height : 75 / 110;
			return cardH * aspect;
		});
		const texByKey = new Map(loaded.map(({ card, tex }) => [cardKey(card), tex]));

		const placements = computeCardPlacements(hand, combo, cardWidths, centerY, cardH);
		const meshes = [];

		placements.forEach((pl, i) => {
			const tex = texByKey.get(cardKey(pl.card));
			if (!tex) return;

			const cardW = widthForCard(hand, pl.card, cardWidths);
			const cardGroup = new THREE.Group();
			cardGroup.position.set(pl.x, pl.y, 0.14 + pl.z * 0.02);

			const border = 0.05;
			const back = new THREE.Mesh(
				new THREE.PlaneGeometry(cardW + border, cardH + border),
				new THREE.MeshBasicMaterial({ color: 0xf5f5f5 })
			);
			back.position.z = -0.01;
			cardGroup.add(back);

			const mesh = new THREE.Mesh(
				new THREE.PlaneGeometry(cardW, cardH),
				new THREE.MeshBasicMaterial({
					map: tex,
					transparent: true,
					depthWrite: true,
				})
			);
			mesh.userData.cardIndex = i;
			mesh.userData.cardName = pl.card.name || '';
			mesh.userData.cardGroup = cardGroup;
			cardGroup.add(mesh);
			cardsGroup.add(cardGroup);
			meshes.push(mesh);
		});

		return meshes;
	});
}

function setupCardSwap(canvas, camera, cardMeshes) {
	if (!cardMeshes.length) return;

	const raycaster = new THREE.Raycaster();
	const pointer = new THREE.Vector2();
	let selected = null;

	function clearSelection() {
		if (!selected) return;
		selected.material.color.setHex(0xffffff);
		selected = null;
	}

	canvas.addEventListener('pointerdown', (event) => {
		const rect = canvas.getBoundingClientRect();
		pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
		pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
		raycaster.setFromCamera(pointer, camera);
		const hits = raycaster.intersectObjects(cardMeshes, false);
		if (!hits.length) {
			clearSelection();
			return;
		}
		const hit = hits[0].object;
		if (selected === null) {
			selected = hit;
			selected.material.color.setHex(0xffe8a3);
		} else if (selected === hit) {
			clearSelection();
		} else {
			const aGroup = selected.userData.cardGroup;
			const bGroup = hit.userData.cardGroup;
			const aPos = aGroup.position.clone();
			const bPos = bGroup.position.clone();
			aGroup.position.copy(bPos);
			bGroup.position.copy(aPos);
			const aIdx = selected.userData.cardIndex;
			const bIdx = hit.userData.cardIndex;
			selected.userData.cardIndex = bIdx;
			hit.userData.cardIndex = aIdx;
			clearSelection();
		}
	});
}

export function initOasisBonusScene(canvas, config) {
	if (!canvas) throw new Error('canvas not found');

	let containerW = canvas.parentElement ? canvas.parentElement.clientWidth : 0;
	let containerH = canvas.parentElement ? canvas.parentElement.clientHeight : 0;
	if (!containerW || containerW < 100) containerW = 640;
	if (!containerH || containerH < 100) containerH = 360;

	const scene = new THREE.Scene();
	scene.background = new THREE.Color(0x1a1a1a);

	const aspect = containerW / containerH;
	const camera = new THREE.PerspectiveCamera(48, aspect, 0.1, 200);
	const cameraHomePos = { x: 0, y: -13.5, z: 10.5 };
	const cameraHomeTarget = { x: 0, y: 1.2, z: 0 };
	camera.position.set(cameraHomePos.x, cameraHomePos.y, cameraHomePos.z);
	camera.lookAt(cameraHomeTarget.x, cameraHomeTarget.y, cameraHomeTarget.z);

	const controls = new OrbitControls(camera, canvas);
	controls.target.set(cameraHomeTarget.x, cameraHomeTarget.y, cameraHomeTarget.z);
	controls.enableDamping = true;
	controls.dampingFactor = 0.05;
	controls.maxPolarAngle = Math.PI * 0.92;
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
			const raw = sessionStorage.getItem(BONUS_CAMERA_STORAGE_KEY);
			if (!raw) return;
			const o = JSON.parse(raw);
			if (o?.position && o?.target) {
				camera.position.set(o.position.x, o.position.y, o.position.z);
				controls.target.set(o.target.x, o.target.y, o.target.z);
				controls.update();
			}
		} catch (_) {}
	}

	function saveCamera() {
		try {
			sessionStorage.setItem(
				BONUS_CAMERA_STORAGE_KEY,
				JSON.stringify({
					position: { x: camera.position.x, y: camera.position.y, z: camera.position.z },
					target: { x: controls.target.x, y: controls.target.y, z: controls.target.z },
				})
			);
		} catch (_) {}
	}

	controls.addEventListener('end', saveCamera);
	tryApplySavedCamera();

	const payoutForm = canvas.closest('form');
	if (payoutForm) {
		payoutForm.addEventListener('submit', saveCamera);
	}

	const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
	if (!renderer.getContext()) {
		canvas.parentElement?.insertAdjacentHTML(
			'beforeend',
			'<p style="color:#e11;padding:16px;margin:0;">WebGL не доступен. Обновите браузер или включите аппаратное ускорение.</p>'
		);
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
	buildBettingZones(tableRoot, config);
	buildBonusChips(tableRoot, config.bonusBet);

	buildCards(
		tableRoot,
		config.hand || [],
		config.combo || '',
		config.cardsBaseUrl || '/static/cards/',
		renderer
	).then((meshes) => {
		setupCardSwap(canvas, camera, meshes);
		tryApplySavedCamera();
	});

	let resizeRaf = 0;
	function onResize() {
		cancelAnimationFrame(resizeRaf);
		resizeRaf = requestAnimationFrame(() => {
			const nextW = canvas.parentElement?.clientWidth || 640;
			const nextH = canvas.parentElement?.clientHeight || Math.min(480, Math.floor(nextW * 0.66));
			if (nextW === containerW && nextH === containerH) return;
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

	const resetBtn = document.getElementById('pokerBonusCameraReset');
	if (resetBtn) {
		resetBtn.addEventListener('click', () => {
			camera.position.set(cameraHomePos.x, cameraHomePos.y, cameraHomePos.z);
			controls.target.set(cameraHomeTarget.x, cameraHomeTarget.y, cameraHomeTarget.z);
			controls.update();
			saveCamera();
		});
	}

	function animate() {
		requestAnimationFrame(animate);
		controls.update();
		renderer.render(scene, camera);
	}
	animate();

	return { scene, camera, controls, renderer };
}
