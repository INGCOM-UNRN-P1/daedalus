"""Diagnóstico de compiladores y toolchains para Daedalus."""

from __future__ import annotations

import shutil
import subprocess
from typing import Dict, Any, Optional

from rich.console import Console
from rich.table import Table


def chequear_herramienta(comando: str, args_version: str = "--version") -> Dict[str, Any]:
    path = shutil.which(comando)
    if not path:
        return {"disponible": False, "version": None, "ruta": None}
    try:
        res = subprocess.run([comando, args_version], capture_output=True, text=True, timeout=3)
        salida = (res.stdout or res.stderr).strip().splitlines()
        version = salida[0] if salida else "Detectada"
    except Exception:
        version = "Detectada"
    return {"disponible": True, "version": version, "ruta": path}


def ejecutar_diagnostico_doctor(console: Optional[Console] = None) -> bool:
    cons = console or Console()
    herramientas = [
        ("gcc", "Compilador GNU C principal", True, "sudo apt install build-essential"),
        ("clang", "Compilador LLVM alternativo con diagnósticos ricos", False, "sudo apt install clang"),
        ("make", "Gestor de construcción para Makefiles institucionales", True, "sudo apt install make"),
        ("gdb", "Depurador interactivo de GNU", False, "sudo apt install gdb"),
    ]
    
    tabla = Table(title="🏥 Diagnóstico de Compiladores (Daedalus doctor)", border_style="cyan")
    tabla.add_column("Herramienta", style="bold white")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Versión / Ruta", style="dim")
    tabla.add_column("Propósito / Acción sugerida", style="yellow")
    
    todo_ok = True
    for cmd, desc, obligatorio, fix in herramientas:
        info = chequear_herramienta(cmd)
        if info["disponible"]:
            estado = "[bold green]✓ OK[/bold green]"
            detalles = f"{info['version']} ([cyan]{info['ruta']}[/cyan])"
            accion = desc
        else:
            if obligatorio:
                estado = "[bold red]✗ Faltante[/bold red]"
                todo_ok = False
            else:
                estado = "[yellow]! Opcional[/yellow]"
            detalles = "[dim]No encontrado en $PATH[/dim]"
            accion = f"{desc} ↳ {fix}"
        tabla.add_row(cmd, estado, detalles, accion)
        
    cons.print(tabla)
    return todo_ok
