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
        if manifest_config.get("c_files"):
            archivos_c = [Path(f) for f in manifest_config["c_files"]]
        elif workspace.is_file():
            archivos_c = [workspace]
        else:
            archivos_c = list(workspace.glob("*.c")) + list(workspace.glob("src/*.c"))

        if not archivos_c:
            return {"ok": True, "success": True, "observaciones": [], "metricas": {"archivos": 0}}

        out_bin = manifest_config.get("output_bin")
        if out_bin:
            out_bin = Path(out_bin)
        flags = manifest_config.get("extra_flags") or manifest_config.get("flags")
        compilador = manifest_config.get("compiler")

        res = compilar_archivos(
            fuentes=archivos_c,
            binario_salida=out_bin,
            flags_adicionales=flags,
            compilador=compilador,
        )

        observaciones = []
        for d in res.diagnosticos:
            observaciones.append({
                "codigo": f"COMP_{d.severidad.upper()}",
                "rule_code": f"COMP_{d.severidad.upper()}",
                "rule_name": d.titulo or "Error de Compilación",
                "severidad": d.severidad.upper(),
                "severity": d.severidad.upper(),
                "archivo": d.archivo,
                "file": d.archivo,
                "linea": d.linea,
                "line": d.linea,
                "columna": d.columna,
                "column": d.columna,
                "mensaje": f"{d.titulo}: {d.explicacion}",
                "message": f"{d.titulo}: {d.explicacion}",
                "sugerencia": d.sugerencia,
                "suggestion": d.sugerencia,
                "source_plugin": "daedalus",
            })

        translated = [
            {
                "file": d.archivo or "",
                "line": d.linea or 0,
                "column": d.columna or 0,
                "severity": d.severidad or "error",
                "title": d.titulo or "",
                "raw_message": "",
                "translated_message": d.explicacion or d.titulo or "",
                "suggestion": d.sugerencia or "",
            }
            for d in res.diagnosticos
        ]

        return {
            "ok": res.exito,
            "success": res.exito,
            "return_code": res.codigo_retorno,
            "binary_path": str(res.binario) if res.binario else None,
            "raw_stderr": res.stderr_crudo,
            "translated_diagnostics": translated,
            "human_summary": "Compilación exitosa sin errores bloqueantes." if res.exito else "Falló la compilación.",
            "total_observaciones": len(observaciones),
            "observaciones": observaciones,
            "metricas": {"codigo_retorno": res.codigo_retorno, "archivos": len(archivos_c)},
        }
