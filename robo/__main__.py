"""Demonstração: sobe o portal de mentira, enche a fila com clientes fictícios e processa tudo com Playwright.

Uso: python -m robo [--ver] [--instavel 0.15] [--video pasta]
As credenciais vêm de PORTAL_USUARIO e PORTAL_SENHA (os padrões só valem para o portal de demonstração).
"""
import argparse
import logging
import os
import random
from pathlib import Path

from playwright.sync_api import sync_playwright

from portal.servidor import subir

from . import fila
from .processar import processar

MODALIDADES = ["Aquisição de imóvel novo", "Aquisição de imóvel usado", "Construção em terreno próprio"]


def cpf_ficticio(rnd):
    """CPF com dígitos válidos, sempre começando em 000 (faixa usada só para teste)."""
    base = [0, 0, 0] + [rnd.randint(0, 9) for _ in range(6)]
    for n in (9, 10):
        s = sum(d * (n + 1 - i) for i, d in enumerate(base[:n]))
        base.append(s * 10 % 11 % 10)
    d = "".join(map(str, base))
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def clientes_ficticios(qtd=6, semente=11):
    rnd = random.Random(semente)
    lista = [{"nome": f"Cliente Demonstração {i:03d}", "cpf": cpf_ficticio(rnd),
              "nascimento": f"{rnd.randint(1970, 2002)}-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}",
              "renda": round(rnd.uniform(2800, 18000), 2), "modalidade": rnd.choice(MODALIDADES),
              "email": f"cliente{i:03d}@exemplo.com.br"} for i in range(1, qtd + 1)]
    if qtd > 3:
        lista[3]["cpf"] = "000.111.222-00"   # dígito errado de propósito: o robô manda para REVISAR
    return lista


def main():
    if os.name == "nt":
        os.system("")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ver", action="store_true", help="abre o navegador na tela (padrão: sem janela)")
    ap.add_argument("--instavel", type=float, default=0.25, help="chance de o portal falhar no envio")
    ap.add_argument("--video", help="grava a sessão em vídeo nesta pasta")
    ap.add_argument("--pasta", default="saida")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="\033[90m%(asctime)s\033[0m %(message)s", datefmt="%H:%M:%S")

    pasta = Path(args.pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "fila.db").unlink(missing_ok=True)
    con = fila.abrir(pasta / "fila.db")
    fila.incluir(con, clientes_ficticios())
    servidor, url = subir(0)
    try:
        with sync_playwright() as p:
            nav = p.chromium.launch(headless=not args.ver, slow_mo=120 if args.ver or args.video else 0)
            ctx = nav.new_context(viewport={"width": 1100, "height": 760}, locale="pt-BR",
                                  record_video_dir=args.video, record_video_size={"width": 1100, "height": 760})
            from .portal import PortalCadastro
            portal = PortalCadastro(ctx.new_page(), f"{url}?instavel={args.instavel}")
            resultado = processar(con, portal, os.environ.get("PORTAL_USUARIO", "demo.usuario"),
                                  os.environ.get("PORTAL_SENHA", "demo-2026"), evidencias=pasta / "evidencias")
            ctx.close()
            nav.close()
    finally:
        servidor.shutdown()
    print("\n\033[1mfila:\033[0m " + " · ".join(f"{k} {v}" for k, v in sorted(resultado.items())))


if __name__ == "__main__":
    main()
