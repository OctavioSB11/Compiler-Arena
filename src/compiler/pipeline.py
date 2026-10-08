"""Pipeline do compilador: encadeia as etapas e registra o resultado de cada uma.

Cada etapa é uma função que recebe e devolve um `Contexto`. Etapas ainda não
implementadas ficam como `None` em ETAPAS e aparecem como "pendente" no painel.
Quem implementar uma etapa troca o `None` pela sua função.
"""
from dataclasses import dataclass
from typing import List, Optional

from .ast_nodes import NoAST
from .lexer import AutomatoLexico
from .parser import AnalisadorSintatico
from .tokens import ErroCompilacao, Token

OK, ERRO, PENDENTE, PULADA = "ok", "erro", "pendente", "pulada"


@dataclass
class Contexto:
    """Dados que passam de uma etapa para a próxima."""
    codigo: str
    tokens: Optional[List[Token]] = None
    ast: Optional[NoAST] = None
    ir: Optional[list] = None
    ir_otimizada: Optional[list] = None
    bytecode: Optional[list] = None


def etapa_lexica(ctx: Contexto) -> Contexto:
    lexer = AutomatoLexico()
    ctx.tokens = lexer.analisar(ctx.codigo)
    lexer.verificar()
    return ctx


def etapa_sintatica(ctx: Contexto) -> Contexto:
    ctx.ast = AnalisadorSintatico(ctx.tokens).analisar()
    return ctx


# (nome mostrado no painel, função da etapa ou None se ainda não existe)
ETAPAS = [
    ("Análise Léxica", etapa_lexica),
    ("Análise Sintática", etapa_sintatica),
    ("Análise Semântica", None),
    ("Código Intermediário", None),
    ("Otimização", None),
    ("Código Objeto", None),
]


@dataclass
class ResultadoEtapa:
    nome: str
    status: str
    mensagem: str = ""
    linha: Optional[int] = None


@dataclass
class ResultadoCompilacao:
    etapas: List[ResultadoEtapa]
    contexto: Contexto

    @property
    def erro(self) -> Optional[ResultadoEtapa]:
        return next((e for e in self.etapas if e.status == ERRO), None)

    @property
    def ok(self) -> bool:
        """Nenhuma etapa falhou (pode haver etapas pendentes)."""
        return self.erro is None

    @property
    def pronto(self) -> bool:
        """Todas as etapas rodaram com sucesso: o robô pode entrar na arena."""
        return all(e.status == OK for e in self.etapas)


def compilar(codigo: str) -> ResultadoCompilacao:
    ctx = Contexto(codigo)
    resultados: List[ResultadoEtapa] = []
    falhou = False
    for nome, funcao in ETAPAS:
        if falhou:
            resultados.append(ResultadoEtapa(nome, PULADA))
        elif funcao is None:
            resultados.append(ResultadoEtapa(nome, PENDENTE))
        else:
            try:
                ctx = funcao(ctx)
                resultados.append(ResultadoEtapa(nome, OK))
            except ErroCompilacao as erro:
                resultados.append(ResultadoEtapa(nome, ERRO, erro.mensagem, erro.linha))
                falhou = True
    return ResultadoCompilacao(resultados, ctx)


def formatar_painel(resultado: ResultadoCompilacao) -> str:
    """Texto do painel do compilador (a arena usará a mesma informação na tela)."""
    ast = resultado.contexto.ast
    linhas = [f"ROBÔ: {str(ast.valor).upper()}" if ast is not None else "ROBÔ: (sem nome)", ""]
    simbolos = {OK: "✓", ERRO: "✗", PENDENTE: "-", PULADA: "-"}
    notas = {PENDENTE: " (pendente)", PULADA: " (não executada)"}
    for etapa in resultado.etapas:
        linhas.append(f"{simbolos[etapa.status]} {etapa.nome}{notas.get(etapa.status, '')}")
    linhas.append("")
    erro = resultado.erro
    if erro is not None:
        onde = f"Linha {erro.linha}: " if erro.linha is not None else ""
        linhas += [f"{onde}{erro.mensagem}", "COMPILAÇÃO INTERROMPIDA", "A arena não executa o robô."]
    elif resultado.pronto:
        linhas.append("STATUS: PRONTO PARA BATALHA")
    else:
        linhas.append("STATUS: EM CONSTRUÇÃO (há etapas pendentes)")
    return "\n".join(linhas)