"""Uso: python -m src.arena robo1.robot robo2.robot [...] [--texto] [--demo]

Compila cada robô e inicia a batalha. Robô com erro de compilação aparece no
painel, mas não entra na arena.

--texto  roda sem janela e imprime o painel de cada robô e o resultado
--demo   troca a VM por ações fixas, só para ver a arena antes da VM ficar pronta
"""
import sys
from itertools import cycle

from ..compiler.pipeline import formatar_painel
from .arena import preparar_batalha, texto_resultado

ROTEIRO_DEMO = [("scan", None), ("move", 10), ("rotate", 20), ("fire", 1)]


class VMDemo:
    """Substituta temporária da VM: ignora o bytecode e repete ROTEIRO_DEMO."""

    def __init__(self, bytecode, obter_sensor):
        self._acoes = cycle(ROTEIRO_DEMO)

    def executar_tick(self):
        return next(self._acoes)


def criar_vm(bytecode, obter_sensor):
    from ..vm.vm import MaquinaVirtual  # contrato 5.6: módulo da VM
    return MaquinaVirtual(bytecode, obter_sensor)


def rodar_em_texto(arena, participantes) -> None:
    for participante in participantes:
        print(formatar_painel(participante.resultado), end="\n\n")
    vencedor = arena.rodar()
    print(f"--- Fim da batalha no tick {arena.tick} ---")
    for robo in arena.robos:
        print(f"{robo.nome:<12} energia {robo.energia:>3}  {'vivo' if robo.vivo else 'eliminado'}")
    print(texto_resultado(arena, vencedor))


def main(argv) -> int:
    arquivos = [a for a in argv[1:] if not a.startswith("--")]
    if not arquivos:
        print(__doc__)
        return 2
    codigos = []
    for caminho in arquivos:
        with open(caminho, encoding="utf-8") as f:
            codigos.append(f.read())
    fabrica = VMDemo if "--demo" in argv else criar_vm
    try:
        arena, participantes = preparar_batalha(codigos, fabrica)
    except ModuleNotFoundError as erro:
        if erro.name not in ("src.vm", "src.vm.vm"):
            raise  # erro de import dentro da VM: mostra o erro real
        print("A VM (src/vm/vm.py) ainda não existe. Use --demo para ver a arena.")
        return 1
    if "--texto" in argv:
        rodar_em_texto(arena, participantes)
    else:
        from .ui import Interface  # só exige pygame quando há janela
        Interface(arena, participantes).rodar()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
