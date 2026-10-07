# Compiler Arena

Arena de batalha de robôs em que cada robô só luta depois de passar por uma cadeia real de compilação:
código-fonte → léxico → sintático → semântico → IR → otimização → bytecode → VM → arena.

## Estado

| Etapa | Estado |
| --- | --- |
| Léxico (`src/compiler/lexer.py`) | pronto (adaptado da Parte I) |
| Sintático e AST (`parser.py`, `ast_nodes.py`) | pronto (adaptado da Parte I) |
| Semântico, IR, otimização, bytecode, VM, arena | a fazer |

## Rodar

```bash
pip install -r requirements.txt
python -m pytest
python -m src.cli examples/alpha.robot --tokens --ast
```

## Linguagem

Tipos `int` e `bool`. Comandos: `move(n)` e `back(n)` (1 a 10), `rotate(g)` (-180 a 180), `scan()`, `fire(p)` (1 a 3).
Sensores: `energy`, `position.x`, `position.y`, `enemy.visible`, `enemy.distance`, `enemy.direction`.
A gramática completa está no docstring de `AnalisadorSintatico`. Passar de EBNF para `docs/gramatica.md` é a primeira tarefa da fase 0.

## Estrutura

```text
src/compiler/   tokens.py lexer.py ast_nodes.py parser.py   (próximos: semantic.py symbols.py ir.py optimizer.py codegen.py)
src/vm/         (bytecode.py vm.py)
src/arena/      (arena.py robot.py ui.py)
src/cli.py      uma flag por etapa
examples/       alpha.robot e um exemplo por tipo de erro
tests/          um arquivo por etapa
docs/           documentação técnica
```

## Regras

Proibido executar o código do robô na linguagem hospedeira (`exec`, `eval`). A arena só recebe bytecode interpretado pela VM.
