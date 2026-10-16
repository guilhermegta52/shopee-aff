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