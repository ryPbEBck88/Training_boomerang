/**
 * После POST из <main> ответ часто открывается с scroll=0.
 * Сохраняем позицию и pathname; восстанавливаем только если остались на том же пути
 * (если был редирект — запись сбрасываем без прокрутки).
 */
(function () {
  'use strict';

  var PENDING = 'trainerFormScrollPending';

  document.addEventListener(
    'submit',
    function (e) {
      var form = e.target;
      if (!(form instanceof HTMLFormElement)) return;
      if (!form.closest('main')) return;
      var method = (form.getAttribute('method') || 'get').toLowerCase();
      if (method !== 'post') return;
      try {
        sessionStorage.setItem(
          PENDING,
          JSON.stringify({
            path: window.location.pathname,
            y: window.scrollY,
          })
        );
      } catch (err) {}
    },
    true
  );

  var raw;
  try {
    raw = sessionStorage.getItem(PENDING);
  } catch (err) {
    return;
  }
  if (raw === null) return;
  try {
    sessionStorage.removeItem(PENDING);
  } catch (err) {}

  var data;
  try {
    data = JSON.parse(raw);
  } catch (err) {
    return;
  }
  if (!data || typeof data.path !== 'string' || data.path !== window.location.pathname) {
    return;
  }
  var y = parseInt(data.y, 10);
  if (isNaN(y) || y < 0) return;

  function restore() {
    window.scrollTo(0, y);
  }

  function run() {
    requestAnimationFrame(function () {
      requestAnimationFrame(restore);
    });
  }

  if (document.readyState === 'complete') {
    run();
  } else {
    window.addEventListener('load', run);
  }
})();
