# O que mudou em relação ao analisador da Parte I

- `automato.py` → `src/compiler/lexer.py` e `tokens.py`. Mesma interface (`AutomatoLexico.analisar`, `Token`).
  Vocabulário novo: `robot int bool if else while true false`. Removidos `real`, `string` e `escreva`. Adicionado o delimitador `.` para sensores.
  Erros léxicos agora viram `ErroLexico` com linha e coluna (`verificar()`), e `12abc` é número malformado.
- `automato_sintatico.py` → `src/compiler/parser.py` e `ast_nodes.py`. Mesmo estilo (descendente recursivo, `NoAST`, `ErroSintatico`).
  Novos: bloco `robot Nome { }`, chamadas (`move(20);`), acesso a sensor (`enemy.distance`), `bool`, `!` e `-` unários,
  `else if`, condição de `if`/`while` sem parênteses, `&&` com precedência maior que `||`.
  Corrigido: `!` era lexado mas o parser não o aceitava; `&&` e `||` tinham a mesma precedência.
  `NoAST` ganhou `tipo_semantico`, preenchido pela análise semântica.
- `interface_sintatico.py` (customtkinter) não foi portada: o painel do compilador da arena será feito em pygame.
  A tabela de tokens e a AST ficam disponíveis pela CLI (`--tokens`, `--ast`).
