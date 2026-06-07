/**
 * Ввод: системная клавиатура (в т.ч. на телефоне) + кастомная сетка цифр.
 * Активное поле подсвечивается (payout-keyboard-target).
 */
(function() {
	function initPayoutKeyboard(container) {
		var form = container.closest && container.closest('form');
		if (!form) form = container;
		var keyboard = container.classList && container.classList.contains('payout-keyboard') ? container : container.querySelector('.payout-keyboard');
		if (!keyboard) return;
		var inputs = [].slice.call(form.querySelectorAll('.payout-input'));
		if (!inputs.length) return;

		var enabledInputs = inputs.filter(function(i) {
			return !i.disabled;
		});
		if (!enabledInputs.length) return;

		var lastActiveInput = enabledInputs[0];
		var lastHandledKey = null;
		var lastHandledTime = 0;

		var coarsePointer = typeof window.matchMedia === 'function' && window.matchMedia('(pointer: coarse)').matches;

		function syncKeyboardTarget() {
			inputs.forEach(function(inp) {
				inp.classList.remove('payout-keyboard-target');
			});
			if (lastActiveInput && !lastActiveInput.disabled) {
				lastActiveInput.classList.add('payout-keyboard-target');
			}
		}

		function caretAtEnd(inp) {
			if (!inp || inp.disabled) return;
			try {
				inp.focus({ preventScroll: true });
				var len = inp.value.length;
				if (inp.setSelectionRange) {
					inp.setSelectionRange(len, len);
				}
			} catch (e) { /* старые браузеры */ }
		}

		inputs.forEach(function(inp) {
			if (!inp.getAttribute('inputmode')) {
				inp.setAttribute('inputmode', 'decimal');
			}
			inp.addEventListener('focus', function() {
				if (!this.disabled) {
					lastActiveInput = this;
					syncKeyboardTarget();
				}
			});
			inp.addEventListener('input', function() {
				if (!this.disabled) {
					lastActiveInput = this;
					syncKeyboardTarget();
				}
			});
			inp.addEventListener('keydown', function(e) {
				if (e.key === 'Enter') {
					e.preventDefault();
					this.blur();
					var btn = this.form && this.form.querySelector('[name=action][value=check]');
					if (btn) btn.click();
				}
			});
		});

		function afterValueChangeFromKeyboard() {
			syncKeyboardTarget();
			requestAnimationFrame(function() {
				caretAtEnd(lastActiveInput);
			});
		}

		function handleKeyPress(keyEl) {
			if (keyEl.type === 'submit') {
				keyEl.click();
				return;
			}
			if (!lastActiveInput || lastActiveInput.disabled) return;
			var now = Date.now();
			if (keyEl === lastHandledKey && now - lastHandledTime < 80) return;
			lastHandledKey = keyEl;
			lastHandledTime = now;
			var action = keyEl.getAttribute('data-action');
			if (action === 'backspace') {
				lastActiveInput.value = lastActiveInput.value.slice(0, -1);
				afterValueChangeFromKeyboard();
			} else if (action === 'nextcell') {
				var idx = inputs.indexOf(lastActiveInput);
				var nextIdx = (idx < 0 ? 0 : idx + 1) % inputs.length;
				var nextInput = inputs[nextIdx];
				if (!nextInput || nextInput.disabled) return;
				lastActiveInput = nextInput;
				syncKeyboardTarget();
				if (nextInput.scrollIntoView) {
					nextInput.scrollIntoView({ block: 'nearest', inline: 'nearest' });
				}
				requestAnimationFrame(function() {
					caretAtEnd(nextInput);
				});
			} else {
				var val = keyEl.getAttribute('data-val');
				if (val != null) {
					lastActiveInput.value += val;
					afterValueChangeFromKeyboard();
				}
			}
		}

		var keys = keyboard.querySelectorAll('.payout-key');
		keys.forEach(function(k) {
			var isSubmit = k.type === 'submit';
			k.addEventListener('pointerdown', function(e) {
				if (isSubmit) return;
				e.preventDefault();
				if (lastActiveInput && !lastActiveInput.disabled) {
					lastActiveInput.focus({ preventScroll: true });
				}
				handleKeyPress(k);
			});
			k.addEventListener('touchstart', function(e) {
				if (!isSubmit) e.preventDefault();
			}, { passive: false });
		});

		syncKeyboardTarget();
		if (!coarsePointer) {
			requestAnimationFrame(function() {
				caretAtEnd(lastActiveInput);
			});
		}
	}

	document.addEventListener('DOMContentLoaded', function() {
		var keyboards = document.querySelectorAll('.payout-keyboard');
		keyboards.forEach(function(kb) {
			initPayoutKeyboard(kb);
		});
	});
})();
