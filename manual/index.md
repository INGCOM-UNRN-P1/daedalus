---
title: "Manual de Referencia: daedalus"
subtitle: "Daedalus — Compilador Asistido con Cátedra Flags y Traducción de Diagnósticos GCC/Clang"
author: "Cátedra de Algoritmos y Programación"
date: "2026-08-31"
---

(manual-daedalus)=
# Daedalus — Compilador Asistido con Cátedra Flags y Traducción de Diagnósticos GCC/Clang

````{abstract}
**Rol en el ecosistema:** Compilador pedagógico que aplica los flags de cátedra (-std=c11, -Wall, -Wextra, -Werror, -pedantic) y traduce mensajes crípticos del compilador a español claro con explicaciones didácticas.
````

---

(manual-daedalus-proposito)=
## 1. Propósito y Filosofía Pedagógica

La herramienta **`daedalus`** forma parte del ecosistema oficial de software de la cátedra. Su diseño sigue principios pedagógicos rigurosos:

1. **Evidencia Técnica Directa**: Todo diagnóstico se fundamenta en la norma ISO C (C11/C23), en el modelo de memoria del sistema o en convenciones arquitectónicas formales.
2. **Acción Correctiva Concreta**: Cada advertencia incluye la prescripción técnica inmediata para resolver el defecto sin recurrir a conjeturas.
3. **Autonomía del Estudiante**: Facilita la autoevaluación local antes de la entrega final del trabajo práctico.
4. **Objetividad Docente**: Estandariza la corrección automática eliminando discrepancias subjetivas en la evaluación.

---

(manual-daedalus-instalacion)=
## 2. Instalación y Diagnóstico del Entorno

````{important}
Asegurate de contar con el compilador GCC/Clang y las librerías del sistema instaladas antes de ejecutar `daedalus`.
````

Para comprobar el estado de salud de tu entorno de trabajo y las dependencias auxiliares:

````{code-block} bash
# Comprobación de dependencias del sistema
daedalus doctor
````

Si se detecta la falta de alguna utilidad (como `gdb`, `valgrind`, `clang-format` o `typst`), el comando indicará el paquete exacto a instalar según tu distribución GNU/Linux o entorno MSYS2.

---

(manual-daedalus-comandos)=
## 3. Referencia Completa de Comandos CLI

A continuación se detallan los subcomandos principales disponibles en `daedalus`:

| Sintaxis del Comando | Descripción y Efecto |
| :--- | :--- |
| `daedalus compile src/*.c -o ./bin/programa` | Compila bajo flags estrictos con traducción pedagógica. |
| `daedalus explain "<error_str>"` | Explica un error o advertencia de GCC/Clang en lenguaje accesible. |
| `daedalus suggest-flags` | Sugiere los flags defensivos adecuados según el estándar fijado. |
| `daedalus doctor` | Verifica compiladores GCC y Clang instalados en el sistema. |

````{tip}
Podés agregar el flag `--json` a la mayoría de los comandos para exportar resultados en formato estructurado o `--md` para generar reportes Markdown para el informe de entrega.
````

---

(manual-daedalus-tutorial)=
## 4. Tutorial Paso a Paso con Ejemplos Reales

### Caso de Estudio

Considerá el siguiente fragmento de código representativo:

````{code-block} c
:linenos:
#include <stdio.h>

int main(void) {
    int x; // Variable sin inicializar
    if (x = 5) { // Asignación dentro del if en lugar de comparación ==
        printf("Valor: %d\n", x);
    }
    return 0;
}
````

### Ejecución de la Herramienta

Ejecutá el análisis desde tu terminal:

````{code-block} bash
daedalus compile src/*.c -o ./bin/programa
````

### Salida Obtenida en Consola

````{code-block} text
[!] ERROR PEDAGÓGICO DAEDALUS en main.c:5:9:
    Advertencia: sugerencia de paréntesis alrededor de la asignación usada como condición de verdad [-Wparentheses]

💡 EXPLICACIÓN DE CÁTEDRA:
    Escribiste 'x = 5' con un solo '=', lo cual ASIGNA el valor 5 a 'x' y siempre evalúa como verdadero.
    Si querías verificar igualdad, debés usar '==': 'if (x == 5)'.
    Si realmente deseabas una asignación dentro de la condición, encerrala entre paréntesis: 'if ((x = 5))'.
````

````{note}
Prestá atención a la explicación pedagógica generada: la herramienta no solo señala la línea del problema, sino que explica la causa raíz y el impacto en memoria o arquitectura.
````

---

(manual-daedalus-ejercicios)=
## 5. Ejercicios Prácticos y Desafíos

Practicá el uso avanzado de **`daedalus`** resolviendo los siguientes ejercicios:

````{exercise} Desafío 1: Corrección de Warnings Defensivos
Compilar un código con variables sin inicializar y resolver todos los warnings.

**Instrucción de ejecución:**
```bash
daedalus compile src/calculadora.c -o bin/calc
```
````

````{solution} Desafío 1
```bash
daedalus compile src/calculadora.c -o bin/calc
# Verificá que la operación concluya exitosamente con código de salida 0.
```
````

````{exercise} Desafío 2: Traducción de Error de Enlazado (Linker / undefined reference)
Explicar didácticamente el error `undefined reference to main` o función faltante.

**Instrucción de ejecución:**
```bash
daedalus explain "undefined reference to 'lista_crear'"
```
````

````{solution} Desafío 2
```bash
daedalus explain "undefined reference to 'lista_crear'"
# Revisá el archivo generado o el informe en terminal para confirmar la resolución del problema.
```
````

````{exercise} Desafío 3: Configuración de Flags de Optimización y Debug
Compilar con símbolos DWARF completos para depurar con GDB.

**Instrucción de ejecución:**
```bash
daedalus compile src/main.c -g3 -o bin/debug_app
```
````

````{solution} Desafío 3
```bash
daedalus compile src/main.c -g3 -o bin/debug_app
# Comprobá que la salida confirme la ausencia de advertencias o errores pendientes.
```
````

---

(manual-daedalus-makefile)=
## 6. Integración en el Flujo de Trabajo y Makefile

Para incorporar `daedalus` de forma automática a tu flujo de desarrollo, agregá la siguiente regla en el `Makefile` de tu proyecto:

````{code-block} makefile
check-daedalus:
	@echo "=== Ejecutando verificación con daedalus ==="
	daedalus check src/ include/

.PHONY: check-daedalus
````

Ejecutá `make check-daedalus` antes de cada commit para asegurar que tu código conserve el estado de aprobación.
