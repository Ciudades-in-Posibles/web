#!/usr/bin/env python3
"""Generador de la identidad «Mosaico» de Ciudades(In)Posibles.

Composición abstracta de bloques de color (paleta Spectral) sobre negro:
retículas empaquetadas por subdivisión recursiva (BSP) con «calles» negras,
2–3 barrios con distinta orientación, «avenidas» diagonales y recorte
circular. Una deformación suave curva calles y avenidas; las manzanas son
células de esquinas redondeadas y contorno irregular: una ciudad
que crece como un tejido vivo visto al microscopio.
No es un mapa ni un diagrama.

El del Manual (/el-juego/) es la misma composición a medio armar: el centro
entero y, hacia el borde, piezas sueltas y avenidas abiertas como grietas.

Uso:  python3 herramientas/mosaico.py
Salida: public/assets/img/mosaico-*.svg, public/assets/img/grano.svg,
        public/favicon.svg

Solo biblioteca estándar. Semillas fijas: la salida es reproducible.
Para cambiar una pieza, cambia su semilla o sus parámetros abajo.
"""

import math
import os
import random

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(RAIZ, "public", "assets", "img")

NEGRO = "#0B0B0C"
# Spectral (matplotlib), de cálido a frío.
PALETA = [
    "#9E0142",  # 0 vinotinto
    "#D53E4F",  # 1 rojo
    "#F46D43",  # 2 naranja
    "#FDAE61",  # 3 naranja claro
    "#FEE08B",  # 4 amarillo
    "#FFFFBF",  # 5 crema
    "#E6F598",  # 6 lima
    "#ABDDA4",  # 7 menta
    "#66C2A5",  # 8 turquesa
    "#3288BD",  # 9 azul
    "#5E4FA2",  # 10 violeta
]
VINO, ROJO, NAR, NARC, AMA, CREMA, LIMA, MENTA, TURQ, AZUL, VIOL = range(11)


# --------------------------------------------------------------------------
# Campos suaves (suma de senoides) para zonas de color y de densidad
# --------------------------------------------------------------------------

class Campo:
    """Campo escalar suave en [0, 1] a partir de senoides aleatorias.

    `contraste` < 1 empuja los valores hacia los extremos (más zonas de
    vinotinto y de violeta, menos franja media)."""

    def __init__(self, rng, escala, n=4, caja=(0, 0, 600, 600), contraste=1.0):
        self.contraste = contraste
        self.ondas = []
        for _ in range(n):
            ang = rng.uniform(0, math.tau)
            k = math.tau / (escala * rng.uniform(0.6, 1.5))
            self.ondas.append((k * math.cos(ang), k * math.sin(ang),
                               rng.uniform(0, math.tau), rng.uniform(0.5, 1)))
        # Normaliza con un muestreo de la caja.
        x0, y0, x1, y1 = caja
        vals = [self._crudo(x0 + (x1 - x0) * i / 24, y0 + (y1 - y0) * j / 24)
                for i in range(25) for j in range(25)]
        self.lo, self.hi = min(vals), max(vals)

    def _crudo(self, x, y):
        return sum(a * math.sin(kx * x + ky * y + f) for kx, ky, f, a in self.ondas)

    def __call__(self, x, y):
        v = (self._crudo(x, y) - self.lo) / (self.hi - self.lo)
        t = min(1.0, max(-1.0, 2 * v - 1))
        t = math.copysign(abs(t) ** self.contraste, t)
        return (t + 1) / 2


class Deformacion:
    """Curva el plano con dos campos suaves: la retícula se dobla como un
    tejido que crece, sin que las calles cambien mucho de ancho.

    Se apaga en la `banda` exterior del círculo (fracción de R) para que el
    recorte circular siga lleno hasta el borde."""

    def __init__(self, rng, amplitud, escala, cx, cy, R, banda=0.25):
        caja = (cx - R, cy - R, cx + R, cy + R)
        self.fx = Campo(rng, escala, n=3, caja=caja)
        self.fy = Campo(rng, escala, n=3, caja=caja)
        self.a, self.c, self.R, self.banda = amplitud, (cx, cy), R, banda * R

    def __call__(self, x, y):
        t = (self.R - math.hypot(x - self.c[0], y - self.c[1])) / self.banda
        t = min(1.0, max(0.0, t))
        a = self.a * t * t * (3 - 2 * t)
        return x + a * (2 * self.fx(x, y) - 1), y + a * (2 * self.fy(x, y) - 1)


# --------------------------------------------------------------------------
# Geometría
# --------------------------------------------------------------------------

class Linea:
    """Recta por el punto (px, py) con ángulo `ang` (grados). hw = semiancho."""

    def __init__(self, px, py, ang, hw):
        a = math.radians(ang)
        self.p = (px, py)
        self.d = (math.cos(a), math.sin(a))
        self.n = (-math.sin(a), math.cos(a))
        self.hw = hw

    def dist(self, x, y):  # distancia con signo
        return (x - self.p[0]) * self.n[0] + (y - self.p[1]) * self.n[1]

    def extremos(self, cx, cy, r):
        """Segmento que atraviesa el círculo (cx, cy, r) con holgura."""
        t0 = (cx - self.p[0]) * self.d[0] + (cy - self.p[1]) * self.d[1]
        mx, my = self.p[0] + self.d[0] * t0, self.p[1] + self.d[1] * t0
        return ((mx - self.d[0] * r, my - self.d[1] * r),
                (mx + self.d[0] * r, my + self.d[1] * r))


class Curva:
    """Avenida curva: bezier cuadrática muestreada como polilínea."""

    def __init__(self, p0, c, p1, hw, n=40):
        self.ctrl = (p0, c, p1)
        self.hw = hw
        self.pts = []
        for i in range(n + 1):
            t = i / n
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]
            self.pts.append((x, y))

    def dist(self, x, y):  # distancia sin signo a la polilínea
        best = 1e9
        for (ax, ay), (bx, by) in zip(self.pts, self.pts[1:]):
            vx, vy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy)))
            best = min(best, math.hypot(x - ax - t * vx, y - ay - t * vy))
        return best


def rotador(ang, cx, cy):
    """Local -> mundo, igual que SVG `rotate(ang cx cy)`."""
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)

    def f(u, v):
        return cx + c * (u - cx) - s * (v - cy), cy + s * (u - cx) + c * (v - cy)
    return f


# --------------------------------------------------------------------------
# Mosaico por subdivisión recursiva
# --------------------------------------------------------------------------

def mosaico(rng, cx, cy, R, barrios, fronteras, avenidas, color, cfg):
    """Devuelve [(ang, signos, [(icolor, x, y, w, h), ...]), ...] por barrio.

    barrios:   [(ang, {indice_frontera: signo})]
    fronteras: rectas que separan barrios (también se dibujan como avenidas)
    avenidas:  rectas/curvas extra que atraviesan sin separar barrios
    color:     f(x, y, desfase_manzana) -> índice de paleta
    cfg:       parámetros de tamaño (en px)
    """
    q = cfg["q"]                    # cuantización (1 = enteros, 0.5 = medios)
    densidad = cfg["densidad"]      # campo 0..1 (1 = bloques grandes)
    salida = []

    def Q(v):
        return round(v / q) * q

    for ang, signos in barrios:
        mundo = rotador(ang, cx, cy)
        hojas = []

        def estado(x, y, w, h):
            """¿Asoma algo del rectángulo en el barrio? Los bordes del barrio y del círculo se
            recortan con clipPath, así que basta con que asome algo."""
            # Círculo: punto del rectángulo más cercano al centro (invariante
            # a la rotación porque rotamos alrededor del centro).
            nx, ny = min(max(cx, x), x + w), min(max(cy, y), y + h)
            if math.hypot(nx - cx, ny - cy) > R - 2 * q:
                return False
            esq = [mundo(x, y), mundo(x + w, y), mundo(x, y + h), mundo(x + w, y + h)]
            for i, sg in signos.items():
                L = fronteras[i]
                if max(sg * L.dist(*p) for p in esq) < L.hw + 2 * q:
                    return False            # no asoma fuera de la avenida
            return True

        def visible(x, y, w, h):
            esq = [mundo(x, y), mundo(x + w, y), mundo(x, y + h), mundo(x + w, y + h)]
            for A in avenidas:
                if isinstance(A, Linea):
                    if max(abs(A.dist(*p)) for p in esq) < A.hw + 2 * q:
                        return False
                elif A.dist(*mundo(x + w / 2, y + h / 2)) < A.hw and max(w, h) < 2 * A.hw + 4:
                    return False
            return True

        def dividir(x, y, w, h, desfase, nivel):
            if not estado(x, y, w, h):
                return
            mx, my = mundo(x + w / 2, y + h / 2)
            largo, corto = max(w, h), min(w, h)
            if nivel == 0 and largo <= cfg["manzana"]:
                nivel = 1
                desfase = rng.gauss(0, cfg["ruido_manzana"])
            T = cfg["tmin"] + (cfg["tmax"] - cfg["tmin"]) * densidad(mx, my) ** 1.4
            T *= rng.uniform(0.75, 1.3)
            cabe = largo <= cfg["largo_max"] and corto <= cfg["corto_max"]
            if cabe and (largo <= T or largo <= cfg["min"] * 2.2):
                # Algún solar vacío, solo entre bloques pequeños.
                vacio = largo <= cfg["largo_max"] * 0.55 and rng.random() < cfg["vacio"]
                if not vacio and visible(x, y, w, h):
                    hojas.append((color(mx, my, desfase), x, y, w, h))
                return
            if largo < cfg["min"] * 2 + cfg["gaps"][-1][1]:
                if visible(x, y, w, h):
                    hojas.append((color(mx, my, desfase), x, y, w, h))
                return
            # Calle: más ancha entre bloques grandes.
            g = next(gg for umbral, gg in cfg["gaps"] if largo >= umbral)
            eje_x = w >= h if rng.random() < cfg["p_largo"] else w < h
            dim = w if eje_x else h
            if dim - g < cfg["min"] * 2:
                eje_x, dim = (not eje_x), (h if eje_x else w)
                if dim - g < cfg["min"] * 2:
                    if visible(x, y, w, h):
                        hojas.append((color(mx, my, desfase), x, y, w, h))
                    return
            lo, hi = cfg["min"], dim - g - cfg["min"]
            corte = Q(rng.uniform(max(lo, dim * 0.28), min(hi, dim * 0.72)))
            corte = min(max(corte, lo), hi)
            if eje_x:
                dividir(x, y, corte, h, desfase, nivel)
                dividir(x + corte + g, y, w - corte - g, h, desfase, nivel)
            else:
                dividir(x, y, w, corte, desfase, nivel)
                dividir(x, y + corte + g, w, h - corte - g, desfase, nivel)

        lado = Q(R * 1.04)
        dividir(Q(cx - lado), Q(cy - lado), 2 * lado, 2 * lado, 0.0, 0)
        salida.append((ang, signos, hojas))
    return salida


# --------------------------------------------------------------------------
# Serialización SVG compacta
# --------------------------------------------------------------------------

def n(v):
    """Número corto: 12, 12.5, -3, .5"""
    v = round(v, 1)
    if v == int(v):
        return str(int(v))
    s = f"{v:.1f}"
    return s.replace("0.", ".", 1) if s.startswith("0.") else s.replace("-0.", "-.", 1)


def une(nums):
    """Une números SVG sin separadores superfluos."""
    out, prev = "", ""
    for t in nums:
        # «-» siempre separa; «.5» separa si el número anterior ya tiene punto.
        out += t if (not out or t[0] == "-" or (t[0] == "." and "." in prev)) else " " + t
        prev = t
    return out


def trazos(rects):
    """Rectángulos del mismo color como un solo <path> (mucho más ligero).

    Tras cada `z` el punto actual vuelve al origen del rectángulo, así que el
    siguiente se mueve en relativo (`m`) desde ahí: números más cortos."""
    rects = sorted(rects, key=lambda r: (round(r[1] / 40), r[0] if round(r[1] / 40) % 2 == 0 else -r[0]))
    d, px, py = "", None, None
    for x, y, w, h in rects:
        if px is None:
            d += "M" + une([n(x), n(y)])
        else:
            d += "m" + une([n(x - px), n(y - py)])
        d += "h" + n(w) + "v" + n(h) + "h" + n(-w) + "z"
        px, py = x, y
    return d


def por_color(hojas):
    grupos = {}
    for c, x, y, w, h in hojas:
        grupos.setdefault(c, []).append((x, y, w, h))
    return "".join(f'<path fill="{PALETA[c]}" d="{trazos(r)}"/>'
                   for c, r in sorted(grupos.items()))


def manzanas(hojas, mundo, deform, forma, rng):
    """Hojas locales de un barrio -> {(color, radio): [cuadriláteros]}.

    La esquina redondeada sale del trazo: la manzana se encoge `radio` por
    lado, se deforma y se pinta con un trazo de su mismo color, de ancho
    2·radio y uniones redondas, que le devuelve su tamaño con las esquinas
    curvas. Cuatro puntos por manzana: mucho más ligero que curvas.

    Cada esquina se mete hacia adentro al azar (hasta `irregular` × lado
    corto): células algo distintas entre sí que nunca invaden a su vecina."""
    grupos = {}
    for c, x, y, w, h in hojas:
        corto = min(w, h)
        tope = min(forma["k"] * corto, forma["radios"][-1])
        posibles = [r for r in forma["radios"] if r <= tope]
        r = rng.choice(posibles[-2:]) if posibles else 0   # algo de variación
        holgura = min(w, h) / 2 - r                         # medio lado encogido
        esq = []
        for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            d = min(rng.uniform(0, forma["irregular"] * corto), 0.6 * holgura)
            ex = (x + r if sx > 0 else x + w - r) + sx * d * rng.uniform(0.3, 1)
            ey = (y + r if sy > 0 else y + h - r) + sy * d * rng.uniform(0.3, 1)
            esq.append((ex, ey))
        grupos.setdefault((c, r), []).append([deform(*mundo(*p)) for p in esq])
    return grupos


def trazos_poligonos(polis, prec):
    """Polígonos como un solo <path> con órdenes relativas.

    Se redondea a `prec` en absoluto y luego se resta, así no se acumula
    error. Tras cada `z` se vuelve al primer punto: el siguiente polígono
    se mueve en relativo desde ahí."""
    def R(p):
        return round(p[0] / prec) * prec, round(p[1] / prec) * prec

    polis = sorted(([R(p) for p in poli] for poli in polis),
                   key=lambda k: (round(k[0][1] / 40), k[0][0] if round(k[0][1] / 40) % 2 == 0 else -k[0][0]))
    d, ref = "", None
    for poli in polis:
        s = poli[0]
        d += ("M" + une([n(s[0]), n(s[1])]) if ref is None
              else "m" + une([n(s[0] - ref[0]), n(s[1] - ref[1])]))
        nums, cur = [], s
        for p in poli[1:]:
            nums += [n(p[0] - cur[0]), n(p[1] - cur[1])]
            cur = p
        d += "l" + une(nums) + "z"
        ref = s
    return d


def curva_suave(pts, prec):
    """Polilínea -> curva suave (cuadráticas por los puntos medios)."""
    pts = [(round(x / prec) * prec, round(y / prec) * prec) for x, y in pts]
    d = "M" + une([n(pts[0][0]), n(pts[0][1])])
    cur, nums = pts[0], []
    for a, b in zip(pts[1:-1], pts[2:]):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        nums += [n(a[0] - cur[0]), n(a[1] - cur[1]), n(m[0] - cur[0]), n(m[1] - cur[1])]
        cur = m
    d += "q" + une(nums) if nums else ""
    return d + "l" + une([n(pts[-1][0] - cur[0]), n(pts[-1][1] - cur[1])])


def muestrear(a, b, paso):
    """Puntos del segmento a–b cada `paso` como máximo (incluye extremos)."""
    k = max(1, math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / paso))
    return [(a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k) for j in range(k + 1)]


def semiplano(poli, f):
    """Parte del polígono donde f(p) >= 0 (Sutherland–Hodgman)."""
    nuevo = []
    for j, p in enumerate(poli):
        q_ = poli[(j + 1) % len(poli)]
        fp, fq = f(p), f(q_)
        if fp >= 0:
            nuevo.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            nuevo.append((p[0] + t * (q_[0] - p[0]), p[1] + t * (q_[1] - p[1])))
    return nuevo


def poligono_barrio(signos, fronteras, cx, cy, R, deform=None, paso=10):
    """Cuadrado que cubre el círculo, recortado por los semiplanos del barrio
    (Sutherland–Hodgman). El borde cae en el eje de la avenida y, si hay
    deformación, se curva con ella."""
    m = R + 4
    poli = [(cx - m, cy - m), (cx + m, cy - m), (cx + m, cy + m), (cx - m, cy + m)]
    for i, sg in signos.items():
        L = fronteras[i]
        poli = semiplano(poli, lambda p: sg * L.dist(*p))
    if deform:
        # Solo se subdividen los lados que pasan por el círculo; fuera de él
        # la deformación es nula.
        def cruza(a, b):
            vx, vy = b[0] - a[0], b[1] - a[1]
            t = max(0.0, min(1.0, ((cx - a[0]) * vx + (cy - a[1]) * vy) / (vx * vx + vy * vy)))
            return math.hypot(a[0] + t * vx - cx, a[1] + t * vy - cy) < R
        poli = [deform(*p) for a, b in zip(poli, poli[1:] + poli[:1])
                for p in (muestrear(a, b, paso) if cruza(a, b) else [a, b])[:-1]]
    return "M" + "L".join(une([n(x), n(y)]) for x, y in poli) + "z"


def svg_mosaico(ident, tam, cx, cy, R, rclip, barrios_hojas, fronteras, avenidas,
                deform, forma, fondo_circulo=True):
    """forma: k (radio de esquina máximo / lado corto), radios (posibles,
    de menor a mayor), prec (redondeo), paso_av (muestreo de avenidas),
    semilla (variación de radios) e irregular (esquinas hacia adentro, en
    fracción del lado corto)."""
    rng = random.Random(forma["semilla"])
    defs = [f'<clipPath id="{ident}"><circle cx="{n(cx)}" cy="{n(cy)}" r="{n(rclip)}"/></clipPath>']
    cuerpo = []
    for k, (ang, signos, hojas) in enumerate(barrios_hojas):
        capa = ""
        for (c, r), polis in sorted(manzanas(hojas, rotador(ang, cx, cy), deform, forma, rng).items()):
            trazo = f' stroke="{PALETA[c]}" stroke-width="{n(2 * r)}"' if r else ""
            capa += f'<path fill="{PALETA[c]}"{trazo} d="{trazos_poligonos(polis, forma["prec"])}"/>'
        if signos:
            defs.append(f'<clipPath id="{ident}{k}"><path d="'
                        f'{poligono_barrio(signos, fronteras, cx, cy, R, deform, forma["paso_av"] / 2)}"/></clipPath>')
            capa = f'<g clip-path="url(#{ident}{k})">{capa}</g>'
        cuerpo.append(capa)
    # Avenidas: franjas negras encima, curvadas por la misma deformación.
    av = []
    for L in list(fronteras) + list(avenidas):
        if isinstance(L, Linea):
            pts = muestrear(*L.extremos(cx, cy, R * 1.1), forma["paso_av"])
        else:
            pts = L.pts[::2] if len(L.pts) % 2 else L.pts[::2] + L.pts[-1:]
        pts = [deform(*p) for p in pts]
        av.append(f'<path stroke-width="{n(L.hw * 2)}" d="{curva_suave(pts, forma["prec"])}"/>')
    partes = ["<defs>" + "".join(defs) + "</defs>"]
    if fondo_circulo:
        partes.append(f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(R)}" fill="{NEGRO}"/>')
    partes.append(f'<g clip-path="url(#{ident})" stroke-linejoin="round">{"".join(cuerpo)}'
                  f'<g fill="none" stroke="{NEGRO}">{"".join(av)}</g></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tam} {tam}" '
            f'width="{tam}" height="{tam}">{"".join(partes)}</svg>')


def area(poli):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poli, poli[1:] + poli[:1]))) / 2


def centroide(poli):
    return (sum(p[0] for p in poli) / len(poli), sum(p[1] for p in poli) / len(poli))


def separadas(A, B, m):
    """¿Hay al menos `m` entre dos polígonos convexos? (ejes separadores)"""
    for P in (A, B):
        for (ax, ay), (bx, by) in zip(P, P[1:] + P[:1]):
            nx, ny = ay - by, bx - ax
            L = math.hypot(nx, ny)
            if L < 1e-9:
                continue
            pa = [(p[0] * nx + p[1] * ny) / L for p in A]
            pb = [(p[0] * nx + p[1] * ny) / L for p in B]
            if min(pb) - max(pa) >= m or min(pa) - max(pb) >= m:
                return True
    return False


def svg_desarmado(tam, cx, cy, R, barrios_hojas, fronteras, avenidas, deform, forma, suelta):
    """El mosaico de svg_mosaico() a medio armar: piezas sueltas.

    Sin clipPath: cada manzana se corta en Python por su barrio y por las
    avenidas, y cada trozo es una pieza. El centro queda armado; hacia el
    borde las piezas derivan hacia afuera, giran y algunas faltan o quedan
    fuera del círculo. Las avenidas se abren como grietas. Cada pieza lleva
    debajo su calle negra: sobre papel se leen como losetas.

    suelta: semilla, inicio (fracción de R donde empieza a desarmarse),
    deriva, grieta, giro (grados), p_suelta, lejos (deriva de las sueltas),
    p_falta, margen (lienzo extra por lado) y calle (borde negro de cada pieza)."""
    rng = random.Random(suelta["semilla"])
    formas = random.Random(forma["semilla"])
    lineas = list(fronteras) + list(avenidas)
    assert all(isinstance(L, Linea) for L in lineas)
    piezas = []                                   # (color, radio, puntos)
    for ang, signos, hojas in barrios_hojas:
        mundo = rotador(ang, cx, cy)
        for (c, r), polis in sorted(manzanas(hojas, mundo, lambda x, y: (x, y), forma, formas).items()):
            for poli in polis:
                trozos = [poli]
                for i, L in enumerate(lineas):
                    m = L.hw + r
                    sg = signos.get(i)
                    lados = (sg,) if sg else (1, -1)
                    trozos = [semiplano(t, lambda p, L=L, s=s: s * L.dist(*p) - m)
                              for t in trozos for s in lados]
                for t in trozos:
                    # Recorte circular: las piezas del borde guardan su arco.
                    for j in range(72):
                        a = math.radians(j * 5)
                        t = semiplano(t, lambda p, a=a: R - r - (p[0] - cx) * math.cos(a)
                                      - (p[1] - cy) * math.sin(a))
                    if len(t) < 3 or area(t) < 1:
                        continue
                    piezas.append((c, r, [deform(*p) for p in t]))

    a, b = suelta["inicio"], 1.0
    lim = (-suelta["margen"] + 2, tam + suelta["margen"] - 2)
    # Del centro hacia afuera: las sueltas buscan lugar entre las ya puestas.
    piezas.sort(key=lambda k: math.hypot(*(v - w for v, w in zip(centroide(k[2]), (cx, cy)))))
    calle = suelta["calle"]
    grupos, fondo, puestas = {}, {}, []
    for c, r, t in piezas:
        x, y = centroide(t)
        d = math.hypot(x - cx, y - cy)
        u = min(1.0, max(0.0, (d / R - a) / (b - a)))
        e = u * u * (3 - 2 * u)                   # 0 en el centro, 1 en el borde
        if e > 0.6 and rng.random() < suelta["p_falta"] * e:
            continue
        # Grieta: cada lado de cada avenida se aparta de ella.
        dx = dy = 0.0
        for L in lineas:
            s = 1 if L.dist(x, y) >= 0 else -1
            k = suelta["grieta"] * (0.35 + 0.65 * e)
            dx, dy = dx + s * k * L.n[0], dy + s * k * L.n[1]
        # Deriva hacia afuera, más fuerte cuanto más lejos del centro.
        rumbo = math.atan2(y - cy, x - cx) + math.radians(rng.uniform(-25, 25))
        lejos = suelta["deriva"] * e * rng.uniform(0.6, 1.4)
        if e > 0.75 and rng.random() < suelta["p_suelta"]:
            lejos = rng.uniform(*suelta["lejos"])
        giro = math.radians(rng.uniform(-1, 1) * suelta["giro"] * e)
        # Dentro del lienzo y sin montarse sobre otra pieza: si choca, prueba
        # otro rumbo más corto; si no encuentra lugar, la pieza falta.
        for intento in range(16):
            co, si = math.cos(giro), math.sin(giro)
            mx, my = dx + lejos * math.cos(rumbo), dy + lejos * math.sin(rumbo)
            nuevo = [(x + mx + co * (p[0] - x) - si * (p[1] - y),
                      y + my + si * (p[0] - x) + co * (p[1] - y)) for p in t]
            if (all(lim[0] + r <= v <= lim[1] - r for p in nuevo for v in p)
                    and all(separadas(nuevo, q, r + rq + 0.4) for rq, q in puestas)):
                break
            rumbo += math.radians(rng.uniform(-40, 40))
            lejos *= 0.85
            giro *= 0.8
        else:
            continue
        puestas.append((r, nuevo))
        grupos.setdefault((c, r), []).append(nuevo)
        fondo.setdefault(r + calle, []).append(nuevo)

    cuerpo = []
    for (c, r), polis in sorted(grupos.items()):
        trazo = f' stroke="{PALETA[c]}" stroke-width="{n(2 * r)}"' if r else ""
        cuerpo.append(f'<path fill="{PALETA[c]}"{trazo} d="{trazos_poligonos(polis, forma["prec"])}"/>')
    calles = "".join(f'<path stroke-width="{n(2 * a)}" d="{trazos_poligonos(p, forma["prec"])}"/>'
                     for a, p in sorted(fondo.items()))
    m, lado = suelta["margen"], tam + 2 * suelta["margen"]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-m} {-m} {lado} {lado}" '
            f'width="{lado}" height="{lado}"><g stroke-linejoin="round">'
            f'<g fill="{NEGRO}" stroke="{NEGRO}">{calles}</g>{"".join(cuerpo)}</g></svg>')


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto + "\n")
    print(f"{os.path.relpath(ruta, RAIZ):40s} {len(texto.encode()) + 1:6d} B")


def contar(bh):
    return sum(len(h) for _, _, h in bh)


# --------------------------------------------------------------------------
# Piezas
# --------------------------------------------------------------------------

def portada():
    rng = random.Random(2038)
    cx = cy = 300
    tono = Campo(rng, 520, n=4, contraste=0.55)
    dens = Campo(rng, 380, n=3)

    def color(x, y, desfase):
        v = tono(x, y) * 10.6 - 0.3 + desfase + rng.gauss(0, 0.75)
        return int(min(10, max(0, round(v))))

    fronteras = [Linea(318, 262, 31, 5), Linea(262, 318, 112, 4.5)]
    avenidas = [Linea(300, 430, -9, 3.5),
                Curva((20, 150), (250, 205), (430, 40), 3)]
    barrios = [(0, {0: 1, 1: 1}), (17, {0: 1, 1: -1}),
               (-23, {0: -1, 1: 1}), (17, {0: -1, 1: -1})]
    cfg = dict(q=1, densidad=dens, tmin=11, tmax=40, largo_max=40, corto_max=28,
               min=4, manzana=90, ruido_manzana=0.8, vacio=0.03, p_largo=0.85,
               gaps=[(160, 4), (70, 3), (0, 2)])
    bh = mosaico(rng, cx, cy, 296, barrios, fronteras, avenidas, color, cfg)
    # Semilla aparte: la deformación no altera la composición.
    deform = Deformacion(random.Random(2039), 14, 180, cx, cy, 300)
    forma = dict(k=0.45, radios=[1.5, 3, 5, 7], prec=1, paso_av=24, semilla=2040,
                 irregular=0.1)
    escribir(os.path.join(IMG, "mosaico-portada.svg"),
             svg_mosaico("mp", 600, cx, cy, 300, 296, bh, fronteras, avenidas, deform, forma))
    print(f"  bloques: {contar(bh)}")


# Gama por coordenada: dominante, acento A, acento B.
COORDENADAS = {
    "i": (VINO, ROJO, VIOL, 11),
    "ii": (NAR, NARC, ROJO, 22),
    "iii": (ROJO, VINO, NAR, 33),
    "iv": (TURQ, MENTA, AZUL, 44),
    "v": (AZUL, VIOL, TURQ, 55),
    "juego": (TURQ, MENTA, AMA, 77),
}


def composicion(nombre, gama=None, avenida=None):
    dom, a, b, semilla = gama or COORDENADAS[nombre]
    rng = random.Random(semilla)
    cx = cy = 100
    zona = Campo(rng, 150, n=3, caja=(0, 0, 200, 200))
    dens = Campo(rng, 130, n=3, caja=(0, 0, 200, 200))

    def color(x, y, desfase):
        if rng.random() < 0.035:                    # acento de otra gama
            return rng.randrange(11)
        z = zona(x, y) + desfase * 0.25 + rng.gauss(0, 0.12)
        if z < 0.22:
            return a
        if z > 0.8:
            return b
        return dom

    ang = rng.uniform(20, 60) * rng.choice((1, -1))
    fronteras = [Linea(100 + rng.uniform(-15, 15), 100 + rng.uniform(-15, 15), ang, 2.5)]
    avenidas = []
    if avenida if avenida is not None else nombre in ("ii", "iv", "v", "juego"):
        avenidas.append(Linea(100 + rng.uniform(-30, 30), 100 + rng.uniform(-30, 30),
                              ang + rng.uniform(60, 110), 1.8))
    rot = rng.uniform(10, 25) * rng.choice((1, -1))
    barrios = [(0, {0: 1}), (round(rot, 1), {0: -1})]
    cfg = dict(q=0.5, densidad=dens, tmin=15, tmax=34, largo_max=36, corto_max=24,
               min=3.5, manzana=50, ruido_manzana=0.8, vacio=0.02, p_largo=0.85,
               gaps=[(70, 2.5), (30, 2), (0, 1.5)])
    bh = mosaico(rng, cx, cy, 98, barrios, fronteras, avenidas, color, cfg)
    deform = Deformacion(random.Random(semilla + 1), 5, 70, cx, cy, 100)
    forma = dict(k=0.45, radios=[.5, 1, 2, 3], prec=0.2, paso_av=10, semilla=semilla + 2,
                 irregular=0.1)
    return cx, cy, bh, fronteras, avenidas, deform, forma


def coordenada(nombre):
    cx, cy, bh, fronteras, avenidas, deform, forma = composicion(nombre)
    escribir(os.path.join(IMG, f"mosaico-{nombre}.svg"),
             svg_mosaico(f"m{nombre}", 200, cx, cy, 100, 98, bh, fronteras, avenidas,
                         deform, forma))
    print(f"  bloques: {contar(bh)}")


def desarmado(nombre):
    """Mosaico de la coordenada a medio armar: el del Manual (/el-juego/)."""
    cx, cy, bh, fronteras, avenidas, deform, forma = composicion(nombre)
    suelta = dict(semilla=COORDENADAS[nombre][3] + 3, inicio=0.45, deriva=13, grieta=3.5,
                  giro=32, p_suelta=0.45, lejos=(22, 36), p_falta=0.14, margen=30,
                  calle=1.4)
    escribir(os.path.join(IMG, f"mosaico-{nombre}.svg"),
             svg_desarmado(200, cx, cy, 98, bh, fronteras, avenidas, deform, forma, suelta))
    print(f"  bloques: {contar(bh)}")


# Una pieza por tema en «Momento, mosaico y presente alternativo» (/el-juego/):
# el mosaico entero, el momento que lo abre por sus avenidas y el presente
# alternativo que nace del cruce, con los colores de ambos.
TEMAS = {
    "mosaico": (AZUL, TURQ, VIOL, 91),
    "momento": (ROJO, VINO, NAR, 92),
    "presente": (AMA, TURQ, ROJO, 93),
}


def tema(nombre):
    cx, cy, bh, fronteras, avenidas, deform, forma = composicion(nombre, TEMAS[nombre], True)
    ruta = os.path.join(IMG, f"pieza-{nombre}.svg")
    if nombre == "momento":
        # Sin deriva: solo se abren las grietas de las avenidas.
        suelta = dict(semilla=TEMAS[nombre][3] + 3, inicio=0.99, deriva=0, grieta=11,
                      giro=0, p_suelta=0, lejos=(0, 0), p_falta=0, margen=6, calle=1.4)
        escribir(ruta, svg_desarmado(200, cx, cy, 98, bh, fronteras, avenidas, deform,
                                     forma, suelta))
    else:
        escribir(ruta, svg_mosaico(f"p{nombre[:3]}", 200, cx, cy, 100, 98, bh, fronteras,
                                   avenidas, deform, forma))
    print(f"  bloques: {contar(bh)}")


def grano():
    """Franja 240×12 que empalma en horizontal (ningún bloque cruza los bordes)."""
    rng = random.Random(12)
    rects = []
    orden = list(range(11))
    for carril_y in (1, 7):
        x = 1.0
        i = rng.randrange(11)
        while True:
            w = rng.choice((2, 2, 3, 3, 4, 5, 6, 7, 9))
            if x + w > 239:
                break
            h = rng.choice((2, 3, 3, 4, 5))
            y = carril_y + rng.choice((0, 0, 1)) if h < 5 else carril_y
            if rng.random() > 0.1:
                # Deriva lenta por la paleta: tramos de color, no confeti.
                i = (i + rng.choice((-1, 0, 0, 1, 1, 2))) % 11
                rects.append((orden[i], x, y, w, min(h, 5)))
            x += w + rng.choice((1, 1, 2, 2, 3))
    usados = {c for c, *_ in rects}
    assert usados == set(range(11)), usados
    cuerpo = por_color(rects)
    escribir(os.path.join(IMG, "grano.svg"),
             f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 12" '
             f'width="240" height="12">{cuerpo}</svg>')


def favicon():
    rng = random.Random(64)
    cx = cy = 32
    tono = Campo(rng, 70, n=3, caja=(0, 0, 64, 64), contraste=0.5)
    dens = Campo(rng, 60, n=2, caja=(0, 0, 64, 64))

    def color(x, y, desfase):
        v = tono(x, y) * 10.6 - 0.3 + desfase + rng.gauss(0, 1.1)
        return int(min(10, max(0, round(v))))

    fronteras = [Linea(33, 31, -38, 1.5)]
    barrios = [(0, {0: 1}), (14, {0: -1})]
    cfg = dict(q=0.5, densidad=dens, tmin=11, tmax=15, largo_max=15, corto_max=11,
               min=3, manzana=18, ruido_manzana=1.2, vacio=0.0, p_largo=0.8,
               gaps=[(24, 2), (0, 1.5)])
    bh = mosaico(rng, cx, cy, 26, barrios, fronteras, [], color, cfg)
    deform = Deformacion(random.Random(65), 1.5, 30, cx, cy, 26)
    forma = dict(k=0.45, radios=[.5, 1, 1.5], prec=0.5, paso_av=4, semilla=66, irregular=0.15)
    cuerpo = svg_mosaico("f", 64, cx, cy, 26, 26, bh, fronteras, [], deform, forma,
                         fondo_circulo=False)
    cuerpo = cuerpo.replace('width="64" height="64">',
                            f'width="64" height="64"><rect width="64" height="64" rx="12" fill="{NEGRO}"/>', 1)
    escribir(os.path.join(RAIZ, "public", "favicon.svg"), cuerpo)
    print(f"  bloques: {contar(bh)}")


if __name__ == "__main__":
    portada()
    for c in COORDENADAS:
        desarmado(c) if c == "juego" else coordenada(c)
    for t in TEMAS:
        tema(t)
    grano()
    favicon()
