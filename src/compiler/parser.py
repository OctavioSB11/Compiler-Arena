from typing import List, Optional

from .ast_nodes import NoAST
from .tokens import ErroCompilacao, Token


class ErroSintatico(ErroCompilacao):
    """Erro de sintaxe com posição e expectativa."""

    def __init__(self, mensagem: str, token: Optional[Token] = None,
                 linha: Optional[int] = None):
        self.token = token
        if token is not None:
            super().__init__(
                mensagem, token.linha, token.coluna,
                texto=(f"Erro sintático na linha {token.linha}, coluna {token.coluna}: "
                       f"{mensagem}. Encontrado {token.classificacao} ({token.lexema!r})."),
            )
        else:
            super().__init__(mensagem, linha, texto=f"Erro sintático: {mensagem}.")


class AnalisadorSintatico:
    """Parser descendente recursivo da linguagem dos robôs.

    programa    -> 'robot' IDENT bloco
    bloco       -> '{' comando* '}'
    comando     -> declaracao | atribuicao | condicional | enquanto | chamada ';'
    declaracao  -> ('int'|'bool') IDENT ('=' expressao)? ';'
    atribuicao  -> IDENT '=' expressao ';'
    condicional -> 'if' expressao bloco ('else' (bloco | condicional))?
    enquanto    -> 'while' expressao bloco
    chamada     -> IDENT '(' (expressao (',' expressao)*)? ')'

    expressao   -> ou
    ou          -> e ('||' e)*
    e           -> relacional ('&&' relacional)*
    relacional  -> aritmetica (('>'|'<'|'>='|'<='|'=='|'!=') aritmetica)?
    aritmetica  -> termo (('+'|'-') termo)*
    termo       -> unario (('*'|'/') unario)*
    unario      -> ('-'|'!') unario | primario
    primario    -> NUMERO | 'true' | 'false' | chamada
                 | IDENT ('.' IDENT)? | '(' expressao ')'

    Parênteses em torno da condição de if/while são opcionais (o exemplo do
    enunciado usa `while enemy.visible {`).
    """

    OPERADORES_RELACIONAIS = {">", "<", ">=", "<=", "==", "!="}

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.posicao = 0

    @property
    def atual(self) -> Optional[Token]:
        return self.tokens[self.posicao] if self.posicao < len(self.tokens) else None

    def _e(self, lexema: str) -> bool:
        t = self.atual
        return t is not None and t.lexema == lexema and t.classificacao != "IDENTIFICADOR"

    def analisar(self) -> NoAST:
        erro = next((t for t in self.tokens if t.classificacao == "ERRO"), None)
        if erro is not None:
            raise ErroSintatico("token inválido produzido pelo analisador léxico", erro)
        raiz = self.programa()
        if self.atual is not None:
            self.erro("fim do arquivo")
        return raiz

    def erro(self, esperado: str, token: Optional[Token] = None):
        token = token or self.atual
        if token is None:
            if self.tokens:
                ultimo = self.tokens[-1]
                raise ErroSintatico(
                    f"fim do arquivo encontrado depois da linha {ultimo.linha}; esperado {esperado}",
                    linha=ultimo.linha)
            raise ErroSintatico(f"arquivo vazio; esperado {esperado}")
        raise ErroSintatico(f"esperado {esperado}", token)

    def consumir(self, lexema: Optional[str] = None, classificacao: Optional[str] = None,
                 esperado: Optional[str] = None) -> Token:
        t = self.atual
        if t is None:
            self.erro(esperado or lexema or classificacao)
        if lexema is not None and (t.lexema != lexema or t.classificacao == "IDENTIFICADOR"):
            self.erro(esperado or repr(lexema), t)
        if classificacao is not None and t.classificacao != classificacao:
            self.erro(esperado or classificacao, t)
        self.posicao += 1
        return t

    def aceitar(self, lexema: str) -> Optional[Token]:
        return self.consumir(lexema=lexema) if self._e(lexema) else None

    # ---------------- estrutura ----------------

    def programa(self) -> NoAST:
        inicio = self.consumir(lexema="robot", esperado="'robot'")
        nome = self.consumir(classificacao="IDENTIFICADOR", esperado="o nome do robô")
        return NoAST("Robo", nome.lexema, [self.bloco()], inicio.linha, inicio.coluna)

    def bloco(self) -> NoAST:
        abre = self.consumir(lexema="{", esperado="'{'")
        comandos = []
        while self.atual is not None and not self._e("}"):
            comandos.append(self.comando())
        self.consumir(lexema="}", esperado="'}'")
        return NoAST("Bloco", filhos=comandos, linha=abre.linha, coluna=abre.coluna)

    def comando(self) -> NoAST:
        t = self.atual
        if t is None:
            self.erro("um comando")
        if t.lexema in {"int", "bool"} and t.classificacao == "PALAVRA_RESERVADA":
            return self.declaracao()
        if self._e("if"):
            return self.condicional()
        if self._e("while"):
            return self.enquanto()
        if t.classificacao == "IDENTIFICADOR":
            proximo = self.tokens[self.posicao + 1] if self.posicao + 1 < len(self.tokens) else None
            if proximo is not None and proximo.lexema == "(":
                no = self.chamada()
                self.consumir(lexema=";", esperado="';'")
                return no
            return self.atribuicao()
        self.erro("declaração, atribuição, chamada, 'if' ou 'while'", t)

    def declaracao(self) -> NoAST:
        tipo = self.consumir()
        nome = self.consumir(classificacao="IDENTIFICADOR", esperado="um identificador")
        no = NoAST("Declaracao", tipo.lexema, linha=nome.linha, coluna=nome.coluna)
        no.adicionar(NoAST("Identificador", nome.lexema, linha=nome.linha, coluna=nome.coluna))
        if self.aceitar("="):
            no.adicionar(self.expressao())
        self.consumir(lexema=";", esperado="';'")
        return no

    def atribuicao(self) -> NoAST:
        nome = self.consumir(classificacao="IDENTIFICADOR", esperado="um identificador")
        self.consumir(lexema="=", esperado="'='")
        valor = self.expressao()
        self.consumir(lexema=";", esperado="';'")
        return NoAST("Atribuicao", filhos=[
            NoAST("Identificador", nome.lexema, linha=nome.linha, coluna=nome.coluna), valor
        ], linha=nome.linha, coluna=nome.coluna)

    def condicional(self) -> NoAST:
        inicio = self.consumir(lexema="if")
        filhos = [self.expressao(), self.bloco()]
        if self.aceitar("else"):
            filhos.append(self.condicional() if self._e("if") else self.bloco())
        return NoAST("Condicional", filhos=filhos, linha=inicio.linha, coluna=inicio.coluna)

    def enquanto(self) -> NoAST:
        inicio = self.consumir(lexema="while")
        return NoAST("Enquanto", filhos=[self.expressao(), self.bloco()],
                     linha=inicio.linha, coluna=inicio.coluna)

    def chamada(self) -> NoAST:
        nome = self.consumir(classificacao="IDENTIFICADOR", esperado="um identificador")
        self.consumir(lexema="(", esperado="'('")
        args = []
        if not self._e(")"):
            args.append(self.expressao())
            while self.aceitar(","):
                args.append(self.expressao())
        self.consumir(lexema=")", esperado="')'")
        return NoAST("Chamada", nome.lexema, args, nome.linha, nome.coluna)

    # ---------------- expressões ----------------

    def expressao(self) -> NoAST:
        return self._binaria_ou()

    def _op(self, operador: str, filhos: List[NoAST], token: Token) -> NoAST:
        return NoAST("Operacao", operador, filhos, token.linha, token.coluna)

    def _binaria_ou(self) -> NoAST:
        esq = self._binaria_e()
        while self._e("||"):
            op = self.consumir()
            esq = self._op(op.lexema, [esq, self._binaria_e()], op)
        return esq

    def _binaria_e(self) -> NoAST:
        esq = self._relacional()
        while self._e("&&"):
            op = self.consumir()
            esq = self._op(op.lexema, [esq, self._relacional()], op)
        return esq

    def _relacional(self) -> NoAST:
        esq = self._aritmetica()
        if self.atual is not None and self.atual.lexema in self.OPERADORES_RELACIONAIS:
            op = self.consumir()
            esq = self._op(op.lexema, [esq, self._aritmetica()], op)
        return esq

    def _aritmetica(self) -> NoAST:
        esq = self._termo()
        while self.atual is not None and self.atual.lexema in {"+", "-"}:
            op = self.consumir()
            esq = self._op(op.lexema, [esq, self._termo()], op)
        return esq

    def _termo(self) -> NoAST:
        esq = self._unario()
        while self.atual is not None and self.atual.lexema in {"*", "/"}:
            op = self.consumir()
            esq = self._op(op.lexema, [esq, self._unario()], op)
        return esq

    def _unario(self) -> NoAST:
        if self.atual is not None and self.atual.lexema in {"-", "!"}:
            op = self.consumir()
            return self._op(op.lexema + "unario", [self._unario()], op)
        return self._primario()

    def _primario(self) -> NoAST:
        t = self.atual
        if t is None:
            self.erro("número, true, false, identificador ou '('")
        if t.classificacao == "NUMERO_INTEIRO":
            self.posicao += 1
            return NoAST("Numero", t.valor, linha=t.linha, coluna=t.coluna)
        if t.lexema in {"true", "false"} and t.classificacao == "PALAVRA_RESERVADA":
            self.posicao += 1
            return NoAST("Booleano", t.lexema, linha=t.linha, coluna=t.coluna)
        if t.classificacao == "IDENTIFICADOR":
            proximo = self.tokens[self.posicao + 1] if self.posicao + 1 < len(self.tokens) else None
            if proximo is not None and proximo.lexema == "(":
                return self.chamada()
            self.posicao += 1
            if self._e("."):
                self.consumir()
                campo = self.consumir(classificacao="IDENTIFICADOR", esperado="nome do campo (ex.: distance)")
                return NoAST("Acesso", f"{t.lexema}.{campo.lexema}", linha=t.linha, coluna=t.coluna)
            return NoAST("Identificador", t.lexema, linha=t.linha, coluna=t.coluna)
        if self.aceitar("("):
            no = self.expressao()
            self.consumir(lexema=")", esperado="')'")
            return no
        self.erro("número, true, false, identificador ou '('", t)


def analisar_tokens(tokens: List[Token]) -> NoAST:
    return AnalisadorSintatico(tokens).analisar()
