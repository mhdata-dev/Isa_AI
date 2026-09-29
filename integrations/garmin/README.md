# Integração Garmin e n8n

Projeto Docker independente: `isa-integrations`.

```
Garmin Connect → coletor Python → n8n → PostgreSQL → MCP de leitura → Isa
```

O coletor usa [python-garminconnect](https://github.com/cyberjunky/python-garminconnect), cliente não oficial escolhido para esta integração. Ele consulta atividades, resumo diário, sono, frequência cardíaca, HRV, estresse e Body Battery. Não altera atividades ou configurações na conta Garmin.

## Isolamento

- PostgreSQL, n8n e sessão Garmin têm volumes novos, exclusivos deste projeto.
- PostgreSQL e APIs não publicam portas no host.
- n8n escuta apenas em `127.0.0.1:5678`; acesso por túnel SSH.
- O MCP entra em uma rede privada que recebe somente o container da Isa. Não há autenticação HTTP nessa rede dedicada, pois o cliente MCP desta revisão do MIRA não oferece headers configuráveis. Não conecte outros containers a essa rede nem publique a porta MCP.
- O usuário PostgreSQL do MCP só pode ler dados; a credencial do n8n só executa a função de ingestão. O n8n usa outro usuário e banco para seus próprios metadados.
- O Compose existente da Isa, o proxy compartilhado e os demais projetos permanecem fora deste diretório.

## Instalação em diretório novo

Na VPS, copiar esta pasta para `/opt/isa-integrations` e executar:

```bash
cd /opt/isa-integrations
python3 scripts/provision.py
docker compose config --quiet
docker compose build garmin-collector
docker compose run --rm --no-deps garmin-collector python -m unittest discover -s tests -v
docker compose up -d
python3 scripts/bootstrap_n8n.py
docker compose exec -T n8n n8n publish:workflow --id=isaGarminDailySync
docker compose restart n8n
```

Os segredos são gerados no servidor, em `secrets/`, com diretório acessível apenas ao operador. Eles são montados individualmente nos containers que precisam deles. Não copie essa pasta para o Git. O script preserva valores existentes; uma nova execução não faz rotação de senhas.

As migrações em `database/` executam somente na primeira inicialização do volume PostgreSQL. Alterações futuras devem usar novas migrações. Não apagar volumes para reaplicar uma migração.

## Autorizar Garmin e conectar à Isa

Com a instalação pronta, o usuário pode concluir as duas autorizações em um comando:

```bash
cd /opt/isa-integrations
python3 scripts/authorize.py
```

O script pede primeiro email/senha/MFA da Garmin, executa a sincronização pelo n8n e depois pede usuário/senha da Isa para cadastrar o MCP na conta correta. As entradas ficam ocultas e a sessão de login da Isa é encerrada ao terminar. Se uma etapa falhar, ela não é declarada concluída; as etapas anteriores são preservadas. O cadastro não modifica outros servidores MCP.

### Autorizar somente Garmin

O próprio usuário executa, em um terminal SSH interativo:

```bash
cd /opt/isa-integrations
docker compose exec garmin-collector python login.py
```

Email, senha e código MFA são digitados de forma oculta e enviados à Garmin pelo cliente. A senha não é salva; a sessão fica no volume `garmin_session`. Não compartilhe a sessão ou cole credenciais no chat. Antes do login, o workflow verifica a ausência da sessão e encerra sem chamar a Garmin.

## Acessar n8n

No computador local:

```powershell
ssh -i "$env:USERPROFILE\.ssh\isa_vps_ed25519" -N -L 5678:127.0.0.1:5678 root@SEU_SERVIDOR
```

Com o terminal aberto, acesse `http://localhost:5678` e crie a conta proprietária do n8n. O painel não está exposto à internet. Use `localhost`, pois cookies seguros em HTTP local dependem desse tratamento do navegador.

O workflow `Isa - Garmin daily synchronization` traz os últimos sete dias em cada execução, às 08:15 e 20:15 no fuso Europe/Madrid, após ser publicado. Uma execução manual inicia a primeira sincronização. Arquivos de workflow versionados são exportados pelo n8n; a definição programática usada na importação está em `n8n/definition.py`.

Para executar pela linha de comando sem imprimir os payloads de saúde: `python3 scripts/run_sync.py`.

Dados de execução não são salvos no histórico do n8n, inclusive em erros. As credenciais ficam cifradas pelo n8n. Falhas da Garmin retornam códigos de erro sem corpo de respostas, senhas ou tokens. Um limite de requisições impõe pausa de 15 minutos, sem repetição automática imediata.

## Conectar à Isa

```bash
cd /opt/isa-integrations
sh scripts/link_mira.sh
```

Esse comando conecta somente `warp-drive-pilot-mira-1` à rede do MCP, sem reiniciar o container. Na tela de servidores MCP da Isa, adicione:

- Nome: `garmin`
- Transporte: `http` (Streamable HTTP)
- URL: `http://isa-garmin-mcp:8000/mcp`
- Ativado: sim

Ferramentas: `garmin_sync_status`, `garmin_daily_summary` e `garmin_activities`.
O código MIRA encontrado suporta recarregar o registro após cadastro pela API/UI. Após recriar o container da Isa em uma implantação futura, executar novamente `link_mira.sh`; a conexão de rede feita em execução não altera seu Compose existente.

## Dados e limites

- Uma chave por data/métrica e uma chave por ID Garmin evitam duplicações. Uma nova leitura substitui somente dados mais antigos; métricas que falham não apagam leituras anteriores.
- O banco guarda os payloads originais. O MCP retorna resumos com unidades explícitas e valores ausentes como `null`, sem inventar zeros ou oferecer interpretações médicas.
- A data do sono segue a data da Garmin (normalmente o despertar). Consultas MCP aceitam no máximo 31 dias; atividades têm paginação.
- Reexecuções não removem atividades apagadas na Garmin. Trata-se de um histórico de ingestão, não de um espelho com propagação de exclusões.
- Dados reais só estarão disponíveis depois da autorização Garmin e da primeira sincronização. Login feito não significa que todos os sensores/métricas estejam disponíveis para a conta.

## Verificar e manter

```bash
docker compose ps
docker compose exec -T postgres psql -X -U postgres -d garmin < database/test_ingestion.sql
docker compose exec -T garmin-mcp python smoke_mcp.py
python3 scripts/verify.py
```

O teste SQL usa dados sintéticos dentro de uma transação e termina em `ROLLBACK`; não deixa registros de teste. Testes Python verificam falhas de autenticação, limites de requisições, datas, ausência de métricas e proteção dos endpoints.

`scripts/test_workflow.py` cria um workflow temporário identificado, verifica sete itens passando por Code → HTTP → SQL parametrizado e remove apenas esse workflow ao terminar. Não grava dados de saúde. As imagens e as dependências Python estão fixadas nas versões testadas.

Na instalação inicial de 29/09/2026, o banco novo foi ajustado de PostgreSQL 16 para 17 por compatibilidade com n8n 2.39.5. O volume anterior e os backups privados em `runtime/` foram preservados no servidor; o Compose atual usa `postgres17_data`. Nenhum banco de outro projeto participou dessa mudança.

Para parar esta integração, use `docker compose stop` somente neste diretório. Não usar limpeza global do Docker. Backups privados precisam incluir os três volumes e `secrets/`; publicar o código não preserva dados nem credenciais.
