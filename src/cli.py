"""Uso: python -m src.cli arquivo.robot [--tokens] [--ast] [--ir] [--ir-opt]
                                       [--bytecode] [--painel]

Cada etapa do compilador ganha uma flag à medida que for implementada
(falta --symbols, da análise semântica)."""
import sys

from .compiler.ast_nodes import imprimir_ast
from .compiler import pipeline
from .compiler.codegen import formatar_bytecode, gerar_bytecode
from .compiler.ir import formatar_ir, gerar_ir
from .compiler.lexer import AutomatoLexico
from .compiler.optimizer import otimizar
from .compiler.parser import AnalisadorSintatico
from .compiler.tokens import ErroCompilacao


def compilar(codigo: str, mostrar_tokens=False, mostrar_ast=False,
             mostrar_ir=False, mostrar_ir_opt=False, mostrar_bytecode=False):
    lexer = AutomatoLexico()
    tokens = lexer.analisar(codigo)
    if mostrar_tokens:
        for i, t in enumerate(tokens, 1):
            print(f"{i:>3}  {t.lexema!r:<12} {t.classificacao:<20} {t.linha}:{t.coluna}")
    lexer.verificar()
    arvore = AnalisadorSintatico(tokens).analisar()
    if mostrar_ast:
                        print(imprimir_ast(arvore))
    ir = gerar_ir(arvore)
    if mostrar_ir:
        print("--- IR ---")
        print(formatar_ir(ir))
    ir_otimizada = otimizar(ir)
    if mostrar_ir_opt:
        print("--- IR otimizada ---")
        print(formatar_ir(ir_otimizada))
    if mostrar_bytecode:
        print("--- Bytecode ---")
        print(formatar_bytecode(gerar_bytecode(ir_otimizada), com_enderecos=True))
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
        compilar(codigo, "--tokens" in argv, "--ast" in argv, "--ir" in argv,
                 "--ir-opt" in argv, "--bytecode" in argv)
    except ErroCompilacao as e:
        print(f"✗ {e}\nCOMPILAÇÃO INTERROMPIDA")
        return 1
    print("✓ léxico  ✓ sintático  ✓ ir  ✓ otimização  ✓ bytecode")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
