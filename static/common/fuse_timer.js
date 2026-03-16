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
 */
function initFuseTimer(opts) {
	var prefix = opts.prefix || 'fuse';
	var fillId = prefix + '-fuse-fill';
	var fillEl = document.getElementById(fillId);
	if (!fillEl) return; /* fuse not in DOM = timer disabled, do nothing */
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
		/* User unchecked timer in overlay and closed without saving — stop countdown */
		var cb = overlay && overlay.querySelector('input[name="timer_enabled"]');
		if (cb && !cb.checked) return;
		lastTick = Date.now();
		var elapsed = (Date.now() - start) / 1000;
		var t = Math.max(0, seconds - elapsed);
		var pct = (t / seconds) * 100;
		if (fillEl) fillEl.style.width = pct + '%';
		if (t <= 0) {
			if (window._fuseTimerGen && window._fuseTimerGen[prefix] !== myGen) return;
			var btn = document.querySelector(timeoutBtnSel);
			if (btn) btn.click();
			return;
		}
		requestAnimationFrame(tick);
	}
	requestAnimationFrame(tick);
}
