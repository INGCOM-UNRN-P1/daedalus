"""CLI de DAEDALUS — Compilador pedagógico y traductor de diagnósticos GCC/Clang."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from daedalus import __version__
from daedalus.core.compiler import compilar_archivos
from daedalus.core.translator import parsear_stderr_compilador

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="daedalus",
    help="🛠️ DAEDALUS — Compilador C pedagógico y traductor de diagnósticos GCC/Clang/ld a español rioplatense.",
    add_completion=True,
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]DAEDALUS[/bold cyan] versión [bold]{__version__}[/bold]")
        raise typer.Exit(code=0)


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Muestra la versión de DAEDALUS.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    pass


def generar_seccion_markdown(resultado) -> str:
    """Genera sección de compilación y diagnósticos pedagógicos para Dredd."""
    lines = ["## Compilación y Diagnósticos (Daedalus)\n"]
    estado = "✓ Compilación Exitosa" if resultado.exito else "❌ Falló Compilación"
    lines.append(f"- **Estado:** {estado}")
    if resultado.binario:
        lines.append(f"- **Binario de salida:** `{resultado.binario}`")
    lines.append(f"- **Diagnósticos detectados:** {len(resultado.diagnosticos)}")
    lines.append(f"- **Banderas utilizadas:** `{resultado.flags_utilizadas}`\n")

    if resultado.exito and not resultado.diagnosticos:
        lines.append("> [!TIP]\n> **Compilación Limpia:** El código compiló sin errores ni advertencias bajo los estándares estrictos de la cátedra (`-Wall -Wextra -Werror -std=c11 -pedantic`).\n")
    elif resultado.diagnosticos:
        lines.append("| Severidad | Ubicación | Diagnóstico | Explicación Pedagógica | Sugerencia |")
        lines.append("| :---: | :--- | :--- | :--- | :--- |")
        for d in resultado.diagnosticos:
            loc = f"`{d.archivo}:{d.linea}:{d.columna}`" if d.linea else (f"`{d.archivo}`" if d.archivo else "Compilador")
            sev_badge = "❌ ERROR" if d.severidad == "error" else "⚠️ ADVERTENCIA"
            lines.append(f"| {sev_badge} | {loc} | **{d.titulo}** | {d.explicacion} | {d.sugerencia} |")
        lines.append("")
    return "\n".join(lines)


@app.command("compile")
def compile_cmd(
    fuentes: List[Path] = typer.Argument(..., help="Archivos fuentes .c a compilar."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta del binario de salida."),
    json_output: bool = typer.Option(False, "--json", help="Emitir reporte en JSON."),
    output_md: Optional[Path] = typer.Option(None, "--md", "--output-md", help="Generar sección de reporte en formato Markdown para fusión en Dredd."),
    flags: Optional[str] = typer.Option(None, "--flags", help="Banderas adicionales para GCC separadas por espacio."),
) -> None:
    """Compila código C con banderas estrictas de cátedra y traduce errores a español didáctico."""
    extra_flags = flags.split() if flags else None
    resultado = compilar_archivos(fuentes, binario_salida=output, flags_adicionales=extra_flags)

    if output_md:
        md_text = generar_seccion_markdown(resultado)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(md_text, encoding="utf-8")
        console.print(f"[green]✓ Sección Markdown generada en:[/green] [cyan]{output_md}[/cyan]")
        raise typer.Exit(code=0 if resultado.exito else 1)

    if json_output:
        print(json.dumps(resultado.to_dict(), indent=2, ensure_ascii=False))
        raise typer.Exit(code=0 if resultado.exito else 1)

    if resultado.exito:
        console.print(Panel(
            f"[bold green]✓ Compilación Exitosa[/bold green]\n\n"
            f"Binario generado: [cyan]{resultado.binario}[/cyan]",
            title="DAEDALUS Compilation OK",
            border_style="green",
        ))
        raise typer.Exit(code=0)

    # Mostrar diagnósticos pedagógicos
    console.print(f"\n[bold red]❌ Falló la compilación ({len(resultado.diagnosticos)} diagnósticos detectados):[/bold red]\n")

    for idx, d in enumerate(resultado.diagnosticos, 1):
        color = "red" if d.severidad == "error" else "yellow" if d.severidad == "warning" else "blue"
        loc = f"{d.archivo}:{d.linea}:{d.columna}" if d.linea else (d.archivo or "compilador")

        cuerpo = (
            f"📍 [bold]Ubicación:[/bold] [yellow]{loc}[/yellow]\n"
            f"🔍 [bold]Causa:[/bold] {d.explicacion}\n\n"
            f"💡 [bold green]Sugerencia:[/bold green] {d.sugerencia}\n\n"
            f"[dim]Mensaje crudo: {d.mensaje_original}[/dim]"
        )
        console.print(Panel(cuerpo, title=f"[{color}][bold]{d.severidad.upper()}: {d.titulo}[/bold][/{color}]", border_style=color))

    raise typer.Exit(code=1)


@app.command("report")
def report_cmd(
    fuentes: List[Path] = typer.Argument(..., help="Archivos fuentes .c a compilar y auditar."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta de destino del archivo Markdown."),
    flags: Optional[str] = typer.Option(None, "--flags", help="Banderas adicionales para GCC."),
) -> None:
    """Genera directamente la sección de reporte Markdown de DAEDALUS para Dredd."""
    extra_flags = flags.split() if flags else None
    resultado = compilar_archivos(fuentes, flags_adicionales=extra_flags)
    md_content = generar_seccion_markdown(resultado)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")
        console.print(f"[green]✓ Reporte Markdown generado en:[/green] [cyan]{output}[/cyan]")
    else:
        print(md_content)


@app.command("translate")
def translate_cmd(
    stderr_file: Optional[Path] = typer.Argument(None, help="Archivo con stderr crudo o leer desde stdin."),
    json_output: bool = typer.Option(False, "--json", help="Salida en JSON."),
) -> None:
    """Traduce un bloque de texto o log de compilador a diagnósticos didácticos."""
    if stderr_file and stderr_file.is_file():
        texto = stderr_file.read_text(encoding="utf-8")
    else:
        import sys
        texto = sys.stdin.read()

    diagnosticos = parsear_stderr_compilador(texto)

    if json_output:
        print(json.dumps([d.to_dict() for d in diagnosticos], indent=2, ensure_ascii=False))
        raise typer.Exit(code=0)

    if not diagnosticos:
        console.print("[green]No se encontraron errores ni advertencias en el log proporcionado.[/green]")
        raise typer.Exit(code=0)

    for d in diagnosticos:
        console.print(f"[bold red]• {d.titulo}[/bold red] ({d.archivo}:{d.linea}): {d.explicacion}")


@app.command("doctor")
def doctor_cmd() -> None:
    """Verifica disponibilidad de herramientas del toolchain (GCC, Clang, Make, GDB, ld)."""
    from daedalus.core.doctor import ejecutar_diagnostico_doctor
    ok = ejecutar_diagnostico_doctor(console=console)
    if not ok:
        raise typer.Exit(code=1)


@app.command("preprocess")
def preprocess_cmd(
    fuente: Path = typer.Argument(..., help="Archivo fuente .c a preprocesar."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Guardar salida preprocesada en archivo."),
) -> None:
    """Ejecuta el preprocesador de C (gcc -E) y limpia comentarios y directivas del sistema."""
    import subprocess
    if not fuente.is_file():
        console.print(f"[bold red]Archivo no encontrado: {fuente}[/bold red]")
        raise typer.Exit(code=1)

    cmd = ["gcc", "-E", "-P", str(fuente)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        console.print(f"[bold red]Error en preprocesador:[/bold red]\n{res.stderr}")
        raise typer.Exit(code=1)

    # Filtrar líneas vacías redundantes
    lineas = [l for l in res.stdout.splitlines() if l.strip()]
    contenido = "\n".join(lineas)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(contenido, encoding="utf-8")
        console.print(f"[bold green]✓ Código preprocesado guardado en:[/bold green] [cyan]{output}[/cyan]")
    else:
        from rich.syntax import Syntax
        console.print(Syntax(contenido, "c", theme="monokai", line_numbers=True))


@app.command("explain-opt")
def explain_opt_cmd(
    nivel: str = typer.Argument("O2", help="Nivel de optimización a explicar: O0, O1, O2, O3, Os, Og."),
) -> None:
    """Explica el comportamiento didáctico y los efectos de los niveles de optimización de GCC."""
    lvl = nivel.upper().lstrip("-")
    explicaciones = {
        "O0": ("Sin optimizaciones (Default)", "Compilación rápida y depuración paso a paso perfecta con GDB. No elimina código muerto ni reordena instrucciones."),
        "O1": ("Optimización básica", "Reduce tamaño y tiempo de ejecución sin aumentar el tiempo de compilación. Puede activar advertencias de variables no inicializadas."),
        "O2": ("Optimización estándar de cátedra/producción", "Aplica vectorización básica, inlining de funciones chicas y análisis profundo de flujo de datos. Muchas advertencias pedagógicas de GCC requieren -O2 para detectar variables no inicializadas."),
        "O3": ("Optimización agresiva", "Aplica desenrollado de bucles (loop unrolling), vectorización SIMD agresiva y reordenamiento de memoria. Puede alterar el orden de instrucciones y dificultar depuración."),
        "OS": ("Optimización para tamaño", "Deshabilita optimizaciones que incrementen el tamaño del binario. Ideal para microcontroladores y C embebido."),
        "OG": ("Optimización para depuración", "Aplica optimizaciones que no interfieren con la experiencia de depuración paso a paso con GDB."),
    }

    info = explicaciones.get(lvl, ("Nivel desconocido", "Consultá la documentación oficial de GCC (man gcc)."))
    console.print(Panel(
        f"[bold white]{info[0]}[/bold white]\n\n{info[1]}",
        title=f"GCC Optimization Level: -{lvl}",
        border_style="cyan",
    ))


@app.command("compile-commands")
def compile_commands_cmd(
    fuentes: List[Path] = typer.Argument(..., help="Archivos fuentes del proyecto."),
    output: Path = typer.Option(Path("compile_commands.json"), "--output", "-o", help="Ruta de destino del archivo JSON."),
) -> None:
    """Genera compile_commands.json para Language Servers (Clangd / VS Code / Neovim)."""
    import json
    entries = []
    cwd = str(Path.cwd().resolve())

    for f in fuentes:
        p = Path(f).resolve()
        entries.append({
            "directory": cwd,
            "command": f"gcc -std=c11 -Wall -Wextra -Wpedantic -Werror -I{cwd} -c {p.name}",
            "file": str(p),
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    console.print(f"[bold green]✓ compile_commands.json generado exitosamente con {len(entries)} archivos en:[/bold green] [cyan]{output}[/cyan]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()

