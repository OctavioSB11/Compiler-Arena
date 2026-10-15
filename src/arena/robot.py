"""Robô da arena: estado físico, sensores e a VM que executa o seu bytecode.

O robô não conhece o código-fonte. Ele guarda a VM e responde às leituras
que ela faz por `obter_sensor(nome)` (contrato 5.6). As regras de movimento,
`scan` e `fire` ficam na arena.
"""
from dataclasses import dataclass
from typing import Any

ENERGIA_INICIAL = 100

# nome do sensor no bytecode (SENSE nome) -> atributo do robô
SENSORES = {
    "energy": "energia",
    "pos_x": "x",
    "pos_y": "y",
    "enemy_visible": "inimigo_visivel",
    "enemy_distance": "inimigo_distancia",
    "enemy_direction": "inimigo_direcao",
}


@dataclass
class Robo:
    nome: str
    x: float
    y: float
    direcao: float  # graus: 0 aponta para +x e cresce no sentido horário
    energia: int = ENERGIA_INICIAL
    vm: Any = None
    inimigo_visivel: bool = False  # atualizados só pelo scan()
    inimigo_distancia: int = 0
    inimigo_direcao: int = 0

    @property
    def vivo(self) -> bool:
        return self.energia > 0

    def obter_sensor(self, nome: str) -> int:
        """Leitura feita pela VM. `true` é 1 e `false` é 0, como no bytecode."""
        if nome not in SENSORES:
            raise ValueError(f"sensor desconhecido: {nome}")
        return int(round(getattr(self, SENSORES[nome])))
