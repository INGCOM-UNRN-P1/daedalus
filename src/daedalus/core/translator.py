"""Motor de traducción de diagnósticos de GCC/Clang/ld a español rioplatense didáctico."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple
from daedalus.core.models import DiagnosticoCompilacion

REGLAS_TRADUCCION: List[Tuple[str, str, str, str]] = [
    (
        r"expected .*?;.*? before",
        "Falta un punto y coma (;)",
        "El compilador esperaba un punto y coma antes de continuar: alguna sentencia previa no fue cerrada.",
        "Revisá la línea anterior al error: casi siempre falta `;` al final de una declaración o llamada.",
    ),
    (
        r"expected .*'\}'.*? at end of input|expected declaration",
        "Falta cerrar una llave (})",
        "El archivo terminó sin cerrar todas las llaves de funciones o bloques.",
        "Contá las llaves abiertas vs cerradas; indentá el código para verlas mejor.",
    ),
    (
        r"expected .*'\('.*? before|expected expression before",
        "Paréntesis o expresión incompleta",
        "Hay una estructura de control o llamada con paréntesis desbalanceados o una expresión vacía.",
        "Verificá que cada `if`, `while` o llamada tenga sus paréntesis completos.",
    ),
    (
        r"'(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)' undeclared \(first use in this function\)",
        "Identificador no declarado: `{name}`",
        "Se usó `{name}` pero nunca se declaró. Puede ser un error de tipeo o falta la declaración/prototipo.",
        "Declará `{name}` antes de usarlo o corregí su escritura (C distingue mayúsculas de minúsculas).",
    ),
    (
        r"implicit declaration of function '(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)'",
        "Función usada sin prototipo: `{name}`",
        "Se llamó a `{name}` sin declararla antes.",
        "Incluí la cabecera correspondiente (por ejemplo `<string.h>`) o agregá el prototipo arriba del archivo.",
    ),
    (
        r"conflicting types for '(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)'",
        "Tipos contradictorios para `{name}`",
        "La firma de `{name}` difiere entre su prototipo y su definición.",
        "Compará ambas firmas carácter por carácter; recordá que `char *` no es lo mismo que `const char *`.",
    ),
    (
        r"lvalue required as (left )?operand of assignment",
        "Asignación inválida: lo de la izquierda no es asignable",
        "El lado izquierdo de `=` debe ser una variable modificable, no una constante, literal o expresión.",
        "Ejemplo típico: `if (x = 0)` cuando se quiso comparar, o asignar a un literal.",
    ),
    (
        r"undefined reference to [`'](?P<name>main)'",
        "Falta la función `main`",
        "Se pidió armar un ejecutable, pero ninguno de los archivos compilados define `int main(void)`.",
        "Si el archivo es una biblioteca, compilalo con `-c` (genera un `.o`); si no, revisá que `main` esté escrito así, en minúsculas.",
    ),
    (
        r"undefined reference to [`'](?P<name>[^']+)'",
        "Símbolo no encontrado al enlazar (linker): `{name}`",
        "El compilador conoce el prototipo de `{name}`, pero el enlazador no encontró su definición en ningún archivo compilado.",
        "Compilá también el `.c` que define `{name}` (por ejemplo `gcc main.c lista.c`), revisá que el nombre coincida "
        "exactamente con la definición o agregá la biblioteca que la contiene (por ejemplo `-lm`).",
    ),
    (
        r"multiple definition of [`'](?P<name>[^']+)'",
        "Definición duplicada de `{name}`",
        "`{name}` está definida en más de un archivo: dos `.c`, o un `.h` con la definición incluido por varios `.c`.",
        "Definila en un solo `.c`. En el `.h` dejá solo el prototipo (funciones) o `extern` (variables globales).",
    ),
    (
        r"assignment to '(?P<dst>[^']+)' from incompatible pointer type '(?P<src>[^']+)'",
        "Punteros incompatibles: {dst} ← {src}",
        "Se intentó asignar un puntero a otro de tipo diferente sin casteo explícito.",
        "Verificá los niveles de indirección o el tipo base apuntado.",
    ),
    (
        r"control reaches end of non-void function",
        "Falta 'return' en función no void",
        "La función promete devolver un valor pero hay caminos de ejecución donde no se ejecuta ningún `return`.",
        "Asegurate de que cada rama condicional termine en un `return valor;` explícito.",
    ),
    (
        r"array subscript is not an integer",
        "Índice de vector no entero",
        "Se intentó indexar un arreglo con un tipo no entero (por ejemplo un float o un puntero).",
        "Usá variables enteras (`int`, `size_t`) como índices de arreglos.",
    ),
]

# La ruta puede empezar con una letra de unidad (Windows: «C:\\Users\\…\\tp.c:3:5: error: …»); sin
# contemplarla, el «:» de la unidad cortaba el archivo y no se reconocía ningún diagnóstico.
_GCC_LINE_RE = re.compile(
    r"^(?P<file>(?:[A-Za-z]:)?[^:\n]+):(?P<line>\d+):(?:(?P<col>\d+):)?\s*(?P<kind>error|warning|note|fatal error):\s*(?P<msg>.+)$"
)


from daedalus.core.diagnostic_catalog import lookup_explanation


# GCC y Clang en locale UTF-8 citan los identificadores con comillas
# tipográficas (‘foo’), no con apóstrofos ASCII. Las reglas de traducción se
# escribieron con ASCII, así que sin normalizar no matcheaban justo los
# diagnósticos más frecuentes (no declarado, declaración implícita, tipos
# contradictorios, punteros incompatibles) y el alumno recibía el mensaje
# crudo en inglés. El linker sigue usando `nombre', que se deja intacto.
_COMILLAS_TIPOGRAFICAS = str.maketrans({"\u2018": "'", "\u2019": "'"})


def normalizar_comillas(mensaje: str) -> str:
    """Convierte las comillas tipográficas del compilador a apóstrofos ASCII."""
    return mensaje.translate(_COMILLAS_TIPOGRAFICAS)


def traducir_linea_diagnostico_completo(
    mensaje: str,
) -> Tuple[str, str, str, Optional[str], Optional[str], Optional[str], List[str]]:
    """Traduce un mensaje de compilador retornando:
    (titulo, explicacion, sugerencia, flag, causa_raiz, cita_iso_c, flags_sugeridos)
    """
    mensaje = normalizar_comillas(mensaje)
    cat_title, cat_expl, cat_cause, cat_sugg, cat_flag, cat_cit, cat_flags = lookup_explanation(mensaje)
    has_catalog_match = cat_title != "Diagnóstico de Compilación GCC"

    for pattern, tit_tpl, exp_tpl, sug_tpl in REGLAS_TRADUCCION:
        m = re.search(pattern, mensaje, re.IGNORECASE)
        if m:
            groups = m.groupdict()
            titulo = tit_tpl.format(**groups) if groups else tit_tpl
            explicacion = exp_tpl.format(**groups) if groups else exp_tpl
            sugerencia = sug_tpl.format(**groups) if groups else sug_tpl
            return (
                titulo,
                explicacion,
                sugerencia,
                cat_flag,
                cat_cause if has_catalog_match else None,
                cat_cit,
                cat_flags,
            )

    if has_catalog_match:
        return (
            cat_title,
            cat_expl,
            cat_sugg,
            cat_flag,
            cat_cause,
            cat_cit,
            cat_flags,
        )

    # Fallback genérico
    return (
        "Diagnóstico del compilador",
        mensaje,
        "Revisá la línea indicada y la sintaxis estándar de C11.",
        None,
        None,
        None,
        [],
    )


def traducir_linea_diagnostico(mensaje: str) -> Tuple[str, str, str]:
    """Traduce un mensaje de compilador a título, explicación y sugerencia didáctica."""
    tit, exp, sug, _, _, _, _ = traducir_linea_diagnostico_completo(mensaje)
    return tit, exp, sug


# Mensajes del enlazador (ld, collect2): no tienen la forma archivo:línea, así que _GCC_LINE_RE no los
# reconocía y un error de enlace terminaba sin ningún diagnóstico. ld antepone «in function `f':» en
# una línea aparte y nombra el archivo fuente solo cuando el objeto tiene información de depuración.
_LD_EN_FUNCION_RE = re.compile(r"in function [`'](?P<fn>[^'`]+)':?\s*$")
_LD_MENSAJE_RE = re.compile(r"(?P<msg>(?:undefined reference to|multiple definition of|cannot find -l).*)$")
_LD_ARCHIVO_RE = re.compile(r"(?:^|\s)(?P<file>(?:[A-Za-z]:)?[^\s:(]+\.c):\(")
_LD_FALLO_RE = re.compile(r"ld returned \d+ exit status")


def _diagnostico_de_enlace(linea: str, funcion: Optional[str]) -> Optional[DiagnosticoCompilacion]:
    m = _LD_MENSAJE_RE.search(linea)
    if not m:
        return None
    msg = m.group("msg").strip()
    archivo = _LD_ARCHIVO_RE.search(linea[: m.start()])
    tit, exp, sug, flag, cause, cit, flags_sugg = traducir_linea_diagnostico_completo(msg)
    return DiagnosticoCompilacion(
        archivo=archivo.group("file") if archivo else None,
        linea=None,
        columna=None,
        severidad="error",
        mensaje_original=msg,
        titulo=tit,
        explicacion=exp,
        sugerencia=sug,
        flag=flag,
        causa_raiz=cause,
        cita_iso_c=cit,
        flags_sugeridos=flags_sugg,
        funcion=funcion,
    )


def parsear_stderr_compilador(stderr: str) -> List[DiagnosticoCompilacion]:
    """Parsea el stderr emitido por GCC o Clang y genera la lista de diagnósticos didácticos."""
    diagnosticos: List[DiagnosticoCompilacion] = []
    lineas = stderr.splitlines()
    funcion_ld: Optional[str] = None
    fallo_de_enlace = False

    for l in lineas:
        l_str = normalizar_comillas(l.strip())
        m = _GCC_LINE_RE.match(l_str)
        if not m:
            en_funcion = _LD_EN_FUNCION_RE.search(l_str)
            if en_funcion:
                funcion_ld = en_funcion.group("fn")
                continue
            diag = _diagnostico_de_enlace(l_str, funcion_ld)
            if diag:
                diagnosticos.append(diag)
            elif _LD_FALLO_RE.search(l_str):
                fallo_de_enlace = True
            continue
        if m:
            f = m.group("file")
            lin = int(m.group("line"))
            col = int(m.group("col")) if m.group("col") else None
            kind = m.group("kind").lower()
            msg = m.group("msg").strip()

            tit, exp, sug, flag, cause, cit, flags_sugg = traducir_linea_diagnostico_completo(msg)
            diagnosticos.append(DiagnosticoCompilacion(
                archivo=f,
                linea=lin,
                columna=col,
                severidad="error" if "error" in kind else "warning" if "warning" in kind else "note",
                mensaje_original=msg,
                titulo=tit,
                explicacion=exp,
                sugerencia=sug,
                flag=flag,
                causa_raiz=cause,
                cita_iso_c=cit,
                flags_sugeridos=flags_sugg,
            ))

    if fallo_de_enlace and not any(d.severidad == "error" for d in diagnosticos):
        diagnosticos.append(DiagnosticoCompilacion(
            archivo=None, linea=None, columna=None, severidad="error",
            mensaje_original="ld returned 1 exit status",
            titulo="Falló el enlazado",
            explicacion="El enlazador (ld) no pudo armar el ejecutable; el motivo está en las líneas anteriores del compilador.",
            sugerencia="Compilá con `-v` o mirá la salida completa de gcc para ver qué símbolo o biblioteca falta.",
        ))
    return diagnosticos


def primer_error(diagnosticos: List[DiagnosticoCompilacion]) -> List[DiagnosticoCompilacion]:
    """El primer error (o, si no hay errores, la primera advertencia): los siguientes suelen ser
    consecuencia del primero, y en las primeras semanas conviene arreglar de a uno."""
    for severidad in ("error", "warning"):
        for d in diagnosticos:
            if d.severidad == severidad:
                return [d]
    return diagnosticos[:1]
