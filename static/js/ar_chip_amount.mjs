/** Номиналы по убыванию — жадная разбивка суммы на фишки. */
export const CHIP_VALUES_DESC = [5000, 1000, 500, 100, 25, 5, 2, 1];

/** BJ Bonus: Pair — отдельный набор: 2.5 вместо 2 (фишка 2 остаётся в AR и других тренажёрах). */
export const BJ_BONUS_CHIP_VALUES_DESC = [5000, 1000, 500, 100, 25, 5, 2.5, 1];

/** Тот же набор по возрастанию (удобно для перебора / UI). */
export const CHIP_VALUES_ASC = [...CHIP_VALUES_DESC].reverse();

/**
 * Разложить сумму на стопки фишек (крупные номиналы первыми в результате).
 * @param {number} amount
 * @param {number[]} [chipValuesDesc]
 * @returns {{ denomination: number, count: number }[]}
 */
export function amountToChipStacks(amount, chipValuesDesc = CHIP_VALUES_DESC) {
	let remaining = Number(amount);
	if (!Number.isFinite(remaining) || remaining < 0) {
		throw new Error('amount must be a non-negative number');
	}
	remaining = Math.round(remaining * 100) / 100;
	const stacks = [];
	for (const d of chipValuesDesc) {
		const count = Math.floor((remaining + 1e-9) / d);
		if (count > 0) {
			stacks.push({ denomination: d, count });
			remaining = Math.round((remaining - count * d) * 100) / 100;
		}
	}
	return stacks;
}
