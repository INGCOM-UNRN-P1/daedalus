"""Motor de compilación pedagógica con GCC/Clang en DAEDALUS."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from daedalus.core.models import ResultadoCompilacion
from daedalus.core.translator import parsear_stderr_compilador

FLAGS_CATEDRA_DEFAULT = [
    "-std=c11",
    "-Wall",
    "-Wextra",
    "-pedantic",
    "-Wconversion",
    "-Werror=implicit-function-declaration",
    "-Werror=return-type",
    "-g",
    "-O0",
]


def compilar_archivos(
    fuentes: List[Path],
    binario_salida: Optional[Path] = None,
    flags_adicionales: Optional[List[str]] = None,
    compilador: Optional[str] = None,
    timeout: int = 10,
) -> ResultadoCompilacion:
    """Compila una lista de archivos fuente C aplicando flags estrictos y traduciendo errores."""
    cc = compilador or shutil.which("gcc") or shutil.which("clang") or "gcc"

    # Validar existencia de archivos
    for f in fuentes:
        if not Path(f).is_file():
            return ResultadoCompilacion(
                exito=False,
                codigo_retorno=2,
                stderr_crudo=f"El archivo fuente '{f}' no existe.",
            )

    out_file = binario_salida or Path(tempfile.mktemp(prefix="daedalus_bin_"))

    cmd = [cc] + FLAGS_CATEDRA_DEFAULT
    if flags_adicionales:
        cmd.extend(flags_adicionales)
    cmd.extend([str(Path(f).resolve()) for f in fuentes])
    cmd.extend(["-o", str(out_file.resolve()), "-lm"])

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        diagnosticos = parsear_stderr_compilador(res.stderr)
        exito = (res.returncode == 0)

        return ResultadoCompilacion(
            exito=exito,
            codigo_retorno=res.returncode,
            binario=out_file if exito else None,
            diagnosticos=diagnosticos,
            stdout_crudo=res.stdout,
            stderr_crudo=res.stderr,
        )
    except subprocess.TimeoutExpired:
        return ResultadoCompilacion(
            exito=False,
            codigo_retorno=124,
            stderr_crudo="La compilación excedió el tiempo límite permitido (Timeout).",
        )
    except Exception as e:
        return ResultadoCompilacion(
            exito=False,
            codigo_retorno=1,
            stderr_crudo=f"Error inesperado al ejecutar el compilador: {e}",
        )
