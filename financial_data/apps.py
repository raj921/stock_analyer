import os
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.conf import settings

class FinancialDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financial_data'

    def ready(self):
        import financial_data.signals  # This imports the signals
