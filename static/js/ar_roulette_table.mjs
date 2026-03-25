/**
 * Общее построение поля европейской рулетки (сетка + зона 0), как в ar_bets.
 * Материал ячеек клонируется на каждую позицию — можно подсвечивать номера независимо.
 */

/** Углы раскладки (те же константы, что внутри buildArRouletteTable) — для расчёта точек ставок на сериях */
export function getRouletteTableGeometry() {
	const cellW = 8;
	const cellH = 10;
	const gap = 0.3;
	const edge = 0.15;
	const cx0 = cellW / 2;
	const cx1 = cellW + gap + cellW / 2;
	const cx2 = cellW + gap + cellW + gap + cellW / 2;
	const cx3 = cellW + gap + cellW + gap + cellW + gap + cellW / 2;
	const cy0 = cellH / 2;
	const cy1 = cellH + gap + cellH / 2;
	const cy2 = cellH + gap + cellH + gap + cellH / 2;
	const halfW = cellW / 2;
	const halfH = cellH / 2;
	const splitCenter = gap / 2;
	const BLOCK_GAP = 0.3;
	const dozRight = 33.05 - 0.15;
	const BLOCK_WIDTH = dozRight + BLOCK_GAP;
	const zeroSplitX = -0.15;
	const xBound12 = (cx3 + cx0 + BLOCK_WIDTH) / 2;
	const xBound23 = (cx3 + cx0 + 3 * BLOCK_WIDTH) / 2;
	const gridBottom = -edge;
	const gridTop = cellH + gap + cellH + gap + cellH + edge;
	const horzY = [gridBottom, cellH + gap / 2, cellH + gap + cellH + gap / 2, gridTop];
	return {
		cellW,
		cellH,
		gap,
		cx0,
		cx1,
		cx2,
		cx3,
		cy0,
		cy1,
		cy2,
		halfW,
		halfH,
		splitCenter,
		BLOCK_WIDTH,
		zeroSplitX,
		xBound12,
		xBound23,
		horzY,
		zeroTrioY12: horzY[2]
	};
}

export function buildArRouletteTable(THREE, scene, options) {
	const visibleDozens = (options && options.visibleDozens) || [1, 2, 3];

	const whiteStripMat = new THREE.MeshBasicMaterial({
		color: 0xffffff,
		side: THREE.DoubleSide,
		polygonOffset: true,
		polygonOffsetFactor: 1,
		polygonOffsetUnits: 1
	});
	const blueMatTemplate = new THREE.MeshStandardMaterial({ color: 0x2563eb });

	const cellW = 8;
	const cellH = 10;
	const gap = 0.3;
	const edge = 0.15;
	const cornerScale = 0.3;
	const lineDepth = 0.12;

	function makeNumberTexture(num, color) {
		const size = 768;
		const canvas = document.createElement('canvas');
		canvas.width = size;
		canvas.height = size;
		const ctx = canvas.getContext('2d');
		ctx.fillStyle = color || '#ffffff';
		ctx.font = 'bold 576px sans-serif';
		ctx.textAlign = 'center';
		ctx.textBaseline = 'middle';
		ctx.fillText(String(num), size / 2, size / 2);
		const tex = new THREE.CanvasTexture(canvas);
		tex.needsUpdate = true;
		return tex;
	}

	function makeTextTexture(text, color) {
		const width = 1024;
		const height = 256;
		const canvas = document.createElement('canvas');
		canvas.width = width;
		canvas.height = height;
		const ctx = canvas.getContext('2d');
		ctx.fillStyle = color || '#ffffff';
		ctx.font = 'bold 180px sans-serif';
		ctx.textAlign = 'center';
		ctx.textBaseline = 'middle';
		ctx.fillText(String(text), width / 2, height / 2);
		const tex = new THREE.CanvasTexture(canvas);
		tex.needsUpdate = true;
		return tex;
	}

	const DOZEN_CONFIG = {
		1: { numbers: [1, 4, 7, 10, 2, 5, 8, 11, 3, 6, 9, 12], label: '1st Dozen', red: [1, 3, 5, 7, 9, 12] },
		2: { numbers: [13, 16, 19, 22, 14, 17, 20, 23, 15, 18, 21, 24], label: '2nd Dozen', red: [14, 16, 18, 19, 21, 23] },
		3: { numbers: [25, 28, 31, 34, 26, 29, 32, 35, 27, 30, 33, 36], label: '3rd Dozen', red: [25, 27, 30, 32, 34, 36] }
	};

	const BLOCK_GAP = 0.3;
	const dozRight = 33.05 - 0.15;
	const topRectBorderThickness = gap;
	const BLOCK_WIDTH = dozRight + BLOCK_GAP;
	const DOZEN_GAP_FROM_GRID = 0.6;

	const cx0 = cellW / 2;
	const cx1 = cellW + gap + cellW / 2;
	const cx2 = cellW + gap + cellW + gap + cellW / 2;
	const cx3 = cellW + gap + cellW + gap + cellW + gap + cellW / 2;
	const cy0 = cellH / 2;
	const cy1 = cellH + gap + cellH / 2;
	const cy2 = cellH + gap + cellH + gap + cellH / 2;
	const centers = [
		[cx0, cy0], [cx1, cy0], [cx2, cy0], [cx3, cy0],
		[cx0, cy1], [cx1, cy1], [cx2, cy1], [cx3, cy1],
		[cx0, cy2], [cx1, cy2], [cx2, cy2], [cx3, cy2]
	];

	const gridLeft = -edge;
	const gridRight = cellW + gap + cellW + gap + cellW + gap + cellW + edge;
	const gridBottom = -edge;
	const gridTop = cellH + gap + cellH + gap + cellH + edge;
	const vertX = [
		gridLeft,
		cellW + gap / 2,
		cellW + gap + cellW + gap / 2,
		cellW + gap + cellW + gap + cellW + gap / 2,
		gridRight
	];
	const horzY = [gridBottom, cellH + gap / 2, cellH + gap + cellH + gap / 2, gridTop];

	const dozenStripHeight = 36 - (gridTop + DOZEN_GAP_FROM_GRID);
	const dozenRectBottom = gridTop + DOZEN_GAP_FROM_GRID;
	const dozenRectTop = dozenRectBottom + dozenStripHeight;

	function addCell(cx, cy, num, redSet) {
		const mat = blueMatTemplate.clone();
		const cell = new THREE.Mesh(new THREE.PlaneGeometry(cellW, cellH), mat);
		cell.name = 'number ' + num;
		cell.userData.rouletteNumber = num;
		cell.position.set(cx, cy, 0);
		scene.add(cell);

		const isRed = redSet.indexOf(num) !== -1;
		const labelColor = isRed ? '#c00' : '#000';
		const labelMat = new THREE.MeshBasicMaterial({
			map: makeNumberTexture(num, labelColor),
			transparent: true,
			side: THREE.DoubleSide
		});
		const labelPlane = new THREE.Mesh(new THREE.PlaneGeometry(7.2, 7.2), labelMat);
		labelPlane.position.set(cx, cy, 0.02);
		labelPlane.rotation.z = Math.PI / 2;
		labelPlane.name = 'label ' + num;
		labelPlane.userData.rouletteNumber = num;
		labelPlane.userData.labelBaseColor = labelColor;
		scene.add(labelPlane);
	}

	function createDozenBlock(opts) {
		const offsetX = opts.offsetX || 0;
		const offsetY = opts.offsetY || 0;
		const skipLeftEdge = opts.skipLeftEdge || false;
		const skipRightEdge = opts.skipRightEdge || false;
		const skipRightCorner = opts.skipRightCorner || false;
		const { numbers, label, red } = opts;

		centers.forEach(function (c, i) {
			addCell(c[0] + offsetX, c[1] + offsetY, numbers[i], red);
		});

		const stripZ = 0.002;
		const vertLineH = gridTop - gridBottom;
		const horzLineW = gridRight - gridLeft;

		vertX.forEach(function (x, vi) {
			if (skipLeftEdge && vi === 0) return;
			const line = new THREE.Mesh(new THREE.BoxGeometry(gap, vertLineH, lineDepth), whiteStripMat);
			line.name = 'split';
			line.position.set(x + offsetX, (gridTop + gridBottom) / 2 + offsetY, stripZ);
			scene.add(line);
		});

		const horzYFiltered = horzY.slice(0, -1);
		horzYFiltered.forEach(function (y) {
			const line = new THREE.Mesh(new THREE.BoxGeometry(horzLineW, gap, lineDepth), whiteStripMat);
			line.name = 'split';
			line.position.set((gridLeft + gridRight) / 2 + offsetX, y + offsetY, stripZ);
			scene.add(line);
		});

		const localTopRectBottom = dozenRectBottom;
		const localTop = dozenRectTop;
		const rectShape = new THREE.Shape();
		rectShape.moveTo(offsetX, localTopRectBottom + offsetY);
		rectShape.lineTo(offsetX + dozRight, localTopRectBottom + offsetY);
		rectShape.lineTo(offsetX + dozRight, localTop + offsetY);
		rectShape.lineTo(offsetX, localTop + offsetY);
		rectShape.closePath();
		const rect = new THREE.Mesh(new THREE.ShapeGeometry(rectShape), blueMatTemplate.clone());
		rect.name = 'blue-top-rect';
		rect.position.set(0, 0, -0.01);
		scene.add(rect);

		const leftOut = offsetX + gridLeft;
		const rightOut = skipRightEdge ? (offsetX + gridRight) : (offsetX + gridRight);
		const topY = localTop + offsetY + (skipRightEdge ? 0 : topRectBorderThickness);
		const botY = localTopRectBottom + offsetY;
		const bw = rightOut - leftOut;
		const bh = topY - botY;
		const frameSideH = Math.max(0, bh - gap);

		for (let vi = 0; vi < vertX.length - 1; vi++) {
			const segLen = vertX[vi + 1] - vertX[vi] - gap;
			if (segLen > 0) {
				const seg = new THREE.Mesh(new THREE.BoxGeometry(segLen, gap, lineDepth), whiteStripMat);
				seg.name = 'dozen-bottom-seg';
				seg.position.set((vertX[vi] + vertX[vi + 1]) / 2 + offsetX, botY, stripZ);
				scene.add(seg);
			}
		}
		vertX.forEach(function (x, vi) {
			if (skipRightCorner && vi === vertX.length - 1) return;
			const c = new THREE.Mesh(new THREE.BoxGeometry(cornerScale, cornerScale, lineDepth), whiteStripMat);
			c.name = 'dozen-bottom-corner';
			c.position.set(x + offsetX, botY, stripZ);
			scene.add(c);
		});
		const topLine = new THREE.Mesh(new THREE.BoxGeometry(bw - gap, gap, lineDepth), whiteStripMat);
		topLine.name = 'dozen-top';
		topLine.position.set((leftOut + rightOut) / 2, topY, stripZ);
		scene.add(topLine);
		if (!skipLeftEdge) {
			const leftLine = new THREE.Mesh(new THREE.BoxGeometry(gap, frameSideH, lineDepth), whiteStripMat);
			leftLine.name = 'dozen-left';
			leftLine.position.set(leftOut, (botY + topY) / 2, stripZ);
			scene.add(leftLine);
		}
		if (!skipRightEdge) {
			const rightLine = new THREE.Mesh(new THREE.BoxGeometry(gap, frameSideH, lineDepth), whiteStripMat);
			rightLine.name = 'dozen-right';
			rightLine.position.set(rightOut, (botY + topY) / 2, stripZ);
			scene.add(rightLine);
		}
		[[leftOut, topY], [rightOut, topY]].forEach(function (pt) {
			const c = new THREE.Mesh(new THREE.BoxGeometry(cornerScale, cornerScale, lineDepth), whiteStripMat);
			c.name = 'dozen-top-corner';
			c.position.set(pt[0], pt[1], stripZ);
			scene.add(c);
		});

		const labelMesh = new THREE.Mesh(
			new THREE.PlaneGeometry(12, 5),
			new THREE.MeshBasicMaterial({
				map: makeTextTexture(label, '#000000'),
				transparent: true,
				side: THREE.DoubleSide
			})
		);
		labelMesh.position.set(offsetX + 16.45, (localTopRectBottom + localTop) / 2 + offsetY, 0.02);
		labelMesh.name = 'label ' + label;
		scene.add(labelMesh);

		vertX.forEach(function (x) {
			horzYFiltered.forEach(function (y) {
				const corner = new THREE.Mesh(new THREE.BoxGeometry(cornerScale, cornerScale, lineDepth), whiteStripMat);
				corner.name = 'corner';
				corner.position.set(x + offsetX, y + offsetY, stripZ);
				scene.add(corner);
			});
		});
	}

	function addGrayStrip(x1, y1, x2, y2, thickness, z) {
		const dx = x2 - x1;
		const dy = y2 - y1;
		const length = Math.hypot(dx, dy);
		const strip = new THREE.Mesh(new THREE.BoxGeometry(length, thickness, lineDepth), whiteStripMat);
		strip.name = 'white-strip';
		strip.position.set((x1 + x2) / 2, (y1 + y2) / 2, z !== undefined ? z : 0);
		strip.rotation.z = Math.atan2(dy, dx);
		scene.add(strip);
	}

	visibleDozens.forEach(function (dozIdx) {
		const cfg = DOZEN_CONFIG[dozIdx];
		if (!cfg) return;
		const offsetX = (dozIdx - 1) * BLOCK_WIDTH;
		const offsetY = 0;
		const skipLeftEdge = visibleDozens.indexOf(dozIdx - 1) !== -1;
		const skipRightEdge = false;
		const skipRightCorner = visibleDozens.indexOf(dozIdx + 1) !== -1;
		createDozenBlock({
			offsetX, offsetY, skipLeftEdge, skipRightEdge, skipRightCorner,
			numbers: cfg.numbers, label: cfg.label, red: cfg.red
		});
	});

	if (visibleDozens.length > 0) {
		const maxDozIdx = Math.max.apply(null, visibleDozens);
		const rightEdgeX = (maxDozIdx - 1) * BLOCK_WIDTH + gridRight;
		addGrayStrip(-0.15, 30.75, rightEdgeX, 30.75, gap, 0.003);
	}

	addGrayStrip(-0.15, -0.15, -3.15, -0.15, gap);
	addGrayStrip(-3.15, -0.15, -8.15, 10.15, gap);
	addGrayStrip(-0.15, 30.75, -3.15, 30.75, gap);
	addGrayStrip(-3.15, 30.75, -8.15, 20.75, gap);
	addGrayStrip(-8.15, 10.15, -8.15, 20.75, gap);

	const trapezoidShape = new THREE.Shape();
	trapezoidShape.moveTo(-0.15, -0.15);
	trapezoidShape.lineTo(-3.15, -0.15);
	trapezoidShape.lineTo(-8.15, 10.15);
	trapezoidShape.lineTo(-8.15, 20.75);
	trapezoidShape.lineTo(-3.15, 30.75);
	trapezoidShape.lineTo(-0.15, 30.75);
	trapezoidShape.closePath();
	const trapezoid = new THREE.Mesh(new THREE.ShapeGeometry(trapezoidShape), blueMatTemplate.clone());
	trapezoid.name = 'blue-trapezoid';
	trapezoid.userData.isZeroSector = true;
	trapezoid.position.set(0, 0, -0.01);
	scene.add(trapezoid);

	const zeroLabelMat = new THREE.MeshBasicMaterial({
		map: makeNumberTexture(0, '#16a34a'),
		transparent: true,
		side: THREE.DoubleSide
	});
	const zeroLabel = new THREE.Mesh(new THREE.PlaneGeometry(7.2, 7.2), zeroLabelMat);
	zeroLabel.position.set(-4.15, 15.3, 0.02);
	zeroLabel.rotation.z = Math.PI / 2;
	zeroLabel.name = 'label 0';
	zeroLabel.userData.rouletteNumber = 0;
	zeroLabel.userData.labelBaseColor = '#16a34a';
	scene.add(zeroLabel);

	const maxDoz = visibleDozens.length ? Math.max.apply(null, visibleDozens) : 3;
	const maxX = (maxDoz - 1) * BLOCK_WIDTH + gridRight;
	const bounds = {
		minX: -8.5,
		maxX: maxX + 2,
		minY: -1.5,
		maxY: dozenRectTop + 2
	};

	function applyHighlight(activeSet) {
		const has = activeSet && activeSet.size > 0;
		const zeroOn = has && activeSet.has(0);
		scene.traverse(function (o) {
			if (!o.isMesh) return;
			/* тот же золотой emissive, что и у ячеек 1–36 */
			if (o.name === 'blue-trapezoid' && o.material.emissive) {
				o.material.emissive.setHex(zeroOn ? 0xffaa00 : 0x000000);
				o.material.emissiveIntensity = zeroOn ? 0.55 : 0;
				return;
			}
			const n = o.userData.rouletteNumber;
			if (n === undefined || n === null) return;
			const on = has && activeSet.has(n);
			if (o.name.startsWith('number ')) {
				o.material.emissive.setHex(on ? 0xffaa00 : 0x000000);
				o.material.emissiveIntensity = on ? 0.55 : 0;
			} else if (o.name.startsWith('label ')) {
				const base = o.userData.labelBaseColor || '#ffffff';
				const ctxBoost = on ? '#ffee66' : base;
				if (o.material.map) {
					o.material.map.dispose();
				}
				o.material.map = makeNumberTexture(n, ctxBoost);
				o.material.needsUpdate = true;
			}
		});
	}

	return { bounds, applyHighlight, BLOCK_WIDTH, DOZEN_CONFIG };
}
