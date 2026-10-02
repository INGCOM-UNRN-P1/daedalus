"""Cada diagnóstico en la taxonomía común del ecosistema (yutani.hallazgos): código estable y
categoría del programa, para que dredd agrupe por cohorte y la devolución enlace al apunte."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from yutani.hallazgos import hallazgo

from daedalus.core.models import DiagnosticoCompilacion

# (expresión sobre el mensaje original, código, categoría): la primera que coincide.
_CLASIFICACION: List[Tuple[str, str, str]] = [
    (r"undefined reference to [`']main'", "falta-main", "enlazado"),
    (r"undefined reference to", "referencia-sin-definir", "enlazado"),
    (r"multiple definition of", "definicion-duplicada", "enlazado"),
    (r"cannot find -l", "biblioteca-no-encontrada", "enlazado"),
    (r"ld returned", "fallo-de-enlace", "enlazado"),
    (r"undeclared", "no-declarado", "declaraciones"),
    (r"implicit declaration of function", "declaracion-implicita", "declaraciones"),
    (r"conflicting types for", "tipos-contradictorios", "declaraciones"),
    (r"isn.t a prototype|no previous prototype", "sin-prototipo", "declaraciones"),
    (r"^expected|expected .* before|at end of input", "sintaxis", "sintaxis"),
    (r"format .* expects|too many arguments for format|format not a string literal", "formato-printf-scanf", "archivos"),
    (r"control reaches end of non-void function|no return statement", "falta-return", "funciones"),
    (r"(may be|is) used uninitialized", "sin-inicializar", "punteros"),
    (r"incompatible pointer type|from .int \*. to .int.|makes (pointer|integer) from", "punteros-incompatibles", "punteros"),
    (r"dereferencing", "desreferencia-invalida", "punteros"),
    (r"comparison between pointer and integer", "puntero-contra-entero", "punteros"),
    (r"array subscript|array index", "indice-de-arreglo", "arreglos"),
    (r"different signedness|sign-compare|overflow|conversion to|conversion from", "conversion-numerica", "numeros"),
    (r"division by zero", "division-por-cero", "numeros"),
    (r"unused variable|unused parameter|set but not used", "sin-usar", "funciones"),
    (r"suggest parentheses around assignment", "asignacion-en-condicion", "control"),
    (r"comparing floating-point", "comparacion-flotantes", "numeros"),
    (r"no such file or directory", "archivo-inexistente", "compilacion"),
]


def clasificar(d: DiagnosticoCompilacion) -> Tuple[str, str]:
    """(código, categoría) del diagnóstico; los que no se reconocen usan su flag de GCC o
    `diagnostico` y la categoría `compilacion`."""
    mensaje = d.mensaje_original or ""
    for patron, codigo, categoria in _CLASIFICACION:
        if re.search(patron, mensaje, re.IGNORECASE):
            return codigo, categoria
    if d.flag:
        return d.flag.lstrip("-W").lstrip("-") or "diagnostico", "compilacion"
    return "diagnostico", "compilacion"


def a_hallazgo(d: DiagnosticoCompilacion) -> Dict[str, Any]:
    codigo, categoria = clasificar(d)
    return hallazgo("daedalus", codigo, categoria, d.severidad, d.titulo, archivo=d.archivo,
                    linea=d.linea, columna=d.columna, sugerencia=d.sugerencia or None)
