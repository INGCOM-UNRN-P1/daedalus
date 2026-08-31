"""Módulo de expansión y explicación pedagógica de macros en DAEDALUS."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def expandir_macro(
    fuente: Path,
    nombre_macro: Optional[str] = None,
    compilador: Optional[str] = None,
) -> Dict[str, str]:
    """Expande macros del preprocesador paso a paso y extrae definiciones."""
    cc = compilador or "gcc"
    fuente = Path(fuente)
    if not fuente.is_file():
        return {"error": f"El archivo '{fuente}' no existe."}

    # 1. Obtener definiciones de macros con gcc -E -dD
    cmd = [cc, "-E", "-dD", "-P", str(fuente)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            return {"error": f"Error del preprocesador: {res.stderr}"}
    except Exception as e:
        return {"error": f"Fallo al invocar compilador: {e}"}

    lineas = res.stdout.splitlines()
    macros_encontradas: Dict[str, str] = {}
    macro_re = re.compile(r"^#define\s+([a-zA-Z0-9_]+(?:\([^\)]*\))?)\s+(.+)$")

    for l in lineas:
        m = macro_re.match(l.strip())
        if m:
            clave = m.group(1).strip()
            cuerpo = m.group(2).strip()
            macros_encontradas[clave] = cuerpo

    # 2. Código preprocesado limpio
    cmd_clean = [cc, "-E", "-P", str(fuente)]
    try:
        res_clean = subprocess.run(cmd_clean, capture_output=True, text=True, timeout=10)
        codigo_expandido = "\n".join([line for line in res_clean.stdout.splitlines() if line.strip()])
    except Exception:
        codigo_expandido = res.stdout

    resultado = {
        "codigo_expandido": codigo_expandido,
        "total_macros": str(len(macros_encontradas)),
    }

    if nombre_macro:
        macro_pura = nombre_macro.split("(")[0]
        coincidencias = {k: v for k, v in macros_encontradas.items() if k.startswith(macro_pura)}
        if coincidencias:
            resultado["macro_seleccionada"] = str(coincidencias)
        else:
            resultado["macro_seleccionada"] = f"Macro '{nombre_macro}' no encontrada explícitamente en el fuente."
    else:
        resultado["macros"] = str(macros_encontradas)

    return resultado
