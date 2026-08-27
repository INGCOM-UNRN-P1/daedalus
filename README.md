# 🛠️ DAEDALUS — Compilador Pedagógico y Traductor GCC/Clang

DAEDALUS compila programas C bajo los estándares rigurosos de la cátedra (C11, `-Wall -Wextra -pedantic -Wconversion`) y traduce los mensajes crudos de error del compilador a explicaciones amigables en español rioplatense con sugerencias concretas.

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
