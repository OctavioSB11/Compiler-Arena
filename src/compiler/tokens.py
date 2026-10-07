from dataclasses import dataclass


@dataclass
class Token:
    lexema: str
    classificacao: str
    valor: str
    linha: int
    coluna: int


class ErroLexico(Exception):
    def __init__(self, mensagem: str, linha: int, coluna: int):
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        super().__init__(f"Erro léxico na linha {linha}, coluna {coluna}: {mensagem}.")
