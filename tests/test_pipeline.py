from src.compiler import pipeline
from src.compiler.pipeline import ERRO, OK, PENDENTE, PULADA, compilar, formatar_painel

ROBO_OK = "robot Alpha { int x = 1; move(x); }"


def status(resultado):
    return [e.status for e in resultado.etapas]


def test_programa_valido_passa_pelas_etapas_implementadas():
    r = compilar(ROBO_OK)
    assert status(r)[:2] == [OK, OK]
    assert r.ok and r.contexto.ast.valor == "Alpha"


def test_etapas_futuras_aparecem_como_pendentes():
    r = compilar(ROBO_OK)
    assert status(r)[2:] == [PENDENTE] * 4
    assert not r.pronto


def test_erro_lexico_interrompe_e_pula_o_resto():
    r = compilar("robot R { int x = 1 @ 2; }")
    assert status(r) == [ERRO] + [PULADA] * 5
    assert r.erro.nome == "Análise Léxica" and r.erro.linha == 1
    assert not r.ok


def test_erro_sintatico_interrompe_depois_do_lexico():
    r = compilar("robot R {\n  int x = 10\n  move(x);\n}")
    assert status(r)[:2] == [OK, ERRO]
    assert status(r)[2:] == [PULADA] * 4
    assert r.erro.linha == 3


def test_painel_de_programa_valido():
    painel = formatar_painel(compilar(ROBO_OK))
    assert "ROBÔ: ALPHA" in painel
    assert "✓ Análise Léxica" in painel and "✓ Análise Sintática" in painel
    assert "- Análise Semântica (pendente)" in painel
    assert "EM CONSTRUÇÃO" in painel


def test_painel_de_erro_mostra_linha_e_interrompe():
    painel = formatar_painel(compilar("robot R {\n  int x = 10\n  move(x);\n}"))
    assert "✗ Análise Sintática" in painel
    assert "Linha 3:" in painel
    assert "COMPILAÇÃO INTERROMPIDA" in painel
    assert "A arena não executa o robô." in painel


def test_painel_sem_nome_quando_nao_chega_a_sintaxe():
    painel = formatar_painel(compilar("@"))
    assert "ROBÔ: (sem nome)" in painel


def test_etapa_registrada_vira_ok_e_pronto(monkeypatch):
    # simula as etapas futuras já implementadas
    etapas = [(nome, funcao or (lambda ctx: ctx)) for nome, funcao in pipeline.ETAPAS]
    monkeypatch.setattr(pipeline, "ETAPAS", etapas)
    r = compilar(ROBO_OK)
    assert r.pronto
    assert "STATUS: PRONTO PARA BATALHA" in formatar_painel(r)