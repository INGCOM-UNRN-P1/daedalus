"""Motor de compilación pedagógica con GCC/Clang en DAEDALUS."""

from __future__ import annotations

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


# Señales de que el toolchain no trae los sanitizers (glibc: «cannot find libasan…»; MinGW:
# «cannot find -lasan», el caso de MSYS2 UCRT64).
SIN_SANITIZERS = ("libasan", "libubsan", "-lasan", "-lubsan")


def _faltan_sanitizers(stderr: str) -> bool:
    return "cannot find" in stderr and any(s in stderr for s in SIN_SANITIZERS)


def _correr(cmd: List[str], timeout: int, aislar: bool, fuentes: List[Path], salida: Path):
    """(retorno, stdout, stderr, aislado) de un comando de compilación, aislado o no."""
    if not aislar:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return res.returncode, res.stdout, res.stderr, None
    try:
        from nostromo.core.sandbox import ejecutar_comando_aislado
    except ImportError as exc:  # nostromo ausente o anterior a ejecutar_comando_aislado
        raise _SinSandbox(
            "Se pidió compilar aislado y nostromo no está instalado (o es anterior a "
            "ejecutar_comando_aislado): instalalo desde git junto con daedalus."
        ) from exc
    # Además de las carpetas de las fuentes, las de los -I (headers de la actividad o de una librería).
    incluidas = [Path(o[2:]) for o in cmd if o.startswith("-I") and len(o) > 2]
    incluidas += [Path(cmd[i + 1]) for i, o in enumerate(cmd[:-1]) if o == "-I"]
    legibles = sorted({f.resolve().parent for f in fuentes} | {d.resolve() for d in incluidas if d.is_dir()})
    r = ejecutar_comando_aislado(cmd, escribibles=[salida.resolve().parent], legibles=legibles,
                                 directorio=salida.resolve().parent, timeout_segundos=timeout)
    if r.error_tipo == "TIMEOUT":
        raise subprocess.TimeoutExpired(cmd, timeout)
    return r.codigo_retorno, r.stdout, r.stderr, r.aislado


class _SinSandbox(RuntimeError):
    pass


def compilar_archivos(
    fuentes: List[Path],
    binario_salida: Optional[Path] = None,
    flags_adicionales: Optional[List[str]] = None,
    compilador: Optional[str] = None,
    timeout: int = 10,
    flags: Optional[List[str]] = None,
    aislar: bool = False,
    reintentar_sin_sanitizers: bool = False,
) -> ResultadoCompilacion:
    """Compila `fuentes` y traduce los diagnósticos.

    - `flags`: reemplaza a los flags de cátedra (los de una actividad, por ejemplo);
      `flags_adicionales` se agregan después de unos u otros.
    - `aislar`: compila dentro del sandbox de nostromo (bwrap: el código no ve archivos
      fuera de sus fuentes, como un `#include` absoluto a la solución). Si nostromo no está,
      falla en lugar de compilar sin aislar; si bwrap no arranca, compila con límites de
      recursos y el resultado trae `aislado=False`.
    - `reintentar_sin_sanitizers`: si el toolchain no trae libasan/libubsan (MSYS2), reintenta
      sin `-fsanitize=…` y lo marca en `sin_sanitizers`.
    """
    cc = compilador or "gcc"

    # Validar existencia de archivos
    for f in fuentes:
        if not Path(f).is_file():
            return ResultadoCompilacion(
                exito=False,
                codigo_retorno=2,
                stderr_crudo=f"El archivo fuente '{f}' no existe.",
            )

    if binario_salida:
        out_file = binario_salida
    else:
        with tempfile.NamedTemporaryFile(prefix="daedalus_bin_", delete=False) as tf:
            out_file = Path(tf.name)

    base = list(FLAGS_CATEDRA_DEFAULT if flags is None else flags) + list(flags_adicionales or [])
    fuentes_abs = [Path(f).resolve() for f in fuentes]

    def comando(opciones: List[str]) -> List[str]:
        return [cc, *opciones, *map(str, fuentes_abs), "-o", str(out_file.resolve()), "-lm"]

    try:
        ret, stdout, stderr, aislado = _correr(comando(base), timeout, aislar, fuentes_abs, out_file)
        sin_sanitizers = False
        if ret != 0 and reintentar_sin_sanitizers and _faltan_sanitizers(stderr):
            limpias = [f for f in base if not f.startswith("-fsanitize=")]
            ret, stdout, stderr, aislado = _correr(comando(limpias), timeout, aislar, fuentes_abs, out_file)
            sin_sanitizers = True
        diagnosticos = parsear_stderr_compilador(stderr)
        exito = (ret == 0)

        return ResultadoCompilacion(
            exito=exito,
            codigo_retorno=ret,
            binario=out_file if exito else None,
            diagnosticos=diagnosticos,
            stdout_crudo=stdout,
            stderr_crudo=stderr,
            aislado=aislado,
            sin_sanitizers=sin_sanitizers,
        )
    except _SinSandbox as e:
        return ResultadoCompilacion(exito=False, codigo_retorno=2, stderr_crudo=str(e), aislado=False)
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
