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
		var lastHandledKey = null;
		var lastHandledTime = 0;

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

		function handleKeyPress(keyEl) {
			if (keyEl.type === 'submit') {
				keyEl.click();
				return;
			}
			if (!lastActiveInput || lastActiveInput.disabled) return;
			var now = Date.now();
			if (keyEl === lastHandledKey && now - lastHandledTime < 300) return;
			lastHandledKey = keyEl;
			lastHandledTime = now;
			var action = keyEl.getAttribute('data-action');
			if (action === 'backspace') {
				lastActiveInput.value = lastActiveInput.value.slice(0, -1);
			} else {
				var val = keyEl.getAttribute('data-val');
				if (val != null) lastActiveInput.value += val;
			}
		}

		var keys = keyboard.querySelectorAll('.payout-key');
		keys.forEach(function(k) {
			var isSubmit = k.type === 'submit';
			k.addEventListener('pointerdown', function(e) {
				if (isSubmit) return; // Enter — не блокируем, native submit сработает
				e.preventDefault();
				handleKeyPress(k);
			});
			k.addEventListener('touchstart', function(e) {
				if (!isSubmit) e.preventDefault();
			}, { passive: false });
		});
	}

	document.addEventListener('DOMContentLoaded', function() {
		var keyboards = document.querySelectorAll('.payout-keyboard');
		keyboards.forEach(function(kb) {
			initPayoutKeyboard(kb);
		});
	});
})();
