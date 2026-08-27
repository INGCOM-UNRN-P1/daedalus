"""Modelos de datos para el motor de traducción y compilación de DAEDALUS."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DiagnosticoCompilacion:
    """Diagnóstico pedagógico traducido de un mensaje de error o warning del compilador."""
    archivo: Optional[str]
    linea: Optional[int]
    columna: Optional[int]
    severidad: str              # "error", "warning", "note"
    mensaje_original: str
    titulo: str
    explicacion: str
    sugerencia: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archivo": self.archivo,
            "linea": self.linea,
            "columna": self.columna,
            "severidad": self.severidad,
            "mensaje_original": self.mensaje_original,
            "titulo": self.titulo,
            "explicacion": self.explicacion,
            "sugerencia": self.sugerencia,
        }


@dataclass
class ResultadoCompilacion:
    """Resultado del proceso de compilación de código C."""
    exito: bool
    codigo_retorno: int
    binario: Optional[Path] = None
    diagnosticos: List[DiagnosticoCompilacion] = field(default_factory=list)
    stdout_crudo: str = ""
    stderr_crudo: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exito": self.exito,
            "codigo_retorno": self.codigo_retorno,
            "binario": str(self.binario) if self.binario else None,
            "total_diagnosticos": len(self.diagnosticos),
            "diagnosticos": [d.to_dict() for d in self.diagnosticos],
        }
