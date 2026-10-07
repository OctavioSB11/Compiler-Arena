import glob
import os

import pytest

from src.cli import compilar
from src.compiler.lexer import AutomatoLexico
from src.compiler.parser import ErroSintatico
from src.compiler.tokens import ErroLexico

EX = os.path.join(os.path.dirname(__file__), "..", "examples")


def ler(nome):
    with open(os.path.join(EX, nome), encoding="utf-8") as f:
        return f.read()


def test_alpha_do_enunciado_compila():
    arvore = compilar(ler("alpha.robot"))
    assert arvore.tipo == "Robo" and arvore.valor == "Alpha"


def test_erro_lexico_tem_linha_e_coluna():
    with pytest.raises(ErroLexico) as e:
        compilar(ler("erro_lexico.robot"))
    assert (e.value.linha, e.value.coluna) == (2, 14)


def test_erro_sintatico_aponta_token_seguinte():
    with pytest.raises(ErroSintatico) as e:
        compilar(ler("erro_sintatico.robot"))
    assert e.value.token.linha == 3 and "';'" in e.value.mensagem


def test_exemplos_semanticos_sao_sintaticamente_validos():
    compilar(ler("erro_semantico.robot"))
    compilar(ler("otimizacao.robot"))


def test_precedencia():
    arvore = compilar("robot R { int x = 1 + 2 * 3 < 8 && !false; }")
    decl = arvore.filhos[0].filhos[0]
    assert decl.filhos[1].valor == "&&"


def test_acesso_a_sensor_e_chamada_em_expressao():
    compilar("robot R { int d = enemy.distance; scan(); }")


def test_else_if():
    compilar("robot R { if energy < 10 { move(1); } else if energy < 50 { back(1); } else { fire(1); } }")


def test_palavra_reservada_nao_e_identificador():
    toks = AutomatoLexico().analisar("while whiles")
    assert [t.classificacao for t in toks] == ["PALAVRA_RESERVADA", "IDENTIFICADOR"]
