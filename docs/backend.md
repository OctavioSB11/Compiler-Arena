# Back-end do compilador: IR, otimização e bytecode

Responsável: Matheus Porto. Arquivos: `src/compiler/ir.py`, `src/compiler/optimizer.py`, `src/compiler/codegen.py`.

O back-end recebe a AST do parser e entrega o bytecode que a VM executa:

```text
AST -> gerar_ir -> IR -> otimizar -> IR otimizada -> gerar_bytecode -> bytecode
```

Ele usa só a AST do parser, então funciona mesmo antes da análise semântica ficar pronta. As faixas de valores (`move` de 1 a 20, `fire` de 1 a 3 etc.) são verificadas pela semântica, não aqui.

## Como ver cada etapa

```text
python -m src.cli examples/otimizacao.robot --ir --ir-opt --bytecode
```

| Flag | O que mostra |
| --- | --- |
| `--ir` | IR de três endereços, sem otimizar |
| `--ir-opt` | IR depois das otimizações |
| `--bytecode` | Bytecode final, com o endereço de cada instrução |
| `--painel` | Painel do compilador, com as etapas concluídas |

## 1. IR de três endereços (`ir.py`)

Cada instrução é uma `Instrucao(op, arg1, arg2, res, operador)` e é impressa assim:

| Instrução | Significado | Impressa como |
| --- | --- | --- |
| `COPY` | `res = arg1` | `x = 30` |
| `BINOP` | `res = arg1 operador arg2` | `t1 = 10 + 20` |
| `UNOP` | `res = operador arg1` (`neg`, `not`) | `t2 = not t1` |
| `LABEL` | marca um destino | `L1:` |
| `JUMP` | salto incondicional | `goto L1` |
| `JUMPF` | salta se `arg1` for falso | `ifFalse t1 goto L2` |
| `GETSENSOR` | lê um sensor | `t3 = sensor enemy.distance` |
| `PARAM` | empilha o argumento de um comando | `param t3` |
| `CALL` | executa um comando | `call fire, 1` |

Decisões:

- Variáveis do usuário mantêm o nome. Temporários se chamam `t1`, `t2`... e rótulos `L1`, `L2`...
- `true` vira `1` e `false` vira `0`.
- Declaração sem valor (`int x;`) inicia em `0`.
- `energy` e os acessos `position.x`, `enemy.distance` etc. viram `GETSENSOR`.
- `if`, `else if`, `else` e `while` viram rótulos e saltos (`JUMPF` e `JUMP`).

## 2. Otimização (`optimizer.py`)

São 5 técnicas, cada uma em uma função, e qualquer uma pode ser ligada sozinha: `otimizar(ir, tecnicas=["dobrar_constantes"])`. Sem a lista, aplica todas, repetindo até a IR parar de mudar (no máximo 10 voltas).

| Técnica | Antes | Depois |
| --- | --- | --- |
| `dobrar_constantes` | `t1 = 10 + 20` | `t1 = 30` |
| `simplificar_algebra` | `t2 = x + 0` | `t2 = x` |
| `propagar_constantes` | `t1 = 30` e `x = t1` | `x = 30` |
| `eliminar_temporarios` | `t1 = 30` que ninguém usa | (removido) |
| `simplificar_saltos` | `ifFalse 1 goto L1` | (removido) |

Cuidados:

- A simplificação algébrica cobre `+ 0`, `- 0`, `* 1`, `* 0`, `/ 1` e as lógicas com `0` e `1` (`&&`, `||`).
- A divisão inteira trunca em direção a zero, como em C: `-7 / 2` dá `-3`.
- Divisão por zero **não é calculada**: a instrução fica na IR para o erro aparecer na execução.
- Um `while true` não perde o laço, pois só a condição constante do `ifFalse` é simplificada.

Exemplo (`examples/otimizacao.robot`):

```text
antes (--ir)            depois (--ir-opt)
t1 = 10 + 20            x = 30
x = t1                  t2 = x
t2 = x + 0              param t2
param t2                call move, 1
call move, 1
```

## 3. Bytecode de pilha (`codegen.py`)

Cada variável e temporário recebe um índice fixo na ordem em que aparece (`LOAD 0`, `STORE 1`...). Os rótulos viram endereços (posição na lista) e o programa sempre termina com `HALT`.

| Instrução | Efeito na pilha |
| --- | --- |
| `PUSH n` | empilha o número `n` |
| `LOAD i` | empilha o valor da variável `i` |
| `STORE i` | desempilha o topo e guarda na variável `i` |
| `ADD SUB MUL DIV` | desempilha `b`, depois `a`, e empilha `a op b` |
| `LT GT LE GE EQ NE` | desempilha `b` e `a`, e empilha `1` ou `0` |
| `AND OR` | desempilha `b` e `a`, e empilha `1` ou `0` |
| `NEG NOT` | troca o topo por `-topo` ou por `1` se o topo era `0` |
| `JMP addr` | salta para o endereço `addr` |
| `JZ addr` | desempilha o topo e salta para `addr` se for `0` |
| `SENSE nome` | empilha o sensor (`energy`, `pos_x`, `pos_y`, `enemy_visible`, `enemy_distance`, `enemy_direction`) |
| `MOVE BACK ROTATE FIRE` | desempilha o topo como argumento e executa a ação |
| `SCAN` | executa a ação, sem argumento |
| `HALT` | para o robô |

Tradução de cada instrução da IR:

| IR | Bytecode |
| --- | --- |
| `x = 30` | `PUSH 30`, `STORE i` |
| `t1 = a + b` | `LOAD a`, `LOAD b`, `ADD`, `STORE t1` |
| `t2 = not t1` | `LOAD t1`, `NOT`, `STORE t2` |
| `t3 = sensor energy` | `SENSE energy`, `STORE t3` |
| `ifFalse t1 goto L2` | `LOAD t1`, `JZ endereço de L2` |
| `goto L1` | `JMP endereço de L1` |
| `param x` e `call fire, 1` | `LOAD x`, `FIRE` |
| `call scan, 0` | `SCAN` |

Exemplo (`examples/otimizacao.robot`):

```text
  0  PUSH 30
  1  STORE 0
  2  LOAD 0
  3  STORE 1
  4  LOAD 1
  5  MOVE
  6  HALT
```

## 4. O que a VM precisa saber

- Toda variável começa em `0`. A memória precisa ter um espaço para cada índice usado.
- `DIV` é divisão inteira truncada em direção a zero. Divisão por zero é um erro da VM, e ela decide o que fazer (por exemplo, parar o robô).
- `true` é `1` e `false` é `0`. Comparações e `AND`/`OR`/`NOT` sempre produzem `1` ou `0`.
- Todo endereço de `JMP` e `JZ` é um número válido dentro do programa. O último é sempre `HALT`.
- O bytecode é uma lista de `InstrucaoBytecode(op, arg)`. `str()` dá a linha de texto, por exemplo `PUSH 30`.

## Testes

`tests/test_ir.py` (15), `tests/test_optimizer.py` (16), `tests/test_codegen.py` (13) e `tests/test_cli_back_end.py` (4). Cada técnica de otimização tem um teste de antes e depois.
