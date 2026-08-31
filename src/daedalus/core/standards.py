"""Módulo de verificación multi-estándar C y sugerencia de flags en DAEDALUS."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from daedalus.core.compiler import FLAGS_CATEDRA_DEFAULT


ESTANDARES_C = ["c99", "c11", "c17", "c2x"]


def verificar_compatibilidad_estandares(
    fuente: Path,
    compilador: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """Compila el fuente contra múltiples estándares ISO C (C99, C11, C17, C2x/C23) y compara diagnósticos."""
    cc = compilador or shutil.which("gcc") or "gcc"
    fuente = Path(fuente)
    if not fuente.is_file():
        return {"error": {"valido": False, "mensaje": f"Archivo '{fuente}' no encontrado."}}

    resultados: Dict[str, Dict[str, Any]] = {}

    for std in ESTANDARES_C:
        cmd = [
            cc,
            f"-std={std}",
            "-Wall",
            "-Wextra",
            "-pedantic",
            "-fsyntax-only",
            str(fuente.resolve()),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            resultados[std] = {
                "valido": res.returncode == 0,
                "errores": res.stderr.strip() if res.returncode != 0 else "",
                "advertencias": [l for l in res.stderr.splitlines() if "warning:" in l],
            }
        except Exception as e:
            resultados[std] = {
                "valido": False,
                "errores": str(e),
                "advertencias": [],
            }

    return resultados


def sugerir_flags_pedagogicos(
    flags_actuales: Optional[List[str]] = None,
    makefile_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Analiza los flags de compilación actuales o de un Makefile y sugiere banderas de cátedra faltantes."""
    flags_detectados = list(flags_actuales or [])

    if makefile_path and Path(makefile_path).is_file():
        try:
            contenido = Path(makefile_path).read_text(encoding="utf-8")
            for linea in contenido.splitlines():
                if linea.startswith("CFLAGS") or "CFLAGS" in linea:
                    partes = linea.split("=", 1)
                    if len(partes) > 1:
                        flags_detectados.extend(partes[1].strip().split())
        except Exception:
            pass

    flags_set = set(flags_detectados)
    faltantes: List[str] = []
    recomendaciones: Dict[str, str] = {
        "-Wall": "Habilita advertencias sobre construcciones cuestionables y errores comunes.",
        "-Wextra": "Habilita advertencias complementarias rigurosas (comparaciones con signo, variables no usadas).",
        "-pedantic": "Exige estricto apego al estándar ISO C, rechazando extensiones no portables de GNU.",
        "-std=c11": "Fija el estándar C11 obligatorio de cátedra.",
        "-g": "Incluye símbolos de depuración DWARF para diagnósticos con GDB y HAL.",
        "-Wconversion": "Advierte conversiones implícitas de tipos que puedan alterar valores o perder precisión.",
        "-Werror=implicit-function-declaration": "Impide usar funciones sin prototipo previo declarado en cabeceras.",
    }

    for flag, motivo in recomendaciones.items():
        if flag not in flags_set:
            faltantes.append(flag)

    cumple_estricto = len(faltantes) == 0

    return {
        "flags_detectados": flags_detectados,
        "flags_faltantes": faltantes,
        "cumple_estricto": cumple_estricto,
        "explicaciones": {f: recomendaciones[f] for f in faltantes if f in recomendaciones},
    }
