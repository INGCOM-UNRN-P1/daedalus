"""Tests unitarios para el traductor de diagnósticos de DAEDALUS."""

from pathlib import Path
import pytest
from daedalus.core.compiler import compilar_archivos
from daedalus.core.translator import parsear_stderr_compilador, traducir_linea_diagnostico


def test_traducir_falta_punto_y_coma():
    msg = "expected ';' before 'return'"
    tit, exp, sug = traducir_linea_diagnostico(msg)
    assert "punto y coma" in tit
    assert ";" in sug



def test_traducir_variable_no_declarada():
    msg = "'contador' undeclared (first use in this function)"
    tit, exp, sug = traducir_linea_diagnostico(msg)
    assert "contador" in tit
    assert "no declarado" in tit


def test_parsear_stderr_completo():
    stderr = """
main.c:12:5: error: expected ';' before 'return'
main.c:15:10: warning: implicit declaration of function 'strcpy'
"""
    diags = parsear_stderr_compilador(stderr)
    assert len(diags) == 2
    assert diags[0].severidad == "error"
    assert diags[0].linea == 12
    assert diags[1].severidad == "warning"
    assert diags[1].linea == 15


def test_compilar_codigo_valido(tmp_path):
    fuente = tmp_path / "main.c"
    fuente.write_text("#include <stdio.h>\nint main(void) { return 0; }\n")

    res = compilar_archivos([fuente])
    assert res.exito is True
    assert res.binario is not None
    assert res.binario.is_file()


def test_compilar_codigo_con_error_sintaxis(tmp_path):
    fuente = tmp_path / "error.c"
    fuente.write_text("int main(void) { int x = 5 return 0; }\n")

    res = compilar_archivos([fuente])
    assert res.exito is False
    assert len(res.diagnosticos) >= 1
    assert any("punto y coma" in d.titulo for d in res.diagnosticos)
