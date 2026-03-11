/**
 * PvP WebSocket client - connects to room, sends/receives game messages.
 */
(function() {
	var roomId = window.PVP_ROOM_ID;
	var wsUrl = window.PVP_WS_URL;
	var gameType = window.PVP_GAME_TYPE;

	if (!roomId || !wsUrl) return;

	var statusEl = document.getElementById('pvp-status');
	var ws = null;

	function setStatus(text) {
		if (statusEl) statusEl.textContent = text;
	}

	function send(data) {
		if (ws && ws.readyState === 1) {
			ws.send(JSON.stringify(data));
		}
	}

	function connect() {
		try {
			ws = new WebSocket(wsUrl);
		} catch (e) {
			setStatus('Ошибка подключения');
			return;
		}
		ws.onopen = function() {
			setStatus('Подключено');
		};
		ws.onclose = function() {
			setStatus('Отключено');
		};
		ws.onerror = function() {
			setStatus('Ошибка');
		};
		ws.onmessage = function(ev) {
			try {
				var msg = JSON.parse(ev.data);
				handleMessage(msg);
			} catch (e) {}
		};
	}

	function handleMessage(msg) {
		if (msg.action === 'state' && msg.payload) {
			if (gameType === 'ar_neighbors' && msg.payload.center !== undefined) {
				updateArNeighborsState(msg.payload);
			}
		}
		if (msg.action === 'result' && msg.payload) {
			if (gameType === 'ar_neighbors') {
				showArNeighborsResult(msg.payload);
			}
		}
		if (msg.action === 'move') {
			// Opponent's move - ignore for now (we both see same task)
		}
	}

	function updateArNeighborsState(state) {
		var centerEl = document.getElementById('pvpCenter');
		if (centerEl) centerEl.textContent = state.center;
		var taskEl = document.getElementById('pvpTask');
		if (taskEl) taskEl.textContent = 'Центр: ' + state.center;
		var inputs = ['pvpCell1','pvpCell2','pvpCell4','pvpCell5'];
		inputs.forEach(function(id) {
			var el = document.getElementById(id);
			if (el) el.value = '';
		});
	}

	function showArNeighborsResult(payload) {
		if (payload.ok) {
			setStatus('Правильно!');
		} else {
			var exp = payload.expected || [];
			setStatus('Ожидалось: ' + exp.join(' | '));
		}
	}

	connect();

	if (gameType === 'ar_neighbors') {
		var checkBtn = document.getElementById('pvpCheck');
		if (checkBtn) {
			checkBtn.addEventListener('click', function() {
				var c1 = document.getElementById('pvpCell1');
				var c2 = document.getElementById('pvpCell2');
				var c4 = document.getElementById('pvpCell4');
				var c5 = document.getElementById('pvpCell5');
				var payload = {
					cell1: c1 ? c1.value.trim() : '',
					cell2: c2 ? c2.value.trim() : '',
					cell4: c4 ? c4.value.trim() : '',
					cell5: c5 ? c5.value.trim() : '',
				};
				send({ action: 'check', payload: payload });
			});
		}
	}

	window.PvpClient = { send: send, ws: ws };
})();
