# Referência da VPS — 29/09/2026

## Origem

- Instalação ativa: `/home/ops/warp-drive-pilot`, projeto Compose `warp-drive-pilot`.
- Código do calendário: `/home/ops/isa-project/services/mcp-calendar`.
- Checkout MIRA: `/home/ops/mira-src`, remoto público `https://github.com/Vexillon-ai/MIRA.git`.
- Revisão encontrada: `043bbc2ffaa9afeadf2006d860c154a1510993d5` (`Sync public snapshot for v0.350.1`), sem alterações locais.
- A pasta da instalação não tinha repositório Git. Publicar esta cópia não cria sincronização automática nem altera o diretório da VPS.

## Arquivos de referência

`docker-compose.reference.yml` é uma cópia semanticamente equivalente do Compose encontrado, com formatação YAML normalizada. Conserva nomes, caminhos e tags observados. **Não é um arquivo para subir um segundo ambiente ou substituir a instalação ativa.** As tags `mira:local` e `mcp-calendar:local` identificam imagens locais da VPS, não imagens públicas para download.

`Caddyfile.isa.example` contém somente as rotas da Isa, com domínio parametrizado. O Caddy ativo também atende dois sites de outro projeto. Substituir seu Caddyfile por este exemplo removeria essas rotas. Qualquer implantação futura precisa preservar o proxy compartilhado e ser tratada separadamente.

`manifest.json` foi preservado como configuração da interface. Na configuração encontrada, o Caddy referencia `/srv/manifest.json`, mas o Compose não monta esse arquivo em `/srv`. Os ícones citados também não estavam na pasta inventariada. Não houve correção ou alteração no servidor.

## Versões observadas

| Imagem | ID/digest observado |
| --- | --- |
| `mira:local` | `sha256:6e322b92f8acb39cbc360a9a1824d43cd11c6e5df9c52ac3cd3e988cfe63b092` |
| `mcp-calendar:local` | `sha256:094734783b31df89a20ec67dd4a4aef5a1f3d12ff4edb6350bd811897e963465` |
| `ghcr.io/berriai/litellm:main-latest` | `sha256:41d9be75c624d7cfcc9123b74db0f2fbf4a1a3a2a658cf1b27e21a144f8e59ab` |
| `caddy:2-alpine` | `sha256:5f5c8640aae01df9654968d946d8f1a56c497f1dd5c5cda4cf95ab7c14d58648` |

Pacotes observados dentro do calendário: `mcp==2.2.0`, `cryptography==50.0.1`, `httpx==0.28.1`, `starlette==1.6.0`, `uvicorn==0.52.4`. O `requirements.txt` original contém limites mínimos; não é um lockfile. O código usa `mcp.server.mcpserver.MCPServer`. Uma reconstrução deve verificar que a distribuição instalada oferece essa interface; esta importação não fez uma instalação nova para comprová-lo.

Os arquivos `server.py`, `config.py`, `oauth_microsoft.py`, `token_store.py` e `providers/microsoft.py` coincidiram por SHA-256 entre o código no host e o container. Os hashes da cópia exportada estão em `source-manifest.json`.

O submódulo MIRA aponta para a revisão do checkout disponível. Não foi possível estabelecer a origem exata da imagem MIRA a partir de metadados de build. Nenhuma imagem foi reconstruída, exportada ou reiniciada.

## Diferenças no ambiente de desenvolvimento

- Projeto `isa-development`; imagens locais com nomes próprios e portas de loopback distintas.
- MIRA construído a partir do submódulo fixado; dados em volume novo.
- Calendário construído de um caminho relativo; `.dockerignore` impede incluir `.env` e bancos na imagem.
- LiteLLM fixado no digest observado; configuração e callback preservados.
- Proxy Caddy compartilhado não faz parte do Compose de desenvolvimento.
- Cópia duplicada e sem uso de `litellm_hooks/drop_prompt_cache.py` não foi incluída; o arquivo montado pelo Compose está em `litellm/`.

O `.env.pilot` e o `.env` do calendário não foram lidos nem copiados. Os exemplos foram escritos a partir das referências presentes no código. Configuração e memória privadas do MIRA, OAuth, certificados, bancos e demais dados persistentes não fazem parte deste repositório.

## Implantação futura

Esta importação é somente de código. Antes de vincular a instalação ativa a um checkout ou trocar imagens, preparar backup privado dos dados e configurações, comparar o Compose e os mounts e revisar um plano específico para a Isa. Preservar os nomes dos volumes existentes e as rotas dos demais projetos. Não executar comandos globais de limpeza, `down` ou atualização de containers na VPS como parte da publicação.
