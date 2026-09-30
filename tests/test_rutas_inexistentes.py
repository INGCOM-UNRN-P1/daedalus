"""Un archivo que no existe es un error de uso, no un resultado limpio (N-ECO-18).

`daedalus check-deps no_existe.c` respondía «Grafo de inclusiones limpio (0 módulos analizados)»,
`compile-commands` generaba un compile_commands.json con un archivo inexistente y `report` salía
con 0; todos con código 0.
"""

import pytest
from typer.testing import CliRunner

from daedalus.cli import app

runner = CliRunner()


@pytest.mark.parametrize("comando", ["compile", "report", "preprocess", "compile-commands", "expand-macro",
                                     "suggest-flags", "check-standards", "check-deps"])
def test_un_archivo_que_no_existe_es_un_error_de_uso(comando, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # el código anterior escribía compile_commands.json en el directorio actual
    res = runner.invoke(app, [comando, "no_existe.c"], env={"COLUMNS": "200"})
    assert res.exit_code == 2, res.output
    assert "no_existe.c" in res.output
    assert not (tmp_path / "compile_commands.json").exists()
