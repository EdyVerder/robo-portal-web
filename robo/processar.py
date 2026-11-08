"""O laço do robô, separado do navegador: recebe um portal (o de verdade ou um dublê de teste) e a fila."""
import logging
import re
import time
from pathlib import Path

from . import fila
from .portal import ErroDeNegocio, ErroTecnico

log = logging.getLogger("robo")


def mascarar_cpf(cpf):
    """CPF nunca vai inteiro para o log: 000.***.***-91."""
    d = re.sub(r"\D", "", cpf)
    return f"{d[:3]}.***.***-{d[-2:]}" if len(d) == 11 else "***"


def processar(con, portal, usuario, senha, evidencias=Path("saida/evidencias"), tentativas=3, espera_base=1.0):
    portal.entrar(usuario, senha)
    for p in fila.pendentes(con):
        quem = f"#{p['id']} {mascarar_cpf(p['cpf'])}"
        while True:
            try:
                protocolo = portal.cadastrar(p)
            except ErroDeNegocio as e:
                fila.revisar(con, p["id"], str(e))
                log.warning("%s REVISAR: %s", quem, e)
                break
            except ErroTecnico as e:
                arquivo = portal.evidencia(evidencias, f"processo_{p['id']}")
                if fila.falhou(con, p["id"], str(e), limite=tentativas):
                    n = con.execute("SELECT tentativas FROM processos WHERE id = ?", (p["id"],)).fetchone()[0]
                    log.info("%s portal instável (%s); nova tentativa em %.0f s", quem, e, espera_base * 2 ** (n - 1))
                    time.sleep(espera_base * 2 ** (n - 1))
                    continue
                log.error("%s ERRO depois de %d tentativas; evidência em %s", quem, tentativas, arquivo.name)
                break
            fila.concluir(con, p["id"], protocolo)
            log.info("%s CONCLUÍDO, protocolo %s", quem, protocolo)
            break
    return fila.resumo(con)
