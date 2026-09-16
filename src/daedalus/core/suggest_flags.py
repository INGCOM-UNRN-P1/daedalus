"""Sugerencia didáctica de flags de compilación y enlazado faltantes para ESPER."""

from __future__ import annotations
import re
from typing import List, Dict, Tuple, Any
from daedalus.core.models import DiagnosticoCompilacion


MATH_SYMBOLS = {"sin", "cos", "tan", "sqrt", "pow", "fabs", "ceil", "floor", "log", "exp", "asin", "acos", "atan", "fmod"}
PTHREAD_SYMBOLS = {"pthread_create", "pthread_join", "pthread_mutex_init", "pthread_mutex_lock", "pthread_mutex_unlock"}
POSIX_FUNCTIONS = {"strdup", "getline", "getdelim", "strtok_r", "dprintf"}


def analyze_missing_flags(raw_stderr: str, diagnostics: List[Any] | None = None) -> List[Dict[str, str]]:
    """Analiza la salida de error e infiere flags faltantes de GCC/Clang."""
    suggestions: List[Dict[str, str]] = []
    seen_flags = set()

    # 1. Chequeo de símbolos de math.h en errores de enlazado
    for sym in MATH_SYMBOLS:
        if f"undefined reference to `{sym}'" in raw_stderr or f"undefined reference to '{sym}'" in raw_stderr:
            if "-lm" not in seen_flags:
                suggestions.append({
                    "flag": "-lm",
                    "reason": f"Se utilizó la función matemática '{sym}()' de <math.h> pero falta enlazar la biblioteca libm.",
                    "fix": "Agregá '-lm' al final de la línea de compilación: gcc main.c -o app -lm"
                })
                seen_flags.add("-lm")

    # 2. Chequeo de hilos POSIX
    for sym in PTHREAD_SYMBOLS:
        if f"undefined reference to `{sym}'" in raw_stderr or f"undefined reference to '{sym}'" in raw_stderr:
            if "-pthread" not in seen_flags:
                suggestions.append({
                    "flag": "-pthread",
                    "reason": f"Se utilizó la función de hilos '{sym}()' de <pthread.h> pero falta habilitar soporte multihilo.",
                    "fix": "Agregá '-pthread' al compilar: gcc -pthread main.c -o app"
                })
                seen_flags.add("-pthread")

    # 3. Chequeo de funciones POSIX que requieren feature test macro
    for fn in POSIX_FUNCTIONS:
        if f"implicit declaration of function ‘{fn}’" in raw_stderr or f"implicit declaration of function '{fn}'" in raw_stderr:
            macro = "-D_POSIX_C_SOURCE=200809L"
            if macro not in seen_flags:
                suggestions.append({
                    "flag": macro,
                    "reason": f"La función '{fn}()' es una extensión POSIX que requiere definir la macro de características correspondiente.",
                    "fix": f"Agregá '#define _POSIX_C_SOURCE 200809L' antes de los #include o compilá con '{macro}'."
                })
                seen_flags.add(macro)

    # 4. Chequeo de estándares faltantes (ej: variables dentro del for o comentarios //)
    if "for' loop initial declarations are only allowed in C99" in raw_stderr:
        if "-std=c11" not in seen_flags:
            suggestions.append({
                "flag": "-std=c11",
                "reason": "Se declararon variables dentro del encabezado del lazo for (permitido a partir de C99).",
                "fix": "Compilá con el estándar canónico de cátedra: gcc -std=c11 -Wall -Wextra -Wpedantic main.c -o app"
            })
            seen_flags.add("-std=c11")

    return suggestions
