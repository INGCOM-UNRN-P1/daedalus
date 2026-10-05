"""Tests de integración de la CLI de DAEDALUS."""

import json
from typer.testing import CliRunner
from daedalus.cli import app

runner = CliRunner()


def test_cli_version():
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert res.stdout.startswith("daedalus ")  # formato común de yutani: «nombre versión»


def test_cli_doctor():
    res = runner.invoke(app, ["doctor"])
    assert res.exit_code == 0
    assert "gcc" in res.stdout


def test_cli_compile_exito(tmp_path):
    fuente = tmp_path / "ok.c"
    fuente.write_text("int main(void) { return 0; }\n")

    res = runner.invoke(app, ["compile", str(fuente)])
    assert res.exit_code == 0
    assert "Compilación Exitosa" in res.stdout


def test_cli_compile_error_json(tmp_path):
    fuente = tmp_path / "bad.c"
    fuente.write_text("int main(void) { undeclared_func(); return 0; }\n")

    res = runner.invoke(app, ["compile", str(fuente), "--json"])
    assert res.exit_code == 1
    data = json.loads(res.stdout)
    assert data["exito"] is False
    assert data["total_diagnosticos"] >= 1


def test_translate_con_un_archivo_que_no_existe_es_un_error(tmp_path):
    """N-DAEDALUS-01: caía a leer stdin y respondía «No se encontraron errores» con código 0."""
    res = runner.invoke(app, ["translate", str(tmp_path / "no_existe.log")], env={"COLUMNS": "200"})
    assert res.exit_code == 2
    assert "no_existe.log" in res.output
    assert "No se encontraron errores" not in res.output


def test_translate_lee_el_archivo_o_la_entrada_estandar(tmp_path):
    log = tmp_path / "gcc.log"
    log.write_text("main.c:10:5: warning: unused variable 'x' [-Wunused-variable]\n", encoding="utf-8")
    assert "Variable Declarada sin Uso" in runner.invoke(app, ["translate", str(log)]).output
    res = runner.invoke(app, ["translate"], input=log.read_text(encoding="utf-8"))
    assert res.exit_code == 0 and "Variable Declarada sin Uso" in res.output
