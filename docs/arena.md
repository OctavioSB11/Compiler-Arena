# Arena: regras, escalonador e interface

Responsável: Octávio Morais. Revisor: Rafael Tieppo. Arquivos: `src/arena/robot.py`, `src/arena/arena.py`, `src/arena/ui.py`, `src/arena/__main__.py`.

A arena é a última etapa da cadeia. Ela recebe o **bytecode** de cada robô, cria uma VM para cada um e, a cada tick, aplica a ação que a VM devolve:

```text
código-fonte -> pipeline.compilar -> bytecode -> VM (uma por robô) -> ação -> arena
```

A arena nunca vê nem executa o código-fonte: ela só conhece o bytecode (que entrega à VM) e as ações `(nome, argumento)` que a VM devolve.

## Como rodar

```text
python -m src.arena examples/atirador.robot examples/fugitivo.robot
python -m src.arena examples/atirador.robot examples/fugitivo.robot --texto
python -m src.arena examples/atirador.robot examples/erro_semantico.robot --demo
```

| Opção | O que faz |
| --- | --- |
| (nenhuma) | Abre a janela em pygame com a batalha e o painel do compilador |
| `--texto` | Roda sem janela e imprime o painel de cada robô e o resultado |
| `--demo` | Troca a VM por ações fixas (`scan`, `move`, `rotate`, `fire`). Só serve para ver a arena antes da VM ficar pronta |

Na janela: **espaço** pausa, **setas para cima e para baixo** mudam a velocidade (1x a 64x ticks por quadro) e **Esc** sai.

## 1. Robô (`robot.py`)

`Robo(nome, x, y, direcao, energia, vm)` guarda o estado físico e os últimos valores lidos pelo `scan()`.

- `direcao` em graus: `0` aponta para a direita (+x) e o ângulo cresce no **sentido horário** (o eixo y da tela cresce para baixo). Assim `rotate(90)` vira o robô para baixo.
- `obter_sensor(nome)` é a interface que a VM usa (contrato 5.6). Os nomes são os do bytecode (`SENSE nome`):

| Sensor no bytecode | Valor |
| --- | --- |
| `energy` | energia atual (0 a 100) |
| `pos_x`, `pos_y` | posição arredondada (0 a 1000) |
| `enemy_visible` | `1` ou `0`, do último `scan()` |
| `enemy_distance` | distância ao inimigo visto no último `scan()` (0 se não viu) |
| `enemy_direction` | direção absoluta até ele, de 0 a 359 (0 se não viu) |

## 2. Regras e escalonador (`arena.py`)

Constantes no topo do arquivo (seção 5.7 do guia):

| Constante | Valor | Uso |
| --- | --- | --- |
| `TAMANHO` | 1000 | arena de 1000 x 1000 |
| `MAX_TICKS` | 2000 | limite da batalha |
| `ALCANCE_SCAN`, `ABERTURA_SCAN` | 400, 30 | `scan()` vê até 400 unidades e ±30° |
| `ALCANCE_TIRO`, `ABERTURA_TIRO` | 500, 10 | `fire()` acerta até 500 unidades e ±10° |
| `DANO_POR_POTENCIA` | 4 | dano `4*p` |
| `LIMITES` | `move`/`back` 1 a 20, `rotate` -180 a 180, `fire` 1 a 3 | faixa aplicada em execução |

### Um tick

```text
tick += 1
para cada robô, na ordem fixa da lista:
    se está vivo:
        ação = robo.vm.executar_tick()     # None = orçamento esgotado ou HALT
        se ação: arena.aplicar(robo, nome, argumento)
```

| Ação | Efeito |
| --- | --- |
| `move(n)` / `back(n)` | anda `n` na direção atual (ou ao contrário). A posição é limitada às bordas, sem dano |
| `rotate(g)` | `direcao = (direcao + g) % 360` |
| `scan()` | procura o inimigo vivo mais próximo a até 400 e ±30° e atualiza os sensores `enemy_*` |
| `fire(p)` | custa `p` de energia; acerta o inimigo vivo mais próximo a até 500 e ±10°, que perde `4*p` |

Decisões:

- **Faixas em execução:** quando o argumento vem de variável, a semântica não consegue checar a faixa. A arena ajusta o valor ao limite (`move(999)` vira `move(20)`), mesmo que a VM já faça isso: é uma proteção barata.
- **Nome da ação:** a arena aceita `"move"` ou `"MOVE"` (converte para minúsculas), então tanto faz a VM devolver o nome do comando ou da instrução.
- **Eliminação:** energia `<= 0`. Quem é eliminado no meio do tick já não age naquele tick. A energia nunca fica negativa (para de 0).
- **Tiro instantâneo:** não há projétil viajando. A linha do tiro aparece na tela só no tick em que foi disparado.
- **Fim:** resta um robô vivo (ou nenhum), ou o tick 2000. No limite, vence quem tem mais energia; energia igual é empate (`vencedor` é `None`). Se nenhum robô compilou, a tela mostra `NENHUM ROBÔ PRONTO PARA BATALHA` (`texto_resultado`).
- **Determinismo:** não há aleatoriedade. Os robôs agem sempre na mesma ordem e o empate de distância no `scan`/`fire` fica com quem vem antes na lista. A mesma entrada produz sempre a mesma batalha.

### Posições iniciais

`posicoes_iniciais(n)` espalha os `n` robôs em um círculo de raio 400 em volta do centro, começando pela esquerda, cada um voltado para o centro. Com 2 robôs: `(100, 500)` olhando para 0° e `(900, 500)` olhando para 180°.

### Montar a batalha

```python
arena, participantes = preparar_batalha([codigo1, codigo2], criar_vm)
vencedor = arena.rodar()
```

`preparar_batalha` compila cada código com `pipeline.compilar`. Só os robôs com `resultado.pronto` entram na arena (regra 4 do guia). Todos aparecem em `participantes` (`Participante(resultado, robo)`), para o painel mostrar também quem falhou e por quê.

## 3. Contrato com a VM

A arena não importa nada da VM diretamente: recebe uma fábrica `criar_vm(bytecode, obter_sensor)`. O `__main__.py` usa:

```python
from src.vm.vm import MaquinaVirtual
vm = MaquinaVirtual(bytecode, robo.obter_sensor)
acao = vm.executar_tick()    # (nome, argumento) ou None
```

| Item | Combinado |
| --- | --- |
| Classe | `MaquinaVirtual` em `src/vm/vm.py` |
| Construtor | `MaquinaVirtual(bytecode, obter_sensor)`, `bytecode` é a lista de `InstrucaoBytecode` do `codegen` |
| Método | `executar_tick()` executa até 1 ação ou 50 instruções |
| Retorno | `("move", 20)`, `("scan", None)` etc., ou `None` se não houve ação (orçamento esgotado ou `HALT`) |

Se o nome da classe ou do método mudar, só a função `criar_vm` em `src/arena/__main__.py` precisa mudar.

## 4. Interface (`ui.py`)

Janela de 1080 x 700: à esquerda a arena (escala 0,7), à direita o painel.

- **Robô:** círculo na cor do robô, traço branco apontando a direção, nome em cima e barra de energia embaixo. Eliminado vira um círculo cinza com `X`.
- **Tiro:** linha na cor do atirador. Se acertou, um anel vermelho no alvo.
- **Painel do compilador** (seção 5.8): para cada robô, as 6 etapas com um quadrado verde (ok), vermelho (erro) ou cinza (não executada). Depois o status: `PRONTO PARA BATALHA`, `ATIVO`, `ELIMINADO` ou, se houve erro, `ANÁLISE SEMÂNTICA | Linha 1: fire() espera valor entre 1 e 3` e `COMPILAÇÃO INTERROMPIDA: fora da batalha`.
- **Fim:** faixa no meio da arena com `VENCEDOR: NOME` ou `EMPATE`.

## 5. Testes (`tests/test_arena.py`)

Os testes usam uma `VMFalsa` que devolve uma lista de ações, uma por tick. Assim a arena é testada sem depender da VM. Cobrem: sensores, posições iniciais, `move`/`back`/`rotate`, parede, faixas, `scan` (cone, alcance e mais próximo), `fire` (acerto, erro e custo), eliminação, fim por tick com vencedor e empate, determinismo e `preparar_batalha` (robô com erro fica de fora).

```text
python -m pytest tests/test_arena.py -v
```
