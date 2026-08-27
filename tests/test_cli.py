"""Tests de integración de la CLI de DAEDALUS."""

import json
from pathlib import Path
from typer.testing import CliRunner
from daedalus.cli import app

runner = CliRunner()


def test_cli_version():
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "DAEDALUS" in res.stdout


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
