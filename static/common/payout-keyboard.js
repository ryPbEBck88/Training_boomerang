/**
 * Payout keyboard: мобильная клавиатура только при тапе по input,
 * при нажатии на кастомную клавиатуру — ввод через JS, мобильная не выскакивает.
 */
(function() {
	function initPayoutKeyboard(container) {
		var form = container.closest && container.closest('form');
		if (!form) form = container;
		var keyboard = container.classList && container.classList.contains('payout-keyboard') ? container : container.querySelector('.payout-keyboard');
		if (!keyboard) return;
		var inputs = [].slice.call(form.querySelectorAll('.payout-input'));
		if (!inputs.length) return;

		var lastActiveInput = inputs[0];

		inputs.forEach(function(inp) {
			inp.addEventListener('focus', function() {
				if (!this.disabled) {
					lastActiveInput = this;
					if (this.readOnly) this.blur();
				}
			});
			inp.addEventListener('keydown', function(e) {
				if (e.key === 'Enter') {
					e.preventDefault();
					var btn = this.form && this.form.querySelector('[name=action][value=check]');
					if (btn) btn.click();
				}
			});
		});

		keyboard.addEventListener('mousedown', function(e) { e.preventDefault(); });
		keyboard.addEventListener('touchstart', function(e) { e.preventDefault(); }, { passive: false });

		var keys = keyboard.querySelectorAll('.payout-key');
		keys.forEach(function(k) {
			k.addEventListener('click', function(e) {
				if (this.type === 'submit') return;
				if (!lastActiveInput || lastActiveInput.disabled) return;
				e.preventDefault();
				var action = this.getAttribute('data-action');
				if (action === 'backspace') {
					lastActiveInput.value = lastActiveInput.value.slice(0, -1);
				} else {
					var val = this.getAttribute('data-val');
					if (val != null) lastActiveInput.value += val;
				}
			});
		});
	}

	document.addEventListener('DOMContentLoaded', function() {
		var keyboards = document.querySelectorAll('.payout-keyboard');
		keyboards.forEach(function(kb) {
			initPayoutKeyboard(kb);
		});
	});
})();
