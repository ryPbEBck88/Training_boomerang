/**
 * Fuse timer: countdown with burning fuse visual.
 * Pauses when settings overlay is open. On timeout, clicks the target button.
 * При повторном вызове initFuseTimer(prefix) старый таймер останавливается.
 *
 * @param {Object} opts
 * @param {string} opts.prefix - ID prefix (e.g. 'self-draw', 'payout')
 * @param {number} opts.seconds - Countdown seconds
 * @param {string} opts.timeoutButton - Selector for button to click on timeout (e.g. 'button[value="stand"]')
 * @param {string} [opts.settingsOverlay] - Selector for settings overlay (to pause when open)
 * @param {boolean} [opts.clickOnTimeout=true] - Если false, по истечении времени не нажимать кнопку
 * @param {function} [opts.onTimeout] - Колбэк при истечении времени (вместо клика по кнопке).
 *   С onTimeout: пауза с полоской на 0% (догорел) → скрытие фитиля → пауза → колбэк (например оверлей «Время вышло»).
 */
var FUSE_BURNOUT_PAUSE_MS = 220;
var FUSE_MSG_AFTER_HIDE_MS = 320;

/** Таймер в форме: checkbox или hidden со значением 1/on/true — выкл при 0/false. */
function fuseTimerIsEnabledInSettings(overlay) {
	if (!overlay) return true;
	var hidden = overlay.querySelector('input[name="timer_enabled"][type="hidden"]');
	if (hidden) {
		var v = String(hidden.value || '').trim().toLowerCase();
		return v === '1' || v === 'on' || v === 'true' || v === 'yes';
	}
	var cb = overlay.querySelector('input[name="timer_enabled"]');
	if (cb && cb.type === 'checkbox') return cb.checked;
	return true;
}

function initFuseTimer(opts) {
	var prefix = opts.prefix || 'fuse';
	var clickOnTimeout = opts.clickOnTimeout !== false;
	var onTimeout = opts.onTimeout;
	var fillId = prefix + '-fuse-fill';
	var fillEl = document.getElementById(fillId);
	if (!fillEl) return; /* fuse not in DOM = timer disabled, do nothing */
	var fuseTimerEl = document.getElementById(prefix + '-fuse-timer') || (fillEl.closest && fillEl.closest('.fuse-timer'));
	/* Сначала обёртка *-fuse-wrap (Заставки, Цвет в cash, Выплата через cash, Соседи, …), иначе .fuse-timer, иначе stub — весь блок исчезает вместе с отступами */
	var exhaustTarget =
		(fuseTimerEl && fuseTimerEl.closest && fuseTimerEl.closest('[class*="-fuse-wrap"]')) ||
		(fuseTimerEl && fuseTimerEl.closest && fuseTimerEl.closest('[id$="-fuse-wrap"]')) ||
		fuseTimerEl ||
		(fillEl.closest && fillEl.closest('[class*="-fuse-wrap"]')) ||
		(fillEl.closest && fillEl.closest('[id$="-fuse-wrap"]')) ||
		(fillEl.closest && fillEl.closest('.fuse-timer')) ||
		fillEl.parentElement;
	if (exhaustTarget) exhaustTarget.classList.remove('fuse-timer--exhausted');
	/* Инвалидируем старый таймер с тем же prefix — иначе при перезапуске оба тикают и старый может сработать */
	window._fuseTimerGen = window._fuseTimerGen || {};
	window._fuseTimerGen[prefix] = (window._fuseTimerGen[prefix] || 0) + 1;
	var myGen = window._fuseTimerGen[prefix];

	var seconds = parseInt(opts.seconds, 10) || 3;
	var timeoutBtnSel = opts.timeoutButton || 'button[value="stand"]';
	var overlaySel = opts.settingsOverlay || '[id$="-settings-overlay"], .payout-settings-overlay';
	var overlay = document.querySelector(overlaySel);
	var start = Date.now();
	var lastTick = Date.now();

	function tick() {
		if (window._fuseTimerGen && window._fuseTimerGen[prefix] !== myGen) return; /* вытеснен новым таймером */
		if (overlay && (overlay.classList.contains('open') || overlay.classList.contains('is-open'))) {
			start += (Date.now() - lastTick);
			lastTick = Date.now();
			requestAnimationFrame(tick);
			return;
		}
		/* В настройках выключили фитиль и закрыли без сохранения — остановить отсчёт */
		if (overlay && !fuseTimerIsEnabledInSettings(overlay)) return;
		lastTick = Date.now();
		var elapsed = (Date.now() - start) / 1000;
		var t = Math.max(0, seconds - elapsed);
		var pct = (t / seconds) * 100;
		if (fillEl) fillEl.style.width = pct + '%';
		if (t <= 0) {
			if (window._fuseTimerGen && window._fuseTimerGen[prefix] !== myGen) return;
			if (typeof onTimeout === 'function') {
				var seqGen = myGen;
				function seqCancelled() {
					return window._fuseTimerGen && window._fuseTimerGen[prefix] !== seqGen;
				}
				/* 1) полоска на 0% — «догорел»; 2) пауза; 3) скрыть фитиль; 4) пауза; 5) сообщение */
				setTimeout(function () {
					if (seqCancelled()) return;
					if (exhaustTarget) exhaustTarget.classList.add('fuse-timer--exhausted');
					setTimeout(function () {
						if (seqCancelled()) return;
						onTimeout();
					}, FUSE_MSG_AFTER_HIDE_MS);
				}, FUSE_BURNOUT_PAUSE_MS);
			} else {
				if (exhaustTarget) exhaustTarget.classList.add('fuse-timer--exhausted');
				if (clickOnTimeout) {
					var btn = document.querySelector(timeoutBtnSel);
					if (btn) btn.click();
				}
			}
			return; /* не продолжать цикл и не кликать повторно */
		}
		requestAnimationFrame(tick);
	}
	requestAnimationFrame(tick);
}
