# Apresentação

Material para apresentar o MedicalField: o passo a passo do dia, a explicação do sistema e os diagramas.

| Arquivo | O que é | Quando usar |
| --- | --- | --- |
| [`ROTEIRO-DA-APRESENTACAO.md`](ROTEIRO-DA-APRESENTACAO.md) | **A cola para a hora**: endereços e contas, preparo, SQL dos passos, o cliente no notebook, os 17 passos com o que falar, extras, o que fazer se algo der errado, atualizar e reinstalar a VM | Aberto ao lado durante a apresentação |
| [`GUIA-DE-DEMONSTRACAO.md`](GUIA-DE-DEMONSTRACAO.md) | **O sistema explicado**: cada peça e onde fica no código, bancos, login, sincronização, conflitos, regras clínicas, padrões; e os 17 passos com o que acontece por trás de cada um, mais as perguntas prováveis | Para estudar antes |
| [`diagramas/`](diagramas) | Imagens em formato de slide (16:9, 3840×2160), para projetar e ler de longe | Na tela, durante as explicações |

## Diagramas

Cada parte do sistema tem uma cor, a mesma em todas as imagens: **azul-claro** = cliente e portal, **verde-limão** = auth-service (Node.js), **laranja** = clinical-service (Java), **amarelo** = document-service (Python), **verde-água** = Nginx, **roxo** = bancos, **rosa** = tokens e segurança.

| Imagem | Mostra | Use para |
| --- | --- | --- |
| [`01-arquitetura`](diagramas/01-arquitetura.png) | As peças, a linguagem de cada serviço e quem fala com quem | Abrir a apresentação |
| [`02-banco-servidor`](diagramas/02-banco-servidor.png) | O PostgreSQL: um schema e um usuário por serviço, e as tabelas | "Como é o banco?" |
| [`03-banco-local-sqlite`](diagramas/03-banco-local-sqlite.png) | O SQLite do cliente: a cópia dos dados e as tabelas de controle | "O que o cliente guarda?" |
| [`04-offline-first`](diagramas/04-offline-first.png) | Salvar → transação com a Outbox → enviar agora ou depois | Passos 7, 12 e 14 |
| [`05-sincronizacao`](diagramas/05-sincronizacao.png) | As cinco mensagens de uma rodada: push, resultado, logs, pull | Passos 6, 11 e 14 |
| [`06-conflito`](diagramas/06-conflito.png) | As três estratégias de conflito e para que dado cada uma vale | Pergunta sobre conflitos |
| [`07-login-e-token`](diagramas/07-login-e-token.png) | Login, JWT validado pelos três serviços e login offline | Passos 1 e 5 |
| [`08-rede-e-portas`](diagramas/08-rede-e-portas.png) | O que fica aberto na VM (80 e 22) e o que fica só em 127.0.0.1 | Segurança e o papel do Nginx |
| [`09-padroes-de-projeto`](diagramas/09-padroes-de-projeto.png) | Os sete padrões, onde estão e para quê | Pergunta dos padrões |

## Mudar uma imagem

Cada imagem é uma página HTML em `diagramas/fontes/`: as caixas e os textos ficam no próprio arquivo, e as setas são desenhadas pelo `fontes/base.js` a partir das caixas (`<i class="seta" data-de="caixa.lado" data-para="outra.lado">`). Abra o `.html` no navegador para ver a mudança e gere os PNG de novo com o Google Chrome ou o Chromium instalado:

```bash
./apresentacao/diagramas/gerar.sh
```

`./apresentacao/diagramas/gerar.sh 06` gera só as que têm `06` no nome.
