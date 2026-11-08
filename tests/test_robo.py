"""Testes sem navegador: o portal é trocado por um dublê que responde do jeito que cada caso precisa."""
import random
import re
from pathlib import Path

from robo import fila
from robo.__main__ import clientes_ficticios, cpf_ficticio
from robo.portal import ErroDeNegocio, ErroTecnico
from robo.processar import mascarar_cpf, processar


class PortalDuble:
    def __init__(self, roteiro):
        self.roteiro = roteiro      # nome do cliente -> lista de respostas, uma por tentativa
        self.logado = False
        self.chamadas = []

    def entrar(self, usuario, senha):
        self.logado = True

    def cadastrar(self, cliente):
        assert self.logado
        self.chamadas.append(cliente["nome"])
        resposta = self.roteiro.get(cliente["nome"], ["PC-1"]).pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    def evidencia(self, pasta, nome):
        return Path(pasta) / f"{nome}.png"


def fila_com(tmp_path, nomes):
    con = fila.abrir(tmp_path / "fila.db")
    base = clientes_ficticios(len(nomes))
    fila.incluir(con, [dict(c, nome=n) for c, n in zip(base, nomes)])
    return con


def test_cpf_ficticio_comeca_em_000_e_tem_digito_valido():
    rnd = random.Random(1)
    for _ in range(50):
        cpf = cpf_ficticio(rnd)
        assert re.fullmatch(r"000\.\d{3}\.\d{3}-\d{2}", cpf)


def test_mascara_nao_deixa_cpf_inteiro():
    assert mascarar_cpf("000.123.456-78") == "000.***.***-78"
    assert mascarar_cpf("bobagem") == "***"


def test_fluxo_feliz(tmp_path):
    con = fila_com(tmp_path, ["A", "B"])
    resumo = processar(con, PortalDuble({}), "u", "s", evidencias=tmp_path, espera_base=0)
    assert resumo == {fila.CONCLUIDO: 2}


def test_erro_de_negocio_vai_para_revisar_sem_nova_tentativa(tmp_path):
    con = fila_com(tmp_path, ["A"])
    portal = PortalDuble({"A": [ErroDeNegocio("CPF inválido.")]})
    assert processar(con, portal, "u", "s", evidencias=tmp_path, espera_base=0) == {fila.REVISAR: 1}
    assert portal.chamadas == ["A"]


def test_portal_instavel_tenta_de_novo_e_conclui(tmp_path):
    con = fila_com(tmp_path, ["A"])
    portal = PortalDuble({"A": [ErroTecnico("indisponível"), ErroTecnico("indisponível"), "PC-9"]})
    assert processar(con, portal, "u", "s", evidencias=tmp_path, espera_base=0) == {fila.CONCLUIDO: 1}
    linha = con.execute("SELECT protocolo, tentativas FROM processos").fetchone()
    assert tuple(linha) == ("PC-9", 2)


class PaginaDuble:
    """Imita só o que o page object usa; o campo de CPF acumula o que for digitado, como no navegador."""

    def __init__(self):
        self.campos = {"#cpf": "000.111.222-00"}   # sobra de uma recusa anterior
        self.visiveis = {"#tela-cadastro"}

    def set_default_timeout(self, ms):
        pass

    def fill(self, seletor, valor):
        self.campos[seletor] = valor

    def locator(self, seletor):
        pagina = self

        class _L:
            def press_sequentially(self, texto, delay=0):
                pagina.campos[seletor] = pagina.campos.get(seletor, "") + texto

            def is_visible(self):
                return seletor in pagina.visiveis
        return _L()

    def select_option(self, seletor, label):
        self.campos[seletor] = label

    def check(self, seletor):
        self.campos[seletor] = True

    def click(self, seletor):
        if seletor == "#enviar":
            self.visiveis = {"#tela-protocolo"}

    def wait_for_selector(self, seletor):
        pass

    def inner_text(self, seletor):
        return "PC-2026-000001"


def test_page_object_limpa_o_cpf_antes_de_digitar():
    from robo.portal import PortalCadastro
    pg = PaginaDuble()
    cliente = clientes_ficticios(1)[0]
    assert PortalCadastro(pg, "http://x").cadastrar(cliente) == "PC-2026-000001"
    assert pg.campos["#cpf"] == cliente["cpf"]


def test_passou_do_limite_vai_para_erro(tmp_path):
    con = fila_com(tmp_path, ["A", "B"])
    portal = PortalDuble({"A": [ErroTecnico("fora do ar")] * 3})
    assert processar(con, portal, "u", "s", evidencias=tmp_path, espera_base=0) == {fila.ERRO: 1, fila.CONCLUIDO: 1}
