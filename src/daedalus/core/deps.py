"""Módulo de análisis de dependencias de inclusión y detección de ciclos en DAEDALUS."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


INCLUDE_REGEX = re.compile(r'^\s*#\s*include\s*["<]([^">]+)[">]')


def extraer_inclusiones(archivo: Path) -> List[str]:
    """Extrae la lista de cabeceras incluidas por un archivo fuente o cabecera."""
    if not archivo.is_file():
        return []
    includes = []
    try:
        contenido = archivo.read_text(encoding="utf-8", errors="ignore")
        for linea in contenido.splitlines():
            m = INCLUDE_REGEX.match(linea)
            if m:
                includes.append(m.group(1).strip())
    except Exception:
        pass
    return includes


def construir_grafo_dependencias(directorio_o_archivos: List[Path]) -> Dict[str, List[str]]:
    """Construye el grafo de dependencias de cabeceras locales entre archivos."""
    archivos_validos: List[Path] = []
    for item in directorio_o_archivos:
        p = Path(item)
        if p.is_dir():
            archivos_validos.extend(p.glob("**/*.[ch]"))
            archivos_validos.extend(p.glob("**/*.cpp"))
            archivos_validos.extend(p.glob("**/*.hpp"))
        elif p.is_file():
            archivos_validos.append(p)

    mapa_nombres = {f.name: f for f in archivos_validos}
    grafo: Dict[str, List[str]] = {}

    for f in archivos_validos:
        nombre = f.name
        grafo[nombre] = []
        includes = extraer_inclusiones(f)
        for inc in includes:
            inc_name = Path(inc).name
            if inc_name in mapa_nombres:
                grafo[nombre].append(inc_name)

    return grafo


def detectar_dependencias_circulares(grafo: Dict[str, List[str]]) -> List[List[str]]:
    """Detecta todos los ciclos de inclusión circular en el grafo de dependencias usando DFS."""
    ciclos: List[List[str]] = []
    visitados: Set[str] = set()
    en_camino: List[str] = []

    def dfs(nodo: str) -> None:
        if nodo in en_camino:
            idx = en_camino.index(nodo)
            ciclo = en_camino[idx:] + [nodo]
            # Normalizar para evitar duplicados en distinta rotación
            if ciclo not in ciclos:
                ciclos.append(ciclo)
            return

        if nodo in visitados:
            return

        visitados.add(nodo)
        en_camino.append(nodo)

        for vecino in grafo.get(nodo, []):
            dfs(vecino)

        en_camino.pop()

    for nodo in list(grafo.keys()):
        dfs(nodo)

    return ciclos
