from django.db import models

class StockData(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()

    class Meta:
        unique_together = ('symbol', 'date')

    def __str__(self):
        return f"{self.symbol} - {self.date}"

class Prediction(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('symbol', 'date')
        indexes = [
            models.Index(fields=['symbol', 'date']),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.date} - Predicted: {self.predicted_price}"

class BacktestResult(models.Model):
    symbol = models.CharField(max_length=10)
    start_date = models.DateField()
    end_date = models.DateField()
    initial_investment = models.DecimalField(max_digits=10, decimal_places=2)
    final_value = models.DecimalField(max_digits=10, decimal_places=2)
    total_return = models.DecimalField(max_digits=10, decimal_places=2)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=2)
    num_trades = models.IntegerField()

    def __str__(self):
        return f"{self.symbol} - {self.start_date} to {self.end_date}"



class CompanyOverview(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    exchange = models.CharField(max_length=50)
    currency = models.CharField(max_length=10)
    country = models.CharField(max_length=50)
    sector = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    market_capitalization = models.BigIntegerField()
    pe_ratio = models.FloatField(null=True, blank=True)
    dividend_yield = models.FloatField(null=True, blank=True)
    beta = models.FloatField(null=True, blank=True)
    fifty_two_week_high = models.FloatField()
    fifty_two_week_low = models.FloatField()

    def __str__(self):
        return f"{self.symbol} - {self.name}"
