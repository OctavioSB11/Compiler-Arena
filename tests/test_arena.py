import pytest

from src.arena.arena import (ALCANCE_SCAN, DANO_POR_POTENCIA, MAX_TICKS, TAMANHO,
                             Arena, diferenca_angular, posicoes_iniciais,
                             preparar_batalha, texto_resultado)
from src.arena.robot import Robo


class VMFalsa:
    """Devolve as ações da lista, uma por tick, e depois None (como um HALT)."""

    def __init__(self, acoes=()):
        self.acoes = list(acoes)
        self.chamadas = 0

    def executar_tick(self):
        self.chamadas += 1
        return self.acoes.pop(0) if self.acoes else None


def robo(nome, x, y, direcao, acoes=(), energia=100):
    return Robo(nome, x, y, direcao, energia, VMFalsa(acoes))


def test_sensores_usam_os_nomes_do_bytecode():
    r = Robo("R", 100.4, 899.6, 0, inimigo_visivel=True, inimigo_distancia=50)
    assert r.obter_sensor("energy") == 100
    assert (r.obter_sensor("pos_x"), r.obter_sensor("pos_y")) == (100, 900)
    assert r.obter_sensor("enemy_visible") == 1
    assert r.obter_sensor("enemy_distance") == 50
    with pytest.raises(ValueError):
        r.obter_sensor("xyz")


def test_posicoes_iniciais_simetricas_e_voltadas_ao_centro():
    assert posicoes_iniciais(2) == [(100, 500, 0), (900, 500, 180)]
    for x, y, direcao in posicoes_iniciais(4):
        assert diferenca_angular(direcao, 0) in (0, 90, 180)
        assert 0 <= x <= TAMANHO and 0 <= y <= TAMANHO


def test_move_back_e_rotate():
    a = robo("A", 500, 500, 0, [("move", 20), ("rotate", 90), ("move", 10), ("back", 5)])
    arena = Arena([a, robo("B", 0, 0, 0)])
    for _ in range(4):
        arena.executar_tick()
    assert (round(a.x), round(a.y), a.direcao) == (520, 505, 90)


def test_rotate_negativo_da_volta():
    a = robo("A", 500, 500, 10, [("rotate", -30)])
    Arena([a, robo("B", 0, 0, 0)]).executar_tick()
    assert a.direcao == 340


def test_parede_limita_o_movimento():
    a = robo("A", 995, 3, 0, [("move", 20), ("rotate", -90), ("move", 20)])
    arena = Arena([a, robo("B", 0, 500, 0)])
    for _ in range(3):
        arena.executar_tick()
    assert (round(a.x), round(a.y)) == (TAMANHO, 0)


def test_argumento_fora_da_faixa_e_ajustado():
    a = robo("A", 500, 500, 0, [("move", 999), ("rotate", 500)])
    arena = Arena([a, robo("B", 0, 0, 0)])
    arena.executar_tick()
    arena.executar_tick()
    assert (a.x, a.direcao) == (520, 180)


def test_nome_da_acao_em_maiusculas_tambem_vale():
    a = robo("A", 500, 500, 0, [("MOVE", 10)])
    Arena([a, robo("B", 0, 0, 0)]).executar_tick()
    assert a.x == 510


def test_acao_desconhecida_da_erro():
    a = robo("A", 0, 0, 0)
    with pytest.raises(ValueError):
        Arena([a]).aplicar(a, "voar", 1)


def test_scan_ve_inimigo_no_cone():
    a = robo("A", 100, 500, 0, [("scan", None)])
    b = robo("B", 400, 500, 180)
    Arena([a, b]).executar_tick()
    assert a.inimigo_visivel and a.inimigo_distancia == 300 and a.inimigo_direcao == 0


def test_scan_nao_ve_fora_do_angulo_ou_do_alcance():
    a = robo("A", 100, 500, 90, [("scan", None)])  # olhando para baixo
    Arena([a, robo("B", 400, 500, 0)]).executar_tick()
    assert not a.inimigo_visivel
    c = robo("C", 100, 500, 0, [("scan", None)])
    Arena([c, robo("D", 100 + ALCANCE_SCAN + 1, 500, 0)]).executar_tick()
    assert not c.inimigo_visivel


def test_scan_escolhe_o_mais_proximo():
    a = robo("A", 100, 500, 0, [("scan", None)])
    Arena([a, robo("Longe", 450, 500, 0), robo("Perto", 200, 520, 0)]).executar_tick()
    assert a.inimigo_distancia == 102


def test_fire_custa_energia_e_causa_dano():
    a = robo("A", 100, 500, 0, [("fire", 3)])
    b = robo("B", 300, 500, 180)
    arena = Arena([a, b])
    arena.executar_tick()
    assert a.energia == 97 and b.energia == 100 - DANO_POR_POTENCIA * 3
    assert arena.tiros[0].alvo is b


def test_fire_errado_so_custa_energia():
    a = robo("A", 100, 500, 90, [("fire", 2)])
    b = robo("B", 300, 500, 180)
    arena = Arena([a, b])
    arena.executar_tick()
    assert a.energia == 98 and b.energia == 100
    assert arena.tiros[0].alvo is None


def test_eliminado_nao_age_e_batalha_termina():
    a = robo("A", 100, 500, 0, [("fire", 3)])
    b = robo("B", 300, 500, 180, [("move", 10)], energia=10)
    arena = Arena([a, b])
    arena.executar_tick()
    assert not b.vivo and b.x == 300 and b.vm.chamadas == 0
    assert arena.terminou and arena.vencedor is a


def test_limite_de_ticks_vence_quem_tem_mais_energia():
    a = robo("A", 100, 500, 0, energia=80)
    b = robo("B", 900, 500, 180, energia=60)
    arena = Arena([a, b])
    assert arena.rodar() is a and arena.tick == MAX_TICKS


def test_empate_no_limite_de_ticks():
    arena = Arena([robo("A", 100, 500, 0), robo("B", 900, 500, 180)])
    assert arena.rodar() is None


def test_tick_depois_do_fim_nao_faz_nada():
    arena = Arena([robo("A", 100, 500, 0, [("move", 5)])])
    arena.executar_tick()
    assert arena.tick == 0


def test_mesma_entrada_gera_mesma_batalha():
    def batalha():
        acoes = [("scan", None), ("move", 7), ("rotate", 13), ("fire", 2)] * 40
        arena = Arena([robo("A", 100, 500, 0, acoes), robo("B", 900, 500, 180, acoes)])
        arena.rodar()
        return [(r.x, r.y, r.direcao, r.energia) for r in arena.robos], arena.tick
    assert batalha() == batalha()


def test_preparar_batalha_so_inscreve_robos_prontos():
    codigos = ["robot Alpha { move(1); }",
               "robot Beta { fire(200); }",
               "robot Gama { rotate(10); }"]
    criadas = []

    def criar_vm(bytecode, obter_sensor):
        criadas.append(bytecode)
        return VMFalsa()

    arena, participantes = preparar_batalha(codigos, criar_vm)
    assert [r.nome for r in arena.robos] == ["Alpha", "Gama"]
    assert participantes[1].robo is None and participantes[1].resultado.erro is not None
    assert len(criadas) == 2 and str(criadas[0][-1]) == "HALT"
    assert [(r.x, r.y) for r in arena.robos] == [(100, 500), (900, 500)]


def test_resultado_sem_robos_prontos():
    arena, _ = preparar_batalha(["robot A { fire(9); }"], lambda b, s: VMFalsa())
    assert arena.terminou and texto_resultado(arena, arena.vencedor) == "NENHUM ROBÔ PRONTO PARA BATALHA"
    vencida = Arena([robo("A", 0, 0, 0), robo("B", 9, 0, 0, energia=0)])
    assert texto_resultado(vencida, vencida.vencedor) == "VENCEDOR: A"


def test_vm_le_sensores_pelo_robo():
    lidos = {}

    def criar_vm(bytecode, obter_sensor):
        lidos["energy"] = obter_sensor("energy")
        return VMFalsa()

    preparar_batalha(["robot A { scan(); }"], criar_vm)
    assert lidos == {"energy": 100}
