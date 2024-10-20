# Stock Analyzer

This project is a Django-based stock analysis tool that uses the Alpha Vantage API to fetch stock data and perform backtesting strategies.

## Local Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/stock-analyzer.git
   cd stock-analyzer
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add the following:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DB_NAME=stock_analyzer
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
   ```
   Replace the values with your actual database credentials and Alpha Vantage API key.

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

The application should now be running at `http://localhost:8000`.

## Deployment to AWS

1. Set up an AWS account 

2. Create an RDS PostgreSQL instance and note down the endpoint, database name, username, and password.

3. Create an EC2 instance with Amazon Linux 2. Install Docker and Docker Compose on it.

4. Set up an Elastic Container Registry (ECR) repository.

5. In your GitHub repository, go to Settings > Secrets and add the following secrets:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - EC2_PRIVATE_KEY (the private key to SSH into your EC2 instance)
   - EC2_HOST (the public DNS of your EC2 instance)
   - EC2_USER (usually 'ec2-user' for Amazon Linux 2)

6. Update the `.github/workflows/deploy.yml` file with your ECR repository name.

7. Push your changes to the main branch. The GitHub Action will automatically build the Docker image, push it to ECR, and deploy it to your EC2 instance.

8. SSH into your EC2 instance and create a `.env` file with the production environment variables, including the RDS database credentials.

9. The application should now be accessible via your EC2 instance's public DNS on port 80.

## Usage

- Use the `/api/backtest/` endpoint to run a backtest strategy.
- Use the `/api/predict/` endpoint to get stock price predictions.
- Use the `/api/report/` endpoint to generate a report for a backtest.

For more detailed API documentation, refer to the Django REST framework browsable API interface available when running the server.

