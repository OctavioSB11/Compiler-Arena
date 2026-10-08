import pytest

from src.compiler.lexer import AutomatoLexico
from src.compiler.parser import AnalisadorSintatico, ErroSintatico


def parse(codigo):
    tokens = AutomatoLexico().analisar(codigo)
    return AnalisadorSintatico(tokens).analisar()


def corpo(codigo):
    """Lista de comandos dentro do bloco do robô."""
    return parse(codigo).filhos[0].filhos


def expressao(texto):
    """AST da expressão de `int x = <texto>;`."""
    return corpo(f"robot R {{ int x = {texto}; }}")[0].filhos[1]


def erro_de(codigo):
    with pytest.raises(ErroSintatico) as e:
        parse(codigo)
    return e.value


# ---------- estrutura ----------

def test_robo_vazio():
    arvore = parse("robot R { }")
    assert arvore.tipo == "Robo" and arvore.valor == "R"
    assert arvore.filhos[0].tipo == "Bloco" and arvore.filhos[0].filhos == []


def test_declaracao_sem_e_com_valor():
    sem, com = corpo("robot R { int x; bool b = true; }")
    assert (sem.tipo, sem.valor, len(sem.filhos)) == ("Declaracao", "int", 1)
    assert (com.tipo, com.valor, len(com.filhos)) == ("Declaracao", "bool", 2)


def test_atribuicao():
    (no,) = corpo("robot R { x = 5; }")
    assert no.tipo == "Atribuicao"
    assert [f.tipo for f in no.filhos] == ["Identificador", "Numero"]


def test_chamada_sem_argumentos_e_com_varios():
    a, b = corpo("robot R { scan(); fire(1 + 1); }")
    assert (a.tipo, a.valor, a.filhos) == ("Chamada", "scan", [])
    assert (b.valor, len(b.filhos)) == ("fire", 1)


def test_if_com_else_e_else_if():
    (no,) = corpo("robot R { if a { } else if b { } else { } }")
    assert no.tipo == "Condicional" and len(no.filhos) == 3
    assert no.filhos[2].tipo == "Condicional"
    assert len(no.filhos[2].filhos) == 3


def test_if_sem_else():
    (no,) = corpo("robot R { if a { } }")
    assert len(no.filhos) == 2


def test_while_com_e_sem_parenteses():
    com, sem = corpo("robot R { while (a) { } while a { } }")
    assert com.tipo == sem.tipo == "Enquanto"


def test_blocos_aninhados():
    (externo,) = corpo("robot R { while a { if b { move(1); } } }")
    interno = externo.filhos[1].filhos[0]
    assert interno.tipo == "Condicional"


def test_sensor_acesso():
    no = expressao("enemy.distance")
    assert (no.tipo, no.valor) == ("Acesso", "enemy.distance")


def test_chamada_dentro_de_expressao():
    no = expressao("scan() + 1")
    assert no.valor == "+" and no.filhos[0].tipo == "Chamada"


# ---------- expressões ----------

def test_multiplicacao_antes_de_soma():
    no = expressao("1 + 2 * 3")
    assert no.valor == "+" and no.filhos[1].valor == "*"


def test_parenteses_mudam_a_precedencia():
    no = expressao("(1 + 2) * 3")
    assert no.valor == "*" and no.filhos[0].valor == "+"


def test_soma_e_associativa_a_esquerda():
    no = expressao("10 - 3 - 2")
    assert no.valor == "-" and no.filhos[0].valor == "-"
    assert no.filhos[1].valor == "2"


def test_e_logico_antes_de_ou_logico():
    no = expressao("a || b && c")
    assert no.valor == "||" and no.filhos[1].valor == "&&"


def test_relacional_antes_de_logico():
    no = expressao("a < 1 && b > 2")
    assert no.valor == "&&"
    assert [f.valor for f in no.filhos] == ["<", ">"]


def test_unarios():
    assert expressao("-x").valor == "-unario"
    assert expressao("!ativo").valor == "!unario"
    assert expressao("!!a").filhos[0].valor == "!unario"


def test_menos_unario_e_binario():
    no = expressao("a - -b")
    assert no.valor == "-" and no.filhos[1].valor == "-unario"


def test_booleanos():
    assert expressao("true").tipo == "Booleano"
    assert expressao("false").valor == "false"


def test_posicao_dos_nos():
    arvore = parse("robot R {\n  int x;\n}")
    decl = arvore.filhos[0].filhos[0]
    assert (decl.linha, decl.coluna) == (2, 7)


# ---------- erros ----------

def test_erro_ponto_e_virgula_ausente():
    e = erro_de("robot R {\n  int x = 10\n  move(x);\n}")
    assert e.token.linha == 3 and "';'" in e.mensagem


def test_erro_robot_sem_nome():
    e = erro_de("robot { }")
    assert "nome do robô" in e.mensagem


def test_erro_programa_nao_comeca_com_robot():
    e = erro_de("int x;")
    assert "'robot'" in e.mensagem


def test_erro_chave_nao_fechada():
    e = erro_de("robot R { if a { move(1); }")
    assert "'}'" in e.mensagem and "fim do arquivo" in str(e)


def test_erro_expressao_incompleta():
    e = erro_de("robot R { int x = ; }")
    assert e.token.lexema == ";"


def test_erro_relacional_nao_associa():
    erro_de("robot R { x = 1 < 2 < 3; }")


def test_erro_texto_depois_do_robo():
    e = erro_de("robot R { } int x;")
    assert "fim do arquivo" in e.mensagem


def test_erro_if_sem_bloco():
    erro_de("robot R { if a move(1); }")


def test_erro_campo_de_sensor_ausente():
    e = erro_de("robot R { int x = enemy.; }")
    assert "campo" in e.mensagem


def test_erro_token_invalido_do_lexico_interrompe_o_parser():
    e = erro_de("robot R { int x = 1 @ 2; }")
    assert "inválido" in e.mensagem


def test_erro_arquivo_vazio():
    e = erro_de("")
    assert "vazio" in str(e)


def test_erro_comando_desconhecido_comeca_com_numero():
    e = erro_de("robot R { 5 = x; }")
    assert "declaração, atribuição, chamada" in e.mensagem