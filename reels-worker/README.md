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
## Modelo Apresentador Pro (experimental, DESATIVADO)

Novo módulo `presenter.py`. Com autorização explícita, envia a **foto verdadeira do produto** a um serviço externo de geração de vídeo por IA, solicitando uma pessoa adulta mostrando a ferramenta em oficina. Substitui a primeira cena estática por aproximadamente 4–5 segundos desse vídeo, conserva a narração local, o preço e as cenas seguintes. IA pode deformar mãos/ferramentas, inventar partes do produto e descumprir a referência: **a revisão humana do vídeo final é indispensável**.

**Por padrão não chama nenhum serviço pago.** O teste atual (e o GitHub Actions existente) continuam usando somente o modelo anterior. Para ativar numa execução controlada, é preciso `PRESENTER_MODE=ai`, `ENABLE_PAID_AI_GENERATION=true` e a credencial `HF_KEY` do [Higgsfield API](https://open.higgsfield.ai/api-keys) em variáveis secretas. Isso gera **cobrança de créditos por tentativa**, inclusive quando a saída não é adequada. Não configure essas variáveis nem use `--publish` sem orçamento e revisão prévios.

Foi preparado para `kling-video/v3.0/std/image-to-video`, 5 segundos, `sound=off`. Endpoint, custos, payload e resposta podem mudar; confirme a API/custos do provedor antes do primeiro uso. O limite de espera é 8 minutos e há bloqueio contra tentativa de geração sem aprovação. Quando a geração começar e ocorrer timeout, confira o painel do provedor antes de tentar novamente para não duplicar cobranças.

**Teste local sem gastos**: deixe `PRESENTER_MODE` desativado e execute o dry-run habitual. O PR deste módulo deve ser revisado e mesclado antes de uso; o GitHub workflow não habilita nem cobra o serviço de IA.
