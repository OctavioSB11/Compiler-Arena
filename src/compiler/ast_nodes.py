from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class NoAST:
    """Nó genérico da AST (mesmo formato da Parte I).

    Tipos usados: Robo, Bloco, Declaracao, Atribuicao, Condicional, Enquanto,
    Chamada, Operacao, Numero, Booleano, Identificador, Acesso.
    O campo `tipo_semantico` é preenchido pela análise semântica (int/bool).
    """
    tipo: str
    valor: Any = None
    filhos: List["NoAST"] = field(default_factory=list)
    linha: Optional[int] = None
    coluna: Optional[int] = None
    tipo_semantico: Optional[str] = None

    def adicionar(self, *filhos: "NoAST") -> "NoAST":
        self.filhos.extend(filhos)
        return self


def imprimir_ast(no: NoAST, nivel: int = 0) -> str:
    rotulo = f"{no.tipo}: {no.valor}" if no.valor is not None else no.tipo
    linhas = ["  " * nivel + rotulo]
    for filho in no.filhos:
        linhas.append(imprimir_ast(filho, nivel + 1))
    return "\n".join(linhas)
