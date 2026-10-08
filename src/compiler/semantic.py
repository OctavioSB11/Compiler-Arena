from typing import Optional

from .ast_nodes import NoAST
from .symbols import TabelaDeSimbolos

SENSORES = {
    "energy": "int",
    "position.x": "int",
    "position.y": "int",
    "enemy.visible": "bool",
    "enemy.distance": "int",
    "enemy.direction": "int",
}

COMANDOS = {
    "move": [("int", 1, 20)],
    "back": [("int", 1, 20)],
    "rotate": [("int", -180, 180)],
    "scan": [],
    "fire": [("int", 1, 3)],
}

OPERADORES_ARITMETICOS = {"+", "-", "*", "/"}
OPERADORES_RELACIONAIS = {">", "<", ">=", "<=", "==", "!="}
OPERADORES_LOGICOS = {"&&", "||"}
OPERADORES_UNARIOS = {"-unario", "!unario"}


class ErroSemantico(Exception):
    def __init__(self, mensagem: str, linha: int):
        self.mensagem = mensagem
        self.linha = linha
        super().__init__(f"Linha {linha}: {mensagem}")


def _valor_constante(no: NoAST) -> Optional[int]:
    if no.tipo == "Numero":
        return int(no.valor)
    if no.tipo == "Operacao" and no.valor == "-unario" and no.filhos[0].tipo == "Numero":
        return -int(no.filhos[0].valor)
    return None


class AnalisadorSemantico:
    def __init__(self):
        self.tabela = TabelaDeSimbolos()

    def analisar(self, raiz: NoAST) -> TabelaDeSimbolos:
        self._visitar(raiz)
        return self.tabela

    def _visitar(self, no: NoAST) -> None:
        metodo = getattr(self, f"_visitar_{no.tipo}", None)
        if metodo is None:
            raise ErroSemantico(f"nó de AST não suportado: {no.tipo}", no.linha or 0)
        metodo(no)

    # ---------------- estrutura ----------------

    def _visitar_Robo(self, no: NoAST) -> None:
        # O bloco do robô usa o escopo raiz diretamente (sem empilhar um novo
        # escopo) para que a tabela de símbolos final (--symbols) preserve as
        # declarações de nível superior.
        bloco = no.filhos[0]
        for comando in bloco.filhos:
            self._visitar(comando)

    def _visitar_Bloco(self, no: NoAST) -> None:
        self.tabela.entrar_escopo()
        for comando in no.filhos:
            self._visitar(comando)
        self.tabela.sair_escopo()

    def _visitar_Declaracao(self, no: NoAST) -> None:
        tipo = no.valor
        identificador, *resto = no.filhos
        nome = identificador.valor
        if self.tabela.resolver_no_escopo_atual(nome) is not None:
            existente = self.tabela.resolver_no_escopo_atual(nome)
            raise ErroSemantico(
                f"'{nome}' já foi declarada na linha {existente.linha_declaracao}", no.linha)
        if resto:
            expressao = resto[0]
            self._visitar(expressao)
            if expressao.tipo_semantico != tipo:
                raise ErroSemantico(
                    f"não é possível atribuir '{expressao.tipo_semantico}' a '{tipo}'", no.linha)
        self.tabela.declarar(nome, tipo, no.linha)

    def _resolver_ou_erro(self, nome: str, no: NoAST):
        simbolo = self.tabela.resolver(nome)
        if simbolo is not None:
            return simbolo
        if self.tabela.ja_foi_declarada_em_algum_escopo(nome):
            raise ErroSemantico(f"'{nome}' não existe neste escopo", no.linha)
        raise ErroSemantico(f"'{nome}' não foi declarada", no.linha)

    def _visitar_Atribuicao(self, no: NoAST) -> None:
        identificador, expressao = no.filhos
        nome = identificador.valor
        if nome in SENSORES:
            raise ErroSemantico(f"'{nome}' é um sensor e não pode ser atribuído", no.linha)
        simbolo = self._resolver_ou_erro(nome, no)
        self._visitar(expressao)
        if expressao.tipo_semantico != simbolo.tipo:
            raise ErroSemantico(
                f"não é possível atribuir '{expressao.tipo_semantico}' a '{simbolo.tipo}'", no.linha)

    def _visitar_Condicional(self, no: NoAST) -> None:
        condicao, bloco, *resto = no.filhos
        self._visitar(condicao)
        if condicao.tipo_semantico != "bool":
            raise ErroSemantico("condição do 'if' deve ser 'bool'", no.linha)
        self._visitar(bloco)
        if resto:
            self._visitar(resto[0])

    def _visitar_Enquanto(self, no: NoAST) -> None:
        condicao, bloco = no.filhos
        self._visitar(condicao)
        if condicao.tipo_semantico != "bool":
            raise ErroSemantico("condição do 'while' deve ser 'bool'", no.linha)
        self._visitar(bloco)

    # ---------------- expressões ----------------

    def _visitar_Numero(self, no: NoAST) -> None:
        no.tipo_semantico = "int"

    def _visitar_Booleano(self, no: NoAST) -> None:
        no.tipo_semantico = "bool"

    def _visitar_Identificador(self, no: NoAST) -> None:
        nome = no.valor
        if nome in SENSORES:
            no.tipo_semantico = SENSORES[nome]
            return
        simbolo = self._resolver_ou_erro(nome, no)
        no.tipo_semantico = simbolo.tipo

    def _visitar_Acesso(self, no: NoAST) -> None:
        caminho = no.valor
        if caminho not in SENSORES:
            raise ErroSemantico(f"'{caminho}' não é um sensor conhecido", no.linha)
        no.tipo_semantico = SENSORES[caminho]

    def _visitar_Operacao(self, no: NoAST) -> None:
        for filho in no.filhos:
            self._visitar(filho)
        operador = no.valor
        tipos = [filho.tipo_semantico for filho in no.filhos]

        if operador in OPERADORES_UNARIOS:
            esperado = "bool" if operador == "!unario" else "int"
            if tipos[0] != esperado:
                raise ErroSemantico(
                    f"operador '{operador[:-6]}' não aceita '{tipos[0]}'", no.linha)
            no.tipo_semantico = esperado
            return

        esquerda, direita = tipos
        if operador in OPERADORES_ARITMETICOS:
            if esquerda != "int" or direita != "int":
                errado = direita if esquerda == "int" else esquerda
                raise ErroSemantico(f"operador '{operador}' não aceita '{errado}'", no.linha)
            no.tipo_semantico = "int"
        elif operador in OPERADORES_RELACIONAIS:
            if esquerda != "int" or direita != "int":
                errado = direita if esquerda == "int" else esquerda
                raise ErroSemantico(f"operador '{operador}' não aceita '{errado}'", no.linha)
            no.tipo_semantico = "bool"
        elif operador in OPERADORES_LOGICOS:
            if esquerda != "bool" or direita != "bool":
                errado = direita if esquerda == "bool" else esquerda
                raise ErroSemantico(f"operador '{operador}' não aceita '{errado}'", no.linha)
            no.tipo_semantico = "bool"
        else:
            raise ErroSemantico(f"operador '{operador}' desconhecido", no.linha)

    def _visitar_Chamada(self, no: NoAST) -> None:
        nome = no.valor
        if nome not in COMANDOS:
            raise ErroSemantico(f"'{nome}' não é um comando conhecido", no.linha)
        parametros = COMANDOS[nome]
        if len(no.filhos) != len(parametros):
            raise ErroSemantico(
                f"{nome}() espera {len(parametros)} argumento(s), recebeu {len(no.filhos)}", no.linha)
        for argumento, (tipo_esperado, minimo, maximo) in zip(no.filhos, parametros):
            self._visitar(argumento)
            if argumento.tipo_semantico != tipo_esperado:
                raise ErroSemantico(
                    f"{nome}() espera '{tipo_esperado}', recebeu '{argumento.tipo_semantico}'", no.linha)
            valor_constante = _valor_constante(argumento)
            if valor_constante is not None and not (minimo <= valor_constante <= maximo):
                raise ErroSemantico(
                    f"{nome}() espera valor entre {minimo} e {maximo}", no.linha)
        no.tipo_semantico = None
