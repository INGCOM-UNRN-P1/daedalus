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
    flag: Optional[str] = None
    causa_raiz: Optional[str] = None
    cita_iso_c: Optional[str] = None
    flags_sugeridos: List[str] = field(default_factory=list)
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "archivo": self.archivo,
            "linea": self.linea,
            "columna": self.columna,
            "severidad": self.severidad,
            "mensaje_original": self.mensaje_original,
            "titulo": self.titulo,
            "explicacion": self.explicacion,
            "sugerencia": self.sugerencia,
        }
        if self.flag:
            d["flag"] = self.flag
        if self.causa_raiz:
            d["causa_raiz"] = self.causa_raiz
            d["root_cause_es"] = self.causa_raiz
        if self.cita_iso_c:
            d["cita_iso_c"] = self.cita_iso_c
            d["iso_c_citation"] = self.cita_iso_c
        if self.flags_sugeridos:
            d["flags_sugeridos"] = self.flags_sugeridos
            d["suggested_flags"] = self.flags_sugeridos
        if self.code_snippet:
            d["code_snippet"] = self.code_snippet
        return d


@dataclass
class ResultadoCompilacion:
    """Resultado del proceso de compilación de código C."""
    exito: bool
    codigo_retorno: int
    binario: Optional[Path] = None
    diagnosticos: List[DiagnosticoCompilacion] = field(default_factory=list)
    stdout_crudo: str = ""
    stderr_crudo: str = ""
    suprimidos: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "schema_version": "1.0.0",
            "exito": self.exito,
            "codigo_retorno": self.codigo_retorno,
            "binario": str(self.binario) if self.binario else None,
            "total_diagnosticos": len(self.diagnosticos),
            "diagnosticos": [d.to_dict() for d in self.diagnosticos],
        }
        if self.suprimidos > 0:
            d["suprimidos"] = self.suprimidos
            d["suppressed_count"] = self.suprimidos
        return d
