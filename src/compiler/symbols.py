from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Simbolo:
    nome: str
    tipo: str
    linha_declaracao: int


@dataclass
class Escopo:
    pai: Optional["Escopo"] = None
    simbolos: Dict[str, Simbolo] = field(default_factory=dict)

    def declarar(self, simbolo: Simbolo) -> None:
        self.simbolos[simbolo.nome] = simbolo

    def resolver_local(self, nome: str) -> Optional[Simbolo]:
        return self.simbolos.get(nome)


class TabelaDeSimbolos:
    def __init__(self):
        self._pilha: List[Escopo] = [Escopo()]
        self._todas_declaradas: Dict[str, Simbolo] = {}

    @property
    def escopo_atual(self) -> Escopo:
        return self._pilha[-1]

    def entrar_escopo(self) -> None:
        self._pilha.append(Escopo(pai=self.escopo_atual))

    def sair_escopo(self) -> None:
        self._pilha.pop()

    def declarar(self, nome: str, tipo: str, linha: int) -> Simbolo:
        simbolo = Simbolo(nome, tipo, linha)
        self.escopo_atual.declarar(simbolo)
        self._todas_declaradas[nome] = simbolo
        return simbolo

    def resolver(self, nome: str) -> Optional[Simbolo]:
        escopo: Optional[Escopo] = self.escopo_atual
        while escopo is not None:
            simbolo = escopo.resolver_local(nome)
            if simbolo is not None:
                return simbolo
            escopo = escopo.pai
        return None

    def resolver_no_escopo_atual(self, nome: str) -> Optional[Simbolo]:
        return self.escopo_atual.resolver_local(nome)

    def ja_foi_declarada_em_algum_escopo(self, nome: str) -> bool:
        return nome in self._todas_declaradas
