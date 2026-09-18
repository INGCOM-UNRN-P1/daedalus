# 🛠️ DAEDALUS — Compilador Pedagógico y Traductor GCC/Clang

DAEDALUS compila programas C bajo los estándares rigurosos de la cátedra (C11, `-Wall -Wextra -pedantic -Wconversion`) y traduce los mensajes crudos de error del compilador a explicaciones amigables en español rioplatense con sugerencias concretas.

---

## 🎯 Alcance

### Qué cubre
- Compilación pedagógica de código C bajo el perfil estricto de cátedra (C11, `-Wall -Wextra -pedantic -Wconversion -Werror=vla`).
- Traducción pedagógica de errores y advertencias de compilador (GCC, Clang) y enlazador (`ld`) a explicaciones en español rioplatense.
- Generación automatizada de base de compilación (`compile_commands.json`).
- Modo interactivo y salida estructurada JSON (`--json`) para integración con orquestadores.
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
