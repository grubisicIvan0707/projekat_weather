from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'USER',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='weather_region_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False
) as dag:

    pokreni_weather_region_spark = BashOperator(
        task_id='pokreni_weather_region_spark',
        bash_command="""
        docker exec spark-master \
        spark-submit \
          --master spark://spark-master:7077 \
          --driver-class-path /opt/spark-submit/postgresql-42.3.5.jar \
          --jars /opt/spark-submit/postgresql-42.3.5.jar \
          /opt/spark-submit/loadWeatherRegion.py
        """
    )

