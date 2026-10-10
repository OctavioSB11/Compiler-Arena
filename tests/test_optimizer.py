from src.compiler.ir import Instrucao, formatar_ir, gerar_ir
from src.compiler.lexer import AutomatoLexico
from src.compiler.optimizer import TECNICAS, otimizar
from src.compiler.parser import AnalisadorSintatico


def ir_de(codigo):
    """Compila o texto de um robô até a IR (sem otimizar)."""
    tokens = AutomatoLexico().analisar(f"robot R {{ {codigo} }}")
    return gerar_ir(AnalisadorSintatico(tokens).analisar())


def otimizado(codigo, tecnicas=None):
    return formatar_ir(otimizar(ir_de(codigo), tecnicas)).splitlines()


def test_exemplo_do_guia_fica_com_tres_linhas():
    assert otimizado("int x = 10 + 20; move(x);") == [
        "x = 30", "param x", "call move, 1"]


def test_dobrar_constantes_sozinha():
    # sem propagar, só a conta com dois números vira constante
    assert otimizado("int x = 2 * 3 + 4;", ["dobrar_constantes"]) == [
        "t1 = 6", "t2 = t1 + 4", "x = t2"]


def test_dobrar_constantes_em_operadores_unarios():
    assert otimizado("int x = -5; bool b = !true;", ["dobrar_constantes"]) == [
        "t1 = -5", "x = t1", "t2 = 0", "b = t2"]


def test_dobrar_constantes_em_comparacoes():
    assert otimizado("bool b = 3 < 5;", ["dobrar_constantes"]) == [
        "t1 = 1", "b = t1"]


def test_divisao_inteira_trunca_para_zero():
    assert otimizado("int x = -7 / 2;") == ["x = -3"]


def test_divisao_por_zero_e_preservada():
    codigo = otimizado("int x = 5 / 0;")
    assert any("/" in linha for linha in codigo)


def test_simplificar_algebra_soma_e_multiplicacao_por_identidade():
    assert otimizado("int a = 1; int b = a + 0; int c = b * 1;",
                     ["simplificar_algebra"])[-4:] == [
        "t1 = a", "b = t1", "t2 = b", "c = t2"]


def test_simplificar_algebra_multiplicacao_por_zero():
    linhas = otimizado("int a = 7; int b = a * 0;", ["simplificar_algebra"])
    assert "t1 = 0" in linhas


def test_propagar_constantes_sozinha():
    linhas = otimizado("int x = 1 + 2; move(x);", ["dobrar_constantes",
                                                     "propagar_constantes"])
    assert "x = 3" in linhas


def test_eliminar_temporarios_remove_calculo_sem_uso():
    ir = [Instrucao("BINOP", 1, 2, "t1", "+"),
          Instrucao("COPY", 5, None, "x")]
    assert formatar_ir(otimizar(ir, ["eliminar_temporarios"])) == "x = 5"


def test_simplificar_saltos_if_true_remove_teste():
    linhas = otimizado("if true { move(1); }", ["dobrar_constantes",
                                                  "propagar_constantes",
                                                  "simplificar_saltos"])
    assert not any(l.startswith("ifFalse") for l in linhas)


def test_while_true_nao_perde_o_laco():
    linhas = otimizado("while true { move(1); }")
    assert "goto L1" in linhas
    assert "L1:" in linhas


def test_sensor_nao_e_removido_quando_usado():
    linhas = otimizado("int d = enemy.distance; move(d);")
    assert any("sensor enemy.distance" in l for l in linhas)


def test_cada_tecnica_pode_ser_ligada_sozinha():
    ir = ir_de("int x = 10 + 20; move(x);")
    for nome in TECNICAS:
        assert isinstance(otimizar(ir, [nome]), list)


def test_otimizar_e_idempotente():
    uma = otimizar(ir_de("int x = 10 + 20; move(x + 0);"))
    duas = otimizar(uma)
    assert uma == duas


def test_otimizar_nao_altera_a_lista_original():
    ir = ir_de("int x = 10 + 20;")
    copia = list(ir)
    otimizar(ir)
    assert ir == copia