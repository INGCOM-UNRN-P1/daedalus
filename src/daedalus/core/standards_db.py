"""Base de datos de referencias normativas ISO C (C99, C11, C23) para diagnósticos de ESPER."""

from __future__ import annotations
from typing import Dict, Optional


STANDARDS_ISO_C: Dict[str, str] = {
    "implicit-function-declaration": "ISO/IEC 9899:2011 (C11) §6.5.2.2 - Toda función debe ser declarada explícitamente antes de su invocación.",
    "format": "ISO/IEC 9899:2011 (C11) §7.21.6.1 / §7.21.6.2 - Los especificadores de conversión de printf/scanf deben coincidir con los tipos reales de los argumentos pasados.",
    "int-conversion": "ISO/IEC 9899:2011 (C11) §6.3.2.3 - La conversión entre punteros y tipos enteros no es implícita y produce comportamiento no portable o indefinido.",
    "unused-variable": "ISO/IEC 9899:2011 (C11) §6.7 - Objetos con almacenamiento automático declarados pero nunca evaluados.",
    "return-type": "ISO/IEC 9899:2011 (C11) §6.8.6.4 - Sentencia 'return' en funciones con tipo de retorno no void debe contener una expresión del tipo adecuado.",
    "uninitialized": "ISO/IEC 9899:2011 (C11) §6.7.9 - Objetos con almacenamiento automático no inicializados poseen valor indeterminado (basura).",
    "shadow": "ISO/IEC 9899:2011 (C11) §6.2.1 - Ámbito de identificadores y ocultamiento de nombres en bloques anidados.",
    "conversion": "ISO/IEC 9899:2011 (C11) §6.3.1 - Conversiones aritméticas implícitas con riesgo de truncamiento o cambio de signo.",
    "float-equal": "ISO/IEC 9899:2011 (C11) §6.2.5 - Comparación directa de igualdad en punto flotante susceptible a imprecisión IEEE-754.",
    "pointer-arith": "ISO/IEC 9899:2011 (C11) §6.5.6 - Aritmética de punteros sobre tipos incompletos (void* o funciones) no está permitida en C estándar.",
    "strict-prototypes": "ISO/IEC 9899:2011 (C11) §6.7.6.3 - Funciones sin parámetros deben declararse con '(void)' para indicar lista vacía.",
    "missing-prototypes": "ISO/IEC 9899:2011 (C11) §6.9.1 - Funciones globales deben tener prototipo visible previo para verificar concordancia.",
    "incompatible-pointer-types": "ISO/IEC 9899:2011 (C11) §6.5.16.1 - Asignación entre tipos de punteros incompatibles sin casteo explícito.",
    "overflow": "ISO/IEC 9899:2011 (C11) §6.5 - Desbordamiento aritmético en constantes o expresiones enteras con signo (Undefined Behavior).",
    "array-bounds": "ISO/IEC 9899:2011 (C11) §6.5.6 - Acceso a índices fuera de los límites declarados del arreglo.",
    "null-dereference": "ISO/IEC 9899:2011 (C11) §6.5.3.2 - Desreferencia de puntero nulo o inválido.",
    "missing-declarations": "ISO/IEC 9899:2011 (C11) §6.7 - Declaraciones externas sin prototipo previo.",
    "format-security": "ISO/IEC 9899:2011 (C11) §7.21.6.1 - Paso de cadenas variables no literales como formato en printf/scanf (vulnerabilidad Format String).",
}


def get_standard_citation(flag_or_keyword: str) -> Optional[str]:
    """Obtiene la cita canónica del estándar ISO C asociada al flag o concepto."""
    clean = flag_or_keyword.replace("-W", "").replace("=", "").strip().lower()
    return STANDARDS_ISO_C.get(clean)
