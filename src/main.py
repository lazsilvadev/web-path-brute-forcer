import flet as ft
import sys
import ctypes
from .ui import build_ui  # Certifique-se que a pasta 'ui' tem um __init__.py

# Garantir ícone agrupado corretamente na barra de tarefas do Windows
if sys.platform == "win32":
    my_app_id = "laz.recon.fuzzer.v1"
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)
    except Exception:
        pass

def main(page: ft.Page):
    # Configurações iniciais da página (opcional, mas recomendado)
    page.title = "LazRecon Fuzzer"
    page.theme_mode = ft.ThemeMode.DARK 
    
    # Chama a sua interface customizada
    build_ui(page)

# ESTA LINHA É ESSENCIAL:
if __name__ == "__main__":
   ft.app(target=main, assets_dir="assets")