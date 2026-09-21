"""Catálogo exhaustivo de explicaciones pedagógicas y sugerencias de remediación para GCC/Clang."""

from __future__ import annotations
from typing import Tuple, Dict, Any, Optional, List
from daedalus.core.standards_db import get_standard_citation

# Formato de tupla: (title_es, explanation_es, root_cause_es, suggestion_es, flag_asociado, flags_sugeridos)
CATALOGO_GCC: Dict[str, Tuple[str, str, str, str, Optional[str], List[str]]] = {
    # 1. Funciones y Prototipos
    "implicit declaration of function": (
        "Invocación de Función sin Declaración Previa",
        "Estás usando una función que el compilador no conoce en este punto del archivo fuente.",
        "Te olvidaste de incluir la cabecera correspondiente (ej: #include <stdio.h> o <stdlib.h>) o de declarar el prototipo antes del main.",
        "Agregá el '#include <...>' adecuado al inicio del archivo o declará el prototipo 'tipo nombre_funcion(...);' antes de invocarla.",
        "-Wimplicit-function-declaration",
        []
    ),
    "conflicting types for": (
        "Conflicto de Tipos en Firma de Función",
        "La firma de la función en su definición (.c) no coincide con el prototipo declarado previamente o en la cabecera (.h).",
        "Difieren el tipo de retorno o los tipos/cantidad de parámetros entre la declaración y la definición.",
        "Hacé coincidir exactamente el tipo de retorno y los argumentos entre el prototipo y la definición.",
        None,
        []
    ),
    "control reaches end of non-void function": (
        "Función sin Retorno Garantizado",
        "La función promete devolver un valor pero puede terminar su ejecución sin una sentencia 'return'.",
        "En alguna rama de un if/else, switch o al final del cuerpo de la función no hay un 'return' explícito.",
        "Asegurate de que todas las rutas de ejecución terminen con un 'return <expresión>;' válido.",
        "-Wreturn-type",
        []
    ),
    "function declaration isn’t a prototype": (
        "Declaración de Función sin Prototipo Estricto",
        "Declaraste una función con paréntesis vacíos 'f()', lo cual en C clásico indica parámetros no especificados.",
        "En C moderno, las funciones sin parámetros deben declararse explícitamente con 'void'.",
        "Cambiá la firma a 'tipo nombre(void)'.",
        "-Wstrict-prototypes",
        []
    ),
    "no previous prototype for": (
        "Función Global sin Prototipo Visible",
        "Definiste una función global sin haber expuesto previamente su prototipo en un archivo de cabecera .h.",
        "La función no está pensada para ser pública o te olvidaste de incluir su .h correspondiente.",
        "Si la función es de uso interno del módulo, declarala como 'static'. Si es pública, agregá su prototipo en el .h e incluilo.",
        "-Wmissing-prototypes",
        []
    ),
    "no previous declaration for": (
        "Función sin Declaración Previa",
        "La función global no tiene declaración previa visible en la unidad de traducción.",
        "Falta declarar la función en la cabecera o marcarla como estática si es de ámbito privado.",
        "Agregá 'static' antes del tipo de retorno si sólo se usa en este archivo.",
        "-Wmissing-declarations",
        []
    ),

    # 2. Formato en printf / scanf
    "format ‘%d’ expects argument of type": (
        "Incompatibilidad de Formato en scanf / printf",
        "El especificador de formato ('%d', '%s', '%f', etc.) no coincide con el tipo de la variable provista.",
        "En 'scanf', probablemente olvidaste anteponer '&' a la variable entera. En 'printf', pasaste un puntero o un tipo incompatible.",
        "En scanf pasá la dirección de memoria (&variable). En printf hacé coincidir '%d' para int, '%ld' para long, '%zu' para size_t.",
        "-Wformat",
        []
    ),
    "format ‘%s’ expects argument of type": (
        "Especificador '%s' Espera Puntero a Caracter (char*)",
        "Pasaste una variable de tipo entero o caracter individual ('char') en lugar de una cadena de caracteres terminada en '\\0'.",
        "Para imprimir un único caracter usá '%c'. Para imprimir cadenas usá '%s' pasando un arreglo o puntero char*.",
        "Reemplazá '%s' por '%c' si es un caracter solo, o asegurate de pasar un puntero a char.",
        "-Wformat",
        []
    ),
    "format ‘%zu’ expects argument of type": (
        "Especificador '%zu' Requiere Tipo 'size_t'",
        "Intentaste imprimir o leer con '%zu' una variable que no es de tipo 'size_t'.",
        "El tipo de la variable es 'int' o 'long' en lugar de 'size_t'.",
        "Usá '%zu' para valores devueltos por 'sizeof' y 'strlen', o '%d' / '%u' para enteros normales.",
        "-Wformat",
        []
    ),
    "format not a string literal and no format arguments": (
        "Vulnerabilidad de Cadena de Formato (Format String)",
        "Pasaste una variable directamente como primer argumento de printf(msg) sin especificador.",
        "Si la variable contiene caracteres '%' ingresados por el usuario, el programa intentará leer de la pila provocando crashes o fallos de seguridad.",
        "Escribí siempre 'printf(\"%s\", msg);' en lugar de 'printf(msg);'.",
        "-Wformat-security",
        []
    ),
    "too many arguments for format": (
        "Exceso de Argumentos para Cadena de Formato",
        "Pasaste más argumentos a la función de formato que especificadores '%' presentes en la plantilla.",
        "Parámetros residuales que quedaron tras modificar el mensaje de formato.",
        "Eliminá los argumentos sobrantes o agregá los especificadores '%' correspondientes.",
        "-Wformat-extra-args",
        []
    ),

    # 3. Punteros y Tipos de Datos
    "assignment to ‘int’ from ‘int *’": (
        "Asignación Inválida de Puntero a Entero",
        "Intentaste guardar una dirección de memoria (puntero) directamente en una variable numérica entera sin desreferenciar.",
        "Falta el operador de desreferencia '*' o asignaste un puntero directamente a una variable de tipo 'int'.",
        "Si querés el valor apuntado, usá '*ptr'. Si querés guardar la dirección, declará la variable receptora como puntero 'int*'.",
        "-Wint-conversion",
        []
    ),
    "assignment to ‘int *’ from ‘int’": (
        "Asignación Inválida de Entero a Puntero",
        "Intentaste asignar un número entero directamente a una variable de tipo puntero.",
        "Un puntero sólo puede almacenar direcciones de memoria válidas (obtenidas con '&var' o 'malloc').",
        "Asigná la dirección de una variable existente ('ptr = &x;') o asignale memoria dinámica con 'malloc()'.",
        "-Wint-conversion",
        []
    ),
    "assignment to ‘char *’ from ‘const char *’": (
        "Descarte Inválido de Calificador 'const'",
        "Intentaste asignar un puntero a memoria de sólo lectura ('const char*') a un puntero modificable ('char*').",
        "Los literales de cadena en C (\"texto\") son de sólo lectura; modificarlos causa Segmentation Fault.",
        "Declará la variable receptora como 'const char*' o hacé una copia dinámica con 'strdup()'.",
        "-Wdiscarded-qualifiers",
        []
    ),
    "passing argument": (
        "Incompatibilidad de Tipos en Argumento de Función",
        "El tipo del argumento pasado a la función no coincide con el tipo esperado por el parámetro.",
        "Se pasó un entero donde se esperaba un puntero, o un puntero de tipo incompatible.",
        "Revisá la firma de la función en la cabecera y adaptá el tipo del argumento pasado.",
        "-Wincompatible-pointer-types",
        []
    ),
    "dereferencing pointer to incomplete type": (
        "Desreferencia de Tipo Incompleto / TDA Opaco",
        "Intentaste acceder a los campos internos de un struct ('ptr->campo') cuya estructura interna está oculta o no fue definida en la cabecera.",
        "El archivo .h sólo declaró 'typedef struct s_tda t_tda;' para mantenerlo opaco, o te olvidaste de incluir el .h con la definición completa.",
        "No accedas directamente a 'ptr->campo'. Utilizá las funciones primitivas públicas provistas en el .h para interactuar con el TDA.",
        None,
        []
    ),
    "dereferencing ‘void *’ pointer": (
        "Desreferencia Ilegal de Puntero Genérico 'void*'",
        "Intentaste leer o escribir el valor apuntado por un puntero 'void*' sin castearlo previamente.",
        "El tipo 'void' no tiene tamaño definido en C estándar, por lo que el compilador no sabe cuántos bytes leer.",
        "Casteá el puntero al tipo de dato concreto antes de desreferenciarlo (ej: '*(int*)ptr').",
        "-Wpointer-arith",
        []
    ),
    "comparison between pointer and integer": (
        "Comparación Inválida entre Puntero y Entero",
        "Estás comparando una dirección de memoria contra un valor numérico entero (ej: ptr == 0 o char* == char).",
        "Probablemente olvidaste desreferenciar el puntero con '*' antes de comparar el contenido.",
        "Usá '*ptr == valor' para comparar el dato apuntado, o 'ptr == NULL' para chequear la validez del puntero.",
        "-Wpointer-to-int-cast",
        []
    ),

    # 4. Variables, Inicialización y Ámbito
    "unused variable": (
        "Variable Declarada sin Uso",
        "Declaraste una variable pero nunca leés su valor en el código.",
        "Variable residual de pruebas o cálculo redundante.",
        "Eliminá la variable innecesaria o asegurate de usarla en tu algoritmo si era parte del cálculo.",
        "-Wunused-variable",
        []
    ),
    "unused parameter": (
        "Parámetro de Función sin Uso",
        "La función recibe un parámetro pero nunca lo utiliza dentro de su cuerpo.",
        "Firma genérica requerida por un callback o lógica incompleta.",
        "Si el parámetro no es necesario, eliminalo de la firma; si es un callback obligatorio, podés marcarlo o documentarlo.",
        "-Wunused-parameter",
        []
    ),
    "is used uninitialized": (
        "Lectura de Variable No Inicializada",
        "Estás leyendo el valor de una variable antes de haberle asignado un dato.",
        "En C, las variables locales contienen valores basura aleatorios hasta que se les asigna un valor explícito.",
        "Inicializá la variable al declararla (ej: 'int total = 0;') antes de operarla.",
        "-Wuninitialized",
        []
    ),
    "may be used uninitialized": (
        "Variable Potencialmente No Inicializada",
        "Existe al menos un camino de ejecución donde la variable podría leerse sin haber sido inicializada.",
        "La asignación está dentro de un 'if' condicional que podría no ejecutarse.",
        "Asigná un valor por defecto al momento de la declaración.",
        "-Wmaybe-uninitialized",
        []
    ),
    "declaration of": (
        "Sombreado de Identificador (Variable Shadowing)",
        "Declaraste una variable en un bloque interno con el mismo nombre que otra en un ámbito exterior.",
        "La variable interna oculta a la externa, generando confusión sobre cuál se está modificando.",
        "Cambiá el nombre de la variable interna para evitar ambigüedades.",
        "-Wshadow",
        []
    ),

    # 5. Operaciones Aritméticas, Lógicas y Conversiones
    "conversion to": (
        "Conversión Implícita de Tipos con Riesgo de Pérdida",
        "Se está convirtiendo un tipo más grande o de diferente signo a otro más pequeño (ej: long a int, signed a unsigned).",
        "Riesgo de truncamiento de datos numéricos o interpretación incorrecta de valores negativos.",
        "Utilizá casteo explícito si la conversión es intencional o modificá los tipos para que sean homogéneos.",
        "-Wconversion",
        []
    ),
    "comparison of integer expressions of different signedness": (
        "Comparación entre Enteros con y sin Signo",
        "Estás comparando una variable con signo (int) con una sin signo (unsigned int / size_t).",
        "Si el entero con signo es negativo, la promoción implícita lo convertirá en un número positivo enorme, alterando el resultado lógico.",
        "Declará ambas variables con el mismo tipo (ej: ambas 'int' o ambas 'size_t') o validá que sea mayor o igual a 0 antes de comparar.",
        "-Wsign-compare",
        []
    ),
    "comparing floating-point with ‘==’": (
        "Comparación Exacta de Punto Flotante con '=='",
        "Comparaste dos números float/double usando '==' o '!='.",
        "Debido a la representación binaria IEEE-754, los cálculos con decimales tienen errores de redondeo infinitesimales que impiden la igualdad exacta.",
        "Compará con una tolerancia épsilon: 'fabs(a - b) < 1e-6'.",
        "-Wfloat-equal",
        []
    ),
    "suggest parentheses around assignment used as truth value": (
        "Asignación Usada como Condición Lógica en 'if'",
        "Escribiste 'if (x = 5)' con un solo signo '=' en lugar de comparar con '=='.",
        "Confusión tipográfica entre el operador de asignación '=' y el operador de comparación '=='.",
        "Reemplazá '=' por '==' (ej: 'if (x == 5)'). Si la asignación era deliberada, rodeala de paréntesis: 'if ((x = 5))'.",
        "-Wparentheses",
        []
    ),
    "division by zero": (
        "División por Cero Detectada en Tiempo de Compilación",
        "Una constante divisora en una operación aritmética evalúa a 0.",
        "Dividir por cero produce señal fatal SIGFPE y aborta el programa inmediatamente.",
        "Verificá que el denominador sea distinto de cero antes de realizar la división.",
        "-Wdiv-by-zero",
        []
    ),

    # 6. Enlazado y Librerías (Linker Errors)
    "undefined reference to": (
        "Símbolo no Encontrado en Enlazado (Linker Error)",
        "El compilador encontró la declaración de la función, pero el enlazador (ld) no encontró su código objeto compilado (.c o librería).",
        "Te olvidaste de incluir el archivo .c correspondiente en el comando de compilación (ej: 'gcc main.c tda.c') o falta enlazar una librería de sistema (ej: '-lm' para matemáticas, '-lpthread' para hilos).",
        "Incluí todos los archivos .c en la compilación ('gcc main.c tda.c -o app') o agregá el flag de librería faltante (ej: '-lm').",
        None,
        ["-lm", "-lpthread", "-lrt"]
    ),
    "multiple definition of": (
        "Definición Múltiple del Mismo Símbolo",
        "Una función o variable global fue definida dos o más veces en distintas unidades de compilación.",
        "Probablemente definiste el cuerpo completo de una función o variable dentro de un archivo de cabecera (.h) en lugar de declararla con 'extern' o ponerla en un .c.",
        "Dejá en el .h únicamente los prototipos y poné las definiciones en los archivos .c.",
        None,
        []
    ),
    "cannot find -l": (
        "Librería Externa no Encontrada por el Linker",
        "El linker no encontró el archivo de biblioteca especificado en la directiva '-l<nombre>'.",
        "La biblioteca no está instalada en el sistema o falta indicar la ruta con '-L/ruta'.",
        "Instalá el paquete correspondiente con pacman/apt o verificá la ortografía del nombre.",
        None,
        []
    ),

    # 7. Cabeceras y Preprocesador
    "no such file or directory": (
        "Archivo de Cabecera (#include) no Encontrado",
        "El preprocesador no pudo localizar el archivo de cabecera especificado en la directiva #include.",
        "Ruta incorrecta, error de tipeo en el nombre del .h o falta agregar el flag '-I/ruta/includes' al compilar.",
        "Revisá la ortografía del archivo incluido o agregá la carpeta de headers con '-I<directorio>'.",
        None,
        ["-I."]
    ),
}


def _normalizar_comillas(texto: str) -> str:
    """GCC emite comillas tipográficas (‘x’) según el locale; Clang y GCC en C usan ASCII."""
    return texto.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')


def lookup_explanation(raw_msg: str) -> Tuple[str, str, str, str, Optional[str], Optional[str], List[str]]:
    """Busca la explicación más adecuada para un mensaje de error o warning de GCC.
    
    Retorna: (title_es, explanation_es, root_cause_es, suggestion_es, flag, standard_citation, suggested_flags)
    """
    lower_msg = _normalizar_comillas(raw_msg).lower()
    
    # 1. Búsqueda por subcadena en catálogo
    for key, (title, expl, cause, sugg, flag, flags_sugg) in CATALOGO_GCC.items():
        if _normalizar_comillas(key) in lower_msg:
            # Buscar cita del estándar si hay flag asociado
            citation = get_standard_citation(flag or key)
            return title, expl, cause, sugg, flag, citation, flags_sugg

    # 2. Si el mensaje contiene un flag explícito ej: [-Wunused-variable]
    import re
    flag_match = re.search(r'\[(-W[a-zA-Z0-9_-]+)\]', raw_msg)
    if flag_match:
        f_name = flag_match.group(1)
        citation = get_standard_citation(f_name)
        clean_name = f_name.replace("-W", "")
        return (
            f"Advertencia de Compilador: {f_name}",
            f"El código disparó la advertencia '{f_name}' de GCC/Clang.",
            f"El patrón de código infringe la regla de calidad controlada por {f_name}.",
            f"Revisá la documentación de GCC sobre '{f_name}' para adaptar la construcción.",
            f_name,
            citation,
            []
        )

    # 3. Fallback genérico
    return (
        "Diagnóstico de Compilación GCC",
        f"El compilador reportó: {raw_msg}",
        "El código infringe las reglas sintácticas o semánticas del estándar C.",
        "Revisá la línea indicada y consultá la documentación de C sobre la sintaxis correspondiente.",
        None,
        None,
        []
    )


def list_catalog_entries() -> List[Dict[str, Any]]:
    """Retorna todas las entradas del catálogo para exploración interactiva."""
    entries = []
    for key, (title, expl, cause, sugg, flag, flags_sugg) in CATALOGO_GCC.items():
        citation = get_standard_citation(flag or key)
        entries.append({
            "key": key,
            "title": title,
            "explanation": expl,
            "root_cause": cause,
            "suggestion": sugg,
            "flag": flag,
            "citation": citation,
            "suggested_flags": flags_sugg
        })
    return entries
