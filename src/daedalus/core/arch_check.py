"""Detección y explicación pedagógica de incompatibilidades sutiles entre 32 y 64 bits para ESPER."""

from __future__ import annotations
import re
from typing import List, Dict, Any


ARCH_PATTERNS = [
    (
        r"cast from pointer to integer of different size",
        "Casteo Peligroso de Puntero a Entero (32 vs 64 bits)",
        "En arquitecturas de 64 bits (x86_64, ARM64), los punteros ocupan 8 bytes, mientras que 'int' ocupa 4 bytes.",
        "Al castear un puntero a 'int', se pierden los 4 bytes superiores de la dirección de memoria, produciendo punteros truncados y fallos de segmentación.",
        "Si necesitás almacenar un puntero en un tipo entero, utilizá 'intptr_t' o 'uintptr_t' de <stdint.h>."
    ),
    (
        r"cast to pointer from integer of different size",
        "Reconstrucción de Puntero desde Entero Truncado (32 vs 64 bits)",
        "Se está intentando convertir un número entero de 4 bytes a un puntero de 8 bytes.",
        "El compilador rellenará los 32 bits superiores con ceros o signo, apuntando a una dirección inválida fuera del espacio de memoria del proceso.",
        "Utilizá 'uintptr_t' para conversiones numéricas intermedias de direcciones de memoria."
    ),
    (
        r"format ‘%d’ expects argument of type ‘int’, but argument .* has type ‘size_t’",
        "Formato '%d' Usado para 'size_t' (Incompatibilidad 32 vs 64 bits)",
        "El tipo 'size_t' (retornado por sizeof y strlen) tiene 8 bytes en 64 bits y 4 bytes en 32 bits, mientras que '%d' asume un 'int' de 4 bytes.",
        "En plataformas de 64 bits, '%d' lee solo la mitad del valor o desalinea los argumentos siguientes en la pila de printf.",
        "Reemplazá el especificador '%d' por '%zu' (estándar C99/C11 para size_t)."
    ),
    (
        r"format ‘%ld’ expects argument of type ‘long int’, but argument .* has type ‘int’",
        "Discrepancia entre 'long' e 'int' (Modelos LP64 vs LLP64)",
        "En Linux de 64 bits (modelo LP64), 'long' tiene 8 bytes; en Windows de 64 bits (modelo LLP64), 'long' tiene 4 bytes.",
        "Usar tipos de tamaño dependiente de plataforma dificulta la portabilidad entre Linux y Windows.",
        "Para tamaños fijos garantizados, utilizá 'int32_t' o 'int64_t' de <stdint.h> con macros de formato PRId32/PRId64 de <inttypes.h>."
    ),
]


def check_arch_incompatibilities(raw_stderr: str) -> List[Dict[str, str]]:
    """Analiza la salida del compilador en busca de riesgos de portabilidad 32/64 bits."""
    findings = []
    for pattern, title, expl, root_cause, fix in ARCH_PATTERNS:
        if re.search(pattern, raw_stderr, re.IGNORECASE):
            findings.append({
                "title": title,
                "explanation": expl,
                "root_cause": root_cause,
                "suggestion": fix
            })
    return findings
