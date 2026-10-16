# Análise semântica: tabela de símbolos e verificação de tipos

Responsável: Octávio Bordotti. Arquivos: `src/compiler/semantic.py` e `src/compiler/symbols.py`. Testes em `tests/test_semantic.py`.

A semântica é a terceira etapa do compilador. Ela recebe a AST do parser, confere se o programa faz sentido e anota cada expressão com o seu tipo:

```text
AST -> AnalisadorSemantico.analisar -> AST anotada + tabela de símbolos
```

Se encontra um erro, levanta `ErroSemantico` com a **linha** e o **motivo**, e o pipeline interrompe: as etapas seguintes aparecem como "não executada" e a arena não executa o robô. A análise **para no primeiro erro** que encontrar.

## Como ver o resultado

```text
python -m src.cli examples/alpha.robot --symbols
python -m src.cli examples/erro_semantico.robot
python -m src.cli examples/alpha.robot --painel
```

`--symbols` imprime a tabela de símbolos de nível superior (nome, tipo e linha da declaração). Sem erro, o painel mostra `✓ Análise Semântica`.

## 1. Tabela de símbolos (`symbols.py`)

| Classe | Função |
| --- | --- |
| `Simbolo` | nome, tipo (`int` ou `bool`) e linha da declaração |
| `Escopo` | dicionário de símbolos de um bloco, com ligação ao escopo pai |
| `TabelaDeSimbolos` | pilha de escopos: `entrar_escopo`, `sair_escopo`, `declarar`, `resolver` |

Regras:

- Cada bloco `{ }` abre um escopo novo, e as variáveis dele deixam de existir ao fechar o bloco.
- `resolver(nome)` procura no escopo atual e sobe pelos escopos pais até achar.
- Declarar de novo o mesmo nome **no mesmo escopo** é erro. Em um bloco interno, o mesmo nome é permitido e esconde a variável de fora.
- A tabela guarda também todo nome já declarado em algum escopo. Isso permite diferenciar "não foi declarada" de "não existe neste escopo".
- O bloco do robô usa o escopo raiz, para que `--symbols` mostre as variáveis de nível superior.

## 2. Tipos

A linguagem tem dois tipos, `int` e `bool`. Cada expressão recebe um `tipo_semantico`:

| Expressão | Tipo |
| --- | --- |
| número (`10`) | `int` |
| `true` e `false` | `bool` |
| variável | o tipo com que foi declarada |
| sensores `energy`, `position.x`, `position.y`, `enemy.distance`, `enemy.direction` | `int` |
| sensor `enemy.visible` | `bool` |
| `+ - * /` e `-` unário | `int` (operandos `int`) |
| `< > <= >= == !=` | `bool` (operandos `int`) |
| `&& \|\|` e `!` | `bool` (operandos `bool`) |
| chamada de comando | sem tipo (comandos não retornam valor) |

Atribuições e declarações com valor exigem o mesmo tipo dos dois lados. A condição de `if` e de `while` precisa ser `bool`.

## 3. Comandos

A tabela `COMANDOS` define a aridade, o tipo e a faixa de cada comando:

| Comando | Argumento | Faixa válida |
| --- | --- | --- |
| `move(n)` | `int` | 1 a 20 |
| `back(n)` | `int` | 1 a 20 |
| `rotate(g)` | `int` | -180 a 180 |
| `fire(p)` | `int` | 1 a 3 |
| `scan()` | nenhum | |

A faixa só é verificada em compilação quando o argumento é uma constante (inclusive negativa, como `rotate(-45)`). Com variável, a semântica não sabe o valor: quem aplica a faixa é a VM, em execução, ajustando o valor ao limite.

## 4. Erros detectados

Toda mensagem inclui a linha e o motivo. Estas mensagens foram conferidas com o compilador:

| Erro | Exemplo | Mensagem |
| --- | --- | --- |
| Tipos incompatíveis | `int d; d = true;` | `Linha 2: não é possível atribuir 'bool' a 'int'` |
| Uso antes da declaração | `x = 1;` | `Linha 2: 'x' não foi declarada` |
| Declaração duplicada | `int x; int x;` | `Linha 2: 'x' já foi declarada na linha 2` |
| Parâmetro fora da faixa | `fire(200);` | `Linha 2: fire() espera valor entre 1 e 3` |
| Tipo de parâmetro inválido | `move(false);` | `Linha 2: move() espera 'int', recebeu 'bool'` |
| Escopo incorreto | `if energy < 10 { int y = 1; } y = 2;` | `Linha 2: 'y' não existe neste escopo` |
| Operador incompatível | `int x = true + 1;` | `Linha 2: operador '+' não aceita 'bool'` |

Outros erros também detectados:

| Erro | Exemplo | Mensagem |
| --- | --- | --- |
| Número de argumentos | `move(1, 2);` | `move() espera 1 argumento(s), recebeu 2` |
| Atribuição a sensor | `energy = 5;` | `'energy' é um sensor e não pode ser atribuído` |
| Condição que não é `bool` | `if 5 { ... }` | `condição do 'if' deve ser 'bool'` |

## 5. Como a semântica se liga ao resto

- **Entrada:** a AST do parser. O campo `tipo_semantico` dos nós, vazio no front-end, é preenchido aqui.
- **Saída:** a `TabelaDeSimbolos`, guardada no `Contexto` do pipeline (`ctx.tabela_simbolos`).
- **Erro:** `ErroSemantico` é uma `ErroCompilacao`. O pipeline marca a etapa com ✗, mostra a linha e a mensagem no painel e pula as etapas seguintes.
- **Depois:** o back-end (IR, otimização e bytecode) usa só a AST e não depende desta etapa. A faixa de valores com variáveis fica para a VM.

## Limitações conhecidas

- A análise para no primeiro erro, e não lista todos de uma vez.
- Não há verificação de código inalcançável nem de variável nunca usada.
- A faixa de argumentos não constantes só é aplicada na VM.

## Testes

`tests/test_semantic.py` cobre o robô válido, cada um dos 7 erros do enunciado, os sensores com tipo correto e a atribuição a sensor.
