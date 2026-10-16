"""Create a local-only fake product and product image for safe GitHub Actions smoke tests."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
folder=Path(__file__).resolve().parent/'out';folder.mkdir(exist_ok=True)
image=Image.new('RGB',(900,900),'#f6f6f6')
d=ImageDraw.Draw(image)
d.rounded_rectangle((220,155,690,720),radius=55,fill='#f08b34')
d.rounded_rectangle((285,205,625,650),radius=30,fill='#fbd9ac')
d.ellipse((360,300,550,490),fill='#e78223')
d.text((260,750),'IMAGEM DE TESTE — PRODUTO FICTICIO',fill='#333333')
image.save(folder/'smoke-image.jpg',quality=93)
product={'itemId':'SMOKE-ONLY-NOT-REAL','title':'Produto demonstrativo de teste, sem venda real','price':49.90,'discount':10,'image':'https://down-br.img.susercontent.com/FAKE','affiliateLink':'https://example.org/test'}
(folder/'smoke-product.json').write_text(json.dumps(product,ensure_ascii=False),encoding='utf8')
print('SMOKE_FIXTURE_OK',folder)