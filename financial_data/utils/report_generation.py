# financial_data/utils/report_generation.py

import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend which doesn't require a GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import base64
from reportlab.lib.pagesizes import letter
from financial_data.models import StockData, Prediction, BacktestResult
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PlatypusImage
from reportlab.lib.styles import getSampleStyleSheet
import logging

logger = logging.getLogger(__name__)

def fetch_chart_data(backtest_result):
    try:
        stock_data = StockData.objects.filter(
            symbol=backtest_result.symbol,
            date__range=(backtest_result.start_date, backtest_result.end_date)
        ).order_by('date')
        
        predictions = Prediction.objects.filter(
            symbol=backtest_result.symbol,
            date__range=(backtest_result.start_date, backtest_result.end_date)
        ).order_by('date')
        
        return stock_data, predictions
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        raise

def generate_performance_chart(backtest_result):
    try:
        logger.debug(f"Generating performance chart for backtest_id: {backtest_result.id}")
        stock_data, predictions = fetch_chart_data(backtest_result)
        
        logger.debug(f"Fetched {len(stock_data)} stock data points and {len(predictions)} prediction points")

        if not stock_data:
            raise ValueError("No data available for the specified date range")
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Prepare data
        dates = [data.date for data in stock_data]
        actual_prices = [float(data.close_price) for data in stock_data]
        predicted_prices = [float(pred.predicted_price) for pred in predictions]
        
        logger.debug(f"Date range: {min(dates)} to {max(dates)}")
        logger.debug(f"Actual price range: {min(actual_prices)} to {max(actual_prices)}")
        logger.debug(f"Predicted price range: {min(predicted_prices) if predicted_prices else 'N/A'} to {max(predicted_prices) if predicted_prices else 'N/A'}")

        # Plot actual prices
        ax.plot(dates, actual_prices, label='Actual', color='blue')
        
        # Plot predicted prices
        if predicted_prices:
            ax.plot(dates, predicted_prices, label='Predicted', color='orange', linestyle='--')
        else:
            logger.warning("No prediction data available for plotting")

        # Format x-axis to show every month
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        # Rotate and align the tick labels so they look better
        fig.autofmt_xdate()
        
        # Use a scientific notation for y-axis if the range is large
        ax.yaxis.set_major_formatter(plt.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        
        ax.set_title(f'{backtest_result.symbol} Stock Price - Actual vs Predicted')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.legend(loc='upper left')
        
        plt.tight_layout()
        
        # Save to BytesIO object
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300)
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        # Encode the image to base64
        graphic = base64.b64encode(image_png)
        graphic = graphic.decode('utf-8')
        
        plt.close(fig)  # Close the figure to free up memory
        
        logger.debug("Performance chart generated successfully")
        return graphic
    except Exception as e:
        logger.error(f"Error generating performance chart: {str(e)}")
        raise

def generate_pdf_report(backtest_result, chart_img):
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Add title
        styles = getSampleStyleSheet()
        story.append(Paragraph(f"Backtest Report for {backtest_result.symbol}", styles['Title']))
        story.append(Spacer(1, 12))

        # Add performance metrics
        data = [
            ["Metric", "Value"],
            ["Initial Investment", f"${backtest_result.initial_investment:.2f}"],
            ["Final Value", f"${backtest_result.final_value:.2f}"],
            ["Total Return", f"{backtest_result.total_return:.2%}"],
            ["Max Drawdown", f"{backtest_result.max_drawdown:.2%}"],
            ["Number of Trades", str(backtest_result.num_trades)]
        ]

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)
        story.append(Spacer(1, 12))

        # Add performance chart
        if chart_img:
            story.append(Paragraph("Performance Chart", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # Decode the base64 image
            image_data = base64.b64decode(chart_img)
            img = PlatypusImage(io.BytesIO(image_data), width=500, height=300)
            
            story.append(img)

        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"Error in generate_pdf_report: {str(e)}")
        raise ValueError(f"Failed to generate PDF report: {str(e)}")

def generate_report(params):
    try:
        backtest_result = BacktestResult.objects.get(id=params['backtest_id'])
        chart_img = generate_performance_chart(backtest_result)
        pdf_buffer = generate_pdf_report(backtest_result, chart_img)
        return pdf_buffer
    except Exception as e:
        logger.error(f"Error in generate_report: {str(e)}")
        raise ValueError(f"Failed to generate report: {str(e)}")
