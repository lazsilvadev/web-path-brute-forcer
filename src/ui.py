import flet as ft
import threading
import webbrowser
import os
import datetime
import re
from urllib.parse import urlparse
from . import core, report
from .resources import get_asset_path
from .wordlist import DEFAULT_WORDLIST, load_wordlist


# Função que monta a interface e registra callbacks
def build_ui(page: ft.Page):
    page.title = "LazRecon v1.1 - Web Path Reconnaissance Tool"
    page.theme_mode = ft.ThemeMode.DARK

    # Definir tamanho inicial e travar tamanho (não redimensionável)
    page.window.width = 700  # Largura fixa
    page.window.height = 880  # Altura fixa
    page.window.resizable = False  # Trava o tamanho (impede esticar)
    page.window.maximizable = False  # Desativa o botão de maximizar

    if hasattr(page, "window_center"):
        try:
            page.window_center()
        except Exception:
            pass

    page.add(ft.Text(""))
    page.window_resizable = False
    try:
        page.window_maximizable = False
    except Exception:
        pass

    page.window_icon = "lazrecon.png"
    header_image_src = "/lazrecon.png"

    icon_path = get_asset_path("icon.ico")
    for _attr in ("window_icon", "app_icon", "icon"):
        try:
            if hasattr(page, _attr):
                setattr(page, _attr, icon_path)
        except Exception:
            pass

    current_wordlist = DEFAULT_WORDLIST.copy()
    found_results = []
    collected_results = {}
    stop_event = threading.Event()

    browser_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
    }

    def open_link(e, link_url):
        webbrowser.open(link_url)

    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            try:
                new_list = load_wordlist(file_path)
                current_wordlist.clear()
                current_wordlist.extend(new_list)

                wordlist_status.value = (
                    f"✅ Wordlist carregada: {len(current_wordlist)} itens"
                )
                wordlist_status.color = ft.Colors.GREEN_400
            except Exception as ex:
                wordlist_status.value = f"❌ Erro ao ler arquivo: {ex}"
                wordlist_status.color = ft.Colors.RED_400
            page.update()

    def generate_pdf_report(e):
        try:
            groups = (
                collected_results
                if len(collected_results) > 0
                else {url_input.value: found_results}
            )
            exports_dir = os.path.abspath("exports")
            os.makedirs(exports_dir, exist_ok=True)
            out_path = report.save_pdf(groups, exports_dir)
            try:
                os.startfile(out_path)
            except Exception:
                webbrowser.open("file://" + out_path)
            page.snack_bar = ft.SnackBar(ft.Text(f"PDF gerado: {out_path}"))
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            print(f"Erro ao gerar PDF: {ex}")

    def restore_default_wordlist(e):
        progress_refresh.visible = True
        btn_reset_wordlist.disabled = True
        page.update()

        def do_restore():
            import time

            time.sleep(0.6)
            current_wordlist.clear()
            current_wordlist.extend(DEFAULT_WORDLIST)
            wordlist_status.value = (
                f"🔁 Wordlist padrão restaurada: {len(current_wordlist)} itens"
            )
            wordlist_status.color = ft.Colors.GREY_500
            progress_refresh.visible = False
            btn_reset_wordlist.disabled = False
            page.update()

        threading.Thread(target=do_restore, daemon=True).start()

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    url_input = ft.TextField(
        label="URL Alvo",
        hint_text="http://exemplo.com/",
        expand=True,
        on_submit=lambda _: start_scan(None),
    )

    wordlist_status = ft.Text(
        "Usando wordlist padrão", color=ft.Colors.GREY_500, size=12
    )

    btn_file = ft.IconButton(
        icon=ft.Icons.FILE_OPEN,
        tooltip="Carregar Wordlist (.txt)",
        on_click=lambda _: file_picker.pick_files(
            allow_multiple=False, allowed_extensions=["txt"]
        ),
    )

    btn_reset_wordlist = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="Restaurar wordlist padrão",
        on_click=restore_default_wordlist,
    )

    progress_refresh = ft.ProgressRing(visible=False, width=20, height=20)

    results_list = ft.ListView(expand=True, spacing=10, padding=10)
    progress_bar = ft.ProgressBar(width=None, color=ft.Colors.BLUE, visible=False)
    status_text = ft.Text("Pronto para iniciar", color=ft.Colors.GREY_400)
    counter_text = ft.Text("0/0", color=ft.Colors.BLUE_200, weight=ft.FontWeight.BOLD)

    def stop_scan(e):
        stop_event.set()
        status_text.value = "Parando..."
        page.update()

    def start_scan(e):
        target = url_input.value.strip().rstrip("/")
        url_input.error_text = None
        if not target or not target.startswith("http"):
            url_input.error_text = "Insira uma URL válida."
            page.update()
            return
        current_wordlist[:] = list(dict.fromkeys(current_wordlist))
        found_results.clear()

        parsed = urlparse(target)
        if parsed.hostname:
            target_host = parsed.hostname
        else:
            target_host = target.split("://")[-1].split("/")[0].split(":")[0]
        target_host = re.sub(r"[^0-9A-Za-z._-]", "_", target_host)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_folder = os.path.join("findigns", f"{target_host}_{ts}", "html")
        os.makedirs(target_folder, exist_ok=True)

        results_list.controls.clear()
        progress_bar.visible = True
        stop_event.clear()
        status_text.value = "Buscando..."
        counter_text.value = f"0/{len(current_wordlist)}"
        btn_scan.disabled = True
        btn_stop.disabled = False
        page.update()

        def _on_progress(i, total):
            counter_text.value = f"{i}/{total}"
            page.update()

        def _on_found(status, full_url, res_text):
            if status == 200:
                results_list.controls.insert(
                    0,
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN),
                        title=ft.Text(
                            f"/{full_url.split('/', 3)[-1]}", weight=ft.FontWeight.BOLD
                        ),
                        subtitle=ft.Row(
                            [
                                ft.Text("Status 200", color=ft.Colors.GREEN_100),
                                ft.TextButton(
                                    content=ft.Text("Abrir"),
                                    on_click=lambda e, url=full_url: open_link(e, url),
                                ),
                            ],
                            spacing=12,
                        ),
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREEN),
                    ),
                )
            else:
                results_list.controls.insert(
                    0,
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.SECURITY, color=ft.Colors.ORANGE),
                        title=ft.Text(
                            f"PROTEGIDO: {full_url.split('/', 3)[-1]}",
                            weight=ft.FontWeight.BOLD,
                        ),
                        subtitle=ft.Row(
                            [
                                ft.Text(f"Status {status}", color=ft.Colors.ORANGE_100),
                                ft.TextButton(
                                    content=ft.Text("Abrir"),
                                    on_click=lambda e, url=full_url: open_link(e, url),
                                ),
                            ],
                            spacing=12,
                        ),
                    ),
                )

            found_results.append({"status": status, "url": full_url})
            page.update()

        def _on_finished(interrupted):
            if interrupted:
                status_text.value = "Busca interrompida pelo usuário"
            else:
                if len(results_list.controls) == 0:
                    results_list.controls.append(
                        ft.ListTile(
                            title=ft.Text("Nada encontrado", color=ft.Colors.GREY_500)
                        )
                    )
                    status_text.value = "Busca finalizada!"
                else:
                    status_text.value = "Busca finalizada!"

            if len(found_results) > 0:
                collected_results.setdefault(target, [])
                for r in found_results:
                    if not any(
                        x.get("url") == r.get("url") for x in collected_results[target]
                    ):
                        collected_results[target].append(r)

            any_collected = (
                any(len(v) > 0 for v in collected_results.values())
                if len(collected_results) > 0
                else False
            )
            btn_pdf.visible = (len(found_results) > 0) or any_collected
            progress_bar.visible = False
            btn_scan.disabled = False
            btn_stop.disabled = True
            page.update()

        threading.Thread(
            target=lambda: core.run_scan(
                target,
                current_wordlist,
                browser_headers,
                stop_event,
                _on_found,
                _on_progress,
                _on_finished,
                save_html_dir=target_folder,
            ),
            daemon=True,
        ).start()

    btn_scan = ft.ElevatedButton(
        "Iniciar Scan", icon=ft.Icons.SEARCH, on_click=start_scan
    )

    btn_stop = ft.ElevatedButton(
        "Parar", icon=ft.Icons.STOP, on_click=stop_scan, disabled=True
    )

    btn_pdf = ft.ElevatedButton(
        "Gerar Relatório",
        icon=ft.Icons.PICTURE_AS_PDF,
        on_click=generate_pdf_report,
        visible=False,
    )

    page.add(
        ft.Row(
            [
                ft.Image(
                    src=header_image_src, width=36, height=36, fit=ft.ImageFit.CONTAIN
                ),
                ft.Text("LazRecon", size=25, weight="bold"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        ft.Divider(),
        ft.Row(
            [
                url_input,
                btn_file,
                btn_reset_wordlist,
                progress_refresh,
                btn_scan,
                btn_stop,
            ]
        ),
        ft.Row([wordlist_status], alignment=ft.MainAxisAlignment.START),
        progress_bar,
        ft.Row(
            [status_text, counter_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        ft.Container(
            content=results_list,
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_700),
            border_radius=10,
            bgcolor=ft.Colors.BLACK12,
        ),
        ft.Row([btn_pdf], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row(
            [
                ft.Row(
                    controls=[
                        ft.Text(
                            "⚠️ Use com responsabilidade em sistemas autorizados.",
                            size=11,
                            color=ft.Colors.BLUE_GREY_200,
                        ),
                        ft.TextButton(
                            content=ft.Text(
                                "Saiba Mais © 2026",
                                size=11,
                                color=ft.Colors.BLUE_GREY_200,
                            ),
                            on_click=lambda _: page.launch_url(
                                "https://github.com/lazsilvadev/lazrecon"
                            ),
                            style=ft.ButtonStyle(padding=0),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        ),
    )

