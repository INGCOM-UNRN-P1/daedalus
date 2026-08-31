"""Pruebas unitarias e integración de funcionalidades QoL añadidas en DAEDALUS."""

from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner

from daedalus.cli import app
from daedalus.core.deps import construir_grafo_dependencias, detectar_dependencias_circulares
from daedalus.core.macro_explainer import expandir_macro
from daedalus.core.standards import sugerir_flags_pedagogicos, verificar_compatibilidad_estandares
from daedalus.core.stats import obtener_estadisticas, registrar_diagnosticos

runner = CliRunner()


def test_expand_macro_core(tmp_path: Path):
    c_code = """
#define CUADRADO(x) ((x) * (x))
#define MULTIPLO(a, b) ((a) * (b))
int main() {
    int y = CUADRADO(5);
    return 0;
}
"""
    f = tmp_path / "macro_test.c"
    f.write_text(c_code, encoding="utf-8")

    res = expandir_macro(f, nombre_macro="CUADRADO")
    assert "error" not in res
    assert "CUADRADO" in res.get("macro_seleccionada", "")
    assert int(res.get("total_macros", 0)) >= 2


def test_cli_expand_macro(tmp_path: Path):
    c_code = """
#define SUMA(a, b) ((a) + (b))
int main() { return SUMA(2, 3); }
"""
    f = tmp_path / "test_suma.c"
    f.write_text(c_code, encoding="utf-8")

    result = runner.invoke(app, ["expand-macro", str(f), "--macro", "SUMA"])
    assert result.exit_code == 0
    assert "SUMA" in result.output


def test_stats_and_history(tmp_path: Path):
    hist_file = tmp_path / "hist.json"
    
    class DummyDiag:
        def __init__(self, tit, sev="error"):
            self.titulo = tit
            self.severidad = sev
            self.archivo = "main.c"
            self.linea = 10

    diags = [DummyDiag("Puntero no inicializado"), DummyDiag("Puntero no inicializado"), DummyDiag("Falta punto y coma")]
    registrar_diagnosticos(diags, [Path("main.c")], historial_path=hist_file)

    stats = obtener_estadisticas(historial_path=hist_file)
    assert stats["total_sesiones"] == 1
    assert stats["total_diagnosticos"] == 3
    assert stats["frecuencia_errores"]["Puntero no inicializado"] == 2
    assert stats["frecuencia_errores"]["Falta punto y coma"] == 1


def test_cli_stats(tmp_path: Path):
    result = runner.invoke(app, ["stats", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total_sesiones" in data


def test_suggest_flags():
    # Sin flags -> faltan casi todos
    res = sugerir_flags_pedagogicos(flags_actuales=["-O2"])
    assert not res["cumple_estricto"]
    assert "-Wall" in res["flags_faltantes"]
    assert "-std=c11" in res["flags_faltantes"]

    # Con todos los flags
    res_ok = sugerir_flags_pedagogicos(flags_actuales=[
        "-Wall", "-Wextra", "-pedantic", "-std=c11", "-g", "-Wconversion", "-Werror=implicit-function-declaration"
    ])
    assert res_ok["cumple_estricto"]
    assert len(res_ok["flags_faltantes"]) == 0


def test_cli_check_flags(tmp_path: Path):
    makefile = tmp_path / "Makefile"
    makefile.write_text("CFLAGS = -Wall -Wextra -pedantic -std=c11 -g -Wconversion -Werror=implicit-function-declaration\n", encoding="utf-8")

    result = runner.invoke(app, ["check-flags", "--makefile", str(makefile)])
    assert result.exit_code == 0
    assert "Cumple" in result.output


def test_circular_deps(tmp_path: Path):
    h1 = tmp_path / "a.h"
    h2 = tmp_path / "b.h"

    h1.write_text('#include "b.h"\n', encoding="utf-8")
    h2.write_text('#include "a.h"\n', encoding="utf-8")

    grafo = construir_grafo_dependencias([tmp_path])
    assert "b.h" in grafo["a.h"]
    assert "a.h" in grafo["b.h"]

    ciclos = detectar_dependencias_circulares(grafo)
    assert len(ciclos) > 0


def test_cli_check_deps_clean(tmp_path: Path):
    h1 = tmp_path / "modulo.h"
    c1 = tmp_path / "modulo.c"
    h1.write_text("// header limpio\n", encoding="utf-8")
    c1.write_text('#include "modulo.h"\nint main(){return 0;}\n', encoding="utf-8")

    result = runner.invoke(app, ["check-deps", str(tmp_path)])
    assert result.exit_code == 0
    assert "Sin dependencias" in result.output


def test_check_standards(tmp_path: Path):
    c_file = tmp_path / "valid.c"
    c_file.write_text("int main(void) { return 0; }\n", encoding="utf-8")

    res = verificar_compatibilidad_estandares(c_file)
    assert "c11" in res
    assert res["c11"]["valido"] is True

    result = runner.invoke(app, ["check-standards", str(c_file)])
    assert result.exit_code == 0
    assert "C11" in result.output
