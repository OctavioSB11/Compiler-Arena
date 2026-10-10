# Front-end do compilador (Danilo)

Este documento explica a parte do compilador que transforma o texto de um
arquivo `.robot` em uma árvore (AST) e mostra o resultado de cada etapa.
Código em `src/compiler/` e `src/cli.py`.

## Visão geral

```
arquivo .robot -> léxico -> sintático -> (semântica -> IR -> otimização -> bytecode)
                  tokens      AST          etapas dos outros módulos
```

| Arquivo | O que faz |
| --- | --- |
| `tokens.py` | `Token` e as classes de erro (`ErroCompilacao` é a base de todos) |
| `lexer.py` | `AutomatoLexico`: texto -> lista de tokens |
| `parser.py` | `AnalisadorSintatico`: tokens -> AST |
| `ast_nodes.py` | `NoAST` e `imprimir_ast` |
| `pipeline.py` | encadeia as etapas e gera o painel |
| `cli.py` | linha de comando (`--tokens`, `--ast`, `--painel`) |

## 1. Análise léxica

Lê o código caractere por caractere e agrupa em **tokens**, cada um com
lexema, classificação, linha e coluna.

- **Palavras reservadas:** `robot`, `int`, `bool`, `if`, `else`, `while`, `true`, `false`
- **Identificadores:** letra ou `_`, seguida de letras, dígitos ou `_`
  (`move`, `fire`, `enemy` são identificadores, não palavras reservadas)
- **Números inteiros:** `NUMERO_INTEIRO`
- **Operadores:** aritméticos `+ - * /`, relacionais `> < >= <= == !=`,
  lógicos `&& || !` e atribuição `=`
- **Delimitadores:** `; ( ) { } , .`
- **Comentários:** `//` até o fim da linha (são ignorados)

Operadores de dois caracteres (`>=`, `==`, `&&`...) são testados antes dos de
um caractere. **Erros léxicos:** caractere inválido (como `@`) e número
malformado (como `12abc`). O léxico não para no primeiro erro: ele marca o
token como `ERRO` e guarda o erro; `verificar()` levanta o primeiro, e
qualquer erro interrompe a compilação.

## 2. Análise sintática

Parser **descendente recursivo**: cada regra da gramática é um método. Não
há backtracking; o próximo token decide qual regra usar.

```
programa    -> 'robot' IDENT bloco
bloco       -> '{' comando* '}'
comando     -> declaracao | atribuicao | condicional | enquanto | chamada ';'
declaracao  -> ('int'|'bool') IDENT ('=' expressao)? ';'
atribuicao  -> IDENT '=' expressao ';'
condicional -> 'if' expressao bloco ('else' (bloco | condicional))?
enquanto    -> 'while' expressao bloco
chamada     -> IDENT '(' (expressao (',' expressao)*)? ')'
```

**Precedência das expressões** (da mais fraca para a mais forte), uma regra
por nível: `||`, `&&`, relacionais, `+ -`, `* /`, unários (`-`, `!`),
primários (número, `true`/`false`, chamada, `IDENT`, `IDENT.IDENT`,
parênteses). Por isso `1 + 2 * 3` vira `1 + (2 * 3)`.

Decisões de projeto:
- Parênteses na condição do `if`/`while` são opcionais (`while enemy.visible {`).
- `else if` funciona porque o `else` aceita um bloco **ou** outro `if`.
- O relacional não encadeia: `a < b < c` é erro de sintaxe.
- `x.y` vira um nó `Acesso` (usado por `enemy.distance`, `position.x`).

Erros sintáticos dizem o que era esperado, a linha e a coluna
(ex.: `Linha 3: esperado ';'`).

## 3. A AST

Nós genéricos `NoAST(tipo, valor, filhos, linha, coluna)`. Tipos: `Robo`,
`Bloco`, `Declaracao`, `Atribuicao`, `Condicional`, `Enquanto`, `Chamada`,
`Operacao`, `Numero`, `Booleano`, `Identificador`, `Acesso`. O campo
`tipo_semantico` fica vazio no front-end e é preenchido pela semântica.
Veja uma AST com `python -m src.cli examples/alpha.robot --ast`.

## 4. Pipeline e painel

`pipeline.py` guarda a lista `ETAPAS`: pares (nome, função). Léxico e
sintático já têm função; as outras etapas são `None` e aparecem como
"pendente". Quem implementa uma etapa troca o `None` pela sua função, que
recebe e devolve um `Contexto` (código, tokens, AST, IR, bytecode).

`compilar(codigo)` roda as etapas em ordem. Se uma levanta
`ErroCompilacao`, ela é marcada com ✗, o painel mostra a linha e a mensagem
e **as etapas seguintes ficam "não executada"**. A arena só recebe um robô
cujas etapas passaram todas.

## 5. Como usar e testar

```
python -m src.cli examples/alpha.robot --tokens
python -m src.cli examples/alpha.robot --ast
python -m src.cli examples/alpha.robot --painel
python -m pytest
```

Testes: `test_lexer.py`, `test_parser.py`, `test_pipeline.py`,
`test_exemplos.py` e `test_front_end.py`.

## Perguntas para treinar a defesa

1. Qual a diferença entre léxico e sintático? Onde cada erro aparece?
2. Por que `move` é um identificador e `while` é palavra reservada?
3. Como o parser garante que `*` ganha de `+`?
4. Por que `else if` não precisou de regra própria?
5. O que acontece com as etapas depois de um erro? Por quê?
6. Onde um colega encaixa a sua etapa no pipeline?
7. Mostre no terminal um erro léxico e um sintático e explique a mensagem.