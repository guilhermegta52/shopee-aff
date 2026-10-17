# Promo Radar — Reels automáticos (versão de testes)

Pipeline: busca Shopee API > filtro de oferta inédita > Piper pt_BR-faber-medium > 4 cenas FFmpeg em 1080x1920/30fps > verificação MP4/H264/AAC > Vercel Blob > criação de contêiner Reels Instagram > aguarda FINISHED > publica > registra item no history.json.

**Segurança:** o programa NUNCA publica sem o argumento `--publish` e `ENABLE_REAL_POSTING=true`. A workflow só roda no agendamento quando a variável GitHub `ENABLE_DAILY_REELS=true`. É necessário validar a qualidade e conferir as políticas antes de ativar.

## Dry-run local (sem publicação)
Instale Python 3.11+, Pillow, FFmpeg e Piper:
```
pip install pillow piper-tts
python reels-worker/daily.py
```
Sem credenciais da Shopee, a ferramenta consulta os produtos reais salvos em `PROMO_RADAR_API/api/status`; ignora dados de demonstração. Com `SHOPEE_APP_ID` e `SHOPEE_APP_SECRET`, consulta a API GraphQL da Shopee diretamente.

## GitHub Actions
Copie o projeto **para um repositório GitHub apropriado** mantendo `.github/workflows/daily-reels.yml`.
Configure em Repository Settings > Secrets and variables > Actions:

Secrets obrigatórios para execução integral:
- `SHOPEE_APP_ID` e `SHOPEE_APP_SECRET`: consulta diária e afiliados.
- `BLOB_READ_WRITE_TOKEN`: Vercel Blob público para disponibilizar MP4.
- `INSTAGRAM_TOKEN` e `INSTAGRAM_ACCOUNT_ID`: conta profissional com permissão de conteúdo.

Variables:
- `PROMO_RADAR_API`: URL oficial do catálogo (fallback se não houver API Shopee).
- `ENABLE_DAILY_REELS`: comece sem esta variável. Configure como `true` SOMENTE depois de aprovar uma execução workflow_dispatch > dry-run.

Horário agendado: 12:00 UTC / 09:00 America/Sao_Paulo (sem horário de verão, sujeito a atrasos da fila GitHub).

`history.json` é atualizado **somente após confirmação de publicação** e a workflow cria um commit automático com o item publicado. O agendamento usa `concurrency` para não executar duas instâncias simultâneas. Mantenha o repositório sem dados sensíveis. Os MP4 de teste aparecem na aba Actions como artefatos temporários por sete dias.

## Limitações atuais
- A edição é um template original de quatro cenas, com movimentos suaves de fundo/foto e texto; ainda precisa avaliação visual humana.
- O script testa duração/formato/trilhas; não garante qualidade comercial ou sincronismo palavra por palavra.
- Uma fonte pública de vídeo hospedado é obrigatória para a API do Instagram; GitHub Actions artifacts não servem como URL.
- Credenciais Vercel/Instagram pré-existentes **não são copiadas automaticamente** ao GitHub.
- Custos e cotas do GitHub Actions, Vercel Blob, Instagram e hospedagem dependem do plano e uso.
- O repositório GitHub ainda precisa estar conectado ao código deste projeto para a agenda rodar.
## Apresentador com IA e publicação diária

Agenda: 12:00 UTC / 09:00 America/Sao_Paulo. Ative a variável Actions ENABLE_DAILY_REELS=true; false ou ausente interrompe a agenda.

A rotina usa Kling 3.0 Standard, 5 segundos, sem áudio do modelo, uma tentativa paga por dia de São Paulo. O Reel recebe a narração e cenas existentes e é publicado no Instagram conectado. Orçamento autorizado para IA: US$ 0,65/dia.

Antes da tentativa, daily_guard.py consulta a tabela pública do modelo e calcula 5 segundos pela maior tarifa padrão exibida. Se a tarifa não puder ser lida ou exceder o orçamento, não gera nem publica. Isso usa preço público, não uma cotação vinculante da cobrança da conta. Custos de câmbio, GitHub Actions e armazenamento não estão incluídos no teto da IA.

A reserva do dia é salva em ai-daily-ledger.json e enviada ao main ANTES de chamar a IA. Falhas não liberam a reserva e não causam novas tentativas automáticas no dia. Não apague reservas para tentar novamente sem conferir a cobrança e nova autorização. O histórico de produtos é atualizado apenas após a publicação confirmada.

Artifacts incluem presenter.mp4, promo-reel.mp4, result.json, presenter-request.json, publish.json quando existir e o registro diário. Retenção de 7 dias.

Teste sem gastos: pull requests usam o fixture e verificam o limite e a duplicação. O modo manual ai-presenter-preview continua exigindo approve_paid_ai=true e não publica; ele é um teste pago separado, a usar somente com autorização específica.

Teste real em 17/10/2026: execução 39041637640, pedido 761d7cb1-1520-4fcc-90d8-9e04f946cc65, concluído com vídeo e sem publicação. O usuário aprovou depois a publicação diária com orçamento de US$ 0,65.
