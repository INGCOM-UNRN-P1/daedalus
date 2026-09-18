"""Regresión: el README debe documentar todos los comandos que la CLI registra.

Documentaba 4 de 12 (daedalus) y 3 de 11 (esper): el resto solo se descubría con `--help`.
"""

from pathlib import Path

from typer.main import get_command

from daedalus.cli import app

README = Path(__file__).resolve().parents[1] / "README.md"


def test_todos_los_comandos_estan_en_el_readme():
    texto = README.read_text(encoding="utf-8")
    comandos = sorted(get_command(app).commands)
    sin_documentar = [c for c in comandos if f"`{c}" not in texto and f"/ `{c}" not in texto]
    assert sin_documentar == [], f"comandos ausentes del README: {sin_documentar}"
