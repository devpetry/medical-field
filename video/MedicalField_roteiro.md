# MedicalField — roteiro, narração e storyboard

Duração total: 7:36 · 1920 × 1080 · 30 fps · narração pt-BR

## Cena 1 — Apresentação (0:00 – 0:38)

| Tempo | Narração | Na tela |
| --- | --- | --- |
| 0:00 | Em uma emergência, cada segundo conta. | Ambulância em movimento; linha de ECG pulsando. |
| 0:03 | Equipes do SAMU, de rodovias e de resgate em desastres atendem pacientes em locais onde a internet é instável, lenta ou simplesmente não existe. | Ícone de sinal de rede falha e fica cortado sobre a ambulância. |
| 0:13 | Mesmo assim, sinais vitais, nível de consciência, triagem e medicamentos precisam ser registrados na hora. | Quatro ícones surgem: sinais vitais, Glasgow, triagem e medicamentos. |
| 0:20 | A falta de conexão não pode impedir esse registro. | Os ícones convergem para um prontuário com a marca de 'sem conexão'. |
| 0:23 | Para resolver esse problema, nasceu o MedicalField: um prontuário eletrônico de emergência com arquitetura offline-first. | Revelação da marca MedicalField e do subtítulo. |
| 0:30 | O profissional registra tudo no próprio dispositivo, e os dados são sincronizados com o servidor central assim que a conexão retorna. | Dispositivo grava localmente; ao voltar o sinal, dados seguem para o servidor. |

## Cena 2 — Arquitetura (0:38 – 1:47)

| Tempo | Narração | Na tela |
| --- | --- | --- |
| 0:39 | Vamos conhecer a arquitetura. | Surgem as duas áreas: dispositivo da ambulância e VM da Univates. |
| 0:42 | Na ambulância fica o cliente desktop, construído com Electron, React e TypeScript. | Card do cliente desktop. |
| 0:47 | Ele guarda os dados num banco local SQLite, embarcado no próprio dispositivo. | Cilindro SQLite ligado ao cliente. |
| 0:53 | Do outro lado, na máquina virtual da Univates, fica toda a parte do servidor. | Destaque da área da VM. |
| 0:58 | A porta de entrada é o Nginx, que atua como API Gateway e encaminha cada requisição para o serviço certo. | Barra do Nginx; requisições saem do cliente e chegam ao gateway. |
| 1:05 | O auth-service, em Node.js, cuida do login e da emissão dos tokens. | Card auth-service. |
| 1:10 | O clinical-service, em Java com Spring Boot, é o núcleo: pessoas, prontuários, atendimentos, sincronização e logs. | Card clinical-service. |
| 1:18 | O document-service, em Python com FastAPI, gera a ficha em PDF e envia o e-mail. | Card document-service e a chamada REST ao clinical-service. |
| 1:24 | Os três serviços gravam no banco central PostgreSQL, cada um no seu próprio schema. | Cilindro PostgreSQL com os schemas auth, clinical, audit e document. |
| 1:29 | O document-service também se comunica com um servidor SMTP para enviar os e-mails. | Servidor SMTP fora da VM. |
| 1:35 | Já o portal administrativo, feito com React, Vite e TypeScript, é servido pelo próprio Nginx. | Card do portal ligado ao Nginx. |
| 1:42 | Resumindo: SQLite no cliente, PostgreSQL no servidor. | Os dois bancos piscam em destaque. |

## Cena 3 — Autenticação e segurança (1:47 – 2:44)

| Tempo | Narração | Na tela |
| --- | --- | --- |
| 1:48 | Tudo começa pelo login. | Tela de login no cliente. |
| 1:50 | O profissional informa seu registro, que pode ser CRM, COREN ou ID de socorrista, e sua senha. | Seleção do tipo de registro e digitação. |
| 1:57 | O auth-service confere o hash da senha e devolve um token JWT, válido por doze horas, o tempo de um plantão. | POST /auth/login vai ao auth-service; o JWT volta. |
| 2:04 | O cliente guarda esse token e um hash da senha no SQLite. | Token e hash entram na tabela sessao do SQLite. |
| 2:09 | A partir daí, cada requisição leva o token, e os outros serviços validam a assinatura localmente, sem consultar o auth-service. | Requisições com JWT chegam ao clinical-service e ao document-service; assinatura validada. |
| 2:17 | Sem token, ou com token inválido, a resposta é 401: acesso negado. | Requisição sem token recebe 401. |
| 2:23 | E se não houver internet? O login local confere o hash guardado no dispositivo, e o token é renovado quando a conexão voltar. | Modo offline: login validado contra o hash local. |
| 2:31 | Além disso, todos os serviços têm um middleware de auditoria. | Camada de middleware sobre os três serviços. |
| 2:35 | Cada requisição registra data e hora, IP, profissional, método, rota, status e tempo de resposta, na tabela audit.access_log. | Linhas da auditoria sendo gravadas. |

## Cena 4 — Atendimento de emergência (2:44 – 3:35)

| Tempo | Narração | Na tela |
| --- | --- | --- |
| 2:45 | Agora, vamos acompanhar um atendimento dentro da ambulância. | Cliente desktop aberto; etapas do atendimento à esquerda. |
| 2:49 | Primeiro, o profissional identifica o paciente, ou cadastra uma nova pessoa. | Etapa 1: pessoa. |
| 2:54 | Em seguida, consulta o prontuário, ou cria um novo. | Etapa 2: prontuário. |
| 2:57 | Então abre um novo atendimento. | Etapa 3: atendimento. |
| 3:00 | Registra os sinais vitais: pressão arterial, frequência cardíaca e respiratória, saturação, temperatura e glicemia. | Etapa 4: sinais vitais. |
| 3:08 | Preenche a Escala de Glasgow: abertura ocular, resposta verbal e resposta motora, somando de três a quinze. | Etapa 5: Glasgow, total 13. |
| 3:14 | Classifica a triagem pelos protocolos Manchester e START. | Etapa 6: triagem Manchester e START. |
| 3:19 | E registra a conduta e os medicamentos administrados, conferindo a dose com a dose máxima do medicamento cadastrado. | Etapa 7: medicação e conduta. |
| 3:26 | Cada informação é gravada primeiro no SQLite do dispositivo. Esteja online ou offline, o fluxo na tela é exatamente o mesmo. | Chave online/offline alterna; gravação no SQLite continua igual. |

## Cena 5 — Offline-first (3:35 – 4:55)

| Tempo | Narração | Na tela |
| --- | --- | --- |
| 3:36 | Esta é a parte mais importante: o funcionamento offline-first. | Cliente, SQLite, Outbox e servidor em cena. |
| 3:41 | Imagine que a ambulância entra em uma área sem sinal. | Sinal cai. |
| 3:44 | O indicador muda para OFFLINE. Mas o profissional continua trabalhando normalmente. | Indicador vermelho OFFLINE. |
| 3:49 | Cada registro é salvo no SQLite e, na mesma transação, gera um item na Outbox, a fila do que ainda não chegou ao servidor. | Pessoa, prontuário e atendimento entram no SQLite e na Outbox. |
| 3:57 | As ações também ficam registradas no log local. | Linhas do local_log. |
| 4:01 | O contador de pendências aumenta: uma pessoa, um prontuário, um atendimento. | Contador vai a 3. |
| 4:06 | Nenhum atendimento depende do servidor para ser registrado. | Selo 'salvo localmente'. |
| 4:09 | Algum tempo depois, a ambulância chega ao hospital, e a conexão volta. | Sinal volta. |
| 4:14 | O indicador muda para ONLINE. O ConnectivityMonitor avisa o SyncService, seguindo o padrão Observer. | Indicador verde; notificação ConnectivityMonitor para SyncService. |
| 4:21 | Começa o push: a Outbox é enviada em lotes, na ordem certa: pessoa, depois prontuário, depois atendimento. | Itens viajam para POST /sync/push. |
| 4:28 | O servidor processa cada item e responde com a confirmação. | Respostas APLICADO voltam. |
| 4:32 | Os registros passam para SINCRONIZADO, e o contador de pendências volta a zero. | Status muda; contador zera. |
| 4:38 | Os logs locais seguem para o servidor pela rota POST /log. | Logs enviados. |
| 4:41 | Depois vem o pull: o cliente pergunta o que mudou desde a última sincronização e recebe as novidades, como novos medicamentos e dados de apoio. | GET /sync/pull traz medicamentos e dados de apoio. |
| 4:50 | Push envia o que está no dispositivo. Pull traz o que está no servidor. | Setas PUSH e PULL lado a lado. |

## Cena 6 — Idempotência e conflitos (4:55 – 6:03)

| Tempo | Narração | Na tela |
| --- | --- | --- |
| 4:56 | Mas e se a conexão cair no meio do envio? Os dados não podem ser duplicados. | Envio interrompido no meio do caminho. |
| 5:02 | Por isso, cada registro nasce com um UUID gerado no próprio dispositivo. O mesmo registro tem o mesmo identificador no cliente e no servidor. | UUID igual no cliente e no servidor. |
| 5:11 | Cada item da Outbox também carrega uma chave de idempotência, formada pelo ID do item e pelo ID do dispositivo. | Idempotency-Key = outboxId + deviceId. |
| 5:18 | Se o mesmo item chegar duas vezes, o servidor reconhece a chave e responde DUPLICADO, sem gravar nada de novo. | Segundo envio recebe DUPLICADO. |
| 5:25 | E quando o servidor já tem uma versão mais nova do registro? Aí entra a resolução de conflitos, com o padrão Strategy. | Três cartões de estratégia. |
| 5:33 | Na LastWriteWinsStrategy, usada para pessoa e prontuário, vence a alteração mais recente feita pelo profissional. | Versão mais recente vence. |
| 5:40 | Na AppendOnlyMergeStrategy, usada para sinais vitais e medicações, as listas são unidas. Nada é apagado. | Listas unidas pelo id. |
| 5:48 | E na ServerWinsStrategy, usada para medicamentos, prevalece o cadastro do servidor. | Versão do servidor mantida. |
| 5:54 | Cada decisão é gravada na tabela audit.sync_evento, com os dados de antes, os de depois e a estratégia usada. Tudo pode ser auditado. | Linha de auditoria com antes, depois e estratégia. |

## Cena 7 — Portal administrativo (6:03 – 6:27)

| Tempo | Narração | Na tela |
| --- | --- | --- |
| 6:04 | No portal administrativo, o profissional faz login e consulta as informações. | Portal web: login e painel. |
| 6:10 | Os profissionais cadastrados, as pessoas atendidas, os prontuários, os atendimentos e os registros de auditoria. | Menu percorre as cinco listas. |
| 6:16 | Enquanto o cliente estava offline, o atendimento novo não aparecia no portal. | Lista de atendimentos sem o registro novo; cliente com 3 pendências. |
| 6:21 | Depois da sincronização, ele surge na lista, marcado como criado offline. | Registro novo entra na lista com a marca 'criado offline'. |

## Cena 8 — Ficha em PDF e e-mail (6:27 – 7:02)

| Tempo | Narração | Na tela |
| --- | --- | --- |
| 6:28 | Por fim, a Ficha de Atendimento. | Atendimento selecionado. |
| 6:30 | O profissional seleciona um atendimento e pede a ficha em PDF. | Botão 'Gerar ficha (PDF)'. |
| 6:34 | O document-service recebe a solicitação e busca os dados do atendimento no clinical-service, repassando o token do usuário. | document-service consulta o clinical-service com o JWT. |
| 6:42 | Com os dados em mãos, gera o PDF com o paciente, os sinais vitais, o Glasgow, a triagem e as medicações. | Ficha em PDF sendo montada. |
| 6:50 | O arquivo fica disponível para download. | Download do PDF. |
| 6:53 | E também pode ser enviado por e-mail ao paciente ou a um familiar. O envio passa pelo servidor SMTP e fica registrado no histórico. | E-mail com anexo passa pelo SMTP e chega ao familiar. |

## Cena 9 — Encerramento (7:02 – 7:36)

| Tempo | Narração | Na tela |
| --- | --- | --- |
| 7:03 | Esse é o MedicalField. | Marca ao centro. |
| 7:05 | O atendimento continua mesmo sem internet. | Benefício 1. |
| 7:08 | Os dados ficam no dispositivo e sincronizam automaticamente. | Benefício 2. |
| 7:13 | As informações clínicas ficam organizadas, seguras e rastreáveis. | Benefícios 3 e 4. |
| 7:18 | A arquitetura é baseada em microsserviços, em três linguagens diferentes. | Benefício 5. |
| 7:23 | E a ficha de atendimento pode ser gerada e compartilhada em poucos cliques. | Benefício 6. |
| 7:28 | MedicalField: tecnologia, confiabilidade e continuidade no atendimento de emergência, mesmo onde a conexão não chega. | Assinatura final. |
