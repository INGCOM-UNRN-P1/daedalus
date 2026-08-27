"""Tests adicionales para maximizar la cobertura en DAEDALUS."""

import json
from pathlib import Path
from typer.testing import CliRunner
import daedalus.cli
from daedalus.cli import app
from daedalus.core.compiler import compilar_archivos, parsear_stderr_compilador
from daedalus.ripley_plugin import DaedalusPlugin

runner = CliRunner()


def test_plugin_execution(tmp_path):
    p = DaedalusPlugin()
    assert p.is_available() is True

    # Empty workspace
    res_empty = p.execute(tmp_path, {})
    assert res_empty["ok"] is True

    # Workspace with valid file
    f = tmp_path / "main.c"
    f.write_text("int main(void) { return 0; }\n")
    res_ok = p.execute(tmp_path, {})
    assert res_ok["ok"] is True


def test_cli_compile_rich_failure(tmp_path):
    fuente = tmp_path / "broken.c"
    fuente.write_text("int main() { return undeclared_variable; }\n")

    res = runner.invoke(app, ["compile", str(fuente)])
    assert res.exit_code == 1
    assert "Falló la compilación" in res.stdout


def test_cli_translate_file(tmp_path):
    log_err = tmp_path / "err.log"
    log_err.write_text("main.c:10:5: error: expected ';' before 'return'\n")

    res = runner.invoke(app, ["translate", str(log_err)])
    assert res.exit_code == 0
    assert "Falta un punto y coma" in res.stdout

    # Empty log
    log_clean = tmp_path / "clean.log"
    log_clean.write_text("")
    res_clean = runner.invoke(app, ["translate", str(log_clean)])
    assert res_clean.exit_code == 0
    assert "No se encontraron errores" in res_clean.stdout


def test_cli_doctor():
    res = runner.invoke(app, ["doctor"])
    assert res.exit_code == 0
    assert "Toolchain de Compilación" in res.stdout


def test_compilar_archivos_no_existente(tmp_path):
    res = compilar_archivos([tmp_path / "inexistente.c"])
    assert res.exito is False


def test_cli_main_block(monkeypatch):
    monkeypatch.setattr("sys.argv", ["daedalus", "--version"])
    try:
        daedalus.cli.main()
    except SystemExit as e:
        assert e.code == 0
