"""Generador de diagramas visuales ASCII para incompatibilidades de tipos de punteros en Daedalus."""

from __future__ import annotations

import re
from typing import Optional


def detectar_incompatibilidad_punteros(mensaje_error: str) -> Optional[tuple[str, str]]:
    """Extrae tipos origen y destino de mensajes como 'incompatible pointer type assigning to int* from int**'."""
    m = re.search(r"from\s+['`]([^'`]+)['`]\s+to\s+['`]([^'`]+)['`]", mensaje_error)
    if m:
        return m.group(1), m.group(2)
    m2 = re.search(r"passing argument \d+ of [^ ]+ from incompatible pointer type", mensaje_error)
    if m2:
        return "tipo_incompatible", "tipo_esperado"
    return None


def generar_diagrama_punteros(tipo_origen: str, tipo_destino: str) -> str:
    """Renderiza un esquema visual ASCII explicando el nivel de indirección de punteros."""
    niveles_orig = tipo_origen.count("*")
    niveles_dest = tipo_destino.count("*")
    
    lineas = [
        f"┌─────────────────────────────────────────────────────────────┐",
        f"│ 🔍 Visualizador de Indirección de Tipos (Daedalus Diagram) │",
        f"└─────────────────────────────────────────────────────────────┘",
        f"  • Tipo Provisto:  `{tipo_origen}` (Nivel de indirección: {niveles_orig})",
        f"  • Tipo Esperado:  `{tipo_destino}` (Nivel de indirección: {niveles_dest})",
        "",
    ]
    
    if niveles_orig > niveles_dest:
        lineas.append("  [Provisto]  [Dirección RAM]  ───▶  [Puntero Intermedio]  ───▶  [Valor Final]")
        lineas.append(f"  ↳ Sobra un operador de desreferencia '*': usá `*{tipo_origen.split('*')[0].strip()}` o pasá un nivel menos de indirección.")
    elif niveles_dest > niveles_orig:
        lineas.append("  [Provisto]  [Valor Directo]")
        lineas.append(f"  [Esperado]  [Dirección RAM]  ───▶  [Valor Final]")
        lineas.append(f"  ↳ Falta el operador '&' (dirección de memoria) para obtener un puntero a la variable.")
    else:
        lineas.append("  [Provisto]  [Tipo A]  ───✖───▶  [Tipo B] (Tipos base incompatibles sin conversión implícita)")
        
    return "\n".join(lineas)
