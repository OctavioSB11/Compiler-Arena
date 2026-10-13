# type: ignore

"""Gerador de código objeto: IR de três endereços -> bytecode de pilha.

Cada instrução da IR vira uma ou mais instruções de pilha. As variáveis e os
temporários recebem um índice fixo (na ordem em que aparecem) usado por
`LOAD i` e `STORE i`. Os rótulos viram endereços (posição na lista) e o
programa sempre termina com `HALT`.
"""

from typing import Dict, List, NamedTuple, Optional, Union

from .ir import Instrucao

OPERADORES_BINARIOS = {
    "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV",
    "<": "LT", ">": "GT", "<=": "LE", ">=": "GE", "==": "EQ", "!=": "NE",
    "&&": "AND", "||": "OR",
}
OPERADORES_UNARIOS = {"neg": "NEG", "not": "NOT"}
SENSORES = {
    "energy": "energy",
    "position.x": "pos_x",
    "position.y": "pos_y",
    "enemy.visible": "enemy_visible",
    "enemy.distance": "enemy_distance",
    "enemy.direction": "enemy_direction",
}
COMANDOS = {
    "move": "MOVE", "back": "BACK", "rotate": "ROTATE",
    "fire": "FIRE", "scan": "SCAN",
}


class InstrucaoBytecode(NamedTuple):
    op: str
    arg: Optional[Union[int, str]] = None

    def __str__(self) -> str:
        return self.op if self.arg is None else f"{self.op} {self.arg}"


def formatar_bytecode(programa: List[InstrucaoBytecode],
                      com_enderecos: bool = False) -> str:
    if com_enderecos:
        return "\n".join(f"{n:3}  {i}" for n, i in enumerate(programa))
    return "\n".join(str(i) for i in programa)


class GeradorBytecode:
    def __init__(self):
        self.programa: List[InstrucaoBytecode] = []
        self.variaveis: Dict[str, int] = {}
        self._rotulos: Dict[str, int] = {}

    def _indice(self, nome: str) -> int:
        if nome not in self.variaveis:
            self.variaveis[nome] = len(self.variaveis)
        return self.variaveis[nome]

    def _emitir(self, op: str, arg=None) -> None:
        self.programa.append(InstrucaoBytecode(op, arg))

    def _empilhar(self, operando) -> None:
        if isinstance(operando, int):
            self._emitir("PUSH", operando)
        else:
            self._emitir("LOAD", self._indice(operando))

    def gerar(self, ir: List[Instrucao]) -> List[InstrucaoBytecode]:
        for i in ir:
            self._instrucao(i)
        self._emitir("HALT")
        return self._resolver_rotulos()

    def _instrucao(self, i: Instrucao) -> None:
        if i.op == "COPY":
            self._empilhar(i.arg1)
            self._emitir("STORE", self._indice(i.res))
        elif i.op == "BINOP":
            self._empilhar(i.arg1)
            self._empilhar(i.arg2)
            self._emitir(OPERADORES_BINARIOS[i.operador])
            self._emitir("STORE", self._indice(i.res))
        elif i.op == "UNOP":
            self._empilhar(i.arg1)
            self._emitir(OPERADORES_UNARIOS[i.operador])
            self._emitir("STORE", self._indice(i.res))
        elif i.op == "LABEL":
            self._rotulos[i.res] = len(self.programa)
        elif i.op == "JUMP":
            self._emitir("JMP", i.res)
        elif i.op == "JUMPF":
            self._empilhar(i.arg1)
            self._emitir("JZ", i.res)
        elif i.op == "GETSENSOR":
            self._emitir("SENSE", SENSORES[i.arg1])
            self._emitir("STORE", self._indice(i.res))
        elif i.op == "PARAM":
            self._empilhar(i.arg1)
        elif i.op == "CALL":
            self._emitir(COMANDOS[i.arg1])
        else:
            raise ValueError(f"instrução de IR desconhecida: {i.op}")

    def _resolver_rotulos(self) -> List[InstrucaoBytecode]:
        return [
            InstrucaoBytecode(b.op, self._rotulos[b.arg])
            if b.op in ("JMP", "JZ") else b
            for b in self.programa
        ]


def gerar_bytecode(ir: List[Instrucao]) -> List[InstrucaoBytecode]:
    return GeradorBytecode().gerar(ir)