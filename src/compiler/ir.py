"""Gerador da IR de três endereços (AST -> lista de instruções).

Cada instrução é uma `Instrucao(op, arg1, arg2, res, operador)`:

    COPY       res = arg1
    BINOP      res = arg1 operador arg2     (+ - * / < > <= >= == != && ||)
    UNOP       res = operador arg1          (neg, not)
    LABEL      res:                         (res é o nome do rótulo)
    JUMP       goto res
    JUMPF      ifFalse arg1 goto res
    GETSENSOR  res = sensor arg1
    PARAM      param arg1
    CALL       call arg1, arg2              (arg1 = comando, arg2 = nº de argumentos)

Operandos são nomes de variáveis (str), temporários `t1`, `t2`... (str) ou
constantes inteiras (int). `true` e `false` viram 1 e 0.
"""
import re
from typing import List, NamedTuple, Optional, Union

from .ast_nodes import NoAST

Operando = Union[str, int]

SENSORES_SIMPLES = {"energy"}


class Instrucao(NamedTuple):
    op: str
    arg1: Optional[Operando] = None
    arg2: Optional[Operando] = None
    res: Optional[str] = None
    operador: Optional[str] = None

    def __str__(self) -> str:
        if self.op == "COPY":
            return f"{self.res} = {self.arg1}"
        if self.op == "BINOP":
            return f"{self.res} = {self.arg1} {self.operador} {self.arg2}"
        if self.op == "UNOP":
            return f"{self.res} = {self.operador} {self.arg1}"
        if self.op == "LABEL":
            return f"{self.res}:"
        if self.op == "JUMP":
            return f"goto {self.res}"
        if self.op == "JUMPF":
            return f"ifFalse {self.arg1} goto {self.res}"
        if self.op == "GETSENSOR":
            return f"{self.res} = sensor {self.arg1}"
        if self.op == "PARAM":
            return f"param {self.arg1}"
        if self.op == "CALL":
            return f"call {self.arg1}, {self.arg2}"
        return f"{self.op} {self.arg1} {self.arg2} {self.res}"


def formatar_ir(instrucoes: List[Instrucao]) -> str:
    return "\n".join(str(i) for i in instrucoes)


class GeradorIR:
    """Percorre a AST e produz a lista de instruções de três endereços."""

    def __init__(self):
        self.codigo: List[Instrucao] = []
        self._temporarios = 0
        self._rotulos = 0
        self._escopos: List[dict] = []
        self._declaradas: dict = {}

    # ---------------- utilidades ----------------

    def _novo_temp(self) -> str:
        self._temporarios += 1
        return f"t{self._temporarios}"

    def _novo_rotulo(self) -> str:
        self._rotulos += 1
        return f"L{self._rotulos}"

    def _emitir(self, op, arg1=None, arg2=None, res=None, operador=None) -> None:
        self.codigo.append(Instrucao(op, arg1, arg2, res, operador))

    def _declarar(self, nome: str) -> str:
        """Dá um nome único à variável, para que blocos diferentes que
        reusam o mesmo nome não se misturem na IR."""
        base = f"v_{nome}" if re.fullmatch(r"[tL]\d+", nome) else nome
        vezes = self._declaradas.get(base, 0)
        self._declaradas[base] = vezes + 1
        unico = base if vezes == 0 else f"{base}_{vezes}"
        self._escopos[-1][nome] = unico
        return unico

    def _resolver(self, nome: str) -> str:
        for escopo in reversed(self._escopos):
            if nome in escopo:
                return escopo[nome]
        return nome

    # ---------------- ponto de entrada ----------------

    def gerar(self, raiz: NoAST) -> List[Instrucao]:
        self.__init__()
        self._escopos.append({})
        for filho in raiz.filhos:
            self._comando(filho)
        return self.codigo

    # ---------------- comandos ----------------

    def _comando(self, no: NoAST) -> None:
        metodo = getattr(self, f"_cmd_{no.tipo}", None)
        if metodo is None:
            raise ValueError(f"nó '{no.tipo}' não é um comando")
        metodo(no)

    def _cmd_Bloco(self, no: NoAST) -> None:
        self._escopos.append({})
        for comando in no.filhos:
            self._comando(comando)
        self._escopos.pop()

    def _cmd_Declaracao(self, no: NoAST) -> None:
        nome = self._declarar(no.filhos[0].valor)
        valor: Operando = 0
        if len(no.filhos) > 1:
            valor = self._expressao(no.filhos[1])
        self._emitir("COPY", valor, res=nome)

    def _cmd_Atribuicao(self, no: NoAST) -> None:
        valor = self._expressao(no.filhos[1])
        self._emitir("COPY", valor, res=self._resolver(no.filhos[0].valor))

    def _cmd_Chamada(self, no: NoAST) -> None:
        argumentos = [self._expressao(a) for a in no.filhos]
        for argumento in argumentos:
            self._emitir("PARAM", argumento)
        self._emitir("CALL", no.valor, len(argumentos))

    def _cmd_Condicional(self, no: NoAST) -> None:
        condicao = self._expressao(no.filhos[0])
        tem_senao = len(no.filhos) > 2
        rotulo_senao = self._novo_rotulo()
        rotulo_fim = self._novo_rotulo() if tem_senao else rotulo_senao
        self._emitir("JUMPF", condicao, res=rotulo_senao)
        self._comando(no.filhos[1])
        if tem_senao:
            self._emitir("JUMP", res=rotulo_fim)
            self._emitir("LABEL", res=rotulo_senao)
            self._comando(no.filhos[2])
        self._emitir("LABEL", res=rotulo_fim)

    def _cmd_Enquanto(self, no: NoAST) -> None:
        inicio = self._novo_rotulo()
        fim = self._novo_rotulo()
        self._emitir("LABEL", res=inicio)
        condicao = self._expressao(no.filhos[0])
        self._emitir("JUMPF", condicao, res=fim)
        self._comando(no.filhos[1])
        self._emitir("JUMP", res=inicio)
        self._emitir("LABEL", res=fim)

    # ---------------- expressões ----------------

    def _expressao(self, no: NoAST) -> Operando:
        """Gera o código da expressão e devolve o operando com o resultado."""
        if no.tipo == "Numero":
            return int(no.valor)
        if no.tipo == "Booleano":
            return 1 if no.valor == "true" else 0
        if no.tipo == "Identificador":
            if no.valor in SENSORES_SIMPLES:
                temp = self._novo_temp()
                self._emitir("GETSENSOR", no.valor, res=temp)
                return temp
            return self._resolver(no.valor)
        if no.tipo == "Acesso":
            temp = self._novo_temp()
            self._emitir("GETSENSOR", no.valor, res=temp)
            return temp
        if no.tipo == "Operacao":
            return self._operacao(no)
        raise ValueError(f"nó '{no.tipo}' não é uma expressão")

    def _operacao(self, no: NoAST) -> Operando:
        if len(no.filhos) == 1:
            operando = self._expressao(no.filhos[0])
            temp = self._novo_temp()
            operador = "neg" if no.valor == "-unario" else "not"
            self._emitir("UNOP", operando, res=temp, operador=operador)
            return temp
        esquerda = self._expressao(no.filhos[0])
        direita = self._expressao(no.filhos[1])
        temp = self._novo_temp()
        self._emitir("BINOP", esquerda, direita, temp, no.valor)
        return temp


def gerar_ir(raiz: NoAST) -> List[Instrucao]:
    return GeradorIR().gerar(raiz)