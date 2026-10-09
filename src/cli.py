"""Uso: python -m src.cli arquivo.robot [--tokens] [--ast] [--painel]

Cada etapa do compilador ganha uma flag à medida que for implementada
(--symbols, --ir, --ir-opt, --bytecode)."""
import sys

from .compiler.ast_nodes import imprimir_ast
from .compiler import pipeline
from .compiler.lexer import AutomatoLexico
from .compiler.parser import AnalisadorSintatico
from .compiler.tokens import ErroCompilacao


def compilar(codigo: str, mostrar_tokens=False, mostrar_ast=False):
    lexer = AutomatoLexico()
    tokens = lexer.analisar(codigo)
    if mostrar_tokens:
        for i, t in enumerate(tokens, 1):
            print(f"{i:>3}  {t.lexema!r:<12} {t.classificacao:<20} {t.linha}:{t.coluna}")
    lexer.verificar()
    arvore = AnalisadorSintatico(tokens).analisar()
    if mostrar_ast:
        print(imprimir_ast(arvore))
    return arvore


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        codigo = f.read()
    if "--painel" in argv:
        resultado = pipeline.compilar(codigo)
        print(pipeline.formatar_painel(resultado))
        return 0 if resultado.ok else 1
    try:
        compilar(codigo, "--tokens" in argv, "--ast" in argv)
    except ErroCompilacao as e:
        print(f"✗ {e}\nCOMPILAÇÃO INTERROMPIDA")
        return 1
    print("✓ léxico  ✓ sintático")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
