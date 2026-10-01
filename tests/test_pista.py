"""Modo pista (`--pista` o P1_PISTA=1): el tipo de error y la función, sin la línea ni la corrección."""

import json
import shutil

import pytest
from typer.testing import CliRunner

from daedalus.cli import app
from daedalus.core.pista import funcion_que_contiene, pista_activa

runner = CliRunner()

FUENTE = """\
#include <stdio.h>

int contador = 0;

int suma(int a, int b)
{
    int total = a + b
    return total;
}

static void
saludar(const char *nombre) {
    printf("%s\\n", nombre);
}

int main(void)
{
    return suma(1, 2);
}
"""


def test_funcion_que_contiene():
    lineas = FUENTE.splitlines()
    assert funcion_que_contiene(lineas, 7) == "suma"
    assert funcion_que_contiene(lineas, 13) == "saludar"
    assert funcion_que_contiene(lineas, 18) == "main"
    assert funcion_que_contiene(lineas, 3) is None  # una global, fuera de toda función
    assert funcion_que_contiene(lineas, 10) is None  # después del cierre de suma


def test_pista_activa_por_bandera_o_variable(monkeypatch):
    monkeypatch.delenv("P1_PISTA", raising=False)
    assert not pista_activa() and pista_activa(True)
    monkeypatch.setenv("P1_PISTA", "1")
    assert pista_activa()


@pytest.mark.skipif(not shutil.which("gcc"), reason="hace falta gcc")
def test_compile_en_modo_pista(tmp_path, monkeypatch):
    fuente = tmp_path / "prog.c"
    fuente.write_text(FUENTE, encoding="utf-8")
    monkeypatch.delenv("P1_PISTA", raising=False)
    normal = json.loads(runner.invoke(app, ["compile", str(fuente), "-o", str(tmp_path / "p"), "--json"]).stdout)
    assert normal["diagnosticos"][0]["linea"] in (7, 8) and "pista" not in normal

    res = runner.invoke(app, ["compile", str(fuente), "-o", str(tmp_path / "p"), "--json", "--pista"])
    datos = json.loads(res.stdout)
    assert res.exit_code == 1 and datos["pista"] is True
    error = datos["diagnosticos"][0]
    assert error["linea"] is None and error["columna"] is None and error["funcion"] == "suma"
    assert error["sugerencia"] == "" and error["mensaje_original"] == "" and error["titulo"]

    monkeypatch.setenv("P1_PISTA", "1")
    res = runner.invoke(app, ["compile", str(fuente), "-o", str(tmp_path / "p")], env={"COLUMNS": "400"})
    assert "prog.c, en la función suma()" in res.output and "prog.c:" not in res.output
    assert "Sugerencia" not in res.output


def test_translate_en_modo_pista(tmp_path, monkeypatch):
    monkeypatch.delenv("P1_PISTA", raising=False)
    fuente = tmp_path / "prog.c"
    fuente.write_text(FUENTE, encoding="utf-8")
    log = tmp_path / "log.txt"
    log.write_text(f"{fuente}:7:22: error: expected ';' before 'return'\n", encoding="utf-8")
    datos = json.loads(runner.invoke(app, ["translate", str(log), "--json", "--pista"]).stdout)
    assert datos[0]["linea"] is None and datos[0]["funcion"] == "suma"
