"""Diagnósticos desde el SARIF de GCC (ola R2)."""

import json
import shutil
from pathlib import Path

import pytest

from daedalus.core import compiler
from daedalus.core.compiler import compilar_archivos, soporta_sarif
from daedalus.core.diagnostic_catalog import explicacion_por_flag
from daedalus.core.sarif import flag_de_regla, parsear_sarif_gcc
from daedalus.core.translator import traducir_desde_sarif

CAPTURA = (Path(__file__).parent / "fixtures" / "gcc16_main.sarif").read_text(encoding="utf-8")
con_sarif = pytest.mark.skipif(shutil.which("gcc") is None or not soporta_sarif("gcc"),
                               reason="hace falta gcc 13 o posterior")


def _documento(*resultados):
    return json.dumps({"version": "2.1.0", "runs": [{"results": list(resultados)}]})


def _resultado(regla, nivel="warning", texto="algo", uri="a.c", linea=3, columna=7, **extra):
    ubicacion = {"physicalLocation": {"artifactLocation": {"uri": uri},
                                      "region": {"startLine": linea, "startColumn": columna}}}
    return {"ruleId": regla, "level": nivel, "message": {"text": texto}, "locations": [ubicacion], **extra}


@pytest.mark.parametrize("regla, flag", [
    ("-Wuninitialized", "-Wuninitialized"),
    ("-Werror=return-type", "-Wreturn-type"),
    ("-Wformat=", "-Wformat"),
    ("error", None),
    ("fatal error", None),
    ("note", None),
    (None, None),
])
def test_flag_de_regla(regla, flag):
    assert flag_de_regla(regla) == flag


def test_captura_real_de_gcc_16():
    diagnosticos = parsear_sarif_gcc(CAPTURA)
    errores = {(d["regla"], d["linea"]) for d in diagnosticos if d["severidad"] == "error"}

    assert ("-Wimplicit-function-declaration", 6) in errores
    assert ("-Werror=return-type", 11) in errores
    assert ("error", 7) in errores  # `foo` sin declarar: un error sin flag
    assert ("error", 12) in errores  # falta el `;`
    # El error del .h se ubica en el .h, no en el .c que lo incluye.
    assert {d["archivo"] for d in diagnosticos if d["regla"] == "-Wint-conversion" and d["linea"] == 1} == {"/tp/lib.h"}


def test_las_llaves_vienen_escapadas():
    assert any(d["mensaje"] == "expected ',' or ';' before '}' token" for d in parsear_sarif_gcc(CAPTURA))


def test_la_nota_con_mensaje_sigue_a_su_diagnostico_y_la_cadena_de_includes_no():
    diagnosticos = parsear_sarif_gcc(CAPTURA)
    i = next(n for n, d in enumerate(diagnosticos) if d["regla"] == "-Wimplicit-function-declaration")

    assert diagnosticos[i + 1]["severidad"] == "note"
    assert "string.h" in diagnosticos[i + 1]["mensaje"]
    assert all(d["mensaje"] for d in diagnosticos)


def test_varios_documentos_con_texto_alrededor():
    salida = "gcc: warning: algo\n" + _documento(_resultado("-Wshadow")) + "\n" + _documento(_resultado("error", "error"))
    salida += "\n/usr/bin/ld: a.o: undefined reference to `g'\n"

    assert [d["regla"] for d in parsear_sarif_gcc(salida)] == ["-Wshadow", "error"]


@pytest.mark.parametrize("salida", ["", "a.c:1:1: error: nada", "{sin cerrar", '{"otra": "cosa"}'])
def test_sin_sarif_devuelve_none(salida):
    assert parsear_sarif_gcc(salida) is None


def test_json_con_otra_forma_devuelve_none():
    assert parsear_sarif_gcc('{"runs": [{"results": [{"ruleId": "x"}]}]}') is None


def test_diagnostico_sin_ubicacion():
    assert parsear_sarif_gcc(_documento({"ruleId": "-Wfoo", "level": "warning", "message": {"text": "x"}}))[0]["linea"] is None


@pytest.mark.parametrize("uri, ruta", [
    ("/home/ana/tp 1/a.c", "/home/ana/tp 1/a.c"),
    ("file:///home/ana/tp%201/a.c", "/home/ana/tp 1/a.c"),
    ("file:///C:/Users/ana/a.c", "C:/Users/ana/a.c"),
])
def test_rutas(uri, ruta):
    assert parsear_sarif_gcc(_documento(_resultado("error", uri=uri)))[0]["archivo"] == ruta


def test_la_traduccion_da_el_mismo_mensaje_que_el_texto_de_gcc():
    d = traducir_desde_sarif(_documento(_resultado("-Wimplicit-function-declaration", "error",
                                                   "implicit declaration of function ‘strlen’")))[0]

    assert d.mensaje_original == "implicit declaration of function 'strlen' [-Wimplicit-function-declaration]"
    assert "<string.h>" in d.sugerencia  # la regla que nombra la función gana sobre la del flag


def test_un_mensaje_reescrito_se_explica_por_su_flag():
    d = traducir_desde_sarif(_documento(_resultado("-Wuninitialized", texto="‘x’ tiene un texto que nadie conoce")))[0]

    assert d.titulo == explicacion_por_flag("-Wuninitialized")[0]
    assert d.flag == "-Wuninitialized"


@pytest.mark.parametrize("texto, titulo", [
    ("initialization of 'char *' from 'int' makes pointer from integer without a cast", "Entero a Puntero"),
    ("returning 'char *' from a function with return type 'int' makes integer from pointer without a cast", "Puntero a Entero"),
])
def test_el_catalogo_respeta_el_sentido_de_la_conversion(texto, titulo):
    d = traducir_desde_sarif(_documento(_resultado("-Wint-conversion", "error", texto)))[0]

    assert titulo in d.titulo


def test_un_flag_que_el_catalogo_no_tiene_no_inventa_explicacion():
    assert explicacion_por_flag("-Wnadie-lo-conoce") is None
    d = traducir_desde_sarif(_documento(_resultado("-Wnadie-lo-conoce", texto="raro")))[0]
    assert d.flag == "-Wnadie-lo-conoce"


def _programa(tmp_path, codigo, nombre="main.c"):
    fuente = tmp_path / nombre
    fuente.write_text(codigo, encoding="utf-8")
    return fuente


@con_sarif
def test_compilar_usa_sarif_y_deja_el_texto_para_los_demas(tmp_path):
    fuente = _programa(tmp_path, "int main(void) {\n    int x = \"a\";\n    return x;\n}\n")

    res = compilar_archivos([fuente], binario_salida=tmp_path / "prog")

    assert res.motor == "sarif"
    assert res.to_dict()["motor"] == "sarif"
    assert ": error: " in res.stderr_crudo or ": warning: " in res.stderr_crudo
    assert not res.stderr_crudo.lstrip().startswith("{")
    assert res.diagnosticos[0].archivo == str(fuente.resolve())
    assert res.diagnosticos[0].linea == 2


@con_sarif
def test_programa_limpio_sin_pasada_extra(tmp_path, monkeypatch):
    fuente = _programa(tmp_path, "int main(void) { return 0; }\n")
    monkeypatch.setattr(compiler, "_diagnosticos_sarif", lambda *a: pytest.fail("no hacía falta"))

    res = compilar_archivos([fuente], binario_salida=tmp_path / "prog")

    assert res.exito and res.motor == "texto" and res.diagnosticos == []


@con_sarif
def test_advertencia_del_optimizador(tmp_path):
    fuente = _programa(tmp_path, "#include <stdio.h>\nint main(void) {\n    int x;\n    printf(\"%d\", x);\n    return 0;\n}\n")

    res = compilar_archivos([fuente], binario_salida=tmp_path / "prog")

    assert res.exito and res.motor == "sarif"
    assert any(d.flag == "-Wuninitialized" for d in res.diagnosticos)


@con_sarif
def test_error_de_enlace_junto_con_advertencias_de_varias_fuentes(tmp_path):
    a = _programa(tmp_path, "void falta(void);\nint main(void) { int x; falta(); return 0; }\n", "a.c")
    b = _programa(tmp_path, "void otra(void) { int y; }\n", "b.c")

    res = compilar_archivos([a, b], binario_salida=tmp_path / "prog")

    assert res.motor == "sarif"
    assert [d.flag for d in res.diagnosticos if d.severidad == "warning"] == ["-Wunused-variable"] * 2
    assert {d.archivo for d in res.diagnosticos if d.linea} == {str(a.resolve()), str(b.resolve())}
    assert any("`falta`" in d.titulo and d.linea is None for d in res.diagnosticos)


@con_sarif
def test_no_quedan_archivos_de_la_pasada(tmp_path):
    fuente = _programa(tmp_path, "int main(void) { int x; return 0; }\n")

    compilar_archivos([fuente], binario_salida=tmp_path / "prog")

    # En Windows gcc agrega .exe al binario.
    assert sorted(p.stem for p in tmp_path.iterdir()) == ["main", "prog"]


@con_sarif
def test_sarif_y_texto_coinciden(tmp_path, monkeypatch):
    fuente = _programa(tmp_path, "#include <stdio.h>\nint f(void) { }\nint main(void) {\n    printf(\"%d %s\\n\", 1);\n"
                                 "    g(3);\n    char *p = 5;\n    return 0\n}\n")

    con = compilar_archivos([fuente], binario_salida=tmp_path / "prog")
    monkeypatch.setattr(compiler, "soporta_sarif", lambda cc: False)
    sin = compilar_archivos([fuente], binario_salida=tmp_path / "prog")

    assert (con.motor, sin.motor) == ("sarif", "texto")
    # La columna no se compara: el texto marca el foco (la `s` de `%s`) y SARIF el inicio del rango.
    resumen = lambda r: [(d.linea, d.severidad, d.mensaje_original, d.titulo) for d in r.diagnosticos]
    assert resumen(con) == resumen(sin)


def test_sin_soporte_se_queda_con_el_texto(tmp_path, monkeypatch):
    fuente = _programa(tmp_path, "int main(void) { return 0 }\n")
    monkeypatch.setattr(compiler, "soporta_sarif", lambda cc: False)

    res = compilar_archivos([fuente], binario_salida=tmp_path / "prog")

    assert res.motor == "texto" and res.diagnosticos


@pytest.mark.parametrize("devuelve", [None, []])
def test_si_la_pasada_no_sirve_vale_el_texto(tmp_path, monkeypatch, devuelve):
    fuente = _programa(tmp_path, "int main(void) { return 0 }\n")
    monkeypatch.setattr(compiler, "_diagnosticos_sarif", lambda *a: devuelve)

    res = compilar_archivos([fuente], binario_salida=tmp_path / "prog")

    assert res.motor == "texto" and res.diagnosticos


def test_compilador_inexistente_no_soporta_sarif():
    assert soporta_sarif("gcc-que-no-existe") is False
