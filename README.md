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
