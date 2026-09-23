"""Filtro de supresión de advertencias repetitivas y en cascada para DAEDALUS."""

from __future__ import annotations
from typing import List, Tuple
from daedalus.core.models import DiagnosticoCompilacion


def filter_and_deduplicate(
    diagnostics: List[DiagnosticoCompilacion],
    max_per_type: int = 2,
    suppress_header_cascades: bool = True,
) -> Tuple[List[DiagnosticoCompilacion], int]:
    """Filtra y deduplica advertencias repetitivas o en cascada para no abrumar al estudiante.

    Retorna: (diagnosticos_filtrados, cantidad_suprimidos)
    """
    seen_counts: dict[str, int] = {}
    filtered: List[DiagnosticoCompilacion] = []
    suppressed_count = 0

    first_error_file = None
    for d in diagnostics:
        if d.severidad == "error":
            first_error_file = d.archivo
            break

    for d in diagnostics:
        file_key = d.archivo or "compilador"
        key = f"{file_key}:{d.flag or d.titulo}"

        # 1. Supresión de cascadas: si hubo un error en un .h y este es un warning/note en otro archivo
        if suppress_header_cascades and first_error_file and first_error_file.endswith(".h") and not file_key.endswith(".h"):
            if d.severidad in ("note", "warning") or "previous declaration" in d.mensaje_original.lower():
                suppressed_count += 1
                continue

        # 2. Control de repeticiones máximas del mismo tipo
        count = seen_counts.get(key, 0)
        if count >= max_per_type:
            suppressed_count += 1
            continue

        seen_counts[key] = count + 1
        filtered.append(d)

    return filtered, suppressed_count
