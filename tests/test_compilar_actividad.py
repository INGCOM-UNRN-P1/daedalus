"""Lo que ripley evaluate necesita de daedalus para dejar su compilador interno (N-RIPLEY-03):
los flags de la actividad, compilar aislado en nostromo y el reintento sin sanitizers."""

import shutil
import subprocess
import sys
import types

import pytest

from daedalus.core import compiler
from daedalus.core.compiler import FLAGS_CATEDRA_DEFAULT, compilar_archivos

necesita_gcc = pytest.mark.skipif(not shutil.which("gcc"), reason="requiere gcc")


class _Proc:
    def __init__(self, returncode=0, stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, "", stderr


@pytest.fixture
def comandos(monkeypatch):
    vistos = []

    def run(cmd, **_k):
        vistos.append(cmd)
        return _Proc()

    monkeypatch.setattr(compiler.subprocess, "run", run)
    return vistos


def test_flags_reemplazan_a_los_de_catedra(tmp_path, comandos):
    (tmp_path / "a.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
    compilar_archivos([tmp_path / "a.c"], tmp_path / "a", flags=["-std=c99", "-O2"], flags_adicionales=["-DX"])
    cmd = comandos[0]
    assert cmd[1:4] == ["-std=c99", "-O2", "-DX"]
    assert not set(FLAGS_CATEDRA_DEFAULT) - {"-std=c99", "-O2"} & set(cmd)


def test_sin_flags_usa_los_de_catedra(tmp_path, comandos):
    (tmp_path / "a.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
    compilar_archivos([tmp_path / "a.c"], tmp_path / "a", flags_adicionales=["-DX"])
    assert comandos[0][1:len(FLAGS_CATEDRA_DEFAULT) + 2] == [*FLAGS_CATEDRA_DEFAULT, "-DX"]


def test_reintenta_sin_sanitizers_si_el_toolchain_no_los_trae(tmp_path, monkeypatch):
    (tmp_path / "a.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
    vistos = []

    def run(cmd, **_k):
        vistos.append(cmd)
        if any(o.startswith("-fsanitize=") for o in cmd):
            return _Proc(1, "ld: cannot find -lasan: No such file or directory")
        return _Proc()

    monkeypatch.setattr(compiler.subprocess, "run", run)
    res = compilar_archivos([tmp_path / "a.c"], tmp_path / "a", flags=["-fsanitize=address", "-g"],
                            reintentar_sin_sanitizers=True)
    assert res.exito and res.sin_sanitizers
    assert len(vistos) == 2 and "-fsanitize=address" not in vistos[1]
    assert res.to_dict()["sin_sanitizers"] is True


def test_aislar_sin_nostromo_falla_en_lugar_de_compilar_sin_aislar(tmp_path, monkeypatch, comandos):
    (tmp_path / "a.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "nostromo.core.sandbox", None)  # import → ImportError
    res = compilar_archivos([tmp_path / "a.c"], tmp_path / "a", aislar=True)
    assert not res.exito and res.aislado is False
    assert "nostromo" in res.stderr_crudo
    assert comandos == []


def test_aislar_monta_fuentes_includes_y_salida(tmp_path, monkeypatch):
    fuentes, inc, salida = tmp_path / "src", tmp_path / "include", tmp_path / "bin"
    for d in (fuentes, inc, salida):
        d.mkdir()
    (fuentes / "a.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
    llamadas = {}

    def falso(cmd, escribibles, legibles, directorio, timeout_segundos):
        llamadas.update(cmd=cmd, escribibles=escribibles, legibles=legibles)
        return types.SimpleNamespace(codigo_retorno=0, stdout="", stderr="", error_tipo=None, aislado=True)

    modulo = types.ModuleType("nostromo.core.sandbox")
    modulo.ejecutar_comando_aislado = falso
    monkeypatch.setitem(sys.modules, "nostromo.core.sandbox", modulo)
    res = compilar_archivos([fuentes / "a.c"], salida / "a", flags_adicionales=[f"-I{inc}"], aislar=True)
    assert res.exito and res.aislado is True and res.to_dict()["aislado"] is True
    assert llamadas["escribibles"] == [salida.resolve()]
    assert set(llamadas["legibles"]) == {fuentes.resolve(), inc.resolve()}


def _nostromo_con_comando_aislado():
    try:
        from nostromo.core.sandbox import ejecutar_comando_aislado  # noqa: F401
    except ImportError:
        return False
    return True


@necesita_gcc
@pytest.mark.skipif(not _nostromo_con_comando_aislado(), reason="requiere nostromo con ejecutar_comando_aislado")
def test_aislado_de_verdad_no_ve_la_solucion(tmp_path):
    secreto = tmp_path / "canon" / "s.c"
    secreto.parent.mkdir()
    secreto.write_text("int s(void){return 1;}\n", encoding="utf-8")
    entrega = tmp_path / "entrega"
    entrega.mkdir()
    (entrega / "a.c").write_text(f'#include "{secreto}"\nint main(void){{return s();}}\n', encoding="utf-8")
    res = compilar_archivos([entrega / "a.c"], entrega / "a", aislar=True)
    if res.aislado:
        assert not res.exito
    else:  # sin bwrap utilizable: compiló con límites y lo informa
        assert res.exito


def test_plugin_pasa_las_opciones_de_la_actividad(tmp_path, monkeypatch):
    from daedalus import ripley_plugin

    recibido = {}

    def falso(**kw):
        recibido.update(kw)
        return compiler.ResultadoCompilacion(exito=True, codigo_retorno=0, aislado=True)

    monkeypatch.setattr(ripley_plugin, "compilar_archivos", falso)
    (tmp_path / "a.c").write_text("", encoding="utf-8")
    salida = ripley_plugin.DaedalusPlugin().execute(tmp_path, {
        "flags": ["-std=c11"], "reemplazar_flags": True, "aislar": True, "timeout": 30,
        "reintentar_sin_sanitizers": True})
    assert recibido["flags"] == ["-std=c11"] and recibido["flags_adicionales"] is None
    assert recibido["aislar"] and recibido["reintentar_sin_sanitizers"] and recibido["timeout"] == 30
    assert salida["aislado"] is True


def test_timeout_aislado_se_informa_como_timeout(tmp_path, monkeypatch):
    (tmp_path / "a.c").write_text("", encoding="utf-8")
    modulo = types.ModuleType("nostromo.core.sandbox")
    modulo.ejecutar_comando_aislado = lambda *a, **k: types.SimpleNamespace(
        codigo_retorno=124, stdout="", stderr="", error_tipo="TIMEOUT", aislado=True)
    monkeypatch.setitem(sys.modules, "nostromo.core.sandbox", modulo)
    assert compilar_archivos([tmp_path / "a.c"], tmp_path / "a", aislar=True).codigo_retorno == 124
    assert subprocess  # el módulo real sigue disponible para el resto de la suite
