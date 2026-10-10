"""Otimizador da IR de três endereços (IR -> IR).

Cada técnica é uma função própria que recebe a lista de instruções e devolve
uma lista nova (a original não é alterada). `otimizar` aplica as técnicas
escolhidas, em ordem, até a IR parar de mudar.

Técnicas:
    dobrar_constantes          t1 = 10 + 20        ->  t1 = 30
    simplificar_algebra        t2 = x + 0          ->  t2 = x
    propagar_constantes        usa t1 = 30 onde t1 aparece
    eliminar_temporarios       remove temporários que ninguém lê
    simplificar_saltos         ifFalse 1 goto L    ->  (removido)

Só os temporários (t1, t2...) são propagados e removidos: o gerador de IR
atribui cada temporário uma única vez, então a troca é sempre segura.
Variáveis do usuário não são tocadas, porque mudam ao longo do programa.
"""
import re
from typing import Callable, Dict, List, Optional

from .ir import Instrucao

OPERADORES_ARITMETICOS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
}
OPERADORES_RELACIONAIS = {
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def _e_temporario(operando) -> bool:
    return isinstance(operando, str) and re.fullmatch(r"t\d+", operando) is not None


def _e_constante(operando) -> bool:
    return isinstance(operando, int)


def _copia(res, valor) -> Instrucao:
    return Instrucao("COPY", valor, None, res)


def _dividir(a: int, b: int) -> int:
    """Divisão inteira que trunca em direção a zero (como em C)."""
    quociente = abs(a) // abs(b)
    return quociente if (a >= 0) == (b >= 0) else -quociente


# ---------------- técnica 1: constant folding ----------------

def dobrar_constantes(codigo: List[Instrucao]) -> List[Instrucao]:
    novo = []
    for i in codigo:
        if i.op == "BINOP" and _e_constante(i.arg1) and _e_constante(i.arg2):
            valor = _calcular(i.operador, i.arg1, i.arg2)   # type: ignore
            if valor is not None:
                novo.append(_copia(i.res, valor))
                continue
        if i.op == "UNOP" and _e_constante(i.arg1):
            valor = -i.arg1 if i.operador == "neg" else int(i.arg1 == 0) # type: ignore
            novo.append(_copia(i.res, valor))
            continue
        novo.append(i)
    return novo


def _calcular(operador: str, a: int, b: int) -> Optional[int]:
    if operador in OPERADORES_ARITMETICOS:
        return OPERADORES_ARITMETICOS[operador](a, b)
    if operador == "/":
        return None if b == 0 else _dividir(a, b)  # divisão por zero fica para a VM
    if operador in OPERADORES_RELACIONAIS:
        return int(OPERADORES_RELACIONAIS[operador](a, b))
    if operador == "&&":
        return int(bool(a) and bool(b))
    if operador == "||":
        return int(bool(a) or bool(b))
    return None


# ---------------- técnica 2: simplificação algébrica ----------------

def simplificar_algebra(codigo: List[Instrucao]) -> List[Instrucao]:
    novo = []
    for i in codigo:
        if i.op == "BINOP":
            resultado = _simplificar(i.operador, i.arg1, i.arg2)
            if resultado is not None:
                novo.append(_copia(i.res, resultado[0]))
                continue
        novo.append(i)
    return novo


def _simplificar(operador, a, b):
    """Devolve (operando,) se a operação se reduz a um operando; senão None."""
    if operador == "+":
        if b == 0 and _e_constante(b):
            return (a,)
        if a == 0 and _e_constante(a):
            return (b,)
    elif operador == "-":
        if _e_constante(b) and b == 0:
            return (a,)
    elif operador == "*":
        if _e_constante(b) and b == 1:
            return (a,)
        if _e_constante(a) and a == 1:
            return (b,)
        if (_e_constante(b) and b == 0) or (_e_constante(a) and a == 0):
            return (0,)
    elif operador == "/":
        if _e_constante(b) and b == 1:
            return (a,)
    elif operador == "&&":
        if _e_constante(b) and b == 1:
            return (a,)
        if _e_constante(a) and a == 1:
            return (b,)
        if (_e_constante(b) and b == 0) or (_e_constante(a) and a == 0):
            return (0,)
    elif operador == "||":
        if _e_constante(b) and b == 0:
            return (a,)
        if _e_constante(a) and a == 0:
            return (b,)
        if (_e_constante(b) and b == 1) or (_e_constante(a) and a == 1):
            return (1,)
    return None


# ---------------- técnica 3: propagação de constantes (temporários) ----------------

CAMPOS_DE_USO = {
    "COPY": ("arg1",), "BINOP": ("arg1", "arg2"), "UNOP": ("arg1",),
    "JUMPF": ("arg1",), "PARAM": ("arg1",),
}


def _usos(i: Instrucao):
    return [getattr(i, campo) for campo in CAMPOS_DE_USO.get(i.op, ())]


def propagar_constantes(codigo: List[Instrucao]) -> List[Instrucao]:
    constantes = {
        i.res: i.arg1 for i in codigo
        if i.op == "COPY" and _e_temporario(i.res) and _e_constante(i.arg1)
    } 
    novo = []
    for i in codigo:
        trocas = {campo: constantes[getattr(i, campo)]
                  for campo in CAMPOS_DE_USO.get(i.op, ())
                  if getattr(i, campo) in constantes}
        novo.append(i._replace(**trocas) if trocas else i)
    return novo


# ---------------- técnica 4: eliminação de temporários mortos ----------------

def eliminar_temporarios(codigo: List[Instrucao]) -> List[Instrucao]:
    usados = {u for i in codigo for u in _usos(i) if _e_temporario(u)}
    return [i for i in codigo
            if not (i.op in {"COPY", "BINOP", "UNOP", "GETSENSOR"}
                    and _e_temporario(i.res) and i.res not in usados)]


# ---------------- técnica 5: saltos com condição constante ----------------

def simplificar_saltos(codigo: List[Instrucao]) -> List[Instrucao]:
    novo = []
    for i in codigo:
        if i.op == "JUMPF" and _e_constante(i.arg1):
            if i.arg1 == 0:
                novo.append(Instrucao("JUMP", res=i.res))
            continue  # condição sempre verdadeira: o salto nunca acontece
        novo.append(i)
    return novo


# ---------------- orquestração ----------------

TECNICAS: Dict[str, Callable[[List[Instrucao]], List[Instrucao]]] = {
    "dobrar_constantes": dobrar_constantes,
    "simplificar_algebra": simplificar_algebra,
    "propagar_constantes": propagar_constantes,
    "eliminar_temporarios": eliminar_temporarios,
    "simplificar_saltos": simplificar_saltos,
}


def otimizar(codigo: List[Instrucao], tecnicas: Optional[List[str]] = None,
             limite: int = 10) -> List[Instrucao]:
    """Aplica as técnicas (todas, se `tecnicas` for None) até a IR estabilizar."""
    nomes = list(TECNICAS) if tecnicas is None else tecnicas
    for nome in nomes:
        if nome not in TECNICAS:
            raise ValueError(f"técnica desconhecida: {nome}")
    atual = list(codigo)
    for _ in range(limite):
        anterior = atual
        for nome in nomes:
            atual = TECNICAS[nome](atual)
        if atual == anterior:
            break
    return atual