from src.compiler.codegen import (InstrucaoBytecode, formatar_bytecode,
                                  gerar_bytecode)
from src.compiler.ir import Instrucao, gerar_ir
from src.compiler.lexer import AutomatoLexico
from src.compiler.optimizer import otimizar
from src.compiler.parser import AnalisadorSintatico


def bytecode_de(codigo, otimiza=False):
    """Compila o texto de um robô até o bytecode e devolve uma linha por instrução."""
    tokens = AutomatoLexico().analisar(f"robot R {{ {codigo} }}")
    ir = gerar_ir(AnalisadorSintatico(tokens).analisar())
    if otimiza:
        ir = otimizar(ir)
    return formatar_bytecode(gerar_bytecode(ir)).splitlines()


def test_programa_termina_com_halt():
    assert bytecode_de("") == ["HALT"]


def test_exemplo_do_enunciado_move_scan_fire():
    assert bytecode_de("move(30); scan(); fire(3);") == [
        "PUSH 30", "MOVE", "SCAN", "PUSH 3", "FIRE", "HALT"]


def test_variavel_recebe_indice_fixo():
    assert bytecode_de("int x = 5; int y = x;") == [
        "PUSH 5", "STORE 0", "LOAD 0", "STORE 1", "HALT"]


def test_expressao_aritmetica():
    assert bytecode_de("int x = 10 + 20;") == [
        "PUSH 10", "PUSH 20", "ADD", "STORE 0", "LOAD 0", "STORE 1", "HALT"]


def test_todos_os_operadores_binarios():
    pares = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV"}
    for operador, instrucao in pares.items():
        assert instrucao in bytecode_de(f"int a = 8; int b = a {operador} 2;")
    relacionais = {"<": "LT", ">": "GT", "<=": "LE", ">=": "GE",
                   "==": "EQ", "!=": "NE"}
    for operador, instrucao in relacionais.items():
        assert instrucao in bytecode_de(f"int a = 8; bool b = a {operador} 2;")
    assert "AND" in bytecode_de("bool a = true; bool b = a && a;")
    assert "OR" in bytecode_de("bool a = true; bool b = a || a;")


def test_operadores_unarios():
    linhas = bytecode_de("int x = -5; bool b = !true;")
    assert "NEG" in linhas and "NOT" in linhas


def test_sensores_usam_os_nomes_do_contrato():
    linhas = bytecode_de(
        "int a = energy; int b = position.x; int c = position.y;"
        "bool d = enemy.visible; int e = enemy.distance; int f = enemy.direction;")
    sensores = [l for l in linhas if l.startswith("SENSE")]
    assert sensores == [
        "SENSE energy", "SENSE pos_x", "SENSE pos_y",
        "SENSE enemy_visible", "SENSE enemy_distance", "SENSE enemy_direction"]


def test_if_vira_jz_com_endereco_numerico():
    linhas = bytecode_de("bool b = true; if b { move(1); }")
    destino = int(next(l for l in linhas if l.startswith("JZ")).split()[1])
    assert linhas[destino] == "HALT"


def test_while_volta_para_o_inicio():
    linhas = bytecode_de("while true { move(1); }")
    salto = next(l for l in linhas if l.startswith("JMP"))
    assert int(salto.split()[1]) == 0


def test_nao_sobra_nome_de_rotulo_no_bytecode():
    linhas = bytecode_de("bool b = true; if b { move(1); } else { move(2); }")
    assert not any("L1" in l or "L2" in l for l in linhas)
    for l in linhas:
        if l.startswith(("JMP", "JZ")):
            assert l.split()[1].isdigit()


def test_ir_otimizada_gera_bytecode_menor():
    codigo = "int x = 10 + 20; move(x);"
    assert len(bytecode_de(codigo, True)) < len(bytecode_de(codigo))


def test_instrucao_desconhecida_da_erro():
    try:
        gerar_bytecode([Instrucao("XYZ")])
    except ValueError:
        return
    raise AssertionError("era esperado ValueError")


def test_formatar_com_enderecos():
    texto = formatar_bytecode([InstrucaoBytecode("PUSH", 1),
                               InstrucaoBytecode("HALT")], com_enderecos=True)
    assert texto.splitlines() == ["  0  PUSH 1", "  1  HALT"]