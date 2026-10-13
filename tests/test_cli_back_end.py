from src.cli import main


def rodar(capsys, *flags):
    codigo = main(["cli", "examples/otimizacao.robot", *flags])
    return codigo, capsys.readouterr().out


def test_flag_ir_mostra_a_ir_sem_otimizar(capsys):
    codigo, saida = rodar(capsys, "--ir")
    assert codigo == 0
    assert "--- IR ---" in saida and "t1 = 10 + 20" in saida
    assert "--- Bytecode ---" not in saida


def test_flag_ir_opt_mostra_a_ir_otimizada(capsys):
    _, saida = rodar(capsys, "--ir-opt")
    assert "--- IR otimizada ---" in saida and "x = 30" in saida
    assert "t1 = 10 + 20" not in saida


def test_flag_bytecode_mostra_o_bytecode_com_enderecos(capsys):
    _, saida = rodar(capsys, "--bytecode")
    assert "--- Bytecode ---" in saida
    assert "  0  PUSH 30" in saida and "HALT" in saida


def test_sem_flags_nao_imprime_as_listas(capsys):
    _, saida = rodar(capsys)
    assert "---" not in saida