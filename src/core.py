"""Core de varredura do LazRecon.

Contém a função `run_scan` que executa a varredura de paths e chama callbacks
para notificar progresso, achados e término.
"""

import requests
import datetime
import os


def run_scan(
    target: str,
    wordlist: list,
    browser_headers: dict,
    stop_event,
    on_found,
    on_progress,
    on_finished,
    save_html_dir: str | None = None,
):
    """Executa a varredura.

    - target: URL base sem barra final
    - wordlist: lista de paths (strings)
    - browser_headers: headers para requests
    - stop_event: threading.Event para interrupção
    - on_found(status:int, full_url:str, res_text:str): callback para cada achado 200/403
    - on_progress(i:int, total:int): callback de progresso
    - on_finished(interrupted:bool): chamado ao final
    - save_html_dir: se fornecido, salva respostas HTML em pasta (criada se necessário)
    """
    total = len(wordlist)
    seen_urls = set()
    for i, path in enumerate(wordlist, 1):
        if stop_event.is_set():
            on_finished(True)
            return
        full_url = f"{target}/{path}"
        try:
            res = requests.get(
                full_url, timeout=3, allow_redirects=False, headers=browser_headers
            )
            if res.status_code in (200, 403):
                if full_url not in seen_urls:
                    # salvar HTML se solicitado
                    if save_html_dir:
                        try:
                            safe_name = path.strip("/").replace("/", "_") or "root"
                            fname = f"{res.status_code}_{safe_name}_{datetime.datetime.now().strftime('%H%M%S')}.html"
                            os.makedirs(save_html_dir, exist_ok=True)
                            with open(
                                os.path.join(save_html_dir, fname),
                                "w",
                                encoding="utf-8",
                            ) as fh:
                                fh.write(res.text)
                        except Exception:
                            pass
                    on_found(res.status_code, full_url, res.text)
                    seen_urls.add(full_url)
        except Exception:
            # ignora erros de requisição
            pass

        on_progress(i, total)

    on_finished(False)


"""Core de varredura do LazRecon.

Contém a função `run_scan` que executa a varredura de paths e chama callbacks
para notificar progresso, achados e término.
"""

