# Isa

Código e configuração da assistente pessoal Isa, baseada no [MIRA](https://github.com/Vexillon-ai/MIRA).
Esta versão registra a instalação inspecionada em 29/09/2026 e prepara um ambiente separado para desenvolvimento.
**A publicação deste repositório não implanta mudanças na VPS.**

## O que está versionado

| Caminho | Conteúdo |
| --- | --- |
| `docker-compose.yml` | Ambiente de desenvolvimento com MIRA, LiteLLM e calendário MCP |
| `vendor/mira/` | Código e Dockerfile do MIRA, como submódulo na revisão `043bbc2ffaa9afeadf2006d860c154a1510993d5` |
| `services/mcp-calendar/` | Código Python e Dockerfile do calendário Microsoft |
| `litellm/` | Modelos configurados e callback usado na VPS |
| `deploy/vps/` | Referência da instalação existente, versões e limites conhecidos |
| `.env.example` | Variáveis documentadas com placeholders |

O código principal do calendário foi comparado por SHA-256 com os arquivos dentro do container em execução.
O checkout MIRA encontrado na VPS estava limpo e na revisão indicada. A imagem MIRA não tem metadados suficientes para comprovar que foi construída exatamente dessa revisão; seu ID está registrado no inventário.

## Obter o código

```bash
git clone --recurse-submodules https://github.com/mhdata-dev/Isa_AI.git
cd Isa_AI
# Para um clone já existente:
git submodule update --init --recursive
```

O GitHub apresenta `vendor/mira` como um link para o código do upstream na revisão fixada, incluindo seu Dockerfile e licença. Não é uma pasta vazia.

## Ambiente de desenvolvimento

Requer Git e Docker Compose. O Compose usa o projeto `isa-development`, volumes próprios e portas locais `18080` e `14000`; não inclui o proxy compartilhado da VPS.

1. Crie `.env` a partir de `.env.example` e `services/mcp-calendar/.env` a partir do exemplo nessa pasta.
2. Preencha as credenciais de desenvolvimento. A chave do calendário deve ser uma chave Fernet válida.
3. Inicialize o submódulo e valide a configuração:

   ```bash
   docker compose config --quiet
   docker compose build
   ```

4. Configure o MIRA em um volume novo pelo onboarding do upstream:

   ```bash
   docker compose run --rm mira setup
   ```

   Para usar o proxy interno, configure o provedor compatível com OpenAI em `http://litellm:4000/v1`, a chave correspondente a `LITELLM_MASTER_KEY` e um alias definido em `litellm/config.yaml` (por exemplo, `main-model`). Os nomes de modelos foram preservados da VPS; a disponibilidade depende da conta do provedor.

5. Suba somente este ambiente e confira o estado:

   ```bash
   docker compose up -d
   docker compose ps
   ```

   A interface ficará em `http://127.0.0.1:18080`. Para calendário, configure o cliente MCP do MIRA em `http://mcp-calendar:8000/mcp` e um callback OAuth acessível ao navegador, registrado também no aplicativo Microsoft. As portas do calendário ficam apenas na rede Docker; o exemplo de rotas está em `deploy/vps/Caddyfile.isa.example`.

Credenciais, tokens, histórico de conversas, configuração privada do MIRA, bancos e volumes permanecem fora do Git. Um clone novo não restaura as contas nem a memória da Isa.

## Instalação existente e próximos passos

Leia [a referência da VPS](deploy/vps/README.md) antes de planejar qualquer implantação. O código publicado não deve ser copiado por cima da instalação ativa.

A integração **Garmin Connect → n8n → PostgreSQL → Isa via MCP** está planejada, mas ainda não foi implementada nem implantada. O cliente escolhido é `python-garminconnect`.

## Validação desta importação

- Sintaxe dos arquivos Python e configuração Compose verificadas sem executar serviços.
- Arquivos privados excluídos do Git e do contexto de build do calendário.
- Build completo e autenticação real não fazem parte desta importação; consultar os limites registrados na referência da VPS.
