"""Generador de guías de resolución paso a paso en Markdown para consultas estudiantiles."""

from __future__ import annotations
from pathlib import Path
from typing import Any


def generate_resolution_guide(report: Any) -> str:
    """Genera una guía interactiva en Markdown con pasos claros de resolución para el alumno."""
    lines = [
        "# Guía Didáctica de Resolución de Errores de Compilación",
        "",
        "> [!NOTE]",
        "> Esta guía fue sintetizada automáticamente por **DAEDALUS** para ayudarte a comprender y resolver cada advertencia y error detectado por el compilador.",
        ""
    ]

    is_passed = getattr(report, "exito", getattr(report, "passed", False))
    diagnostics = getattr(report, "diagnosticos", getattr(report, "diagnostics", []))

    if is_passed and not diagnostics:
        lines.append("## ✓ Estado del Código")
        lines.append("El programa compila limpiamente sin advertencias ni errores pendientes.")
        return "\n".join(lines)

    lines.append(f"## Resumen de Diagnósticos ({len(diagnostics)} ítems)")
    lines.append("")

    for idx, d in enumerate(diagnostics, 1):
        sev = str(getattr(d, "severidad", getattr(d, "severity", "error"))).lower()
        sev_icon = "❌" if "error" in sev else "⚠️"
        f_path = getattr(d, "archivo", getattr(d, "file_path", "origen.c"))
        lin = getattr(d, "linea", getattr(d, "line_number", 1))
        loc = f"`{Path(f_path).name}:{lin}`" if f_path else "`origen.c`"
        tit = getattr(d, "titulo", getattr(d, "title_es", "Diagnóstico de compilación"))
        raw_msg = getattr(d, "mensaje_original", getattr(d, "raw_message", ""))
        flag = getattr(d, "flag", None)
        citation = getattr(d, "cita_iso_c", getattr(d, "iso_c_citation", None))
        snippet = getattr(d, "code_snippet", None)
        expl = getattr(d, "explicacion", getattr(d, "explanation_es", ""))
        cause = getattr(d, "causa_raiz", getattr(d, "root_cause_es", ""))
        sugg = getattr(d, "sugerencia", getattr(d, "suggestion_es", ""))
        sugg_flags = getattr(d, "flags_sugeridos", getattr(d, "suggested_flags", []))

        lines.append(f"### {idx}. {sev_icon} {tit} ({loc})")
        lines.append("")
        lines.append(f"- **Mensaje original:** `{raw_msg}`")
        if flag:
            lines.append(f"- **Flag de control:** `{flag}`")
        if citation:
            lines.append(f"- **Norma estándar:** *{citation}*")
        lines.append("")
        if snippet:
            lines.append("```c")
            lines.append(f"// Línea {lin}")
            lines.append(snippet)
            lines.append("```")
            lines.append("")
        if expl:
            lines.append(f"**¿Qué significa?**\n{expl}")
            lines.append("")
        if cause:
            lines.append(f"**Causa raíz habitual:**\n{cause}")
            lines.append("")
        if sugg:
            lines.append("**Pasos para resolverlo:**")
            lines.append(f"1. {sugg}")
            if sugg_flags:
                flags_str = " ".join(sugg_flags)
                lines.append(f"2. Asegurate de incluir los flags de enlazado necesarios en el comando: `{flags_str}`")
            lines.append("")

    return "\n".join(lines)

