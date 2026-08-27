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
        r"undefined reference to `(?P<name>[^']+)'",
        "Símbolo no encontrado al enlazar (linker): `{name}`",
        "El compilador encontró la declaración pero `ld` no halló la implementación binaria.",
        "Asegurate de compilar todos los archivos `.c` involucrados o agregar las banderas de librerías (ej. `-lm`).",
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

_GCC_LINE_RE = re.compile(
    r"^(?P<file>[^:\n]+):(?P<line>\d+):(?:(?P<col>\d+):)?\s*(?P<kind>error|warning|note|fatal error):\s*(?P<msg>.+)$"
)


def traducir_linea_diagnostico(mensaje: str) -> Tuple[str, str, str]:
    """Traduce un mensaje de compilador a título, explicación y sugerencia didáctica."""
    for pattern, tit_tpl, exp_tpl, sug_tpl in REGLAS_TRADUCCION:
        m = re.search(pattern, mensaje, re.IGNORECASE)
        if m:
            groups = m.groupdict()
            titulo = tit_tpl.format(**groups) if groups else tit_tpl
            explicacion = exp_tpl.format(**groups) if groups else exp_tpl
            sugerencia = sug_tpl.format(**groups) if groups else sug_tpl
            return titulo, explicacion, sugerencia

    # Fallback genérico
    return "Diagnóstico del compilador", mensaje, "Revisá la línea indicada y la sintaxis estándar de C11."


def parsear_stderr_compilador(stderr: str) -> List[DiagnosticoCompilacion]:
    """Parsea el stderr emitido por GCC o Clang y genera la lista de diagnósticos didácticos."""
    diagnosticos: List[DiagnosticoCompilacion] = []
    lineas = stderr.splitlines()

    for l in lineas:
        l_str = l.strip()
        m = _GCC_LINE_RE.match(l_str)
        if m:
            f = m.group("file")
            lin = int(m.group("line"))
            col = int(m.group("col")) if m.group("col") else None
            kind = m.group("kind").lower()
            msg = m.group("msg").strip()

            tit, exp, sug = traducir_linea_diagnostico(msg)
            diagnosticos.append(DiagnosticoCompilacion(
                archivo=f,
                linea=lin,
                columna=col,
                severidad="error" if "error" in kind else "warning" if "warning" in kind else "note",
                mensaje_original=msg,
                titulo=tit,
                explicacion=exp,
                sugerencia=sug,
            ))

    return diagnosticos
