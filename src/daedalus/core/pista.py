"""Modo pista (`--pista` o `P1_PISTA=1`): qué tipo de error hay y en qué función, sin la línea ni la corrección.

Revisión 05 §3: en una evaluación, daedalus mostraba siempre la línea culpable y cómo corregirla. En modo
pista cada diagnóstico conserva el título y la explicación del error (lo que hay que entender), dice en
qué función está y oculta la línea, la columna, el mensaje crudo del compilador (que la incluye), el
fragmento de código y la sugerencia. La misma variable activa el modo en hal y tetsuo, y ripley la
exporta a los satélites cuando la práctica lo pide (`[general] pistas = true` en ripley.toml).
"""

from __future__ import annotations

import os
import re
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Optional

from daedalus.core.models import DiagnosticoCompilacion, ResultadoCompilacion

VARIABLE_PISTA = "P1_PISTA"

# Cabecera de una definición de función en la columna 0: el tipo puede estar en la misma línea o en la
# anterior (`static void` / `saludar(...)`) y la llave, en la misma o en la siguiente.
_RE_FUNCION = re.compile(r"^(?!(?:if|else|while|for|switch|return|do|typedef|struct|enum|union)\b)"
                         r"(?:[A-Za-z_][\w\s\*]*?[\s\*])?([A-Za-z_]\w*)\s*\([^;]*$")


def pista_activa(bandera: bool = False) -> bool:
    return bandera or os.environ.get(VARIABLE_PISTA, "").strip().lower() in ("1", "true", "si", "sí", "yes")


def funcion_que_contiene(lineas: List[str], linea: int) -> Optional[str]:
    """La función cuya definición contiene la línea `linea` (1-indexada), o None si está fuera de una."""
    for i in range(min(linea, len(lineas)) - 1, -1, -1):
        texto = lineas[i]
        if texto.startswith("}") and i != linea - 1:
            return None  # se cerró una función antes: la línea está en el ámbito del archivo
        m = _RE_FUNCION.match(texto)
        if m:
            return m.group(1)
    return None


def a_pista(diagnostico: DiagnosticoCompilacion, fuentes: Dict[str, List[str]]) -> DiagnosticoCompilacion:
    funcion = None
    if diagnostico.archivo and diagnostico.linea:
        lineas = fuentes.get(diagnostico.archivo)
        if lineas is None:
            try:
                lineas = Path(diagnostico.archivo).read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                lineas = []
            fuentes[diagnostico.archivo] = lineas
        funcion = funcion_que_contiene(lineas, diagnostico.linea)
    return replace(diagnostico, linea=None, columna=None, mensaje_original="", sugerencia="", code_snippet=None,
                   funcion=funcion)


def resultado_en_pista(resultado: ResultadoCompilacion) -> ResultadoCompilacion:
    fuentes: Dict[str, List[str]] = {}
    return replace(resultado, diagnosticos=[a_pista(d, fuentes) for d in resultado.diagnosticos],
                   stdout_crudo="", stderr_crudo="", pista=True)
