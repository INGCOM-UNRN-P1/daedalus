"""Plugin de DAEDALUS para integración transparente con RIPLEY."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List

from daedalus.core.compiler import compilar_archivos


class DaedalusPlugin:
    """Plugin de compilación y traducción pedagógica de errores para Ripley."""

    name = "compiler"
    version = "0.1.0"

    def is_available(self) -> bool:
        return bool(shutil.which("gcc") or shutil.which("clang"))

    def execute(self, workspace: Path, manifest_config: Dict[str, Any]) -> Dict[str, Any]:
        archivos_c = list(workspace.glob("*.c")) + list(workspace.glob("src/*.c"))
        if not archivos_c:
            return {"ok": True, "observaciones": [], "metricas": {"archivos": 0}}

        res = compilar_archivos(archivos_c)
        observaciones = []
        for d in res.diagnosticos:
            observaciones.append({
                "codigo": f"COMP_{d.severidad.upper()}",
                "severidad": d.severidad.upper(),
                "archivo": d.archivo,
                "linea": d.linea,
                "columna": d.columna,
                "mensaje": f"{d.titulo}: {d.explicacion}",
                "sugerencia": d.sugerencia,
            })

        return {
            "ok": res.exito,
            "total_observaciones": len(observaciones),
            "observaciones": observaciones,
            "metricas": {"codigo_retorno": res.codigo_retorno, "archivos": len(archivos_c)},
        }
