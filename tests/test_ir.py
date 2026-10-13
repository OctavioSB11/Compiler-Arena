from src.compiler.ir import Instrucao, formatar_ir, gerar_ir
from src.compiler.lexer import AutomatoLexico
from src.compiler.parser import AnalisadorSintatico


def ir_de(codigo):
    """Compila o texto de um robô até a IR e devolve a lista de instruções."""
    tokens = AutomatoLexico().analisar(f"robot R {{ {codigo} }}")
    return gerar_ir(AnalisadorSintatico(tokens).analisar())


def texto(codigo):
    return formatar_ir(ir_de(codigo)).splitlines()


def test_exemplo_do_guia():
    assert texto("int x = 10 + 20; move(x);") == [
        "t1 = 10 + 20", "x = t1", "param x", "call move, 1"]


def test_declaracao_sem_valor_comeca_em_zero():
    assert texto("int x; bool b;") == ["x = 0", "b = 0"]


def test_booleanos_viram_um_e_zero():
    assert texto("bool a = true; bool b = false;") == ["a = 1", "b = 0"]


def test_precedencia_multiplicacao_antes_da_soma():
    assert texto("int x = 1 + 2 * 3;") == ["t1 = 2 * 3", "t2 = 1 + t1", "x = t2"]


def test_operadores_unarios():
    assert texto("int x = -5; bool b = !true;") == [
        "t1 = neg 5", "x = t1", "t2 = not 1", "b = t2"]


def test_sensores():
    assert texto("int d = enemy.distance; int e = energy;") == [
        "t1 = sensor enemy.distance", "d = t1", "t2 = sensor energy", "e = t2"]


def test_chamada_sem_argumento_e_com_argumento():
    assert texto("scan(); fire(3);") == ["call scan, 0", "param 3", "call fire, 1"]


def test_if_sem_else():
    assert texto("int x; if x > 1 { move(1); }") == [
        "x = 0", "t1 = x > 1", "ifFalse t1 goto L1",
        "param 1", "call move, 1", "L1:"]


def test_if_com_else():
    assert texto("bool b = true; if b { move(1); } else { move(2); }") == [
        "b = 1", "ifFalse b goto L1", "param 1", "call move, 1", "goto L2",
        "L1:", "param 2", "call move, 1", "L2:"]


def test_else_if_encadeado():
    codigo = texto("bool a = true; bool b = true;"
                   " if a { move(1); } else if b { move(2); } else { move(3); }")
    assert codigo.count("goto L2") == 1 and codigo[-1] == "L2:"
    assert sum(1 for linha in codigo if linha.endswith(":")) == 4


def test_while():
    assert texto("int x; while x < 3 { x = x + 1; }") == [
        "x = 0", "L1:", "t1 = x < 3", "ifFalse t1 goto L2",
        "t2 = x + 1", "x = t2", "goto L1", "L2:"]


def test_variavel_com_mesmo_nome_em_blocos_diferentes_nao_se_mistura():
    codigo = texto("int x = 1; if true { int x = 2; move(x); } move(x);")
    assert "x = 1" in codigo and "x_1 = 2" in codigo
    assert codigo.index("param x_1") < codigo.index("param x")


def test_nome_de_variavel_parecido_com_temporario_e_renomeado():
    assert texto("int t1 = 5;") == ["v_t1 = 5"]


def test_instrucao_e_uma_tupla_com_quatro_campos_principais():
    primeira = ir_de("int x = 7;")[0]
    assert isinstance(primeira, Instrucao)
    assert tuple(primeira[:4]) == ("COPY", 7, None, "x")


def test_gerar_ir_pode_ser_chamado_duas_vezes():
    assert texto("int x = 1;") == texto("int x = 1;") == ["x = 1"]