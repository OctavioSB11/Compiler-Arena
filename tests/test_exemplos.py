from pathlib import Path

import pytest

from src.compiler.pipeline import compilar

EXEMPLOS = Path(__file__).resolve().parent.parent / "examples"


def compilar_exemplo(nome):
    return compilar((EXEMPLOS / nome).read_text(encoding="utf-8"))


VALIDOS = ["alpha.robot", "otimizacao.robot", "atirador.robot", "fugitivo.robot", "misto.robot"]


@pytest.mark.parametrize("nome", VALIDOS)
def test_robos_validos_passam_no_front_end(nome):
    r = compilar_exemplo(nome)
    assert r.ok and r.contexto.ast is not None


def test_erro_lexico_para_na_etapa_lexica():
    r = compilar_exemplo("erro_lexico.robot")
    assert r.erro.nome == "Análise Léxica"
    assert r.erro.linha == 2


def test_erro_sintatico_para_na_etapa_sintatica():
    r = compilar_exemplo("erro_sintatico.robot")
    assert r.erro.nome == "Análise Sintática"
    assert r.erro.linha == 3


def test_erro_semantico_passa_no_front_end():
    # a sintaxe está correta; o erro só será detectado pela Análise Semântica
    r = compilar_exemplo("erro_semantico.robot")
    assert r.ok