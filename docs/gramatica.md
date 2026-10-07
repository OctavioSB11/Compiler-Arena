# Gramática da linguagem dos robôs

Este documento descreve exatamente o que o analisador léxico (`src/compiler/lexer.py`) e o parser (`src/compiler/parser.py`) aceitam.
Se o código mudar, este arquivo muda junto, no mesmo Pull Request.

## 1. Análise léxica

| Categoria | Definição |
| --- | --- |
| Identificador | `(letra \| "_") { letra \| dígito \| "_" }` |
| Número inteiro | `dígito { dígito }` |
| Palavras reservadas | `robot int bool if else while true false` |
| Operadores aritméticos | `+ - * /` |
| Operadores relacionais | `> < >= <= == !=` |
| Operadores lógicos | `&& \|\| !` |
| Atribuição | `=` |
| Delimitadores | `; ( ) { } , .` |
| Comentário | `//` até o fim da linha (descartado) |
| Espaços | espaço, tab e quebra de linha (descartados) |

Cada token guarda `lexema`, `classificacao`, `valor`, `linha` e `coluna`.

Erros léxicos (viram token `ERRO` e interrompem a compilação):

- caractere fora do alfabeto, por exemplo `@`;
- número colado a letras, por exemplo `12abc`.

## 2. Análise sintática (EBNF)

```text
programa     = "robot" IDENT bloco ;
bloco        = "{" { comando } "}" ;
comando      = declaracao | atribuicao | condicional | enquanto | chamada ";" ;

declaracao   = ( "int" | "bool" ) IDENT [ "=" expressao ] ";" ;
atribuicao   = IDENT "=" expressao ";" ;
condicional  = "if" expressao bloco [ "else" ( bloco | condicional ) ] ;
enquanto     = "while" expressao bloco ;
chamada      = IDENT "(" [ expressao { "," expressao } ] ")" ;

expressao    = ou ;
ou           = e { "||" e } ;
e            = relacional { "&&" relacional } ;
relacional   = aritmetica [ OPREL aritmetica ] ;
aritmetica   = termo { ( "+" | "-" ) termo } ;
termo        = unario { ( "*" | "/" ) unario } ;
unario       = ( "-" | "!" ) unario | primario ;
primario     = NUMERO | "true" | "false" | chamada
             | IDENT [ "." IDENT ] | "(" expressao ")" ;

OPREL        = ">" | "<" | ">=" | "<=" | "==" | "!=" ;
```

### Precedência (da menor para a maior)

| Nível | Operadores | Associatividade |
| --- | --- | --- |
| 1 | `\|\|` | esquerda |
| 2 | `&&` | esquerda |
| 3 | `> < >= <= == !=` | não associativa (`a < b < c` é erro) |
| 4 | `+ -` | esquerda |
| 5 | `* /` | esquerda |
| 6 | `-` e `!` unários | direita |

### Decisões de projeto

- Os parênteses em volta da condição de `if` e `while` são **opcionais**: `while enemy.visible { ... }` é válido, assim como `if (x < 1) { ... }`.
- Todo comando termina em `;`, exceto `if` e `while`, que terminam no bloco `{ }`.
- Chamadas como `move(20);` são comandos. `scan()` também pode aparecer dentro de expressões.
- O parser é descendente recursivo e para no **primeiro** erro.
- O nome de um sensor tem a forma `objeto.campo` (por exemplo `enemy.distance`). A semântica decide se o sensor existe.

## 3. Exemplos de erro sintático

| Código | Mensagem |
| --- | --- |
| `robot R { int x = ; }` | `linha 1, coluna 19: esperado número, true, false, identificador ou '('. Encontrado DELIMITADOR (';')` |
| `robot { }` | `linha 1, coluna 7: esperado o nome do robô. Encontrado DELIMITADOR ('{')` |
| `robot R { x = 1 < 2 < 3; }` | `linha 1, coluna 21: esperado ';'. Encontrado OPERADOR_RELACIONAL ('<')` |
| `robot R { if x < 1 { move(1); }` | `fim do arquivo encontrado depois da linha 1; esperado '}'` |

## 4. O que a sintaxe aceita e a semântica rejeita

O parser só confere a **forma**. Estes programas passam pelo parser e são recusados na etapa seguinte:

```text
robot R { int d; d = true; }   // tipos incompatíveis
robot R { fire(200); }         // argumento fora da faixa 1 a 3
robot R { y = 1; }             // variável não declarada
```