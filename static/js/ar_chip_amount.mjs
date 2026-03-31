/** Номиналы по убыванию — жадная разбивка суммы на фишки. */
export const CHIP_VALUES_DESC = [5000, 1000, 500, 100, 25, 5, 1];

/** Тот же набор по возрастанию (удобно для перебора / UI). */
export const CHIP_VALUES_ASC = [...CHIP_VALUES_DESC].reverse();

/**
 * Разложить целую неотрицательную сумму на стопки фишек (крупные номиналы первыми в результате).
 * @param {number} amount
 * @returns {{ denomination: number, count: number }[]}
 */
export function amountToChipStacks(amount) {
	if (!Number.isInteger(amount) || amount < 0) {
		throw new Error('amount must be a non-negative integer');
	}
	let remaining = amount;
	const stacks = [];
	for (const d of CHIP_VALUES_DESC) {
		const count = Math.floor(remaining / d);
		if (count > 0) stacks.push({ denomination: d, count });
		remaining %= d;
	}
	return stacks;
}
