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
from daedalus.core.arch_check import check_arch_incompatibilities
from daedalus.core.compiler import compilar_archivos
from daedalus.core.deps import construir_grafo_dependencias, detectar_dependencias_circulares
from daedalus.core.diagnostic_catalog import list_catalog_entries
from daedalus.core.filter import filter_and_deduplicate
from daedalus.core.guide_generator import generate_resolution_guide
from daedalus.core.macro_explainer import expandir_macro
from daedalus.core.standards import sugerir_flags_pedagogicos, verificar_compatibilidad_estandares
from daedalus.core.stats import obtener_estadisticas, registrar_diagnosticos
from daedalus.core.suggest_flags import analyze_missing_flags
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
    status = "ok" if resultado.exito else "fail"
    lines = [
        f"<!-- dredd-section: daedalus, tool=daedalus, version=1.0.0, status={status} -->\n",
        "## Compilación y Diagnósticos (Daedalus)\n",
    ]
    estado = "✓ Compilación Exitosa" if resultado.exito else "❌ Falló Compilación"
    lines.append(f"- **Estado:** {estado}")
    if resultado.binario:
        lines.append(f"- **Binario de salida:** `{resultado.binario}`")
    lines.append(f"- **Diagnósticos detectados:** {len(resultado.diagnosticos)}")
    lines.append(f"- **Banderas utilizadas:** `{resultado.flags_utilizadas if hasattr(resultado, 'flags_utilizadas') else 'cátedra default'}`\n")

    if resultado.exito and not resultado.diagnosticos:
        lines.append("> [!TIP]\n> **Compilación Limpia:** El código compiló sin errores ni advertencias bajo los estándares estrictos de la cátedra (`-Wall -Wextra -Werror -std=c11 -pedantic`).\n")
    elif resultado.diagnosticos:
        lines.append("| Severidad | Ubicación | Diagnóstico | Explicación Pedagógica | Sugerencia |")
        lines.append("| :---: | :--- | :--- | :--- | :--- |")
        for d in resultado.diagnosticos:
            loc = f"`{d.archivo}:{d.linea}:{d.columna}`" if d.linea else (f"`{d.archivo}`" if d.archivo else "Compilador")
            sev_badge = "❌ ERROR" if d.severidad == "error" else "⚠️ ADVERTENCIA"
            tit_limpio = d.titulo.replace("|", "&#124;")
            exp_limpio = d.explicacion.replace("|", "&#124;")
            sug_limpio = d.sugerencia.replace("|", "&#124;")
            lines.append(f"| {sev_badge} | {loc} | **{tit_limpio}** | {exp_limpio} | {sug_limpio} |")
        lines.append("")
    return "\n".join(lines)


@app.command("compile")
def compile_cmd(
    fuentes: List[Path] = typer.Argument(..., help="Archivos fuentes .c a compilar."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta del binario de salida."),
    json_output: bool = typer.Option(False, "--json", help="Emitir reporte en JSON."),
    output_md: Optional[Path] = typer.Option(None, "--md", "--output-md", help="Generar sección de reporte en formato Markdown para fusión en Dredd."),
    flags: Optional[str] = typer.Option(None, "--flags", help="Banderas adicionales para el compilador separadas por espacio."),
    compiler: Optional[str] = typer.Option(None, "--compiler", "--cc", help="Compilador backend a utilizar: 'gcc' o 'clang'."),
    guide: bool = typer.Option(False, "--guide", help="Generar guía detallada paso a paso en Markdown."),
    dedup: bool = typer.Option(False, "--dedup", help="Suprimir advertencias repetitivas o en cascada."),
) -> None:
    """Compila código C con banderas estrictas de cátedra y traduce errores a español didáctico."""
    extra_flags = flags.split() if flags else None
    resultado = compilar_archivos(fuentes, binario_salida=output, flags_adicionales=extra_flags, compilador=compiler)

    if dedup and resultado.diagnosticos:
        resultado.diagnosticos, resultado.suprimidos = filter_and_deduplicate(resultado.diagnosticos)

    # Registrar en historial de errores
    if resultado.diagnosticos:
        registrar_diagnosticos(resultado.diagnosticos, fuentes)

    if guide:
        guide_text = generate_resolution_guide(resultado)
        console.print(guide_text)
        raise typer.Exit(code=0 if resultado.exito else 1)

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

    if resultado.suprimidos > 0:
        console.print(f"[dim]ℹ Se suprimieron {resultado.suprimidos} advertencias repetitivas o en cascada para mayor claridad.[/dim]")

    raise typer.Exit(code=1)


@app.command("report")
def report_cmd(
    fuentes: List[Path] = typer.Argument(..., help="Archivos fuentes .c a compilar y auditar."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta de destino del archivo Markdown."),
    flags: Optional[str] = typer.Option(None, "--flags", help="Banderas adicionales para GCC."),
    compiler: Optional[str] = typer.Option(None, "--compiler", "--cc", help="Compilador backend ('gcc' o 'clang')."),
) -> None:
    """Genera directamente la sección de reporte Markdown de DAEDALUS para Dredd."""
    extra_flags = flags.split() if flags else None
    resultado = compilar_archivos(fuentes, flags_adicionales=extra_flags, compilador=compiler)
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
    dedup: bool = typer.Option(False, "--dedup", help="Suprimir advertencias repetitivas o en cascada."),
) -> None:
    """Traduce un bloque de texto o log de compilador a diagnósticos didácticos."""
    if stderr_file and stderr_file.is_file():
        texto = stderr_file.read_text(encoding="utf-8")
    else:
        import sys
        texto = sys.stdin.read()

    diagnosticos = parsear_stderr_compilador(texto)
    suprimidos = 0
    if dedup and diagnosticos:
        diagnosticos, suprimidos = filter_and_deduplicate(diagnosticos)

    if json_output:
        res_data = [d.to_dict() for d in diagnosticos]
        print(json.dumps(res_data, indent=2, ensure_ascii=False))
        raise typer.Exit(code=0)

    if not diagnosticos:
        console.print("[green]No se encontraron errores ni advertencias en el log proporcionado.[/green]")
        raise typer.Exit(code=0)

    for d in diagnosticos:
        console.print(f"[bold red]• {d.titulo}[/bold red] ({d.archivo}:{d.linea}): {d.explicacion}")

    if suprimidos > 0:
        console.print(f"[dim]ℹ Se suprimieron {suprimidos} advertencias repetitivas o en cascada para mayor claridad.[/dim]")


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


@app.command("expand-macro")
def expand_macro_cmd(
    fuente: Path = typer.Argument(..., help="Archivo C con definiciones o usos de macros."),
    macro: Optional[str] = typer.Option(None, "--macro", "-m", help="Nombre de la macro a expandir e inspeccionar."),
    compiler: Optional[str] = typer.Option(None, "--compiler", "--cc", help="Compilador a utilizar."),
) -> None:
    """Expande y desglosa macros anidadas paso a paso para traducir errores complejos."""
    res = expandir_macro(fuente, nombre_macro=macro, compilador=compiler)
    if "error" in res:
        console.print(f"[bold red]❌ {res['error']}[/bold red]")
        raise typer.Exit(code=1)

    console.print(Panel(
        f"Total de macros detectadas: [bold cyan]{res.get('total_macros', '0')}[/bold cyan]\n\n"
        + (f"[bold yellow]Macro solicitada:[/bold yellow] {res.get('macro_seleccionada', '')}\n\n" if macro else "")
        + f"[dim]Código expandido:[/dim]\n{res.get('codigo_expandido', '')[:500]}...",
        title="🔍 Expansor de Macros Pedagógico",
        border_style="cyan",
    ))


@app.command("stats")
@app.command("history")
def stats_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emitir estadísticas en JSON."),
) -> None:
    """Muestra el historial y estadísticas de errores frecuentes del estudiante."""
    datos = obtener_estadisticas()
    if json_output:
        print(json.dumps(datos, indent=2, ensure_ascii=False))
        raise typer.Exit(code=0)

    tabla = Table(title="📊 Estadísticas de Errores de Compilación (Daedalus)")
    tabla.add_column("Diagnóstico / Error Frecuente", style="bold red")
    tabla.add_column("Ocurrencias", justify="right", style="cyan")

    for tit, count in datos.get("frecuencia_errores", {}).items():
        tabla.add_row(tit, str(count))

    if not datos.get("frecuencia_errores"):
        console.print("[green]No hay errores registrados en el historial local aún.[/green]")
    else:
        console.print(f"Total de sesiones registradas: [bold cyan]{datos['total_sesiones']}[/bold cyan] (Errores totales: [bold]{datos['total_diagnosticos']}[/bold])")
        console.print(tabla)


@app.command("check-flags")
def check_flags_cmd(
    makefile: Optional[Path] = typer.Option(None, "--makefile", "-m", help="Ruta al Makefile a inspeccionar."),
    flags: Optional[str] = typer.Option(None, "--flags", "-f", help="Lista de flags actuales separados por espacio."),
    json_output: bool = typer.Option(False, "--json", help="Emitir resultado en JSON."),
) -> None:
    """Audita las banderas de compilación y sugiere flags pedagógicos obligatorios faltantes."""
    lista_flags = flags.split() if flags else None
    res = sugerir_flags_pedagogicos(flags_actuales=lista_flags, makefile_path=makefile)

    if json_output:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        raise typer.Exit(code=0 if res["cumple_estricto"] else 1)

    if res["cumple_estricto"]:
        console.print("[bold green]✓ Configuración de flags óptima: Cumple con todos los estándares estrictos de cátedra.[/bold green]")
        raise typer.Exit(code=0)

    console.print("[bold yellow]⚠️ Se detectaron flags pedagógicos recomendados faltantes:[/bold yellow]\n")
    tabla = Table(title="Banderas Faltantes de Cátedra")
    tabla.add_column("Flag", style="bold red")
    tabla.add_column("Motivo Pedagógico", style="dim")

    for f, motivo in res.get("explicaciones", {}).items():
        tabla.add_row(f, motivo)

    console.print(tabla)
    raise typer.Exit(code=1)


@app.command("suggest-flags")
def suggest_flags_cmd(
    fuente_o_log: Optional[Path] = typer.Argument(None, help="Archivo fuente C o log de compilación a analizar."),
    makefile: Optional[Path] = typer.Option(None, "--makefile", "-m", help="Ruta al Makefile a inspeccionar."),
    flags: Optional[str] = typer.Option(None, "--flags", "-f", help="Lista de flags actuales separados por espacio."),
    json_output: bool = typer.Option(False, "--json", help="Emitir resultado en JSON."),
) -> None:
    """Analiza un archivo fuente, log de errores o Makefile y sugiere flags de compilación/enlazado faltantes."""
    if fuente_o_log and fuente_o_log.exists():
        content = fuente_o_log.read_text(encoding="utf-8", errors="replace")
        diagnostics = parsear_stderr_compilador(content)
        suggestions = analyze_missing_flags(content, diagnostics)

        if json_output:
            print(json.dumps(suggestions, indent=2, ensure_ascii=False))
            return

        if not suggestions:
            console.print("[bold green]✓ No se detectaron flags faltantes de enlazado o bibliotecas estándar.[/bold green]")
            return

        table = Table(title="Sugerencias de Flags de Compilación y Enlazado", show_header=True, header_style="bold cyan")
        table.add_column("Flag Sugerido", style="bold yellow")
        table.add_column("Motivo", style="white")
        table.add_column("Instrucción de Remediación", style="green")

        for s in suggestions:
            table.add_row(s["flag"], s["reason"], s["fix"])

        console.print(table)
        return

    check_flags_cmd(makefile=makefile, flags=flags, json_output=json_output)


@app.command("catalog")
@app.command("list-warnings")
def catalog_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON."),
) -> None:
    """Lista todas las advertencias y reglas pedagógicas documentadas en el catálogo de diagnósticos."""
    entries = list_catalog_entries()
    if json_output:
        print(json.dumps(entries, indent=2, ensure_ascii=False))
        return

    tabla = Table(title="Catálogo de Advertencias y Diagnósticos de GCC/Clang", show_header=True, header_style="bold magenta")
    tabla.add_column("Flag / Concepto", style="cyan")
    tabla.add_column("Diagnóstico en Español", style="bold white")
    tabla.add_column("Norma ISO C", style="italic yellow")

    for e in entries:
        flag_s = e["flag"] or e["key"]
        norma_s = e["citation"] or "-"
        tabla.add_row(flag_s, e["title"], norma_s)

    console.print(tabla)


@app.command("guide")
def guide_cmd(
    fuente: Path = typer.Argument(..., help="Archivo C a compilar y generar guía.", exists=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Guardar la guía en un archivo Markdown."),
    flags: Optional[str] = typer.Option(None, "--flags", help="Banderas adicionales para el compilador separadas por espacio."),
) -> None:
    """Genera una guía interactiva de resolución paso a paso en Markdown para el archivo C indicado."""
    extra_flags = flags.split() if flags else None
    resultado = compilar_archivos([fuente], flags_adicionales=extra_flags)
    guide_text = generate_resolution_guide(resultado)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(guide_text, encoding="utf-8")
        console.print(f"[bold green]✓ Guía Markdown generada en:[/bold green] {output}")
    else:
        console.print(guide_text)
    raise typer.Exit(code=0 if resultado.exito else 1)


@app.command("check-arch")
def check_arch_cmd(
    log_file: Path = typer.Argument(..., help="Archivo con la salida de compilador a auditar.", exists=True),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON."),
) -> None:
    """Audita advertencias relacionadas con incompatibilidades de tamaño en 32 vs 64 bits."""
    raw_text = log_file.read_text(encoding="utf-8", errors="replace")
    findings = check_arch_incompatibilities(raw_text)

    if json_output:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
        return

    if not findings:
        console.print("[bold green]✓ No se detectaron riesgos de portabilidad 32 vs 64 bits en el log analizado.[/bold green]")
        return

    for f in findings:
        console.print(Panel(
            f"[bold red]🚨 {f['title']}[/bold red]\n\n"
            f"[bold]Explicación:[/bold] {f['explanation']}\n\n"
            f"[bold yellow]Causa Raíz:[/bold yellow] {f['root_cause']}\n\n"
            f"[bold green]↳ Remediación:[/bold green] {f['suggestion']}",
            title="[bold red]Incompatibilidad 32/64 bits[/bold red]"
        ))


@app.command("check-standards")
def check_standards_cmd(
    fuente: Path = typer.Argument(..., help="Archivo C a validar contra múltiples estándares."),
    json_output: bool = typer.Option(False, "--json", help="Salida en JSON."),
) -> None:
    """Verifica la compatibilidad del código simultáneamente contra C99, C11, C17 y C2x/C23."""
    res = verificar_compatibilidad_estandares(fuente)

    if json_output:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        raise typer.Exit(code=0)

    tabla = Table(title=f"Matriz de Compatibilidad Multi-Estándar ({fuente.name})")
    tabla.add_column("Estándar", style="bold cyan")
    tabla.add_column("Veredicto", justify="center")
    tabla.add_column("Detalle")

    for std, val in res.items():
        if std == "error":
            console.print(f"[bold red]❌ {val['mensaje']}[/bold red]")
            raise typer.Exit(code=1)
        estado = "[green]✓ Compatible[/green]" if val["valido"] else "[red]✗ Incompatible[/red]"
        detalle = "Sin errores sintácticos" if val["valido"] else (val["errores"].splitlines()[0] if val["errores"] else "Error")
        tabla.add_row(std.upper(), estado, detalle)

    console.print(tabla)


@app.command("check-deps")
def check_deps_cmd(
    rutas: List[Path] = typer.Argument(..., help="Directorios o archivos C/H a auditar."),
    json_output: bool = typer.Option(False, "--json", help="Salida en JSON."),
) -> None:
    """Construye el grafo de inclusiones y detecta dependencias circulares entre cabeceras."""
    grafo = construir_grafo_dependencias(rutas)
    ciclos = detectar_dependencias_circulares(grafo)

    if json_output:
        print(json.dumps({"grafo": grafo, "ciclos": ciclos, "tiene_ciclos": len(ciclos) > 0}, indent=2, ensure_ascii=False))
        raise typer.Exit(code=1 if ciclos else 0)

    if not ciclos:
        console.print(f"[bold green]✓ Grafo de inclusiones limpio ({len(grafo)} módulos analizados): Sin dependencias circulares.[/bold green]")
        raise typer.Exit(code=0)

    console.print(f"[bold red]❌ Se detectaron {len(ciclos)} ciclos de inclusión circular:[/bold red]\n")
    for idx, c in enumerate(ciclos, 1):
        cadena = " -> ".join(c)
        console.print(f"  [red]{idx}.[/red] [yellow]{cadena}[/yellow]")

    raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
