import pytest

from src.compiler.lexer import AutomatoLexico
from src.compiler.tokens import ErroLexico


def tokenizar(codigo):
    lexer = AutomatoLexico()
    return lexer.analisar(codigo), lexer


def classes(codigo):
    tokens, _ = tokenizar(codigo)
    return [t.classificacao for t in tokens]


def lexemas(codigo):
    tokens, _ = tokenizar(codigo)
    return [t.lexema for t in tokens]


def test_palavras_reservadas():
    assert classes("robot int bool if else while true false") == ["PALAVRA_RESERVADA"] * 8


def test_identificador_com_underscore_e_digitos():
    tokens, _ = tokenizar("_alvo1 distancia_2")
    assert [t.classificacao for t in tokens] == ["IDENTIFICADOR", "IDENTIFICADOR"]
    assert [t.lexema for t in tokens] == ["_alvo1", "distancia_2"]


def test_palavra_reservada_dentro_de_identificador():
    assert classes("whiles integer") == ["IDENTIFICADOR", "IDENTIFICADOR"]


def test_numero_inteiro():
    tokens, _ = tokenizar("0 42 1000")
    assert [t.classificacao for t in tokens] == ["NUMERO_INTEIRO"] * 3
    assert [t.valor for t in tokens] == ["0", "42", "1000"]


def test_operadores_de_dois_caracteres_tem_prioridade():
    assert lexemas("<= >= == != && ||") == ["<=", ">=", "==", "!=", "&&", "||"]


def test_operador_simples_nao_vira_duplo():
    assert lexemas("< =") == ["<", "="]
    assert classes("< =") == ["OPERADOR_RELACIONAL", "ATRIBUICAO"]


def test_classificacao_dos_operadores():
    assert classes("+ - * /") == ["OPERADOR_ARITMETICO"] * 4
    assert classes("> < == !=") == ["OPERADOR_RELACIONAL"] * 4
    assert classes("&& || !") == ["OPERADOR_LOGICO"] * 3


def test_delimitadores_incluindo_ponto():
    assert classes("; ( ) { } , .") == ["DELIMITADOR"] * 7


def test_sensor_vira_tres_tokens():
    assert lexemas("enemy.distance") == ["enemy", ".", "distance"]


def test_comentario_e_ignorado():
    assert lexemas("int x; // isto some\nx = 1;") == ["int", "x", ";", "x", "=", "1", ";"]


def test_posicao_linha_e_coluna():
    tokens, _ = tokenizar("robot A {\n  int x;\n}")
    por_lexema = {(t.lexema, t.linha): t.coluna for t in tokens}
    assert por_lexema[("robot", 1)] == 1
    assert por_lexema[("A", 1)] == 7
    assert por_lexema[("int", 2)] == 3
    assert por_lexema[("}", 3)] == 1


def test_coluna_depois_de_comentario_na_mesma_linha():
    tokens, _ = tokenizar("x // c\ny")
    assert (tokens[1].lexema, tokens[1].linha, tokens[1].coluna) == ("y", 2, 1)


def test_caractere_invalido_gera_token_erro_e_registra():
    tokens, lexer = tokenizar("int x = 10 @ 2;")
    assert "ERRO" in [t.classificacao for t in tokens]
    assert len(lexer.erros) == 1
    assert (lexer.erros[0].linha, lexer.erros[0].coluna) == (1, 12)


def test_verificar_levanta_o_primeiro_erro():
    _, lexer = tokenizar("# $")
    with pytest.raises(ErroLexico) as e:
        lexer.verificar()
    assert "'#'" in str(e.value)


def test_verificar_nao_levanta_sem_erros():
    _, lexer = tokenizar("int x = 1;")
    lexer.verificar()


def test_numero_malformado():
    tokens, lexer = tokenizar("12abc")
    assert len(tokens) == 1 and tokens[0].classificacao == "ERRO"
    assert "malformado" in lexer.erros[0].mensagem


def test_codigo_vazio():
    tokens, lexer = tokenizar("")
    assert tokens == [] and lexer.erros == []


def test_analisar_duas_vezes_nao_acumula():
    lexer = AutomatoLexico()
    lexer.analisar("@")
    lexer.analisar("int x;")
    assert lexer.erros == []
    assert len(lexer.tokens) == 3