# Manual de Uso y Referencia Técnica: daedalus

> **DAEDALUS** — Compilador C pedagógico y traductor de diagnósticos de GCC/Clang/ld a español rioplatense
> **Versión:** `0.1.0` · **CLI principal:** `daedalus` · **Plugin Ripley:** `compiler`

---

## 1. Arquitectura y Propósito Pedagógico

`daedalus` forma parte del ecosistema de herramientas de la cátedra de Programación 1 (UNRN). Su objetivo central es resolver de forma modular, determinista y automatizada las tareas asociadas a su dominio específico dentro del ciclo de desarrollo, evaluación y aprendizaje de software en C.

### Alcance Funcional (Qué cubre)
- Compilación pedagógica de código C bajo el perfil estricto de cátedra (C11, `-Wall -Wextra -pedantic -Wconversion -Werror=vla`).
- Traducción pedagógica de errores y advertencias de compilador (GCC, Clang) y enlazador (`ld`) a explicaciones en español rioplatense.
- Generación automatizada de base de compilación (`compile_commands.json`).
- Modo interactivo y salida estructurada JSON (`--json`) para integración con orquestadores.
- Verificación del estado de salud del toolchain mediante `daedalus doctor`.

### Límites de Responsabilidad y Delegación (Qué no cubre)
- Ejecución en sandbox y límite de recursos (delegado a `nostromo`).
- Linter de estilo y formato de código (delegado a `gaff`).
- Orquestación masiva y calificación docente (delegado a `dredd`).

### Principios de Diseño
- **Enfoque Pedagógico:** Diagnósticos y mensajes en español rioplatense orientados a facilitar la comprensión de errores conceptuales.
- **Salida Estructurada Dual:** Soporte nativo para visualización enriquecida en terminal (Rich) y salida parseable para orquestadores (`--json`).
- **Integración Contractual:** Capacidad de emitir secciones de reporte para `dredd` (`dredd-section`) y actuar como satélite orquestado por `ripley`.
- **Idempotencia y Robustez:** Validación de precondiciones y comandos de autodiagnóstico (`doctor`) para verificación del entorno.

---

## 2. Instalación y Requisitos

### Requisitos del Sistema
- **Python:** `>= 3.10` (recomendado Python 3.11 o 3.12).
- **Gestor de paquetes:** [`uv`](https://github.com/astral-sh/uv) (entorno estándar de cátedra).
- **Toolchain C (si aplica):** GCC / Clang, Make, GDB y bibliotecas estándar de desarrollo.

### Instalación en el Entorno de Usuario
Para instalar la herramienta de forma global y aislada en el sistema mediante `uv tool`:
```bash
uv tool install --editable /home/mrtin/dev/tools/daedalus
```

### Verificación de Instalación
Ejecutá el comando `doctor` para constatar que todas las dependencias y binarios requeridos estén presentes y operativos:
```bash
daedalus doctor
```

---

## 3. Guía Integral de Comandos (CLI)

| Comando | Descripción Breve |
| :--- | :--- |
| [`daedalus compile`](#compile) | Compila código C con banderas estrictas de cátedra y traduce errores a español didáctico. |
| [`daedalus report`](#report) | Genera directamente la sección de reporte Markdown de DAEDALUS para Dredd. |
| [`daedalus translate`](#translate) | Traduce un bloque de texto o log de compilador a diagnósticos didácticos. |
| [`daedalus doctor`](#doctor) | Verifica disponibilidad de herramientas del toolchain (GCC, Clang, Make, GDB, ld). |
| [`daedalus preprocess`](#preprocess) | Ejecuta el preprocesador de C (gcc -E) y limpia comentarios y directivas del sistema. |
| [`daedalus explain-opt`](#explainopt) | Explica el comportamiento didáctico y los efectos de los niveles de optimización de GCC. |
| [`daedalus compile-commands`](#compilecommands) | Genera compile_commands.json para Language Servers (Clangd / VS Code / Neovim). |
| [`daedalus expand-macro`](#expandmacro) | Expande y desglosa macros anidadas paso a paso para traducir errores complejos. |
| [`daedalus history`](#history) | Muestra el historial y estadísticas de errores frecuentes del estudiante. |
| [`daedalus stats`](#stats) | Muestra el historial y estadísticas de errores frecuentes del estudiante. |
| [`daedalus check-flags`](#checkflags) | Audita las banderas de compilación y sugiere flags pedagógicos obligatorios faltantes. |
| [`daedalus suggest-flags`](#suggestflags) | Analiza un archivo fuente, log de errores o Makefile y sugiere flags de compilación/enlazado faltantes. |
| [`daedalus list-warnings`](#listwarnings) | Lista todas las advertencias y reglas pedagógicas documentadas en el catálogo de diagnósticos. |
| [`daedalus catalog`](#catalog) | Lista todas las advertencias y reglas pedagógicas documentadas en el catálogo de diagnósticos. |
| [`daedalus guide`](#guide) | Genera una guía interactiva de resolución paso a paso en Markdown para el archivo C indicado. |
| [`daedalus check-arch`](#checkarch) | Audita advertencias relacionadas con incompatibilidades de tamaño en 32 vs 64 bits. |
| [`daedalus check-standards`](#checkstandards) | Verifica la compatibilidad del código simultáneamente contra C99, C11, C17 y C2x/C23. |
| [`daedalus check-deps`](#checkdeps) | Construye el grafo de inclusiones y detecta dependencias circulares entre cabeceras. |

### `daedalus compile`

Compila código C con banderas estrictas de cátedra y traduce errores a español didáctico.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `fuentes` | `List[Path]` | Archivos fuentes .c a compilar. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Optional[Path]` | `None` | Ruta del binario de salida. |
| `--json` | `bool` | `False` | Emitir reporte en JSON. |
| `--md`, `--output-md` | `Optional[Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |
| `--flags` | `Optional[str]` | `None` | Banderas adicionales para el compilador separadas por espacio. |
| `--compiler`, `--cc` | `Optional[str]` | `None` | Compilador backend a utilizar: 'gcc' o 'clang'. |
| `--guide` | `bool` | `False` | Generar guía detallada paso a paso en Markdown. |
| `--dedup` | `bool` | `False` | Suprimir advertencias repetitivas o en cascada. |

#### Ejemplo de Invocación
```bash
daedalus compile <fuentes>
```

### `daedalus report`

Genera directamente la sección de reporte Markdown de DAEDALUS para Dredd.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `fuentes` | `List[Path]` | Archivos fuentes .c a compilar y auditar. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Optional[Path]` | `None` | Ruta de destino del archivo Markdown. |
| `--flags` | `Optional[str]` | `None` | Banderas adicionales para GCC. |
| `--compiler`, `--cc` | `Optional[str]` | `None` | Compilador backend ('gcc' o 'clang'). |

#### Ejemplo de Invocación
```bash
daedalus report <fuentes>
```

### `daedalus translate`

Traduce un bloque de texto o log de compilador a diagnósticos didácticos.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--stderr-file` | `Optional[Path]` | `None` | Archivo con stderr crudo o leer desde stdin. |
| `--json` | `bool` | `False` | Salida en JSON. |
| `--dedup` | `bool` | `False` | Suprimir advertencias repetitivas o en cascada. |

#### Ejemplo de Invocación
```bash
daedalus translate
```

### `daedalus doctor`

Verifica disponibilidad de herramientas del toolchain (GCC, Clang, Make, GDB, ld).

#### Ejemplo de Invocación
```bash
daedalus doctor
```

### `daedalus preprocess`

Ejecuta el preprocesador de C (gcc -E) y limpia comentarios y directivas del sistema.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `fuente` | `Path` | Archivo fuente .c a preprocesar. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Optional[Path]` | `None` | Guardar salida preprocesada en archivo. |

#### Ejemplo de Invocación
```bash
daedalus preprocess <fuente>
```

### `daedalus explain-opt`

Explica el comportamiento didáctico y los efectos de los niveles de optimización de GCC.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--nivel` | `str` | `O2` | Nivel de optimización a explicar: O0, O1, O2, O3, Os, Og. |

#### Ejemplo de Invocación
```bash
daedalus explain-opt
```

### `daedalus compile-commands`

Genera compile_commands.json para Language Servers (Clangd / VS Code / Neovim).

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `fuentes` | `List[Path]` | Archivos fuentes del proyecto. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Path` | `compile_commands.json` | Ruta de destino del archivo JSON. |

#### Ejemplo de Invocación
```bash
daedalus compile-commands <fuentes>
```

### `daedalus expand-macro`

Expande y desglosa macros anidadas paso a paso para traducir errores complejos.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `fuente` | `Path` | Archivo C con definiciones o usos de macros. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--macro`, `-m` | `Optional[str]` | `None` | Nombre de la macro a expandir e inspeccionar. |
| `--compiler`, `--cc` | `Optional[str]` | `None` | Compilador a utilizar. |

#### Ejemplo de Invocación
```bash
daedalus expand-macro <fuente>
```

### `daedalus history`

Muestra el historial y estadísticas de errores frecuentes del estudiante.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir estadísticas en JSON. |

#### Ejemplo de Invocación
```bash
daedalus history
```

### `daedalus stats`

Muestra el historial y estadísticas de errores frecuentes del estudiante.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir estadísticas en JSON. |

#### Ejemplo de Invocación
```bash
daedalus stats
```

### `daedalus check-flags`

Audita las banderas de compilación y sugiere flags pedagógicos obligatorios faltantes.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--makefile`, `-m` | `Optional[Path]` | `None` | Ruta al Makefile a inspeccionar. |
| `--flags`, `-f` | `Optional[str]` | `None` | Lista de flags actuales separados por espacio. |
| `--json` | `bool` | `False` | Emitir resultado en JSON. |

#### Ejemplo de Invocación
```bash
daedalus check-flags
```

### `daedalus suggest-flags`

Analiza un archivo fuente, log de errores o Makefile y sugiere flags de compilación/enlazado faltantes.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--fuente-o-log` | `Optional[Path]` | `None` | Archivo fuente C o log de compilación a analizar. |
| `--makefile`, `-m` | `Optional[Path]` | `None` | Ruta al Makefile a inspeccionar. |
| `--flags`, `-f` | `Optional[str]` | `None` | Lista de flags actuales separados por espacio. |
| `--json` | `bool` | `False` | Emitir resultado en JSON. |

#### Ejemplo de Invocación
```bash
daedalus suggest-flags
```

### `daedalus list-warnings`

Lista todas las advertencias y reglas pedagógicas documentadas en el catálogo de diagnósticos.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir salida en formato JSON. |

#### Ejemplo de Invocación
```bash
daedalus list-warnings
```

### `daedalus catalog`

Lista todas las advertencias y reglas pedagógicas documentadas en el catálogo de diagnósticos.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir salida en formato JSON. |

#### Ejemplo de Invocación
```bash
daedalus catalog
```

### `daedalus guide`

Genera una guía interactiva de resolución paso a paso en Markdown para el archivo C indicado.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `fuente` | `Path` | Archivo C a compilar y generar guía. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Optional[Path]` | `None` | Guardar la guía en un archivo Markdown. |
| `--flags` | `Optional[str]` | `None` | Banderas adicionales para el compilador separadas por espacio. |

#### Ejemplo de Invocación
```bash
daedalus guide <fuente>
```

### `daedalus check-arch`

Audita advertencias relacionadas con incompatibilidades de tamaño en 32 vs 64 bits.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `log_file` | `Path` | Archivo con la salida de compilador a auditar. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Emitir salida en formato JSON. |

#### Ejemplo de Invocación
```bash
daedalus check-arch <log_file>
```

### `daedalus check-standards`

Verifica la compatibilidad del código simultáneamente contra C99, C11, C17 y C2x/C23.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `fuente` | `Path` | Archivo C a validar contra múltiples estándares. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Salida en JSON. |

#### Ejemplo de Invocación
```bash
daedalus check-standards <fuente>
```

### `daedalus check-deps`

Construye el grafo de inclusiones y detecta dependencias circulares entre cabeceras.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `rutas` | `List[Path]` | Directorios o archivos C/H a auditar. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `bool` | `False` | Salida en JSON. |

#### Ejemplo de Invocación
```bash
daedalus check-deps <rutas>
```

---

## 4. Formatos de Salida e Integración con el Ecosistema

### Modo Interactivo / Terminal (Rich)
Por defecto, la herramienta renderiza paneles, árboles y tablas estilizadas para facilitar la lectura del estudiante y docente en terminales modernas con soporte ANSI.

### Modo Estructurado JSON (`--json`)
Para integración con pipelines de CI/CD, scripts de automatización u orquestadores externos, la opción `--json` emite un documento JSON estricto por la salida estándar (`stdout`), dirigiendo cualquier mensaje de logging a `stderr`:
```bash
daedalus compile --json
```

### Integración con Dredd (`dredd-section`)
Cuando la herramienta genera reportes de evaluación para entregas de alumnos, produce una sección Markdown estandarizada conforme al contrato de integración de Dredd (v1.0.0):
```markdown
<!-- dredd-section: daedalus, tool=daedalus, version=0.1.0, status=ok -->
```
Este encabezado garantiza la agregación determinista de los hallazgos en la rúbrica docente.

### Integración con Ripley
`daedalus` está registrada en el catálogo de plugins satélites de Ripley (`SATELLITE_CATALOG`). Puede invocarse directamente a través del motor de evaluación de Ripley configurando el análisis en `ripley.toml`.

---

## 5. Diagnóstico y Códigos de Salida

### Códigos de Retorno (`exit code`)
| Código | Significado |
| :---: | :--- |
| `0` | Ejecución exitosa sin hallazgos críticos ni errores de sintaxis. |
| `1` | Hallazgos pedagógicos detectados, infracción de reglas o advertencias activas. |
| `2` | Error de sintaxis en argumentos CLI o archivo fuente no encontrado. |
| `>2` | Error no recuperable del sistema, fallo de memoria o excepción interna. |

### Diagnóstico del Entorno (`doctor`)
Ante comportamientos inesperados, verificá el estado operativo con:
```bash
daedalus doctor
```
Comprueba la presencia de las dependencias requeridas y la integridad de los componentes del paquete.