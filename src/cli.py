"""Uso: python -m src.cli arquivo.robot [--tokens] [--ast] [--symbols]

Cada etapa do compilador ganha uma flag à medida que for implementada
(--ir, --ir-opt, --bytecode)."""
import sys

from .compiler.ast_nodes import imprimir_ast
from .compiler.lexer import AutomatoLexico
from .compiler.parser import AnalisadorSintatico, ErroSintatico
from .compiler.semantic import AnalisadorSemantico, ErroSemantico
from .compiler.tokens import ErroLexico


def compilar(codigo: str, mostrar_tokens=False, mostrar_ast=False, mostrar_symbols=False):
    lexer = AutomatoLexico()
    tokens = lexer.analisar(codigo)
    if mostrar_tokens:
        for i, t in enumerate(tokens, 1):
            print(f"{i:>3}  {t.lexema!r:<12} {t.classificacao:<20} {t.linha}:{t.coluna}")
    lexer.verificar()
    arvore = AnalisadorSintatico(tokens).analisar()
    if mostrar_ast:
        print(imprimir_ast(arvore))
    tabela = AnalisadorSemantico().analisar(arvore)
    if mostrar_symbols:
        for escopo in tabela._pilha:
            for nome, simbolo in escopo.simbolos.items():
                print(f"{nome:<12} {simbolo.tipo:<6} linha {simbolo.linha_declaracao}")
    return arvore


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        codigo = f.read()
    try:
        compilar(codigo, "--tokens" in argv, "--ast" in argv, "--symbols" in argv)
    except (ErroLexico, ErroSintatico, ErroSemantico) as e:
        print(f"✗ {e}\nCOMPILAÇÃO INTERROMPIDA")
        return 1
    print("✓ léxico  ✓ sintático  ✓ semântico")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
