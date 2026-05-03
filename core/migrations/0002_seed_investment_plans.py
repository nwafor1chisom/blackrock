from django.db import migrations


def seed_plans(apps, schema_editor):
    InvestmentPlan = apps.get_model('core', 'InvestmentPlan')
    plans = [
        {'name': 'Starter Plan',  'interest': 6.0,  'duration': '24 hrs',  'min_amount': 100,    'max_amount': 999,    'sort_order': 1},
        {'name': 'Basic Plan',    'interest': 10.0, 'duration': '48 hrs',  'min_amount': 1000,   'max_amount': 4999,   'sort_order': 2},
        {'name': 'Advanced Plan', 'interest': 15.0, 'duration': '7 Days',  'min_amount': 5000,   'max_amount': 19999,  'sort_order': 3},
        {'name': 'Premium Plan',  'interest': 20.0, 'duration': '14 Days', 'min_amount': 20000,  'max_amount': 49999,  'sort_order': 4},
        {'name': 'Elite Plan',    'interest': 25.0, 'duration': '21 Days', 'min_amount': 50000,  'max_amount': 99999,  'sort_order': 5},
        {'name': 'VIP Plan',      'interest': 30.0, 'duration': '30 Days', 'min_amount': 100000, 'max_amount': None,   'sort_order': 6},
    ]
    for p in plans:
        InvestmentPlan.objects.get_or_create(name=p['name'], defaults={**p, 'is_active': True})


class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]
    operations = [migrations.RunPython(seed_plans, migrations.RunPython.noop)]
