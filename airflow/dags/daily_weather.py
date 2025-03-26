from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'start_date': datetime(2025, 3, 23),
    'retries': 1,
}

with DAG(
    dag_id='daily_weather_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['weather'],
) as dag:

    pokreni_spark = BashOperator(
        task_id='pokreni_daily_weather_spark',
        bash_command="""
        docker exec spark-master \
        /opt/bitnami/spark/bin/spark-submit \
        --jars /opt/spark-submit/postgresql-42.3.5.jar \
        /opt/spark-submit/loadDailyWeather.py
        """,
    )

    pokreni_spark

