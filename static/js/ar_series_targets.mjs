import { getRouletteTableGeometry } from './ar_roulette_table.mjs';

const HIT_RADIUS = 3.2;

/**
 * Цели: id, x, y в системе координат поля, chips — сколько фишек должно быть в радиусе.
 */
export function buildSeriesTargets() {
	const g = getRouletteTableGeometry();
	const {
		cx0, cx1, cx2, cx3, cy0, cy1, cy2, halfW, halfH, splitCenter, BLOCK_WIDTH: B,
		zeroSplitX, xBound12, xBound23, zeroTrioY12
	} = g;

	return {
		zero: [
			{ id: 'split 0-3', x: zeroSplitX, y: cy2, chips: 1 },
			{ id: 'split 12-15', x: xBound12, y: cy2, chips: 1 },
			/* 32 col2 row1, 35 col3 row1 — вертикаль между кол.2 и 3 */
			{ id: 'split 32-35', x: cx2 + halfW + splitCenter + 2 * B, y: cy1, chips: 1 },
			{ id: '26', x: cx0 + 2 * B, y: cy1, chips: 1 }
		],
		tiers: [
			{ id: 'split 5-8', x: cx1 + halfW + splitCenter, y: cy1, chips: 1 },
			{ id: 'split 10-11', x: cx3, y: cy0 + halfH + splitCenter, chips: 1 },
			{ id: 'split 13-16', x: cx0 + halfW + splitCenter + B, y: cy0, chips: 1 },
			{ id: 'split 23-24', x: cx3 + B, y: cy1 + halfH + splitCenter, chips: 1 },
			{ id: 'split 27-30', x: cx0 + halfW + splitCenter + 2 * B, y: cy2, chips: 1 },
			{ id: 'split 33-36', x: cx2 + halfW + splitCenter + 2 * B, y: cy2, chips: 1 }
		],
		orphelins: [
			{ id: '1', x: cx0, y: cy0, chips: 1 },
			{ id: 'split 6-9', x: cx1 + halfW + splitCenter, y: cy2, chips: 1 },
			{ id: 'split 14-17', x: cx0 + halfW + splitCenter + B, y: cy1, chips: 1 },
			{ id: 'split 17-20', x: cx1 + halfW + splitCenter + B, y: cy1, chips: 1 },
			/* 31 col2 row0, 34 col3 row0 — граница кол.2–3, не cx1 */
			{ id: 'split 31-34', x: cx2 + halfW + splitCenter + 2 * B, y: cy0, chips: 1 }
		],
		voisins: [
			{ id: 'street 0-2-3', x: zeroSplitX, y: zeroTrioY12, chips: 2 },
			/* 4 col1 row0, 7 col2 row0 — вертикаль между кол.1 и 2 */
			{ id: 'split 4-7', x: cx1 + halfW + splitCenter, y: cy0, chips: 1 },
			/* 12 и 15 — оба row2 по разные стороны стыка дюжин */
			{ id: 'split 12-15', x: xBound12, y: cy2, chips: 1 },
			{ id: 'split 18-21', x: cx1 + halfW + splitCenter + B, y: cy2, chips: 1 },
			{ id: 'split 19-22', x: cx2 + halfW + splitCenter + B, y: cy0, chips: 1 },
			/* 32 col2 row1, 35 col3 row1 — в Voisins; 31–34 только в Orphelins */
			{ id: 'split 32-35', x: cx2 + halfW + splitCenter + 2 * B, y: cy1, chips: 1 },
			{ id: 'corner 25-26-28-29', x: cx0 + halfW + splitCenter + 2 * B, y: cy0 + halfH + splitCenter, chips: 2 }
		]
	};
}

export { HIT_RADIUS };

/** Проверка: каждая фишка в радиусе ровно одной цели, счётчики совпали */
export function validateChipsAgainstTargets(chipList, targets, radius) {
	const r = radius != null ? radius : HIT_RADIUS;
	const need = targets.map(function (t) {
		return { x: t.x, y: t.y, chips: t.chips, got: 0 };
	});
	for (let ci = 0; ci < chipList.length; ci++) {
		const ch = chipList[ci];
		let best = -1;
		let bd = 1e9;
		for (let ti = 0; ti < need.length; ti++) {
			const d = Math.hypot(ch.x - need[ti].x, ch.y - need[ti].y);
			if (d < bd) {
				bd = d;
				best = ti;
			}
		}
		if (bd > r) {
			return { ok: false, reason: 'miss', detail: 'Фишка не на отмеченой позиции' };
		}
		need[best].got++;
	}
	for (let i = 0; i < need.length; i++) {
		if (need[i].got !== need[i].chips) {
			return { ok: false, reason: 'count', detail: 'Неверное число фишек на позиции' };
		}
	}
	return { ok: true };
}
