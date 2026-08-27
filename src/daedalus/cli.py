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


@app.command("compile")
def compile_cmd(
    fuentes: List[Path] = typer.Argument(..., help="Archivos fuentes .c a compilar."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta del binario de salida."),
    json_output: bool = typer.Option(False, "--json", help="Emitir reporte en JSON."),
    flags: Optional[str] = typer.Option(None, "--flags", help="Banderas adicionales para GCC separadas por espacio."),
) -> None:
    """Compila código C con banderas estrictas de cátedra y traduce errores a español didáctico."""
    extra_flags = flags.split() if flags else None
    resultado = compilar_archivos(fuentes, binario_salida=output, flags_adicionales=extra_flags)

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
    """Verifica disponibilidad de herramientas del toolchain (GCC, Clang, Make, ld)."""
    tabla = Table(title="Toolchain de Compilación")
    tabla.add_column("Herramienta", style="bold cyan")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Ruta / Binario")

    for tool in ("gcc", "clang", "make", "ld", "gdb", "valgrind"):
        p = shutil.which(tool)
        tabla.add_row(tool, "[green]✓ Presente[/green]" if p else "[red]✗ Faltante[/red]", p or "No encontrado")

    console.print(tabla)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
