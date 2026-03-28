import os
import sys


def get_asset_path(rel_path: str) -> str:
    """Resolve caminho de asset tanto em desenvolvimento quanto em executável (PyInstaller).

    Retorna o caminho absoluto para `rel_path` relativo à pasta do pacote.
    """
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    else:
        base = os.path.dirname(__file__)
    return os.path.join(base, rel_path)

