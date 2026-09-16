"""Tests de integración de las funcionalidades migradas de ESPER a DAEDALUS."""

import json
from pathlib import Path
from typer.testing import CliRunner
from daedalus.cli import app
from daedalus.core.arch_check import check_arch_incompatibilities
from daedalus.core.diagnostic_catalog import list_catalog_entries, lookup_explanation
from daedalus.core.guide_generator import generate_resolution_guide
from daedalus.core.models import DiagnosticoCompilacion, ResultadoCompilacion
from daedalus.core.standards_db import get_standard_citation
from daedalus.core.suggest_flags import analyze_missing_flags
from daedalus.core.translator import parsear_stderr_compilador

runner = CliRunner()


def test_catalog_entries_and_citations():
    entries = list_catalog_entries()
    assert len(entries) >= 30
    assert any(e["flag"] == "-Wimplicit-function-declaration" for e in entries)

    cit = get_standard_citation("implicit-function-declaration")
    assert cit is not None
    assert "ISO/IEC 9899" in cit


def test_translator_enriches_with_catalog():
    stderr = "app.c:15:4: error: implicit declaration of function 'printf' [-Wimplicit-function-declaration]"
    diags = parsear_stderr_compilador(stderr)
    assert len(diags) == 1
    d = diags[0]
    assert d.flag == "-Wimplicit-function-declaration"
    assert d.cita_iso_c is not None
    assert "ISO/IEC 9899" in d.cita_iso_c
    d_dict = d.to_dict()
    assert "flag" in d_dict
    assert "cita_iso_c" in d_dict


def test_suggest_flags_math_and_posix():
    stderr = (
        "main.c:(.text+0x10): undefined reference to `sqrt'\n"
        "main.c:5:2: warning: implicit declaration of function 'strdup'\n"
    )
    suggs = analyze_missing_flags(stderr)
    flags = [s["flag"] for s in suggs]
    assert "-lm" in flags
    assert "-D_POSIX_C_SOURCE=200809L" in flags


def test_arch_check():
    log_err = "main.c:8:10: warning: cast from pointer to integer of different size [-Wpointer-to-int-cast]"
    findings = check_arch_incompatibilities(log_err)
    assert len(findings) == 1
    assert "uintptr_t" in findings[0]["suggestion"]


def test_guide_generator():
    diag = DiagnosticoCompilacion(
        archivo="test.c",
        linea=10,
        columna=5,
        severidad="error",
        mensaje_original="undefined reference to `sqrt'",
        titulo="Símbolo no encontrado",
        explicacion="Falta la librería matemática",
        sugerencia="Agregá -lm",
        flags_sugeridos=["-lm"],
    )
    res = ResultadoCompilacion(exito=False, codigo_retorno=1, diagnosticos=[diag])
    guide = generate_resolution_guide(res)
    assert "# Guía Didáctica" in guide
    assert "Símbolo no encontrado" in guide
    assert "-lm" in guide


def test_cli_catalog():
    res = runner.invoke(app, ["catalog", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert len(data) >= 30


def test_cli_check_arch(tmp_path):
    log = tmp_path / "build.log"
    log.write_text("test.c:1: warning: cast from pointer to integer of different size [-Wpointer-to-int-cast]")
    res = runner.invoke(app, ["check-arch", str(log), "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert len(data) == 1


def test_cli_suggest_flags(tmp_path):
    log = tmp_path / "build.log"
    log.write_text("test.c:(.text+0x5): undefined reference to `sin'")
    res = runner.invoke(app, ["suggest-flags", str(log), "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert any(item["flag"] == "-lm" for item in data)
