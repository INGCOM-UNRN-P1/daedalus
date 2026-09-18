"""Regresión de DAEDALUS-D0301: traducir la salida real de GCC moderno.

GCC y Clang en locale UTF-8 citan identificadores con comillas tipográficas
(‘foo’). Las reglas estaban escritas con apóstrofos ASCII, así que los
diagnósticos más frecuentes caían al fallback genérico y el alumno recibía el
mensaje crudo en inglés.
"""

import pytest

from daedalus.core.translator import (
    normalizar_comillas,
    traducir_linea_diagnostico_completo,
)

GENERICO = "Diagnóstico del compilador"


@pytest.mark.parametrize(
    "mensaje, fragmento_esperado",
    [
        ("implicit declaration of function ‘foo’ [-Wimplicit-function-declaration]", "prototipo"),
        ("‘x’ undeclared (first use in this function)", "no declarado"),
        ("conflicting types for ‘f’", "contradictorios"),
        (
            "assignment to ‘int *’ from incompatible pointer type ‘char *’",
            "incompatibles",
        ),
    ],
)
def test_diagnosticos_con_comillas_tipograficas_se_traducen(mensaje, fragmento_esperado):
    titulo = traducir_linea_diagnostico_completo(mensaje)[0]
    assert titulo != GENERICO, f"cayó al fallback genérico: {mensaje}"
    assert fragmento_esperado in titulo.lower()


def test_el_identificador_citado_se_extrae(mensaje="implicit declaration of function ‘procesar’"):
    titulo = traducir_linea_diagnostico_completo(mensaje)[0]
    assert "procesar" in titulo


def test_la_forma_ascii_sigue_funcionando():
    """No se rompe la salida de compiladores en locale C."""
    titulo = traducir_linea_diagnostico_completo("implicit declaration of function 'foo'")[0]
    assert titulo != GENERICO


def test_el_backtick_del_linker_se_respeta():
    """`ld` sigue usando `nombre' y no debe verse afectado."""
    titulo = traducir_linea_diagnostico_completo("undefined reference to `falta'")[0]
    assert "linker" in titulo.lower()


def test_normalizar_no_toca_el_resto_del_mensaje():
    assert normalizar_comillas("dice ‘hola’ y nada más") == "dice 'hola' y nada más"


def test_no_regresion_contra_gcc_real(tmp_path):
    """Traduce la salida real del GCC del entorno, no un stderr sintético.

    Los tests del traductor usaban stderr escrito a mano con comillas ASCII,
    que es justamente lo que enmascaraba DAEDALUS-D0301: contra el GCC
    instalado (que cita con ‘...’) las reglas no matcheaban.
    """
    import shutil
    import subprocess

    if not shutil.which("gcc"):
        pytest.skip("requiere gcc en el entorno")

    fuente = tmp_path / "roto.c"
    fuente.write_text("int main(void){ foo(); return 0; }\n", encoding="utf-8")
    proc = subprocess.run(
        ["gcc", "-std=c11", "-Wall", "-Wextra", "-c", str(fuente), "-o", "/dev/null"],
        capture_output=True,
        text=True,
    )

    lineas = [l for l in proc.stderr.splitlines() if "implicit declaration" in l]
    assert lineas, f"el gcc del entorno no emitió el diagnóstico esperado: {proc.stderr[:200]}"

    titulo = traducir_linea_diagnostico_completo(lineas[0])[0]
    assert titulo != GENERICO, f"no se tradujo la salida real de gcc: {lineas[0]}"
    assert "foo" in titulo
