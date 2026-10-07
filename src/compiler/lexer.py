from typing import List

from .tokens import ErroLexico, Token


class AutomatoLexico:
    """Analisador léxico da linguagem dos robôs (Compiler Arena).

    Mantém a interface do analisador da Parte I (classe AutomatoLexico,
    método analisar, tokens com lexema/classificacao/valor/linha/coluna),
    trocando o vocabulário: robot, int, bool, if, else, while, true, false.
    """

    PALAVRAS_RESERVADAS = {"robot", "int", "bool", "if", "else", "while", "true", "false"}

    OPERADORES = {
        "+": "OPERADOR_ARITMETICO", "-": "OPERADOR_ARITMETICO",
        "*": "OPERADOR_ARITMETICO", "/": "OPERADOR_ARITMETICO",
        ">": "OPERADOR_RELACIONAL", "<": "OPERADOR_RELACIONAL",
        ">=": "OPERADOR_RELACIONAL", "<=": "OPERADOR_RELACIONAL",
        "==": "OPERADOR_RELACIONAL", "!=": "OPERADOR_RELACIONAL",
        "&&": "OPERADOR_LOGICO", "||": "OPERADOR_LOGICO", "!": "OPERADOR_LOGICO",
        "=": "ATRIBUICAO",
    }

    DELIMITADORES = {";", "(", ")", "{", "}", ",", "."}

    def __init__(self):
        self.tokens: List[Token] = []
        self.erros: List[ErroLexico] = []

    def analisar(self, codigo: str) -> List[Token]:
        """Tokeniza o código. Caracteres inválidos viram tokens ERRO e são
        registrados em self.erros; use verificar() para falhar na compilação."""
        self.tokens, self.erros = [], []
        pos, linha, coluna = 0, 1, 1
        n = len(codigo)

        while pos < n:
            c = codigo[pos]

            if c in " \t\r":
                pos += 1
                coluna += 1
            elif c == "\n":
                pos += 1
                linha += 1
                coluna = 1
            elif codigo.startswith("//", pos):
                while pos < n and codigo[pos] != "\n":
                    pos += 1
                    coluna += 1
            elif c.isalpha() or c == "_":
                fim = pos + 1
                while fim < n and (codigo[fim].isalnum() or codigo[fim] == "_"):
                    fim += 1
                lexema = codigo[pos:fim]
                classe = "PALAVRA_RESERVADA" if lexema in self.PALAVRAS_RESERVADAS else "IDENTIFICADOR"
                self._add(lexema, classe, lexema, linha, coluna)
                coluna += fim - pos
                pos = fim
            elif c.isdigit():
                fim = pos
                while fim < n and codigo[fim].isdigit():
                    fim += 1
                lexema = codigo[pos:fim]
                if fim < n and (codigo[fim].isalpha() or codigo[fim] == "_"):
                    # ex.: 12abc
                    while fim < n and (codigo[fim].isalnum() or codigo[fim] == "_"):
                        fim += 1
                    lexema = codigo[pos:fim]
                    self._erro(lexema, f"número malformado {lexema!r}", linha, coluna)
                else:
                    self._add(lexema, "NUMERO_INTEIRO", lexema, linha, coluna)
                coluna += fim - pos
                pos = fim
            else:
                duplo = codigo[pos:pos + 2]
                if duplo in self.OPERADORES:
                    self._add(duplo, self.OPERADORES[duplo], duplo, linha, coluna)
                    pos += 2
                    coluna += 2
                elif c in self.OPERADORES:
                    self._add(c, self.OPERADORES[c], c, linha, coluna)
                    pos += 1
                    coluna += 1
                elif c in self.DELIMITADORES:
                    self._add(c, "DELIMITADOR", c, linha, coluna)
                    pos += 1
                    coluna += 1
                else:
                    self._erro(c, f"caractere inválido {c!r}", linha, coluna)
                    pos += 1
                    coluna += 1
        return self.tokens

    def verificar(self) -> None:
        """Levanta o primeiro erro léxico, interrompendo a compilação."""
        if self.erros:
            raise self.erros[0]

    def _add(self, lexema, classe, valor, linha, coluna):
        self.tokens.append(Token(lexema, classe, valor, linha, coluna))

    def _erro(self, lexema, mensagem, linha, coluna):
        self.tokens.append(Token(lexema, "ERRO", lexema, linha, coluna))
        self.erros.append(ErroLexico(mensagem, linha, coluna))
