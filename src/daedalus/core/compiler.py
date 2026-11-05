"""Motor de compilación pedagógica con GCC/Clang en DAEDALUS."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Sequence

from daedalus.core.models import DiagnosticoCompilacion, ResultadoCompilacion
from daedalus.core.translator import parsear_stderr_compilador, traducir_desde_sarif

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


# Las reglas de traducción reconocen los mensajes en inglés. Con un locale en español (y gcc o
# binutils con sus traducciones instaladas) el compilador decía «referencia a `g' sin definir» y el
# alumno se quedaba sin explicación: se fija el idioma del compilador, no el de la terminal.
ENTORNO_COMPILADOR = {"LC_ALL": "C"}


def _faltan_sanitizers(stderr: str) -> bool:
    return "cannot find" in stderr and any(s in stderr for s in SIN_SANITIZERS)


def _correr(cmd: List[str], timeout: int, aislar: bool, fuentes: List[Path], salida: Path):
    """(retorno, stdout, stderr, aislado) de un comando de compilación, aislado o no."""
    if not aislar:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=timeout, env={**os.environ, **ENTORNO_COMPILADOR})
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
    # nostromo hereda el entorno y no deja pasar uno propio: el idioma se fija con `env`.
    fijar_idioma = ["env", *(f"{k}={v}" for k, v in ENTORNO_COMPILADOR.items())] if shutil.which("env") else []
    r = ejecutar_comando_aislado([*fijar_idioma, *cmd], escribibles=[salida.resolve().parent], legibles=legibles,
                                 directorio=salida.resolve().parent, timeout_segundos=timeout)
    if r.error_tipo == "TIMEOUT":
        raise subprocess.TimeoutExpired(cmd, timeout)
    return r.codigo_retorno, r.stdout, r.stderr, r.aislado


class _SinSandbox(RuntimeError):
    pass


FLAG_SARIF = "-fdiagnostics-format=sarif-stderr"


@lru_cache(maxsize=None)
def soporta_sarif(compilador: str = "gcc") -> bool:
    """Si `compilador` emite SARIF por stderr: GCC 13 o posterior. Clang rechaza el flag y queda con
    el camino de texto."""
    try:
        res = subprocess.run([compilador, FLAG_SARIF, "-x", "c", "-fsyntax-only", "-"], input="",
                             capture_output=True, text=True, timeout=5, env={**os.environ, **ENTORNO_COMPILADOR})
    except (OSError, subprocess.SubprocessError):
        return False
    return res.returncode == 0


def _diagnosticos_sarif(cc: str, opciones: List[str], fuentes: Sequence[Path], salida: Path, timeout: int,
                        aislar: bool) -> Optional[List[DiagnosticoCompilacion]]:
    """Los diagnósticos de compilación leídos de SARIF, o None si hay que quedarse con los del texto.

    Es una pasada aparte porque SARIF reemplaza al texto en stderr, y `stderr_crudo` lo leen ripley,
    dredd, tetsuo y sebastian. Va una fuente por vez porque `-c` con varias no admite `-o`, y `-c` y no
    `-fsyntax-only` porque este último saltea las advertencias del optimizador (`-Wuninitialized`).
    """
    if not soporta_sarif(cc) or any(f.suffix != ".c" for f in fuentes):
        return None
    objeto = salida.with_name(salida.name + ".diag.o")
    diagnosticos: List[DiagnosticoCompilacion] = []
    try:
        for fuente in fuentes:
            cmd = [cc, *opciones, FLAG_SARIF, "-c", str(fuente), "-o", str(objeto)]
            _, _, stderr, _ = _correr(cmd, timeout, aislar, list(fuentes), salida)
            de_la_fuente = traducir_desde_sarif(stderr)
            if de_la_fuente is None:
                return None
            diagnosticos.extend(de_la_fuente)
    except (OSError, subprocess.SubprocessError, _SinSandbox):
        return None
    finally:
        objeto.unlink(missing_ok=True)
    return diagnosticos


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
        opciones = base
        ret, stdout, stderr, aislado = _correr(comando(opciones), timeout, aislar, fuentes_abs, out_file)
        sin_sanitizers = False
        if ret != 0 and reintentar_sin_sanitizers and _faltan_sanitizers(stderr):
            opciones = [f for f in base if not f.startswith("-fsanitize=")]
            ret, stdout, stderr, aislado = _correr(comando(opciones), timeout, aislar, fuentes_abs, out_file)
            sin_sanitizers = True
        diagnosticos = parsear_stderr_compilador(stderr)
        motor = "texto"
        if stderr.strip():
            del_texto = [d for d in diagnosticos if d.linea is not None]
            de_sarif = _diagnosticos_sarif(cc, opciones, fuentes_abs, out_file, timeout, aislar)
            # Una pasada SARIF vacía con diagnósticos en el texto no es creíble: vale el texto.
            if de_sarif is not None and (de_sarif or not del_texto):
                # Lo que no tiene línea es del enlazador, que no emite SARIF.
                diagnosticos = de_sarif + [d for d in diagnosticos if d.linea is None]
                motor = "sarif"
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
            motor=motor,
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
