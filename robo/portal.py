"""Page object do portal: tudo o que o robô sabe sobre a tela fica aqui (seletores, esperas e mensagens)."""
import datetime as dt


class ErroDeNegocio(Exception):
    """O portal recusou o dado (CPF inválido, campo faltando): tentar de novo não resolve."""


class ErroTecnico(Exception):
    """O portal falhou (indisponível, lento, tela inesperada): vale tentar de novo."""


RECUSAS = ("CPF inválido", "Preencha todos os campos", "Confirme a declaração")


class PortalCadastro:
    def __init__(self, pagina, url, tempo_limite_ms=15000):
        self.pg = pagina
        self.url = url
        self.pg.set_default_timeout(tempo_limite_ms)

    def entrar(self, usuario, senha):
        self.pg.goto(self.url)
        if self.pg.locator("#tela-cadastro").is_visible():
            return
        self.pg.fill("#usuario", usuario)
        self.pg.fill("#senha", senha)
        self.pg.click("#form-login button[type=submit]")
        self.pg.wait_for_selector("#tela-cadastro:not([hidden]), #erro-login:not([hidden])")
        if self.pg.locator("#erro-login").is_visible():
            raise ErroDeNegocio(self.pg.inner_text("#erro-login"))

    def cadastrar(self, cliente):
        """Preenche e envia o formulário; devolve o protocolo."""
        if self.pg.locator("#tela-protocolo").is_visible():
            self.pg.click("#novo")
        self.pg.wait_for_selector("#tela-cadastro:not([hidden])")
        self.pg.fill("#nome", cliente["nome"])
        self.pg.fill("#cpf", "")   # depois de uma recusa o campo ainda tem o CPF anterior; digitar por cima o estraga
        self.pg.locator("#cpf").press_sequentially(cliente["cpf"], delay=15)
        self.pg.fill("#nascimento", cliente["nascimento"])
        self.pg.fill("#renda", f'{cliente["renda"]:.2f}'.replace(".", ","))
        self.pg.select_option("#modalidade", label=cliente["modalidade"])
        self.pg.fill("#email", cliente["email"])
        self.pg.check("#aceite")
        self.pg.click("#enviar")
        self.pg.wait_for_selector("#tela-protocolo:not([hidden]), #erro-cadastro:not([hidden])")
        if self.pg.locator("#erro-cadastro").is_visible():
            mensagem = self.pg.inner_text("#erro-cadastro")
            if any(m in mensagem for m in RECUSAS):
                raise ErroDeNegocio(mensagem)
            raise ErroTecnico(mensagem)
        return self.pg.inner_text("#protocolo")

    def evidencia(self, pasta, nome):
        pasta.mkdir(parents=True, exist_ok=True)
        caminho = pasta / f"{dt.datetime.now():%Y%m%d_%H%M%S}_{nome}.png"
        self.pg.screenshot(path=str(caminho), full_page=True)
        return caminho
