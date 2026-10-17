#!/usr/bin/env python3
"""Reserve one scheduled paid attempt per Sao Paulo day before contacting AI."""
import datetime as dt
from decimal import Decimal
import json
import os
import pathlib
import re
import subprocess
import urllib.request
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent
PRICE_URL = 'https://open.higgsfield.ai/models/kling-video/v3.0/std/image-to-video/playground'
MODEL = 'kling-video/v3.0/std/image-to-video'

def estimated_cost(page):
    # Fail closed when the provider changes its published pricing format.
    match = re.search(r'standard rates are \$([0-9.]+) per second for 1 second clips and \$([0-9.]+) per second for 3 or 15 second clips', page)
    if not match:
        raise RuntimeError('Cannot verify current Kling standard pricing; no paid request allowed')
    return max(Decimal(x) for x in match.groups()) * 5

def reserve(root=ROOT, today=None, page=None, commit=True):
    config = json.loads((root / 'automation.json').read_text(encoding='utf-8'))
    if not config.get('enabled'):
        raise RuntimeError('Daily automation is disabled')
    budget = Decimal(str(config['daily_budget_usd']))
    if not Decimal('0') < budget <= Decimal('0.65'):
        raise RuntimeError('Daily budget exceeds the authorized USD 0.65')
    if config['model'] != MODEL or config['duration_seconds'] != 5:
        raise RuntimeError('Unapproved model or duration')
    day = today or dt.datetime.now(ZoneInfo('America/Sao_Paulo')).date().isoformat()
    ledger_path = root / 'ai-daily-ledger.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    if day in ledger:
        raise RuntimeError('A paid attempt was already reserved today; no automatic retry allowed')
    if page is None:
        request = urllib.request.Request(PRICE_URL, headers={'User-Agent': 'PromoRadarBudgetCheck/1.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            page = response.read(5 * 1024 * 1024).decode('utf-8')
    estimate = estimated_cost(page)
    if estimate > budget:
        raise RuntimeError(f'Published standard price USD {estimate} exceeds daily budget USD {budget}')
    ledger[day] = {'run_id': os.getenv('GITHUB_RUN_ID'), 'reserved_usd': str(budget),
                   'estimated_max_usd': str(estimate), 'model': MODEL, 'duration': 5,
                   'state': 'reserved-before-request', 'price_source': PRICE_URL}
    ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
    if commit:
        def git(*args):
            subprocess.run(['git', *args], cwd=root, check=True)
        git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
        git('config', 'user.name', 'github-actions[bot]')
        git('add', 'ai-daily-ledger.json')
        git('commit', '-m', f'chore: reserve daily AI attempt {day}')
        # Failure to persist a reservation stops execution before generation.
        git('push', 'origin', 'HEAD:main')
    print(f'DAILY_AI_RESERVED {day} estimated_max_usd={estimate} budget_usd={budget}', flush=True)

if __name__ == '__main__':
    reserve()
