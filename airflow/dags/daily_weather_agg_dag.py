from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'start_date': datetime(2025, 3, 23),
    'retries': 1,
}

with DAG(
    dag_id='daily_weather_agg_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['weather', 'agregacija'],
) as dag:

    pokreni_spark_agregaciju = BashOperator(
        task_id='pokreni_agregaciju_najtoplijih_najhladnijih',
        bash_command="""
        docker exec spark-master \
        spark-submit \
        --jars /opt/spark-submit/postgresql-42.3.5.jar \
        /opt/spark-submit/daily_weather_agg.py
        """,
    )

   
