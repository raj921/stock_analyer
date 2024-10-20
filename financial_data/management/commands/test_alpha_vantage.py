from django.core.management.base import BaseCommand
from financial_data.utils.alpha_vantage_api import test_alpha_vantage_connection

class Command(BaseCommand):
    help = 'Test Alpha Vantage API connection'

    def handle(self, *args, **options):
        self.stdout.write('Testing Alpha Vantage API connection...')
        test_alpha_vantage_connection()
        self.stdout.write(self.style.SUCCESS('Test completed'))
