"""DAEDALUS — Compilador pedagógico y traductor de diagnósticos GCC/Clang."""

from __future__ import annotations

from daedalus.core.compiler import compilar_archivos
from daedalus.core.models import DiagnosticoCompilacion, ResultadoCompilacion
from daedalus.core.translator import (
    parsear_stderr_compilador,
    parsear_stderr_compilador as traducir,
    traducir_linea_diagnostico,
)

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "DiagnosticoCompilacion",
    "ResultadoCompilacion",
    "compilar_archivos",
    "parsear_stderr_compilador",
    "traducir",
    "traducir_linea_diagnostico",
]
