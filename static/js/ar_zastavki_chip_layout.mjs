/** Раскладка фишек как в AR «Заставки 2+» (buildCachePlacements + drawPositionDenomCaches). */

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

export function stacksToDenomArray(stacks) {
	const arr = [];
	for (const stack of stacks) {
		for (let i = 0; i < stack.count; i++) arr.push(stack.denomination);
	}
	return arr;
}

/**
 * @param {number} scale — масштаб фишек (TrackChipFactory)
 * @returns {{ drawPositionDenomCaches: (denomArray: number[], bx: number, by: number, addChip: Function) => void }}
 */
export function createZastavkiChipLayout(scale) {
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
			const zStack = [
				spawnZ + chipStep * 10,
				spawnZ + chipStep * 11,
				spawnZ + chipStep * 12,
				spawnZ + chipStep * 13,
				spawnZ + chipStep * 14,
			];
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

	return { drawPositionDenomCaches };
}
