// Volteo de aparatos y cartas: clic, Enter o Espacio sobre el objeto muestra la otra cara.
(function () {
  document.querySelectorAll('.voltea').forEach(function (v) {
    var objeto = v.querySelector('.voltea-in');
    var caras = v.querySelectorAll('.cara');
    if (!objeto) return;

    function alterna() {
      var atras = v.classList.toggle('vuelta-on');
      objeto.setAttribute('aria-pressed', String(atras));
      caras.forEach(function (c) {
        c.setAttribute('aria-hidden', String(c.classList.contains('cara-e') !== atras));
      });
    }

    // Sin botón aparte: el objeto mismo es el control.
    objeto.setAttribute('role', 'button');
    objeto.setAttribute('tabindex', '0');
    objeto.setAttribute('aria-pressed', 'false');
    if (objeto.dataset.voltea) objeto.setAttribute('aria-label', objeto.dataset.voltea);

    caras.forEach(function (c) { if (c.classList.contains('cara-e')) c.setAttribute('aria-hidden', 'true'); });
    objeto.addEventListener('click', alterna);
    objeto.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); alterna(); }
    });
  });
})();
