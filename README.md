# 🛠️ DAEDALUS — Compilador Pedagógico y Traductor GCC/Clang

> 📖 **Manual de Usuario:** Para una guía exhaustiva de comandos, banderas, arquitectura y ejemplos, consultá el [Manual de Uso](MANUAL.md).

DAEDALUS compila programas C bajo los estándares rigurosos de la cátedra (C11, `-Wall -Wextra -pedantic -Wconversion`) y traduce los mensajes crudos de error del compilador a explicaciones amigables en español rioplatense con sugerencias concretas.

---

## 🎯 Alcance

### Qué cubre
- Compilación pedagógica de código C bajo el perfil estricto de cátedra (C11, `-Wall -Wextra -pedantic -Wconversion -Werror=vla`).
- Traducción pedagógica de errores y advertencias de compilador (GCC, Clang) y enlazador (`ld`) a explicaciones en español rioplatense.
- Generación automatizada de base de compilación (`compile_commands.json`).
- Modo interactivo y salida estructurada JSON (`--json`) para integración con orquestadores.
- Modo pista para evaluaciones (`--pista` o `P1_PISTA=1`, que ripley exporta con `[general] pistas = true`): cada error dice qué tipo de problema es y en qué función está, sin la línea, el mensaje crudo ni la corrección.
- Verificación del estado de salud del toolchain mediante `daedalus doctor`.

### Qué no cubre (Límites y Delegación)
- Ejecución en sandbox y límite de recursos (delegado a `nostromo`).
- Linter de estilo y formato de código (delegado a `gaff`).
- Orquestación masiva y calificación docente (delegado a `dredd`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Linux (nativo / WSL) o Windows (MSYS2 UCRT64). Python >= 3.10.

### Dependencias Externas y Binarios
- `gcc` y/o `clang`, `ld`.

### Integración en el Ecosistema
- CLI `daedalus`. Plugin en `ripley.plugins` (`compiler`). Consumido por `ripley` y `dredd`.

---

## Uso Rápido

```bash
# 1. Compilar código C con banderas pedagógicas y traducción de errores
daedalus compile main.c -o ./programa

# 2. Salida estructurada JSON
daedalus compile main.c --json

# 3. Traducir un archivo de log de compilador
daedalus translate stderr.log

# 4. Comprobar salud del toolchain (gcc, clang, ld, gdb)
daedalus doctor
```


## 📚 Referencia de comandos

| Comando | Para qué sirve |
| :--- | :--- |
| `compile FUENTES... [-o BIN] [--json] [--md ARCHIVO] [--flags ...] [--cc gcc\|clang] [--guide]` | Compila con las banderas estrictas de cátedra y traduce los diagnósticos a español. |
| `report FUENTES... [-o ARCHIVO]` | Compila y genera la sección Markdown para Dredd. |
| `translate [LOG] [--json]` | Traduce un log de compilador (archivo o stdin) sin compilar. |
| `doctor` | Verifica el toolchain: GCC, Clang, Make, GDB, ld. |
| `preprocess FUENTE [-o ARCHIVO]` | Corre `gcc -E` y limpia comentarios y directivas del sistema. |
| `explain-opt [NIVEL]` | Explica qué hace cada nivel de optimización (`-O0`…`-O3`, `-Os`). |
| `compile-commands FUENTES... [-o ARCHIVO]` | Genera `compile_commands.json` para clangd / VS Code / Neovim. |
| `expand-macro FUENTE -m MACRO` | Expande una macro anidada paso a paso. |
| `history` / `stats` | Historial y estadísticas de los errores más frecuentes del estudiante (son el mismo comando). |
| `check-flags [-m MAKEFILE] [-f FLAGS]` | Audita banderas de compilación y marca las obligatorias que faltan. |
| `suggest-flags [FUENTE_O_LOG] [-m MAKEFILE]` | Sugiere flags de compilación/enlazado a partir de un fuente, un log o un Makefile. |
| `list-warnings` / `catalog` | Lista el catálogo de advertencias documentadas (son el mismo comando). |
| `guide FUENTE [-o ARCHIVO]` | Guía de resolución paso a paso en Markdown. |
| `check-arch LOG` | Detecta advertencias de tamaño que cambian entre 32 y 64 bits. |
| `check-standards FUENTE` | Compara la compatibilidad con C99, C11, C17 y C2x/C23. |
| `check-deps RUTAS...` | Grafo de inclusiones y dependencias circulares entre cabeceras. |

<!-- p1:referencia:inicio — generado por p1-tools/scripts/readme_generado.py: no editar a mano -->

## Referencia rápida

### Requisitos

- Python ≥ 3.11 y [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Programas del sistema: `gcc`.

| Sistema | `gcc` |
|:--|:--|
| Debian / Ubuntu | `sudo apt install gcc` |
| Fedora | `sudo dnf install gcc` |
| Windows | incluido en el entorno de la cátedra (MSYS2 UCRT64) |
| macOS | `xcode-select --install` (clang como `gcc`) |

### Comandos

| Comando | Descripción |
|:--|:--|
| `daedalus compile` | Compila código C con banderas estrictas de cátedra y traduce errores a español didáctico. |
| `daedalus report` | Genera directamente la sección de reporte Markdown de DAEDALUS para Dredd. |
| `daedalus translate` | Traduce un bloque de texto o log de compilador a diagnósticos didácticos. |
| `daedalus doctor` | Verifica disponibilidad de herramientas del toolchain (GCC, Clang, Make, GDB, ld). |
| `daedalus preprocess` | Ejecuta el preprocesador de C (gcc -E) y limpia comentarios y directivas del sistema. |
| `daedalus explain-opt` | Explica el comportamiento didáctico y los efectos de los niveles de optimización de GCC. |
| `daedalus compile-commands` | Genera compile_commands.json para Language Servers (Clangd / VS Code / Neovim). |
| `daedalus expand-macro` | Expande y desglosa macros anidadas paso a paso para traducir errores complejos. |
| `daedalus history`, `daedalus stats` | Muestra el historial y estadísticas de errores frecuentes del estudiante. |
| `daedalus check-flags` | Audita las banderas de compilación y sugiere flags pedagógicos obligatorios faltantes. |
| `daedalus suggest-flags` | Analiza un archivo fuente, log de errores o Makefile y sugiere flags de compilación/enlazado faltantes. |
| `daedalus list-warnings`, `daedalus catalog` | Lista todas las advertencias y reglas pedagógicas documentadas en el catálogo de diagnósticos. |
| `daedalus guide` | Genera una guía interactiva de resolución paso a paso en Markdown para el archivo C indicado. |
| `daedalus check-arch` | Audita advertencias relacionadas con incompatibilidades de tamaño en 32 vs 64 bits. |
| `daedalus check-standards` | Verifica la compatibilidad del código simultáneamente contra C99, C11, C17 y C2x/C23. |
| `daedalus check-deps` | Construye el grafo de inclusiones y detecta dependencias circulares entre cabeceras. |

Ayuda de cada comando: `daedalus <comando> -h`.

<!-- p1:referencia:fin -->
