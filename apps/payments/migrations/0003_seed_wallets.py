from django.db import migrations

WALLETS = [
    ('jaib', 'جيب', '#dc3545', 1),
    ('jawali', 'جوالي', '#ffc107', 2),
    ('floosk', 'فلوسك', '#0d6efd', 3),
    ('one_cash', 'وان كاش', '#fd7e14', 4),
]

def seed_wallets(apps, schema_editor):
    Wallet = apps.get_model('payments', 'Wallet')
    for code, name, color, order in WALLETS:
        Wallet.objects.update_or_create(code=code, defaults={'name': name, 'color': color, 'display_order': order, 'is_active': True})

class Migration(migrations.Migration):
    dependencies = [('payments', '0002_wallet_payment_commission_amount_and_more')]
    operations = [migrations.RunPython(seed_wallets, migrations.RunPython.noop)]
