from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import StockData
from .tasks import update_stock_data
from .utils.alpha_vantage_api import setup_alpha_vantage_api

@receiver(post_save, sender=StockData)
def trigger_stock_data_update(sender, instance, created, **kwargs):
    if created:
        update_stock_data.delay(instance.symbol)

@receiver(post_migrate)
def run_post_migrate_tasks(sender, **kwargs):
    if sender.name == 'financial_data':
        setup_alpha_vantage_api()
