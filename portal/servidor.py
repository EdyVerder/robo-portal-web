"""Sobe o portal de demonstração em http://127.0.0.1:<porta> numa thread (só desta máquina)."""
import functools
import http.server
import threading
from pathlib import Path

PASTA = Path(__file__).resolve().parent


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def subir(porta=8765):
    tratador = functools.partial(_Silencioso, directory=str(PASTA))
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", porta), tratador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor, f"http://127.0.0.1:{servidor.server_address[1]}/index.html"


if __name__ == "__main__":
    s, url = subir()
    print(f"portal de demonstração em {url} (Ctrl+C para sair)")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        s.shutdown()
