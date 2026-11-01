// Menú móvil. Sin JS la navegación se muestra completa (mejora progresiva).
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('nav-principal');
  if (!toggle || !nav) return;

  document.documentElement.classList.add('js');
  toggle.hidden = false;

  function setOpen(open) {
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  }

  toggle.addEventListener('click', function () {
    setOpen(toggle.getAttribute('aria-expanded') !== 'true');
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && nav.classList.contains('is-open')) {
      setOpen(false);
      toggle.focus();
    }
  });
})();

// Tema claro u oscuro. Sin elección guardada, sigue al sistema.
(function () {
  var boton = document.querySelector('.tema-toggle');
  if (!boton) return;
  var raiz = document.documentElement;
  var sistema = window.matchMedia('(prefers-color-scheme: light)');
  var metas = document.querySelectorAll('meta[name="theme-color"]');
  var colores = { claro: '#F5F3EA', oscuro: '#2A2A2D' };

  function temaActual() {
    return raiz.dataset.tema || (sistema.matches ? 'claro' : 'oscuro');
  }

  function pintar() {
    var tema = temaActual();
    boton.setAttribute('aria-pressed', String(tema === 'claro'));
    // Con una elección explícita, la barra del navegador la sigue sin importar el sistema.
    for (var i = 0; i < metas.length; i++) {
      if (raiz.dataset.tema) metas[i].setAttribute('content', colores[tema]);
    }
  }

  boton.hidden = false;
  pintar();

  boton.addEventListener('click', function () {
    var tema = temaActual() === 'claro' ? 'oscuro' : 'claro';
    raiz.dataset.tema = tema;
    try { localStorage.setItem('tema', tema); } catch (e) {}
    pintar();
  });

  if (sistema.addEventListener) sistema.addEventListener('change', pintar);
})();
