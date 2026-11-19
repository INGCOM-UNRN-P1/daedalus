"""Módulo de registro persistente y estadísticas de diagnósticos en DAEDALUS."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from yutani.hallazgos import hallazgo

from daedalus.core.models import DiagnosticoCompilacion
from daedalus.core.taxonomia import clasificar

HISTORIAL_PATH_DEFAULT = Path.home() / ".daedalus_history.json"


def _ruta_historial(historial_path: Optional[Path] = None) -> Path:
    if historial_path is not None:
        return historial_path
    env_path = os.environ.get("DAEDALUS_HISTORIAL")
    return Path(env_path) if env_path else HISTORIAL_PATH_DEFAULT


def _telemetria_activa() -> bool:
    valor = os.environ.get("DAEDALUS_TELEMETRIA", "1").strip().lower()
    return valor not in {"0", "false", "no", "off"}


def _item_diagnostico(d: Any) -> Dict[str, Any]:
    titulo = getattr(d, "titulo", str(d))
    severidad = getattr(d, "severidad", "error")
    msg_orig = getattr(d, "mensaje_original", "") or titulo
    flag = getattr(d, "flag", None)
    dummy = DiagnosticoCompilacion(
        archivo=getattr(d, "archivo", None),
        linea=getattr(d, "linea", None),
        columna=getattr(d, "columna", None),
        severidad=severidad,
        mensaje_original=msg_orig,
        titulo=titulo,
        explicacion=getattr(d, "explicacion", ""),
        sugerencia=getattr(d, "sugerencia", ""),
        flag=flag,
    )
    codigo, categoria = clasificar(dummy)
    h = hallazgo("daedalus", codigo, categoria, severidad, titulo)
    item: Dict[str, Any] = {
        "titulo": titulo,
        "severidad": severidad,
        "archivo": getattr(d, "archivo", ""),
        "linea": getattr(d, "linea", None),
        "codigo": codigo,
        "categoria": categoria,
    }
    causa = getattr(d, "causa_raiz", None)
    if causa:
        item["causa_raiz"] = causa
    apunte = h.get("enlace") or h.get("apunte") or getattr(d, "cita_iso_c", None)
    if apunte:
        item["apunte"] = apunte
    return item


def registrar_diagnosticos(
    diagnosticos: List[Any],
    fuentes: List[Path],
    historial_path: Optional[Path] = None,
    cohorte: Optional[str] = None,
) -> None:
    """Registra los diagnósticos en el historial local persistente (opcional, por cohorte)."""
    if not diagnosticos or not _telemetria_activa():
        return

    path = _ruta_historial(historial_path)
    datos: List[Dict[str, Any]] = []

    if path.is_file():
        try:
            datos = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            datos = []

    cohorte_efectiva = cohorte if cohorte is not None else (os.environ.get("DAEDALUS_COHORTE") or None)
    entrada: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "fuentes": [str(f) for f in fuentes],
        "total_errores": len(diagnosticos),
        "items": [_item_diagnostico(d) for d in diagnosticos],
    }
    if cohorte_efectiva:
        entrada["cohorte"] = cohorte_efectiva

    datos.append(entrada)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def obtener_estadisticas(
    historial_path: Optional[Path] = None,
    cohorte: Optional[str] = None,
) -> Dict[str, Any]:
    """Calcula estadísticas agregadas de errores y secciones del apunte a partir del historial."""
    path = _ruta_historial(historial_path)
    if not path.is_file():
        return {
            "cohorte": cohorte,
            "total_sesiones": 0,
            "total_diagnosticos": 0,
            "frecuencia_errores": {},
            "frecuencia_categorias": {},
            "secciones_apunte": {},
            "historial": [],
        }

    try:
        datos: List[Dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        datos = []

    if cohorte is not None:
        datos = [s for s in datos if s.get("cohorte") == cohorte]

    total_diags = 0
    frecuencias: Dict[str, int] = {}
    categorias: Dict[str, int] = {}
    apunte_frec: Dict[str, int] = {}

    for sesion in datos:
        items = sesion.get("items", [])
        total_diags += len(items)
        for item in items:
            tit = item.get("titulo", "Error desconocido")
            frecuencias[tit] = frecuencias.get(tit, 0) + 1
            cat = item.get("categoria")
            if cat:
                categorias[cat] = categorias.get(cat, 0) + 1
            ap = item.get("apunte")
            if ap:
                clave_ap = str(ap.get("seccion") or ap.get("url") or ap) if isinstance(ap, dict) else str(ap)
                apunte_frec[clave_ap] = apunte_frec.get(clave_ap, 0) + 1

    frec_ordenadas = dict(sorted(frecuencias.items(), key=lambda x: x[1], reverse=True))
    cat_ordenadas = dict(sorted(categorias.items(), key=lambda x: x[1], reverse=True))
    apunte_ordenado = dict(sorted(apunte_frec.items(), key=lambda x: x[1], reverse=True))

    return {
        "cohorte": cohorte,
        "total_sesiones": len(datos),
        "total_diagnosticos": total_diags,
        "frecuencia_errores": frec_ordenadas,
        "frecuencia_categorias": cat_ordenadas,
        "secciones_apunte": apunte_ordenado,
        "historial": datos[-10:],  # Últimas 10 sesiones
    }
