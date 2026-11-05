"""El compilador habla en inglés aunque la terminal esté en español."""

import shutil

import pytest

from daedalus.core.compiler import compilar_archivos

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="hace falta gcc")


def test_el_error_de_enlace_se_traduce_con_el_locale_en_espanol(tmp_path, monkeypatch):
    monkeypatch.setenv("LC_ALL", "es_AR.UTF-8")
    monkeypatch.setenv("LANGUAGE", "es")
    fuente = tmp_path / "main.c"
    fuente.write_text("void g(void);\nint main(void) { g(); return 0; }\n", encoding="utf-8")

    res = compilar_archivos([fuente], binario_salida=tmp_path / "prog")

    assert not res.exito
    assert "referencia" not in res.stderr_crudo
    assert any("`g`" in d.titulo for d in res.diagnosticos)
