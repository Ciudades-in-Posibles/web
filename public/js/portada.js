// Portada: rotación de canales del hero. Mejora progresiva; sin JS se ve el canal 1.
(function () {
  var grupo = document.querySelector('[data-grupo]');
  if (!grupo) return;
  var pant = grupo.querySelector('[data-pant]');
  if (!pant) return;

  var BASE = '/assets/img/tomas/';
  var C = {
    1: { img: BASE + '01-huella.webp', nm: 'Huella', alt: 'Toma en blanco y negro de dos huellas de pasos sobre tierra oscura' },
    2: { img: null, nm: 'Ritmo' },
    3: { img: BASE + '03-grieta.webp', nm: 'Grieta' },
    4: { img: BASE + '04-ras.webp', nm: 'A ras' },
    5: { img: BASE + '05-borde.webp', nm: 'Borde' },
    6: { img: BASE + '06-refugio-vacio.webp', nm: 'Refugio' },
    7: { img: null, nm: 'Fuente' },
    8: { img: null, nm: 'Abierto' },
    9: { img: null, nm: 'Abierto' }
  };
  var RONDA = [1, 3, 4, 5, 6];
  var reducido = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  var pausado = reducido;
  var botones = grupo.querySelectorAll('.canales button');
  var pausa = document.querySelectorAll('.b-pausa');

  // Solo se anuncia el canal cuando alguien lo elige; la rotación automática no habla.
  function pintar(n, aMano) {
    var c = C[n];
    pant.dataset.c = n;
    var im = pant.querySelector('img');
    if (c.img && im) {
      im.src = c.img;
      im.alt = c.alt || 'Toma de prueba en blanco y negro del canal ' + n + ', ' + c.nm;
    }
    pant.classList.toggle('sin-senal', !c.img);
    var pl = pant.querySelector('.pill');
    if (pl) {
      pl.setAttribute('aria-live', aMano ? 'polite' : 'off');
      pl.className = 'pill k' + n;
      pl.querySelector('.n').textContent = n;
      pl.querySelector('.nm').textContent = c.img ? c.nm : c.nm + ' · sin señal';
    }
    for (var i = 0; i < botones.length; i++) {
      botones[i].setAttribute('aria-pressed', +botones[i].dataset.c === n ? 'true' : 'false');
    }
  }

  function cambiar(n, aMano) {
    if (reducido) { pintar(n, aMano); return; }
    pant.classList.add('cambia');
    setTimeout(function () { pintar(n, aMano); }, 130);
    setTimeout(function () { pant.classList.remove('cambia'); }, 270);
  }

  function paso() {
    var n = +pant.dataset.c;
    var k = RONDA.indexOf(n);
    cambiar(RONDA[(k + 1) % RONDA.length]);
  }

  function rotular() {
    for (var i = 0; i < pausa.length; i++) {
      pausa[i].textContent = pausado ? 'Seguir' : 'Pausar';
    }
    document.documentElement.classList.toggle('en-pausa', pausado);
  }

  // Precarga las tomas de la ronda para que el cambio no parpadee.
  RONDA.forEach(function (n) { if (C[n].img) { new Image().src = C[n].img; } });

  pintar(+pant.dataset.c || 1);
  rotular();
  var cada = +grupo.dataset.cada || 6000;
  var reloj;
  function arrancar() {
    clearInterval(reloj);
    reloj = setInterval(function () { if (!pausado && !document.hidden) paso(); }, cada);
  }
  arrancar();

  document.addEventListener('click', function (e) {
    if (e.target.closest('.b-pausa')) { pausado = !pausado; rotular(); return; }
    var k = e.target.closest('.canales button');
    // El canal elegido se queda una vuelta completa antes de seguir la ronda.
    if (k) { cambiar(+k.dataset.c, true); arrancar(); }
  });
})();

// Portada: los frottages del laboratorio se turnan en la tarjeta «En curso» con un
// fundido cruzado. Sin JS o con movimiento reducido se queda el primero; la pausa
// del hero también los detiene.
(function () {
  var caja = document.querySelector('[data-frottages]');
  var base = caja && caja.querySelector('.frottage');
  if (!base) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var BASE = '/assets/img/frottages/';
  var V = '?v=4'; // sube al cambiar las imágenes
  var F = [
    ['frottage-01.webp', 'Frottage en grafito de una forma ovalada rodeada de marcas en relieve'],
    ['frottage-02.webp', 'Frottage en grafito de una trama de líneas, como un muro de ladrillos'],
    ['frottage-03.webp', 'Frottage en grafito de manchas densas y oscuras'],
    ['frottage-05.webp', 'Frottage en grafito del borde de una hoja sobre una superficie granulada'],
    ['frottage-06.webp', 'Frottage en grafito de nervaduras que se abren desde un punto'],
    ['frottage-07.webp', 'Frottage en grafito de puntos dispersos sobre el papel']
  ];
  var i = 0;
  var FUNDIDO = 1600;

  // Capa superior: entra con la toma nueva; al terminar, la de abajo la toma y la capa se oculta.
  var capa = base.cloneNode();
  capa.alt = '';
  capa.setAttribute('aria-hidden', 'true');
  capa.classList.add('capa', 'oculta');
  caja.appendChild(capa);

  function listo(im) { return im.decode ? im.decode().catch(function () {}) : Promise.resolve(); }

  // Precarga para que el fundido no espere a la red.
  F.forEach(function (f) { new Image().src = BASE + f[0] + V; });

  setInterval(function () {
    if (document.hidden || document.documentElement.classList.contains('en-pausa')) return;
    i = (i + 1) % F.length;
    var src = BASE + F[i][0] + V;
    capa.src = src;
    listo(capa).then(function () {
      capa.classList.remove('oculta');
      setTimeout(function () {
        base.src = src;
        base.alt = F[i][1];
        listo(base).then(function () {
          capa.style.transition = 'none';
          capa.classList.add('oculta');
          void capa.offsetWidth;
          capa.style.transition = '';
        });
      }, FUNDIDO);
    });
  }, 5000);
})();
