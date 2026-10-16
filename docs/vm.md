# Máquina virtual (VM)

Responsável: Rafael Tieppo. Arquivo: `src/vm/vm.py`. Testes: `tests/test_vm.py`.

A VM é a penúltima etapa da cadeia. Ela recebe o bytecode do `codegen` e o executa, instrução por instrução, sem nunca ver o código-fonte do robô:

```text
código-fonte -> pipeline.compilar -> bytecode -> VM -> ação -> arena
```

## Estado

| Campo | O que guarda |
| --- | --- |
| `programa` | lista de `InstrucaoBytecode(op, arg)` |
| `pc` | endereço da próxima instrução |
| `pilha` | pilha de inteiros (`true` é 1 e `false` é 0) |
| `memoria` | um espaço por índice de variável usado em `LOAD`/`STORE`, todos começando em 0 |
| `parado` | `True` depois de `HALT` ou de um erro |
| `erro` | mensagem do erro de execução, ou `None` |

## Um tick (contrato 5.6)

```text
repita até 50 vezes (orçamento):
    se parado: devolve None
    executa a instrução em pc
    se foi uma ação: devolve (nome, argumento)
devolve None   # orçamento esgotado, o robô continua no próximo tick
```

- Cada tick produz **no máximo uma ação**. Assim todos os robôs agem no mesmo ritmo.
- O orçamento de 50 instruções impede que um `while` sem ação trave a arena: o robô só perde a vez naquele tick e continua de onde parou no seguinte.
- A ação volta em minúsculas: `("move", 20)`, `("rotate", -30)`, `("fire", 3)`, `("scan", None)`.

## Instruções

| Instrução | Efeito |
| --- | --- |
| `PUSH n` | empilha `n` |
| `LOAD i` / `STORE i` | empilha `memoria[i]` / desempilha e guarda em `memoria[i]` |
| `ADD SUB MUL DIV` | desempilha `b`, depois `a`, e empilha `a op b` |
| `LT GT LE GE EQ NE AND OR` | desempilha `b` e `a`, e empilha `1` ou `0` |
| `NEG` / `NOT` | troca o topo por `-topo` / por `1` se era `0`, senão `0` |
| `JMP addr` | `pc = addr` |
| `JZ addr` | desempilha e salta se for `0` |
| `SENSE nome` | empilha `obter_sensor(nome)`, lido da arena |
| `MOVE BACK ROTATE FIRE` | desempilha o argumento, ajusta à faixa e devolve a ação |
| `SCAN` | devolve a ação, sem argumento |
| `HALT` | para o robô, que continua na arena sem agir |

Decisões:

- **Divisão inteira** trunca em direção a zero, como em C e como no otimizador: `-7 / 2` dá `-3`.
- **Faixas:** quando o argumento vem de uma variável, a semântica não sabe o valor. A VM ajusta ao limite (`move` e `back` 1 a 20, `rotate` -180 a 180, `fire` 1 a 3), então `move(999)` vira `move(20)`.
- **Sensores:** a VM não importa nada da arena. Ela recebe a função `obter_sensor(nome)` no construtor e só a chama no `SENSE`.

## Erros de execução

Divisão por zero, pilha vazia, salto para fora do programa e instrução desconhecida levantam `ErroExecucao`. O `executar_tick()` captura o erro, guarda a mensagem em `erro` (por exemplo `endereço 3: divisão por zero`), marca o robô como `parado` e devolve `None`. Só aquele robô para; a batalha continua.

## Como usar

```python
from src.vm.vm import MaquinaVirtual

vm = MaquinaVirtual(bytecode, robo.obter_sensor)   # orcamento=50 é o padrão
acao = vm.executar_tick()                           # (nome, argumento) ou None
```

Batalha com robôs compilados de verdade:

```text
python -m src.arena examples/atirador.robot examples/fugitivo.robot --texto
```
cat > docs/vm.md <<'FIM'
# Máquina virtual (VM)

Responsável: Rafael Tieppo. Arquivo: `src/vm/vm.py`. Testes: `tests/test_vm.py`.

A VM é a penúltima etapa da cadeia. Ela recebe o bytecode do `codegen` e o executa, instrução por instrução, sem nunca ver o código-fonte do robô:

```text
código-fonte -> pipeline.compilar -> bytecode -> VM -> ação -> arena
```

## Estado

| Campo | O que guarda |
| --- | --- |
| `programa` | lista de `InstrucaoBytecode(op, arg)` |
| `pc` | endereço da próxima instrução |
| `pilha` | pilha de inteiros (`true` é 1 e `false` é 0) |
| `memoria` | um espaço por índice de variável usado em `LOAD`/`STORE`, todos começando em 0 |
| `parado` | `True` depois de `HALT` ou de um erro |
| `erro` | mensagem do erro de execução, ou `None` |

## Um tick (contrato 5.6)

```text
repita até 50 vezes (orçamento):
    se parado: devolve None
    executa a instrução em pc
    se foi uma ação: devolve (nome, argumento)
devolve None   # orçamento esgotado, o robô continua no próximo tick
```

- Cada tick produz **no máximo uma ação**. Assim todos os robôs agem no mesmo ritmo.
- O orçamento de 50 instruções impede que um `while` sem ação trave a arena: o robô só perde a vez naquele tick e continua de onde parou no seguinte.
- A ação volta em minúsculas: `("move", 20)`, `("rotate", -30)`, `("fire", 3)`, `("scan", None)`.

## Instruções

| Instrução | Efeito |
| --- | --- |
| `PUSH n` | empilha `n` |
| `LOAD i` / `STORE i` | empilha `memoria[i]` / desempilha e guarda em `memoria[i]` |
| `ADD SUB MUL DIV` | desempilha `b`, depois `a`, e empilha `a op b` |
| `LT GT LE GE EQ NE AND OR` | desempilha `b` e `a`, e empilha `1` ou `0` |
| `NEG` / `NOT` | troca o topo por `-topo` / por `1` se era `0`, senão `0` |
| `JMP addr` | `pc = addr` |
| `JZ addr` | desempilha e salta se for `0` |
| `SENSE nome` | empilha `obter_sensor(nome)`, lido da arena |
| `MOVE BACK ROTATE FIRE` | desempilha o argumento, ajusta à faixa e devolve a ação |
| `SCAN` | devolve a ação, sem argumento |
| `HALT` | para o robô, que continua na arena sem agir |

Decisões:

- **Divisão inteira** trunca em direção a zero, como em C e como no otimizador: `-7 / 2` dá `-3`.
- **Faixas:** quando o argumento vem de uma variável, a semântica não sabe o valor. A VM ajusta ao limite (`move` e `back` 1 a 20, `rotate` -180 a 180, `fire` 1 a 3), então `move(999)` vira `move(20)`.
- **Sensores:** a VM não importa nada da arena. Ela recebe a função `obter_sensor(nome)` no construtor e só a chama no `SENSE`.

## Erros de execução

Divisão por zero, pilha vazia, salto para fora do programa e instrução desconhecida levantam `ErroExecucao`. O `executar_tick()` captura o erro, guarda a mensagem em `erro` (por exemplo `endereço 3: divisão por zero`), marca o robô como `parado` e devolve `None`. Só aquele robô para; a batalha continua.

## Como usar

```python
from src.vm.vm import MaquinaVirtual

vm = MaquinaVirtual(bytecode, robo.obter_sensor)   # orcamento=50 é o padrão
acao = vm.executar_tick()                           # (nome, argumento) ou None
```

Batalha com robôs compilados de verdade:

```text
python -m src.arena examples/atirador.robot examples/fugitivo.robot --texto
```

No Windows, se aparecer `UnicodeEncodeError` por causa do `✓` do painel, rode com `python -X utf8 -m src.arena ...`.

## Testes

```text
python -m pytest tests/test_vm.py -v
```

Cobrem pilha e memória, aritmética e divisão truncada, comparações e lógicas, `JZ`/`JMP`, `SENSE`, uma ação por tick, faixas, orçamento, `HALT`, os quatro erros de execução e robôs compilados pelo pipeline completo (`if`, `while` e sensores).
