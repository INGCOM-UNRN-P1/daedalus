"""Módulo de registro persistente y estadísticas de diagnósticos en DAEDALUS."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


HISTORIAL_PATH_DEFAULT = Path.home() / ".daedalus_history.json"


def registrar_diagnosticos(
    diagnosticos: List[Any],
    fuentes: List[Path],
    historial_path: Optional[Path] = None,
) -> None:
    """Registra los diagnósticos en el historial local persistente."""
    if not diagnosticos:
        return

    path = historial_path or HISTORIAL_PATH_DEFAULT
    datos: List[Dict[str, Any]] = []

    if path.is_file():
        try:
            datos = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            datos = []

    entrada = {
        "timestamp": datetime.now().isoformat(),
        "fuentes": [str(f) for f in fuentes],
        "total_errores": len(diagnosticos),
        "items": [
            {
                "titulo": getattr(d, "titulo", str(d)),
                "severidad": getattr(d, "severidad", "error"),
                "archivo": getattr(d, "archivo", ""),
                "linea": getattr(d, "linea", None),
            }
            for d in diagnosticos
        ],
    }

    datos.append(entrada)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def obtener_estadisticas(historial_path: Optional[Path] = None) -> Dict[str, Any]:
    """Calcula estadísticas agregadas de errores frecuentes a partir del historial."""
    path = historial_path or HISTORIAL_PATH_DEFAULT
    if not path.is_file():
        return {
            "total_sesiones": 0,
            "total_diagnosticos": 0,
            "frecuencia_errores": {},
            "historial": [],
        }

    try:
        datos: List[Dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        datos = []

    total_diags = 0
    frecuencias: Dict[str, int] = {}

    for sesion in datos:
        items = sesion.get("items", [])
        total_diags += len(items)
        for item in items:
            tit = item.get("titulo", "Error desconocido")
            frecuencias[tit] = frecuencias.get(tit, 0) + 1

    # Ordenar por frecuencia descendente
    frec_ordenadas = dict(sorted(frecuencias.items(), key=lambda x: x[1], reverse=True))

    return {
        "total_sesiones": len(datos),
        "total_diagnosticos": total_diags,
        "frecuencia_errores": frec_ordenadas,
        "historial": datos[-10:],  # Últimas 10 sesiones
    }
