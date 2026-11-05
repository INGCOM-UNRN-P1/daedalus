"""Lectura del SARIF 2.1.0 que emite GCC (`-fdiagnostics-format=sarif-stderr`, GCC 13 o posterior).

Da línea, columna y flag sin depender de la forma del texto. Lo que SARIF no resuelve:

- `ruleId` es un flag solo en las advertencias: los errores de sintaxis traen `error`, `fatal error`
  o `note`, y para esos el mensaje sigue siendo la única pista.
- `message.text` está en el idioma del compilador, igual que en la salida de texto.
- El enlazador no emite SARIF: sus errores siguen viniendo como texto.

No depende de daedalus para poder mudarse a `yutani.sarif` cuando la ola R1 lo publique.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import unquote


def flag_de_regla(regla: Optional[str]) -> Optional[str]:
    """El flag de un `ruleId`: `-Werror=return-type` y `-Wreturn-type` son el mismo, y `-Wformat=`
    se llama `-Wformat`. Lo que no es un flag (`error`, `note`) da None."""
    if not regla or not regla.startswith("-W"):
        return None
    if regla.startswith("-Werror="):
        regla = "-W" + regla[len("-Werror="):]
    return regla.split("=", 1)[0]


def _documentos(salida: str) -> Iterator[Dict[str, Any]]:
    """Los documentos SARIF de `salida`: uno por unidad de traducción, y puede haber texto del driver
    alrededor (`gcc: warning: …`, los mensajes de ld)."""
    decodificador = json.JSONDecoder()
    posicion = salida.find("{")
    while posicion != -1:
        try:
            documento, fin = decodificador.raw_decode(salida, posicion)
        except ValueError:
            posicion = salida.find("{", posicion + 1)
            continue
        if isinstance(documento, dict) and "runs" in documento:
            yield documento
        posicion = salida.find("{", fin)


def _archivo(ubicacion: Dict[str, Any]) -> Optional[str]:
    uri = ubicacion.get("artifactLocation", {}).get("uri")
    if not uri:
        return None
    if uri.startswith("file://"):
        ruta = unquote(uri[len("file://"):])
        # file:///C:/Users/… en Windows: la barra inicial no es parte de la ruta.
        return ruta[1:] if len(ruta) > 2 and ruta[0] == "/" and ruta[2] == ":" else ruta
    return uri  # GCC deja la ruta tal cual, sin codificar espacios ni acentos


def _posicion(ubicaciones: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """(archivo, línea, columna) de la primera ubicación; un diagnóstico de la línea de comandos no
    tiene ninguna."""
    fisica = (ubicaciones[0] if ubicaciones else {}).get("physicalLocation", {})
    region = fisica.get("region", {})
    return _archivo(fisica), region.get("startLine"), region.get("startColumn")


def _sin_escapes(mensaje: str) -> str:
    """Los mensajes de SARIF admiten marcadores `{0}`, así que las llaves literales van dobles."""
    return mensaje.replace("{{", "{").replace("}}", "}")


def _diagnostico(regla: Optional[str], nivel: str, mensaje: str,
                 ubicaciones: List[Dict[str, Any]]) -> Dict[str, Any]:
    archivo, linea, columna = _posicion(ubicaciones)
    return {
        "regla": regla,
        "flag": flag_de_regla(regla),
        "severidad": nivel if nivel in ("error", "warning") else "note",
        "mensaje": _sin_escapes(mensaje),
        "archivo": archivo,
        "linea": linea,
        "columna": columna,
    }


def parsear_sarif_gcc(salida: str) -> Optional[List[Dict[str, Any]]]:
    """Los diagnósticos de `salida` en el orden en que GCC los emitió, o None si no hay SARIF válido.

    Cada uno trae `regla`, `flag`, `severidad`, `mensaje`, `archivo`, `linea` y `columna`. Las notas
    que GCC guarda en `relatedLocations` van a continuación de su diagnóstico, como en el texto; las
    que no tienen mensaje solo describen la cadena de `#include` y se descartan.
    """
    diagnosticos: List[Dict[str, Any]] = []
    encontrado = False
    try:
        for documento in _documentos(salida):
            encontrado = True
            for corrida in documento["runs"]:
                for resultado in corrida.get("results", []):
                    diagnosticos.append(_diagnostico(resultado.get("ruleId"), resultado.get("level", "warning"),
                                                     resultado["message"]["text"], resultado.get("locations", [])))
                    for relacionada in resultado.get("relatedLocations", []):
                        texto = relacionada.get("message", {}).get("text")
                        if texto:
                            diagnosticos.append(_diagnostico(None, "note", texto, [relacionada]))
    except (AttributeError, KeyError, TypeError):
        return None  # JSON válido con otra forma: que decida el camino de texto
    return diagnosticos if encontrado else None
