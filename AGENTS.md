# Isa — regras de trabalho

- A VPS hospeda outros projetos. Não alterar, reiniciar ou remover seus serviços.
- O Caddy da instalação existente é compartilhado; não substituir seu arquivo com o exemplo deste repositório.
- Publicar código não significa implantar. Não executar deploy automaticamente após push.
- Não ler, copiar, versionar ou imprimir arquivos `.env` reais, tokens, chaves ou dados de execução. Usar exemplos com placeholders.
- Antes de `git add`, revisar a lista de arquivos e verificar que nenhum arquivo privado está staged.
- `deploy/vps/` registra a instalação observada; consultar sua documentação antes de usar.
- O MIRA é um submódulo fixado em uma revisão do upstream; preservar autoria e licença.
- A integração n8n/Garmin está em `integrations/garmin`, projeto Docker `isa-integrations`, com redes e volumes próprios. Alterações nela não autorizam mudar os demais projetos. Não executar os scripts interativos de login em nome do usuário nem imprimir dados de saúde, sessões ou credenciais.
