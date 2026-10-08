from dataclasses import dataclass
from typing import Optional


@dataclass
class Token:
    lexema: str
    classificacao: str
    valor: str
    linha: int
    coluna: int


class ErroCompilacao(Exception):
    """Base de todos os erros de compilação (léxico, sintático, semântico...).

    O pipeline captura esta classe para montar o painel do compilador:
    `mensagem` é o motivo curto e `linha` diz onde o erro aconteceu.
    """

    def __init__(self, mensagem: str, linha: Optional[int] = None,
                 coluna: Optional[int] = None, texto: Optional[str] = None):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        super().__init__(texto or mensagem)


class ErroLexico(ErroCompilacao):
    def __init__(self, mensagem: str, linha: int, coluna: int):
        super().__init__(
            mensagem, linha, coluna,
            texto=f"Erro léxico na linha {linha}, coluna {coluna}: {mensagem}.",
        )