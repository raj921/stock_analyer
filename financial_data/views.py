from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import FileResponse, HttpResponse
from .models import StockData, BacktestResult, CompanyOverview
from .utils.backtesting import backtest_strategy
from .utils.ml_integration import predict_stock_prices, compare_predictions
from .utils.report_generation import generate_performance_chart, generate_pdf_report
from .serializers import BacktestResultSerializer, CompanyOverviewSerializer
from .utils.alpha_vantage_api import get_company_overview, get_intraday_data, test_alpha_vantage_connection, fetch_stock_data
from datetime import date, datetime, timedelta
from rest_framework.reverse import reverse
from rest_framework.exceptions import APIException
import logging
from rest_framework import status

logger = logging.getLogger(__name__)

class APIRootView(APIView):
    def get(self, request, format=None):
        try:
            return Response({
                'backtest': reverse('backtest', request=request, format=format),
                'predict': reverse('predict', request=request, format=format),
                'report': reverse('report', request=request, format=format),
                'company-overview': reverse('company-overview', request=request, format=format, args=['AAPL']),
                'intraday-data': reverse('intraday-data', request=request, format=format, args=['AAPL']),
                'test-alpha-vantage': reverse('test_alpha_vantage', request=request, format=format),
            })
        except Exception as e:
            logger.error(f"Error in APIRootView: {str(e)}")
            raise APIException(f"An error occurred: {str(e)}")

class BacktestView(APIView):
    def post(self, request):
        try:
            params = request.data
            symbol = params['symbol']
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d').date()
            initial_investment = float(params['initial_investment'])
            short_window = int(params.get('short_window', 50))
            long_window = int(params.get('long_window', 200))

            logger.debug(f"Starting backtest for {symbol} from {start_date} to {end_date}")

           
            existing_data = StockData.objects.filter(
                symbol=symbol,
                date__range=(start_date, end_date)
            ).exists()

            if not existing_data:
                try:
                    fetch_stock_data(symbol, start_date, end_date)
                except ValueError as ve:
                    return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)

            result = backtest_strategy({
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'initial_investment': initial_investment,
                'short_window': short_window,
                'long_window': long_window
            })

            # Generate predictions
            try:
                predict_stock_prices(symbol, start_date, end_date)
                logger.debug(f"Predictions generated for {symbol}")
            except Exception as e:
                logger.error(f"Error generating predictions: {str(e)}")
              

            return Response(result, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in BacktestView: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PredictionView(APIView):
    def get(self, request):
        try:
            symbol = request.query_params.get('symbol')
            if not symbol:
                return Response({'error': 'Symbol parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            end_date = date.today()
            start_date = end_date - timedelta(days=365)  
            
            predictions = predict_stock_prices(symbol, start_date, end_date)
       
            actual_prices = StockData.objects.filter(
                symbol=symbol,
                date__range=(start_date, end_date)
            ).values('date', 'close_price')
            
            return Response({
                'symbol': symbol,
                'predictions': [{'date': pred.date, 'predicted_price': pred.predicted_price} for pred in predictions],
                'actual_prices': list(actual_prices)
            })
        except ValueError as ve:
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in PredictionView: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReportView(APIView):
    def get(self, request):
        try:
            backtest_id = request.query_params.get('backtest_id')
            format = request.query_params.get('format', 'pdf')

            if not backtest_id:
                return Response({'error': 'Backtest ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                backtest_result = BacktestResult.objects.get(id=backtest_id)
            except BacktestResult.DoesNotExist:
                return Response({'error': 'Backtest result not found'}, status=status.HTTP_404_NOT_FOUND)

            # Generate predictions
            try:
                predict_stock_prices(backtest_result.symbol, backtest_result.start_date, backtest_result.end_date)
                logger.debug(f"Predictions generated for {backtest_result.symbol}")
            except Exception as e:
                logger.error(f"Error generating predictions: {str(e)}")

            try:
                chart_img = generate_performance_chart(backtest_result)
                logger.debug(f"Chart image generated: {bool(chart_img)}")
            except Exception as e:
                logger.error(f"Error generating performance chart: {str(e)}")
                chart_img = None  

            if format.lower() == 'json':
                report_data = {
                    'backtest_id': backtest_result.id,
                    'symbol': backtest_result.symbol,
                    'start_date': backtest_result.start_date,
                    'end_date': backtest_result.end_date,
                    'initial_investment': float(backtest_result.initial_investment),
                    'final_value': float(backtest_result.final_value),
                    'total_return': float(backtest_result.total_return),
                    'max_drawdown': float(backtest_result.max_drawdown),
                    'num_trades': backtest_result.num_trades,
                    'chart_image': chart_img,
                }
                return Response(report_data)
            else:
                try:
                    pdf_buffer = generate_pdf_report(backtest_result, chart_img)
                    return FileResponse(pdf_buffer, as_attachment=True, filename='backtest_report.pdf')
                except Exception as e:
                    logger.error(f"Error generating PDF report: {str(e)}")
                    return Response({'error': f'Error generating PDF report: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error in ReportView: {str(e)}")
            return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CompanyOverviewView(APIView):
    def get(self, request, symbol):
        try:
            overview = get_company_overview(symbol)
            serializer = CompanyOverviewSerializer(data=overview)
            if serializer.is_valid():
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in CompanyOverviewView: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class IntradayDataView(APIView):
    def get(self, request, symbol):
        try:
            intraday_data = get_intraday_data(symbol)
            return Response(intraday_data)
        except Exception as e:
            logger.error(f"Error in IntradayDataView: {str(e)}")
            return Response({"error": str(e)}, status=500)

def test_alpha_vantage(request):
    try:
        test_alpha_vantage_connection()
        return HttpResponse("Alpha Vantage API test successful!")
    except Exception as e:
        logger.error(f"Error in test_alpha_vantage: {str(e)}")
        return HttpResponse(f"Error: {str(e)}", status=500)

class PredictionComparisonView(APIView):
    def get(self, request):
        try:
            symbol = request.query_params.get('symbol')
            if not symbol:
                return Response({'error': 'Symbol parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            end_date = date.today()
            start_date = end_date - timedelta(days=30)  # Compare last 30 days
            
            comparison = compare_predictions(symbol, start_date, end_date)
            
            return Response(comparison)
        except ValueError as ve:
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in PredictionComparisonView: {str(e)}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
