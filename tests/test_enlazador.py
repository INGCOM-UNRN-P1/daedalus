"""Errores del enlazador (ld) y --primer-error.

Los mensajes de ld no tienen la forma archivo:línea, así que un error de enlace terminaba sin ningún
diagnóstico: el estudiante veía que no compiló, sin explicación.
"""

import json
import shutil

import pytest
from typer.testing import CliRunner

from daedalus.cli import app
from daedalus.core.translator import parsear_stderr_compilador, primer_error

runner = CliRunner()
con_gcc = pytest.mark.skipif(shutil.which("gcc") is None, reason="hace falta gcc")

SIN_DEFINICION = """/usr/bin/ld.bfd: /tmp/ccFs9Ei3.o: in function `main':
a.c:(.text+0xf): undefined reference to `suma'
collect2: error: ld returned 1 exit status
"""
DUPLICADA = """/usr/bin/ld.bfd: /tmp/ccae.o:(.data+0x0): multiple definition of `x'; /tmp/cc8h.o:(.data+0x0): first defined here
collect2: error: ld returned 1 exit status
"""
SIN_MAIN = """/usr/bin/ld.bfd: /usr/lib64/crt1.o: in function `_start':
(.text+0x1b): undefined reference to `main'
collect2: error: ld returned 1 exit status
"""


def test_referencia_sin_definicion():
    (d,) = parsear_stderr_compilador(SIN_DEFINICION)
    assert d.severidad == "error" and "`suma`" in d.titulo
    assert d.archivo == "a.c" and d.funcion == "main" and d.linea is None
    assert "gcc main.c lista.c" in d.sugerencia


def test_definicion_duplicada_y_falta_main():
    (dup,) = parsear_stderr_compilador(DUPLICADA)
    assert dup.titulo == "Definición duplicada de `x`" and "extern" in dup.sugerencia
    (sin_main,) = parsear_stderr_compilador(SIN_MAIN)
    assert sin_main.titulo == "Falta la función `main`"


def test_falla_de_enlace_sin_detalle_igual_se_informa():
    (d,) = parsear_stderr_compilador("collect2: error: ld returned 1 exit status\n")
    assert d.titulo == "Falló el enlazado"


def test_primer_error_prefiere_errores_a_advertencias():
    stderr = ("t.c:2:5: warning: unused variable 'n' [-Wunused-variable]\n"
              "t.c:3:5: error: 'x' undeclared (first use in this function)\n"
              "t.c:4:5: error: expected ';' before 'return'\n")
    diags = parsear_stderr_compilador(stderr)
    assert len(diags) == 3
    (d,) = primer_error(diags)
    assert d.linea == 3


@con_gcc
def test_compile_con_error_de_enlace(tmp_path):
    fuente = tmp_path / "a.c"
    fuente.write_text("int suma(int a, int b);\nint main(void)\n{\n    return suma(1, 2);\n}\n", encoding="utf-8")
    res = runner.invoke(app, ["compile", str(fuente), "--json"])
    datos = json.loads(res.stdout)
    assert res.exit_code == 1 and datos["diagnosticos"][0]["titulo"].startswith("Símbolo no encontrado")


@con_gcc
def test_compile_primer_error(tmp_path):
    fuente = tmp_path / "t.c"
    fuente.write_text("int main(void)\n{\n    x = 1;\n    y = 2;\n    return 0\n}\n", encoding="utf-8")
    todos = json.loads(runner.invoke(app, ["compile", str(fuente), "--json"]).stdout)
    uno = json.loads(runner.invoke(app, ["compile", str(fuente), "--json", "--primer-error"]).stdout)
    assert len(todos["diagnosticos"]) > 1
    assert uno["diagnosticos"] == [todos["diagnosticos"][0]] and uno["suprimidos"] == len(todos["diagnosticos"]) - 1


def test_formato_y_declaracion_implicita_ya_se_traducen():
    """QoL #183 y #174: el catálogo ya los cubría; este test lo deja fijado."""
    stderr = ("f.c:5:14: warning: format ‘%s’ expects argument of type ‘char *’, but argument 2 has type ‘int’ [-Wformat=]\n"
              "f.c:6:5: error: implicit declaration of function ‘strlen’ [-Wimplicit-function-declaration]\n")
    formato, implicita = parsear_stderr_compilador(stderr)
    assert "char" in formato.titulo.lower() and "Diagnóstico" not in formato.titulo
    assert "strlen" in implicita.titulo
