from src.compiler.codegen import InstrucaoBytecode as I
from src.compiler.pipeline import compilar
from src.vm.vm import MaquinaVirtual, dividir


def sem_sensores(nome):
    return 0


def vm_de(*instrucoes, sensores=sem_sensores, orcamento=50):
    """Monta uma VM a partir de pares (op, arg) escritos à mão."""
    programa = [I(*i) if isinstance(i, tuple) else I(i) for i in instrucoes]
    return MaquinaVirtual(programa, sensores, orcamento)


def vm_do_robo(corpo, sensores=sem_sensores):
    """Compila um robô com o pipeline completo e cria a VM com o bytecode."""
    resultado = compilar(f"robot R {{ {corpo} }}")
    assert resultado.pronto, resultado.erro
    return MaquinaVirtual(resultado.contexto.bytecode, sensores)


def acoes(vm, ticks):
    return [vm.executar_tick() for _ in range(ticks)]


def topo_depois(*instrucoes):
    vm = vm_de(*instrucoes, "HALT")
    vm.executar_tick()
    return vm.pilha[-1]


# pilha, memória e aritmética

def test_push_store_load():
    vm = vm_de(("PUSH", 7), ("STORE", 0), ("LOAD", 0), ("LOAD", 0), "HALT")
    vm.executar_tick()
    assert vm.memoria == [7]
    assert vm.pilha == [7, 7]


def test_memoria_comeca_em_zero():
    vm = vm_de(("LOAD", 2), "HALT")
    assert vm.memoria == [0, 0, 0]
    vm.executar_tick()
    assert vm.pilha == [0]


def test_aritmetica_respeita_a_ordem_dos_operandos():
    assert topo_depois(("PUSH", 10), ("PUSH", 3), "SUB") == 7
    assert topo_depois(("PUSH", 4), ("PUSH", 5), "MUL") == 20
    assert topo_depois(("PUSH", 10), ("PUSH", 3), "ADD") == 13


def test_divisao_trunca_em_direcao_a_zero():
    assert dividir(7, 2) == 3
    assert dividir(-7, 2) == -3
    assert dividir(7, -2) == -3
    assert dividir(-7, -2) == 3


def test_comparacoes_e_logicas_produzem_0_ou_1():
    assert topo_depois(("PUSH", 2), ("PUSH", 5), "LT") == 1
    assert topo_depois(("PUSH", 2), ("PUSH", 5), "GE") == 0
    assert topo_depois(("PUSH", 5), ("PUSH", 5), "EQ") == 1
    assert topo_depois(("PUSH", 3), ("PUSH", 0), "AND") == 0
    assert topo_depois(("PUSH", 3), ("PUSH", 0), "OR") == 1


def test_neg_e_not():
    assert topo_depois(("PUSH", 4), "NEG") == -4
    assert topo_depois(("PUSH", 0), "NOT") == 1
    assert topo_depois(("PUSH", 9), "NOT") == 0


# saltos e sensores

def test_jz_salta_so_quando_o_topo_e_zero():
    vm = vm_de(("PUSH", 0), ("JZ", 3), ("PUSH", 1), ("PUSH", 2), "HALT")
    vm.executar_tick()
    assert vm.pilha == [2]
    vm = vm_de(("PUSH", 5), ("JZ", 3), ("PUSH", 1), "HALT")
    vm.executar_tick()
    assert vm.pilha == [1]


def test_sense_le_o_sensor_pela_interface():
    lidos = []

    def sensores(nome):
        lidos.append(nome)
        return 42

    vm = vm_de(("SENSE", "enemy_distance"), "HALT", sensores=sensores)
    vm.executar_tick()
    assert lidos == ["enemy_distance"]
    assert vm.pilha == [42]


# ações e orçamento por tick

def test_uma_acao_por_tick():
    vm = vm_de(("PUSH", 30), "MOVE", "SCAN", ("PUSH", 3), "FIRE", "HALT")
    assert acoes(vm, 4) == [("move", 20), ("scan", None), ("fire", 3), None]


def test_argumento_e_ajustado_a_faixa():
    vm = vm_de(("PUSH", -500), "ROTATE", ("PUSH", 0), "FIRE", ("PUSH", 0), "BACK", "HALT")
    assert acoes(vm, 3) == [("rotate", -180), ("fire", 1), ("back", 1)]


def test_laco_sem_acao_para_no_orcamento():
    vm = vm_de(("JMP", 0))
    assert vm.executar_tick() is None
    assert vm.pc == 0
    assert not vm.parado


def test_orcamento_conta_instrucoes():
    vm = vm_de(("PUSH", 1), ("PUSH", 2), ("PUSH", 3), "MOVE", orcamento=3)
    assert vm.executar_tick() is None
    assert vm.executar_tick() == ("move", 3)


def test_halt_para_o_robo_para_sempre():
    vm = vm_de("SCAN", "HALT")
    assert acoes(vm, 3) == [("scan", None), None, None]
    assert vm.parado
    assert vm.erro is None


# erros de execução: param só este robô, sem derrubar a arena

def test_divisao_por_zero_para_o_robo():
    vm = vm_de(("PUSH", 1), ("PUSH", 0), "DIV", "SCAN")
    assert acoes(vm, 2) == [None, None]
    assert vm.parado
    assert "divisão por zero" in vm.erro


def test_pilha_vazia_e_erro():
    vm = vm_de("ADD")
    assert vm.executar_tick() is None
    assert "pilha vazia" in vm.erro


def test_salto_invalido_e_erro():
    vm = vm_de(("JMP", 99))
    assert vm.executar_tick() is None
    assert "fora do programa" in vm.erro


def test_instrucao_desconhecida_e_erro():
    vm = vm_de("PULAR")
    assert vm.executar_tick() is None
    assert "instrução desconhecida" in vm.erro


# integração com o compilador

def test_robo_compilado_executa_if_e_while():
    vm = vm_do_robo("int i = 0; while i < 3 { if i == 1 { scan(); } else { move(5); } i = i + 1; }")
    assert acoes(vm, 4) == [("move", 5), ("scan", None), ("move", 5), None]


def test_robo_compilado_usa_sensores():
    def sensores(nome):
        return {"enemy_visible": 1, "enemy_distance": 100}.get(nome, 0)

    vm = vm_do_robo("if enemy.visible { if enemy.distance < 150 { fire(3); } }", sensores)
    assert vm.executar_tick() == ("fire", 3)


def test_variavel_fora_da_faixa_e_ajustada():
    vm = vm_do_robo("int passo = 0; passo = 999; move(passo);")
    assert vm.executar_tick() == ("move", 20)