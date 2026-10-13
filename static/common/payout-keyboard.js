/**
 * Ввод: на телефоне — только кастомная сетка (без системной клавиатуры iOS).
 * На десктопе — системная клавиатура + сетка цифр.
 * Активное поле подсвечивается (payout-keyboard-target).
 */
(function() {
	function isTouchPrimary() {
		if (typeof window.matchMedia !== 'function') {
			return 'ontouchstart' in window;
		}
		return window.matchMedia('(pointer: coarse)').matches
			|| window.matchMedia('(hover: none)').matches;
	}

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
		var touchPrimary = isTouchPrimary();

		function syncKeyboardTarget() {
			inputs.forEach(function(inp) {
				inp.classList.remove('payout-keyboard-target');
			});
			if (lastActiveInput && !lastActiveInput.disabled) {
				lastActiveInput.classList.add('payout-keyboard-target');
			}
		}

		function caretAtEnd(inp) {
			if (!inp || inp.disabled || touchPrimary) return;
			try {
				inp.focus({ preventScroll: true });
				var len = inp.value.length;
				if (inp.setSelectionRange) {
					inp.setSelectionRange(len, len);
				}
			} catch (e) { /* старые браузеры */ }
		}

		function selectTarget(inp, ev) {
			if (!inp || inp.disabled) return;
			lastActiveInput = inp;
			syncKeyboardTarget();
			if (touchPrimary) {
				if (ev) ev.preventDefault();
				try {
					inp.blur();
				} catch (e) { /* ignore */ }
			}
		}

		inputs.forEach(function(inp) {
			if (touchPrimary) {
				/* readonly: iOS не открывает системную клавиатуру */
				inp.readOnly = true;
				inp.setAttribute('inputmode', 'none');
				inp.classList.add('payout-input--custom-kb');
				inp.addEventListener('pointerdown', function(e) {
					selectTarget(this, e);
				});
				inp.addEventListener('focus', function() {
					if (this.disabled) return;
					lastActiveInput = this;
					syncKeyboardTarget();
					var self = this;
					requestAnimationFrame(function() {
						try { self.blur(); } catch (e) { /* ignore */ }
					});
				});
			} else {
				if (!inp.getAttribute('inputmode')) {
					inp.setAttribute('inputmode', 'decimal');
				}
				inp.addEventListener('focus', function() {
					if (!this.disabled) {
						lastActiveInput = this;
						syncKeyboardTarget();
					}
				});
			}
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
			if (!touchPrimary) {
				requestAnimationFrame(function() {
					caretAtEnd(lastActiveInput);
				});
			}
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
				if (!touchPrimary) {
					requestAnimationFrame(function() {
						caretAtEnd(nextInput);
					});
				}
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
				/* На телефоне не вызываем focus — иначе всплывает системная клавиатура */
				if (!touchPrimary && lastActiveInput && !lastActiveInput.disabled) {
					lastActiveInput.focus({ preventScroll: true });
				}
				handleKeyPress(k);
			});
			k.addEventListener('touchstart', function(e) {
				if (!isSubmit) e.preventDefault();
			}, { passive: false });
		});

		syncKeyboardTarget();
		if (!touchPrimary) {
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
