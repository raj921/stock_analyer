from django.urls import path
from .views import BacktestView, PredictionView, ReportView, CompanyOverviewView, IntradayDataView, APIRootView, test_alpha_vantage, PredictionComparisonView

urlpatterns = [
    path('', APIRootView.as_view(), name='api-root'),
    path('backtest/', BacktestView.as_view(), name='backtest'),
    path('predict/', PredictionView.as_view(), name='predict'),
    path('predict/compare/', PredictionComparisonView.as_view(), name='predict-compare'),
    path('report/', ReportView.as_view(), name='report'),
    path('company-overview/<str:symbol>/', CompanyOverviewView.as_view(), name='company-overview'),
    path('intraday-data/<str:symbol>/', IntradayDataView.as_view(), name='intraday-data'),
    path('test-alpha-vantage/', test_alpha_vantage, name='test_alpha_vantage'),
]
