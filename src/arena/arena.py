"""Arena: regras da batalha (seção 5.7 do guia) e escalonador por ticks.

A cada tick a arena percorre os robôs vivos em ordem fixa e pede à VM de cada
um para executar (`vm.executar_tick()`). A VM devolve uma ação `(nome,
argumento)` ou `None` (orçamento esgotado ou HALT) e a arena aplica a ação.
A arena só recebe bytecode já compilado: nunca vê nem executa o código-fonte.
Não há aleatoriedade, então a mesma entrada sempre gera a mesma batalha.
"""
import math
from typing import Callable, List, NamedTuple, Optional

from ..compiler.pipeline import ResultadoCompilacao, compilar
from .robot import Robo

TAMANHO = 1000
MAX_TICKS = 2000
RAIO_INICIAL = 400  # distância do centro em que os robôs começam
ALCANCE_SCAN, ABERTURA_SCAN = 400, 30
ALCANCE_TIRO, ABERTURA_TIRO = 500, 10
DANO_POR_POTENCIA = 4

# faixas aplicadas em tempo de execução (argumento vindo de variável)
LIMITES = {"move": (1, 20), "back": (1, 20), "rotate": (-180, 180), "fire": (1, 3)}

# criar_vm(bytecode, obter_sensor) -> objeto com executar_tick()
FabricaVM = Callable[[list, Callable[[str], int]], object]


class Tiro(NamedTuple):
    atirador: Robo
    alvo: Optional[Robo]
    x_fim: float
    y_fim: float


class Participante(NamedTuple):
    """Robô inscrito na batalha. `robo` é None se a compilação falhou."""
    resultado: ResultadoCompilacao
    robo: Optional[Robo]


def limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def angulo_ate(origem: Robo, alvo: Robo) -> float:
    """Direção absoluta (0 a 360) de `origem` até `alvo`."""
    return math.degrees(math.atan2(alvo.y - origem.y, alvo.x - origem.x)) % 360


def diferenca_angular(a: float, b: float) -> float:
    """Menor diferença entre dois ângulos, de 0 a 180."""
    return abs((a - b + 180) % 360 - 180)


def posicoes_iniciais(quantidade: int) -> List[tuple]:
    """Posições `(x, y, direcao)` em círculo, simétricas e voltadas ao centro."""
    centro = TAMANHO / 2
    posicoes = []
    for i in range(quantidade):
        angulo = 180 + 360 * i / quantidade
        x = round(centro + RAIO_INICIAL * math.cos(math.radians(angulo)))
        y = round(centro + RAIO_INICIAL * math.sin(math.radians(angulo)))
        posicoes.append((x, y, (angulo + 180) % 360))
    return posicoes


class Arena:
    def __init__(self, robos: List[Robo]):
        self.robos = robos
        self.tick = 0
        self.tiros: List[Tiro] = []  # tiros do último tick, para a interface

    @property
    def vivos(self) -> List[Robo]:
        return [r for r in self.robos if r.vivo]

    @property
    def terminou(self) -> bool:
        return len(self.vivos) <= 1 or self.tick >= MAX_TICKS

    @property
    def vencedor(self) -> Optional[Robo]:
        """Último vivo ou, no limite de ticks, quem tem mais energia. None é empate."""
        vivos = self.vivos
        if not self.terminou or not vivos:
            return None
        maior = max(r.energia for r in vivos)
        lideres = [r for r in vivos if r.energia == maior]
        return lideres[0] if len(lideres) == 1 else None

    def executar_tick(self) -> None:
        if self.terminou:
            return
        self.tick += 1
        self.tiros = []
        for robo in self.robos:
            if robo.vivo:  # quem foi eliminado neste tick já não age
                acao = robo.vm.executar_tick()
                if acao is not None:
                    self.aplicar(robo, *acao)

    def rodar(self) -> Optional[Robo]:
        while not self.terminou:
            self.executar_tick()
        return self.vencedor

    def aplicar(self, robo: Robo, nome: str, argumento: Optional[int] = None) -> None:
        nome = nome.lower()
        if nome in LIMITES:
            argumento = limitar(argumento, *LIMITES[nome])
        if nome == "move":
            self._mover(robo, argumento)
        elif nome == "back":
            self._mover(robo, -argumento)
        elif nome == "rotate":
            robo.direcao = (robo.direcao + argumento) % 360
        elif nome == "scan":
            self._scan(robo)
        elif nome == "fire":
            self._atirar(robo, argumento)
        else:
            raise ValueError(f"ação desconhecida: {nome}")

    def _mover(self, robo: Robo, distancia: int) -> None:
        rad = math.radians(robo.direcao)
        robo.x = limitar(robo.x + distancia * math.cos(rad), 0, TAMANHO)
        robo.y = limitar(robo.y + distancia * math.sin(rad), 0, TAMANHO)

    def _mais_proximo(self, robo: Robo, alcance: float, abertura: float) -> Optional[Robo]:
        """Inimigo vivo mais próximo dentro do cone (alcance e ±abertura graus).

        Empate de distância fica com quem vem antes na lista (determinismo).
        """
        candidatos = []
        for i, outro in enumerate(self.robos):
            if outro is robo or not outro.vivo:
                continue
            distancia = math.hypot(outro.x - robo.x, outro.y - robo.y)
            if distancia <= alcance and diferenca_angular(angulo_ate(robo, outro), robo.direcao) <= abertura:
                candidatos.append((distancia, i))
        return self.robos[min(candidatos)[1]] if candidatos else None

    def _scan(self, robo: Robo) -> None:
        alvo = self._mais_proximo(robo, ALCANCE_SCAN, ABERTURA_SCAN)
        robo.inimigo_visivel = alvo is not None
        if alvo is None:
            robo.inimigo_distancia = robo.inimigo_direcao = 0
        else:
            robo.inimigo_distancia = round(math.hypot(alvo.x - robo.x, alvo.y - robo.y))
            robo.inimigo_direcao = round(angulo_ate(robo, alvo)) % 360

    def _atirar(self, robo: Robo, potencia: int) -> None:
        robo.energia = max(0, robo.energia - potencia)
        alvo = self._mais_proximo(robo, ALCANCE_TIRO, ABERTURA_TIRO)
        if alvo is not None:
            alvo.energia = max(0, alvo.energia - DANO_POR_POTENCIA * potencia)
            self.tiros.append(Tiro(robo, alvo, alvo.x, alvo.y))
        else:
            rad = math.radians(robo.direcao)
            self.tiros.append(Tiro(robo, None, robo.x + ALCANCE_TIRO * math.cos(rad),
                                   robo.y + ALCANCE_TIRO * math.sin(rad)))


def texto_resultado(arena: Arena, vencedor: Optional[Robo]) -> str:
    """Linha final da batalha, usada pela janela e pelo modo texto."""
    if not arena.robos:
        return "NENHUM ROBÔ PRONTO PARA BATALHA"
    return f"VENCEDOR: {vencedor.nome.upper()}" if vencedor else "EMPATE"


def preparar_batalha(codigos: List[str], criar_vm: FabricaVM) -> tuple:
    """Compila cada código e monta a arena só com os robôs prontos.

    Devolve `(arena, participantes)`. Robô com erro de compilação aparece nos
    participantes (para o painel), mas não entra na arena (regra 4 do guia).
    """
    resultados = [compilar(codigo) for codigo in codigos]
    posicoes = iter(posicoes_iniciais(sum(r.pronto for r in resultados)))
    participantes = []
    for resultado in resultados:
        robo = None
        if resultado.pronto:
            robo = Robo(resultado.contexto.ast.valor, *next(posicoes))
            robo.vm = criar_vm(resultado.contexto.bytecode, robo.obter_sensor)
        participantes.append(Participante(resultado, robo))
    arena = Arena([p.robo for p in participantes if p.robo is not None])
    return arena, participantes
