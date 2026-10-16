"""Máquina virtual de pilha: executa o bytecode do codegen (seção 5.6 do guia).

A cada tick a arena chama `executar_tick()`. A VM executa instruções até uma
ação (`MOVE`, `BACK`, `ROTATE`, `FIRE` ou `SCAN`) ou até o orçamento de 50
instruções, o que vier primeiro, e devolve a ação como `(nome, argumento)`.
Assim um `while` infinito sem ação não trava a arena.

A VM não importa nada da arena: lê os sensores por `obter_sensor(nome)`.
Um erro de execução (divisão por zero, pilha vazia, salto inválido) para só
este robô e fica guardado em `erro`; a batalha continua.
"""
from typing import Callable, List, Optional, Tuple

ORCAMENTO = 50  # instruções por tick

# faixas dos comandos (seção 5.7): o argumento de uma variável é ajustado aqui
LIMITES = {"MOVE": (1, 20), "BACK": (1, 20), "ROTATE": (-180, 180), "FIRE": (1, 3)}
ACOES = {"MOVE", "BACK", "ROTATE", "FIRE", "SCAN"}

Acao = Tuple[str, Optional[int]]


class ErroExecucao(Exception):
    """Erro em tempo de execução do bytecode."""


def dividir(a: int, b: int) -> int:
    """Divisão inteira truncada em direção a zero, como em C: -7 / 2 = -3."""
    if b == 0:
        raise ErroExecucao("divisão por zero")
    quociente = abs(a) // abs(b)
    return quociente if (a < 0) == (b < 0) else -quociente


def limitar(valor: int, minimo: int, maximo: int) -> int:
    return max(minimo, min(maximo, valor))


OPERACOES = {
    "ADD": lambda a, b: a + b,
    "SUB": lambda a, b: a - b,
    "MUL": lambda a, b: a * b,
    "DIV": dividir,
    "LT": lambda a, b: int(a < b),
    "GT": lambda a, b: int(a > b),
    "LE": lambda a, b: int(a <= b),
    "GE": lambda a, b: int(a >= b),
    "EQ": lambda a, b: int(a == b),
    "NE": lambda a, b: int(a != b),
    "AND": lambda a, b: int(bool(a) and bool(b)),
    "OR": lambda a, b: int(bool(a) or bool(b)),
}


class MaquinaVirtual:
    def __init__(self, bytecode: list, obter_sensor: Callable[[str], int],
                 orcamento: int = ORCAMENTO):
        self.programa = list(bytecode)
        self.obter_sensor = obter_sensor
        self.orcamento = orcamento
        self.pc = 0  # endereço da próxima instrução
        self.pilha: List[int] = []
        self.memoria = [0] * self._tamanho_memoria()  # toda variável começa em 0
        self.parado = False
        self.erro: Optional[str] = None

    def _tamanho_memoria(self) -> int:
        indices = [i.arg for i in self.programa if i.op in ("LOAD", "STORE")]
        return max(indices, default=-1) + 1

    def executar_tick(self) -> Optional[Acao]:
        """Executa até uma ação ou até o orçamento. Devolve a ação ou None."""
        for _ in range(self.orcamento):
            if self.parado:
                return None
            try:
                acao = self.passo()
            except ErroExecucao as erro:
                self.erro = f"endereço {self.pc}: {erro}"
                self.parado = True
                return None
            if acao is not None:
                return acao
        return None

    def passo(self) -> Optional[Acao]:
        """Executa uma instrução. Devolve a ação, se a instrução for uma."""
        if not 0 <= self.pc < len(self.programa):
            raise ErroExecucao(f"salto para fora do programa ({self.pc})")
        op, arg = self.programa[self.pc]
        self.pc += 1

        if op == "PUSH":
            self.pilha.append(arg)
        elif op == "LOAD":
            self.pilha.append(self.memoria[arg])
        elif op == "STORE":
            self.memoria[arg] = self._desempilhar()
        elif op in OPERACOES:
            b = self._desempilhar()
            a = self._desempilhar()
            self.pilha.append(OPERACOES[op](a, b))
        elif op == "NEG":
            self.pilha.append(-self._desempilhar())
        elif op == "NOT":
            self.pilha.append(int(self._desempilhar() == 0))
        elif op == "JMP":
            self.pc = arg
        elif op == "JZ":
            if self._desempilhar() == 0:
                self.pc = arg
        elif op == "SENSE":
            self.pilha.append(int(self.obter_sensor(arg)))
        elif op == "SCAN":
            return ("scan", None)
        elif op in ACOES:
            valor = limitar(self._desempilhar(), *LIMITES[op])
            return (op.lower(), valor)
        elif op == "HALT":
            self.parado = True
        else:
            raise ErroExecucao(f"instrução desconhecida: {op}")
        return None

    def _desempilhar(self) -> int:
        if not self.pilha:
            raise ErroExecucao("pilha vazia")
        return self.pilha.pop()