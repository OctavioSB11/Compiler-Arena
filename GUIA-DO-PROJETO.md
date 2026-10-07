# Guia do Projeto: Compiler Arena

Este documento é a fonte única de verdade da equipe. Quem tiver dúvida sobre o que fazer, como fazer ou quem faz, consulta aqui primeiro.
Se algo mudar, altera este arquivo por Pull Request, assim todo mundo vê a mudança.

Disciplina: Compiladores, UNIFAJ (Ciência da Computação). Trabalho do 2º bimestre, baseado no enunciado do professor Claiton.

---

## 1. O que é o projeto

Uma arena de batalha de robôs em que **cada robô só entra em combate depois que seu programa percorre uma cadeia real de compilação**:

```text
código-fonte (.robot) → léxico → sintático (AST) → semântico (tabela de símbolos)
        → IR (3 endereços) → otimização → código objeto (bytecode) → VM → arena
```

A batalha é o resultado visível. **O compilador é o centro do projeto e é o que será avaliado.**

### Regras que não podem ser quebradas

1. Proibido executar o código do robô na linguagem hospedeira (`exec`, `eval`, `import` do arquivo do robô etc.). A arena só recebe **bytecode** e quem o executa é a **VM**.
2. Proibido "simular" uma etapa sem transformação real. Cada etapa produz uma estrutura própria, que pode ser impressa e testada.
3. O robô interage com a arena **somente** por instruções da linguagem criada (`move`, `fire`...). Código-fonte e arena ficam desacoplados.
4. Qualquer erro (léxico, sintático ou semântico) **interrompe a compilação**: a arena não executa aquele robô.
5. Todos os integrantes precisam entender a solução inteira. A defesa técnica pode ser individual e qualquer um pode ser chamado para explicar ou alterar o código na hora (teste surpresa).

### Uso de IA

Pode usar para estudar conceitos, sugerir estruturas, apoiar a depuração, revisar documentação e investigar erros. **Não** pode substituir o entendimento: se você não consegue explicar um trecho do seu módulo sem olhar, reescreva-o ou estude-o até conseguir. A avaliação mede compreensão, não só a existência de código.

---

## 2. Prazos

| Data | Evento |
| --- | --- |
| 14/09 | Apresentação Parte I (analisador léxico e sintático). Já passou. |
| 21/09 e 28/09 | N1 e devolutiva. Já passaram. |
| **12/11** | **Congelamento de features** (meta interna) |
| **16/11** | **Apresentação Parte II** (compilador completo e arena) |
| 23/11 | Avaliação N2 |
| 30/11 | Devolutiva N2 |
| 07/12 e 14/12 | Avaliação substitutiva e devolutiva (margem de segurança) |

Marcos internos:

| Data | Marco |
| --- | --- |
| 12/10 | Contratos fechados (seção 5) e base no GitHub, com todos rodando os testes |
| 19/10 | Front-end pronto com `fire(200)` etc. sendo aceitos pelo parser; esqueleto da arena com 2 robôs se movendo |
| 26/10 | Semântica detecta todos os erros do enunciado; VM executa bytecode escrito à mão |
| **02/11** | **Marco crítico: um robô escrito na linguagem luta na arena passando pela cadeia inteira** |
| 09/11 | Otimizações, batalha com 3+ robôs, painel do compilador funcionando |
| 15/11 | Documentação final, slides e ensaio da defesa |

---

## 3. Equipe e responsabilidades

> **Atribuição sugerida.** Ajustem na primeira reunião e atualizem esta tabela por Pull Request. O importante é que cada módulo tenha **um dono** e **um revisor**.

| Módulo | Dono | Revisor | Pastas e arquivos | O que entrega |
| --- | --- | --- | --- | --- |
| **Front-end** (léxico, sintático, AST, CLI, testes de integração) | Danilo | Octávio Bordotti | `src/compiler/lexer.py`, `parser.py`, `ast_nodes.py`, `tokens.py`, `src/cli.py` | Já adaptado da Parte I. Passa a cuidar da CLI, da integração entre etapas e dos exemplos |
| **Semântica** (tipos, escopos, tabela de símbolos) | Octávio Bordotti | Rafael Tieppo | `src/compiler/semantic.py`, `symbols.py` | AST anotada, tabela de símbolos e mensagens de erro claras |
| **Back-end** (IR, otimização, geração de bytecode) | Matheus Porto | Danilo | `src/compiler/ir.py`, `optimizer.py`, `codegen.py` | IR de 3 endereços, 2 ou mais otimizações e bytecode |
| **Máquina virtual** | Rafael Tieppo | Matheus Porto | `src/vm/bytecode.py`, `vm.py` | Executor do bytecode com orçamento por tick |
| **Arena** (regras, física, interface, painel do compilador) | Octávio Morais | Rafael Tieppo | `src/arena/` | Batalha multi-robô, interface em pygame e painel das etapas |

Responsabilidades de todos:

- Escrever **testes** do próprio módulo em `tests/`.
- Escrever a **seção de documentação** do próprio módulo em `docs/`.
- Revisar os Pull Requests do módulo pelo qual é revisor, em até 24 horas.
- Explicar, na defesa, o módulo do **colega** (revisão cruzada). Por isso o revisor lê o código de verdade.

Funções de apoio (rodízio semanal, sem dono fixo):

- **Integrador da semana:** garante que a `main` roda e que os testes passam, e resolve conflitos de merge.
- **Anotador:** registra decisões e pendências no fim da reunião, em `docs/decisoes.md`.

---

## 4. Especificação da linguagem dos robôs (v1)

### Exemplo

```text
robot Alpha {
  int distancia;
  distancia = enemy.distance;

  while enemy.visible {
    if distancia < 100 {
      fire(3);
    } else {
      move(20);
    }
    rotate(15);
  }
}
```

### Regras

| Item | Definição |
| --- | --- |
| Programa | Um bloco `robot Nome { ... }` por arquivo `.robot` |
| Tipos | `int` e `bool` |
| Literais | Inteiros (`10`) e `true` / `false` |
| Declaração | `int x;` ou `int x = 10;` (declaração obrigatória antes do uso) |
| Operadores aritméticos | `+ - * /` (divisão inteira) e `-` unário |
| Operadores relacionais | `< > <= >= == !=` (operandos `int`, resultado `bool`) |
| Operadores lógicos | `&&`, `\|\|`, `!` (operandos `bool`) |
| Controle | `if` / `else` / `else if` e `while`. Parênteses na condição são opcionais |
| Comentários | `// até o fim da linha` |
| Escopo | Cada bloco `{ }` abre um escopo. Declaração duplicada no mesmo escopo é erro |

### Comandos (retornam nada; cada um consome 1 tick)

| Comando | Argumento | Faixa válida | Efeito |
| --- | --- | --- | --- |
| `move(n)` | `int` | 1 a 20 | Anda `n` unidades na direção atual |
| `back(n)` | `int` | 1 a 20 | Anda `n` unidades para trás |
| `rotate(g)` | `int` | -180 a 180 | Gira `g` graus (positivo é horário) |
| `scan()` | nenhum | | Atualiza os sensores `enemy.*` |
| `fire(p)` | `int` | 1 a 3 | Dispara com potência `p`: custa `p` de energia e causa `4*p` de dano |

### Sensores (somente leitura, não consomem tick)

| Sensor | Tipo | Faixa |
| --- | --- | --- |
| `energy` | `int` | 0 a 100 |
| `position.x`, `position.y` | `int` | 0 a 1000 |
| `enemy.visible` | `bool` | Atualizado por `scan()` |
| `enemy.distance` | `int` | Distância ao inimigo mais próximo visto no último `scan()` |
| `enemy.direction` | `int` | 0 a 359 graus (direção absoluta até o inimigo) |

Atribuir a um sensor (`energy = 5;`) ou chamar comando com número errado de argumentos é **erro semântico**.

### Erros que a semântica deve detectar (mínimo do enunciado)

| Erro | Exemplo | Mensagem esperada |
| --- | --- | --- |
| Incompatibilidade de tipos | `int d; d = true;` | `Linha 3: não é possível atribuir 'bool' a 'int'` |
| Uso antes da declaração | `x = 1;` sem `int x;` | `Linha 2: 'x' não foi declarada` |
| Declaração duplicada | `int x; int x;` | `Linha 3: 'x' já foi declarada na linha 2` |
| Parâmetro inválido | `fire(200);` | `Linha 5: fire() espera valor entre 1 e 3` |
| Tipo de parâmetro inválido | `move(false);` | `Linha 4: move() espera 'int', recebeu 'bool'` |
| Escopo incorreto | usar variável fora do bloco | `Linha 7: 'y' não existe neste escopo` |
| Operador incompatível | `true + 1` | `Linha 2: operador '+' não aceita 'bool'` |

Toda mensagem de erro inclui **linha** e **motivo**. A faixa de valores só pode ser checada em tempo de compilação quando o argumento é constante; com variável, a VM aplica a faixa em tempo de execução (valor fora da faixa é ajustado ao limite).

---

## 5. Contratos entre módulos

Estes contratos existem para que cinco pessoas trabalhem em paralelo sem esperar umas pelas outras. **Mudança em contrato só por Pull Request aprovado por todos os donos afetados.**

### 5.1 Front-end → Semântica (AST)

Estrutura `NoAST(tipo, valor, filhos, linha, coluna, tipo_semantico)` em `src/compiler/ast_nodes.py`.

| `tipo` | `valor` | `filhos` |
| --- | --- | --- |
| `Robo` | nome | `[Bloco]` |
| `Bloco` | | comandos |
| `Declaracao` | `"int"` ou `"bool"` | `[Identificador]` ou `[Identificador, expressão]` |
| `Atribuicao` | | `[Identificador, expressão]` |
| `Condicional` | | `[condição, Bloco]` ou `[condição, Bloco, Bloco ou Condicional]` |
| `Enquanto` | | `[condição, Bloco]` |
| `Chamada` | nome do comando | argumentos |
| `Operacao` | operador (`+`, `<`, `&&`, `-unario`, `!unario`...) | 1 ou 2 operandos |
| `Numero` / `Booleano` | valor | |
| `Identificador` | nome | |
| `Acesso` | `"enemy.distance"` etc. | |

A semântica preenche `tipo_semantico` (`"int"` ou `"bool"`) em cada expressão e **não altera** a forma da árvore.

### 5.2 Semântica → Back-end

Entrada do back-end: a AST anotada, já validada. Se há erro semântico, o back-end nem é chamado. Erros são lançados como `ErroSemantico(mensagem, linha)`, no mesmo estilo de `ErroSintatico`.

### 5.3 IR (representação intermediária): três endereços

Lista de instruções. Cada uma é uma tupla `(operação, argumento1, argumento2, resultado)` e é impressa assim:

| Instrução | Significado | Exemplo impresso |
| --- | --- | --- |
| `COPY` | `res = a` | `x = 30` |
| `BINOP` | `res = a op b` (`+ - * / < > <= >= == != && \|\|`) | `t1 = 10 + 20` |
| `UNOP` | `res = op a` (`neg`, `not`) | `t2 = not t1` |
| `LABEL` | marca um destino | `L1:` |
| `JUMP` | salto incondicional | `goto L1` |
| `JUMPF` | salta se `a` for falso | `ifFalse t1 goto L2` |
| `GETSENSOR` | lê um sensor | `t3 = sensor enemy.distance` |
| `PARAM` | empilha argumento | `param t3` |
| `CALL` | chama comando (`move`, `back`, `rotate`, `scan`, `fire`) | `call fire, 1` |

Variáveis do usuário mantêm o nome; temporários se chamam `t1`, `t2`... Rótulos se chamam `L1`, `L2`...
Exemplo: `x = 10 + 20; move(x);` vira

```text
t1 = 10 + 20
x = t1
param x
call move, 1
```

### 5.4 Otimização (IR → IR)

Mínimo de **duas** técnicas, cada uma em função própria, ativável por flag e testada com um "antes e depois":

1. **Constant folding:** `t1 = 10 + 20` vira `t1 = 30`.
2. **Simplificação algébrica:** `x + 0`, `x * 1`, `x * 0`, `x - 0`.
3. (Bônus) Propagação de constantes e eliminação de código morto.

### 5.5 Código objeto: bytecode de pilha

Cada variável recebe um índice fixo (`LOAD 0`, `STORE 0`). Instruções (uma por linha, texto legível, também serializável em JSON):

| Grupo | Instruções |
| --- | --- |
| Pilha e memória | `PUSH n`, `LOAD i`, `STORE i` |
| Aritmética | `ADD`, `SUB`, `MUL`, `DIV`, `NEG` |
| Comparação | `LT`, `GT`, `LE`, `GE`, `EQ`, `NE` |
| Lógica | `AND`, `OR`, `NOT` |
| Controle | `JMP addr`, `JZ addr` (salta se o topo for 0), `HALT` |
| Sensores | `SENSE nome` (`energy`, `pos_x`, `pos_y`, `enemy_visible`, `enemy_distance`, `enemy_direction`) |
| Ações da arena | `MOVE`, `BACK`, `ROTATE`, `FIRE` (consomem o topo da pilha) e `SCAN` (sem argumento) |

`true` é `1` e `false` é `0`. Exemplo do enunciado: `PUSH 30`, `MOVE`, `SCAN`, `PUSH 3`, `FIRE`.

### 5.6 VM → Arena (execução justa por ticks)

- A cada **tick**, a arena percorre os robôs em ordem fixa e pede à VM do robô para executar.
- A VM executa instruções até **uma ação** (`MOVE`, `BACK`, `ROTATE`, `FIRE` ou `SCAN`) ou até **50 instruções** (orçamento por tick), o que vier primeiro. Assim nenhum robô monopoliza o processamento e `while` infinito não trava a arena.
- A ação executada é devolvida à arena como `(nome, argumento)`. A VM não importa nada de `arena/`, e a arena não conhece o código-fonte.
- `HALT` (ou fim do programa): o robô fica parado, mas continua na arena.
- A VM lê sensores por uma interface (`obter_sensor(nome)`) fornecida pela arena.

### 5.7 Regras da arena (v1, o dono da arena pode refinar por PR)

| Item | Valor |
| --- | --- |
| Tamanho | 1000 x 1000 |
| Robôs por batalha | 2 ou mais, posições iniciais simétricas, energia 100 e direção voltada ao centro |
| Fim da batalha | Resta um robô vivo, ou 2000 ticks (vence quem tem mais energia; empate é declarado) |
| `scan()` | Vê o inimigo mais próximo a até 400 unidades e dentro de ±30° da direção do robô |
| `fire(p)` | Tiro instantâneo na direção do robô: acerta o primeiro inimigo a até 500 unidades e ±10° da linha. Dano `4*p` |
| Eliminação | Energia 0 ou menos |
| Parede | Movimento é limitado às bordas (sem dano) |
| Determinismo | Mesma entrada produz a mesma batalha (sem aleatoriedade ou com semente fixa) |

### 5.8 Interface e painel do compilador

A interface mostra a batalha, a energia, quem está ativo ou eliminado e o vencedor. Para cada robô, um painel das etapas:

```text
ROBÔ: ALPHA
✓ Análise Léxica   ✓ Análise Sintática   ✓ Análise Semântica
✓ Código Intermediário   ✓ Otimização   ✓ Código Objeto
STATUS: PRONTO PARA BATALHA
```

Em caso de erro: `✗ ANÁLISE SEMÂNTICA | Linha 14: fire() espera valor entre 1 e 3 | COMPILAÇÃO INTERROMPIDA | A arena não executa o robô.`

### 5.9 CLI de depuração (`src/cli.py`)

Cada etapa ganha uma flag: `--tokens`, `--ast`, `--symbols`, `--ir`, `--ir-opt`, `--bytecode`. É a nossa melhor ferramenta de defesa e de teste surpresa.
**Quem termina uma etapa adiciona a sua flag.**

---

## 6. Estrutura do repositório

```text
Compiler-Arena/
  README.md
  requirements.txt
  .gitignore
  .github/pull_request_template.md
  src/
    cli.py
    compiler/   tokens.py lexer.py ast_nodes.py parser.py
                semantic.py symbols.py ir.py optimizer.py codegen.py
    vm/         bytecode.py vm.py
    arena/      arena.py robot.py ui.py
  examples/     alpha.robot, erro_lexico.robot, erro_sintatico.robot,
                erro_semantico.robot, otimizacao.robot (+ robôs de batalha)
  tests/        test_front_end.py test_semantic.py test_ir.py ...
  docs/         este guia, gramática, IR, bytecode, VM, arena, decisões
```

Cada pessoa mexe **somente nas pastas do próprio módulo**. Para mexer em outro módulo, combine com o dono, ou peça ao dono para fazer.

---

## 7. Como trabalhar com o GitHub

### 7.1 Regras de ouro

1. **Ninguém dá `push` direto na `main`.** Todo trabalho entra por **Pull Request** (PR).
2. Cada módulo tem uma **branch própria de longa duração** para o dono, e cada tarefa pequena sai de uma **branch curta**.
3. Todo PR precisa de **1 aprovação** (o revisor do módulo) e de **testes passando** (`python -m pytest`).
4. Commits pequenos e frequentes, com mensagem clara.
5. Antes de começar a trabalhar, **sempre** atualize a sua branch com a `main`.

### 7.2 Configuração única (dono do repositório)

No GitHub, em *Settings → Collaborators*, adicionar os 5 integrantes com permissão **Write**.
Em *Settings → Branches → Add rule* para `main`: marcar **Require a pull request before merging**, com **1 aprovação**.

### 7.3 Nomes de branch

Padrão `tipo/modulo-descricao`, em minúsculas e sem acentos:

| Tipo | Quando | Exemplo |
| --- | --- | --- |
| `feat` | funcionalidade nova | `feat/semantica-tabela-simbolos` |
| `fix` | correção | `fix/parser-else-if` |
| `test` | só testes | `test/vm-saltos` |
| `docs` | só documentação | `docs/ir-especificacao` |

### 7.4 Mensagens de commit

Formato: `tipo(modulo): o que mudou`, no imperativo e em português.

```text
feat(semantica): detecta declaração duplicada
fix(parser): aceita else if encadeado
test(vm): cobre orçamento de 50 instruções por tick
docs(ir): descreve instruções de três endereços
```

### 7.5 Passo a passo do dia a dia

**Primeira vez (cada integrante):**

```bash
git clone https://github.com/OctavioSB11/Compiler-Arena.git
cd Compiler-Arena
python -m venv .venv
.venv\Scripts\Activate.ps1          # no Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                    # tudo deve passar
```

**Começar uma tarefa:**

```bash
git checkout main
git pull origin main                # traz o que os outros fizeram
git checkout -b feat/semantica-tabela-simbolos
```

**Trabalhar e salvar (repita quantas vezes precisar):**

```bash
git status                          # veja o que mudou
git add src/compiler/semantic.py tests/test_semantic.py
git commit -m "feat(semantica): cria tabela de símbolos com escopos"
```

**Enviar para o GitHub:**

```bash
git push -u origin feat/semantica-tabela-simbolos     # -u só na primeira vez da branch
```

**Abrir o Pull Request:** no GitHub, aparece o botão **Compare & pull request**. Preencha o modelo, escolha o revisor do seu módulo em *Reviewers* e crie.

**Revisar (quando você é o revisor):** abra o PR, aba *Files changed*, leia, comente nas linhas e, quando estiver ok, clique **Review changes → Approve**.

**Merge:** quem abriu o PR, depois da aprovação e dos testes verdes, clica **Squash and merge** (junta tudo num commit só) e depois apaga a branch.

**Depois do merge, todos atualizam:**

```bash
git checkout main
git pull origin main
```

### 7.6 Manter a sua branch atualizada (antes de abrir o PR)

```bash
git checkout main
git pull origin main
git checkout feat/sua-branch
git merge main                      # traz a main para dentro da sua branch
python -m pytest                    # confirme que nada quebrou
```

### 7.7 Conflitos de merge

Acontecem quando duas pessoas mexem no mesmo trecho. O Git marca o arquivo assim:

```text
<<<<<<< HEAD
sua versão
=======
versão da main
>>>>>>> main
```

1. Abra o arquivo no Antigravity (ele mostra os botões *Accept Current*, *Accept Incoming* e *Accept Both*).
2. Escolha, ou combine as duas versões, e **apague os marcadores** `<<<<<<<`, `=======` e `>>>>>>>`.
3. Rode `python -m pytest`.
4. `git add arquivo` e `git commit` (a mensagem padrão serve).

Se o conflito for em arquivo de **outro módulo**, não decida sozinho: chame o dono.

### 7.8 Issues e quadro de tarefas

- Cada tarefa vira uma **Issue** com título claro, responsável (*Assignees*) e *label* do módulo (`front-end`, `semantica`, `backend`, `vm`, `arena`, `docs`).
- Use um **GitHub Project** (quadro com colunas *A fazer*, *Fazendo*, *Em revisão*, *Feito*).
- No PR, escreva `Closes #12` na descrição para a issue fechar sozinha no merge.

### 7.9 O que nunca fazer

- `git push --force` em branch compartilhada.
- Subir a pasta `.venv`, `__pycache__` ou arquivos pessoais (o `.gitignore` já cuida, mas confira o `git status`).
- Commitar senhas, tokens ou chaves.
- Resolver conflito apagando o código do colega sem conversar.
- Deixar um PR parado mais de 24 horas sem resposta.

### 7.10 Se algo der errado

| Situação | O que fazer |
| --- | --- |
| Commit na `main` por engano (ainda sem push) | `git checkout -b feat/minha-branch` e depois, na `main`, `git reset --hard origin/main` |
| Quero desfazer alterações de um arquivo | `git restore caminho/do/arquivo` |
| `git push` rejeitado | `git pull origin sua-branch`, resolva conflitos e tente de novo |
| Bagunça geral | Não improvise: chame o integrante da semana |

---

## 8. Definição de pronto (Definition of Done)

Um módulo só está pronto quando:

- [ ] Funciona com os exemplos da pasta `examples/`.
- [ ] Tem testes automatizados que passam, incluindo casos de erro.
- [ ] Imprime a saída da sua etapa pela CLI (flag própria).
- [ ] Erros têm linha e mensagem compreensível.
- [ ] Está documentado em `docs/` (entrada, saída, decisões e exemplo).
- [ ] O dono consegue explicar o código **e** o revisor também.

---

## 9. Plano de trabalho por semana

| Semana | Foco | Front-end | Semântica | Back-end | VM | Arena |
| --- | --- | --- | --- | --- | --- | --- |
| **08/10 a 12/10** | Fase 0: base e contratos | Subir a base no GitHub; ajudar todos a rodar os testes | Ler a seção 4 e rascunhar a tabela de símbolos | Ler as seções 5.3 a 5.5 e propor ajustes | Ler as seções 5.5 e 5.6 e propor ajustes | Ler as seções 5.7 e 5.8 e propor ajustes |
| **13/10 a 19/10** | Fase 1 | Completar testes de erro e mensagens do parser; CLI | Declarações, escopos e tipos de expressão | Esqueleto de `ir.py` (gerar IR de expressões) | Pilha, memória e aritmética da VM (bytecode à mão) | Robôs, movimento, rotação, scheduler por ticks e render básico |
| **20/10 a 26/10** | Fase 2 | Exemplos de erro e `docs/gramatica.md` | Verificar chamadas, faixas, operadores e escopo; mensagens | IR para `if`, `while` e chamadas | Saltos, sensores, ações e orçamento de 50 instruções | Sensores, `scan`, `fire` e dano |
| **27/10 a 02/11** | Fase 3: **integração** | Integrar etapas na CLI e no pipeline | Corrigir o que a integração revelar | Gerador de bytecode a partir da IR | Integrar VM e arena | Carregar robôs compilados; **robô de verdade luta** |
| **03/11 a 09/11** | Fase 4 | Testes ponta a ponta | Casos extremos | **Otimizações** e bytecode otimizado | Robustez (divisão por zero, saltos inválidos) | Fim de jogo, vencedor, 3+ robôs e **painel do compilador** |
| **10/11 a 15/11** | Fase 5 | Apresentação e roteiro de demonstração | Docs da semântica | Docs de IR, otimização e bytecode | Docs da VM | Docs da arena e vídeo/GIF da batalha |
| **16/11** | **Apresentação Parte II** | | | | | |

### Ensaio da defesa (semana de 10/11)

- Cada integrante explica **um módulo que não escreveu** (revisão cruzada).
- Teste surpresa simulado: um colega pede, sem aviso, uma mudança pequena (novo operador, nova faixa de `fire`, novo comando). Meta: fazer em menos de 30 minutos, passando por todas as etapas.
- Revisem as perguntas prováveis: "por que descendente recursivo?", "por que três endereços?", "o que o constant folding faz aqui?", "como a VM impede um loop infinito?", "como vocês garantem que o código do robô não é executado direto?".

---

## 10. Entregáveis finais

- [ ] Código-fonte completo e organizado (este repositório, `main` estável).
- [ ] Documentação técnica em `docs/`: arquitetura, gramática, regras semânticas, IR, otimizações, bytecode, VM e arena.
- [ ] Exemplos: programa válido, erro léxico, erro sintático, erro semântico e caso de otimização (pasta `examples/`).
- [ ] Arena funcional com múltiplos robôs e painel do compilador.
- [ ] Apresentação (slides) e roteiro de demonstração.
- [ ] Todos prontos para a defesa técnica individual e o teste surpresa.

---

## 11. Comunicação e reuniões

- **Reunião curta duas vezes por semana** (15 minutos): o que fiz, o que vou fazer, o que me bloqueia.
- **Bloqueio é avisado na hora**, no grupo, não na reunião seguinte.
- Decisões importantes entram em `docs/decisoes.md` (data, decisão, quem decidiu).
- Dúvida sobre o enunciado: perguntar ao professor, e anotar a resposta em `docs/decisoes.md`.
- Pendências conhecidas hoje, a confirmar com o professor: existência de rubrica com pesos para a N2 e se a linguagem precisa aceitar `float`.

---

## 12. Glossário rápido

| Termo | Significado |
| --- | --- |
| AST | Árvore sintática abstrata: o programa em forma de árvore |
| Tabela de símbolos | Registro de variáveis (nome, tipo, escopo, linha de declaração) |
| IR | Representação intermediária: código simples, independente da linguagem-fonte e da máquina |
| Bytecode | Código objeto da nossa máquina virtual |
| VM | Máquina virtual: programa que executa o bytecode |
| Tick | Um passo de tempo da arena. Cada robô age uma vez por tick |
| PR | Pull Request: pedido para juntar a sua branch na `main` |
