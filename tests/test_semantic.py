import os

import pytest

from src.cli import compilar
from src.compiler.semantic import ErroSemantico

EX = os.path.join(os.path.dirname(__file__), "..", "examples")


def ler(nome):
    with open(os.path.join(EX, nome), encoding="utf-8") as f:
        return f.read()


def test_alpha_passa_pela_semantica():
    compilar(ler("alpha.robot"))


def test_atribuicao_tipo_incompativel():
    with pytest.raises(ErroSemantico) as e:
        compilar(ler("erro_semantico.robot"))
    assert e.value.linha == 3
    assert "não é possível atribuir" in e.value.mensagem


def test_uso_antes_da_declaracao():
    with pytest.raises(ErroSemantico) as e:
        compilar("robot R { x = 1; }")
    assert "não foi declarada" in e.value.mensagem


def test_declaracao_duplicada():
    with pytest.raises(ErroSemantico) as e:
        compilar("robot R { int x; int x; }")
    assert e.value.linha == 1
    assert "já foi declarada na linha 1" in e.value.mensagem


def test_parametro_fora_do_intervalo():
    with pytest.raises(ErroSemantico) as e:
        compilar("robot R { fire(200); }")
    assert "fire() espera valor entre 1 e 3" in e.value.mensagem


def test_parametro_com_tipo_errado():
    with pytest.raises(ErroSemantico) as e:
        compilar("robot R { move(false); }")
    assert "move() espera 'int', recebeu 'bool'" in e.value.mensagem


def test_variavel_fora_do_escopo():
    with pytest.raises(ErroSemantico) as e:
        compilar("robot R { if energy < 10 { int y = 1; } y = 2; }")
    assert "'y' não existe neste escopo" in e.value.mensagem


def test_operador_incompativel():
    with pytest.raises(ErroSemantico) as e:
        compilar("robot R { int x = true + 1; }")
    assert "operador '+' não aceita 'bool'" in e.value.mensagem


def test_sensores_tem_tipo_correto():
    compilar("robot R { int d = enemy.distance; bool v = enemy.visible; int e = energy; }")


def test_atribuicao_a_sensor_e_erro():
    with pytest.raises(ErroSemantico) as e:
        compilar("robot R { energy = 10; }")
    assert "sensor" in e.value.mensagem
