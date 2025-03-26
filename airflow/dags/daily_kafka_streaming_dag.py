from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Default argumenti za DAG
default_args = {
    'start_date': datetime(2025, 3, 26),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# Kreiranje DAG-a
with DAG(
    dag_id='kafka_stream_weather_dag',
    default_args=default_args,
    schedule_interval=None,  # Ručno pokretanje
    catchup=False,
    tags=['weather', 'kafka', 'spark'],
) as dag:

    # Bash komanda za pokretanje spark-submit
    pokreni_kafka_stream = BashOperator(
        task_id='pokreni_kafka_weather_streaming',
        bash_command="""
        docker exec spark-master \
        /opt/bitnami/spark/bin/spark-submit \
        --jars /opt/spark-submit/postgresql-42.3.5.jar,\
/opt/spark-submit/spark-sql-kafka-0-10_2.12-3.3.0.jar,\
/opt/spark-submit/kafka-clients-3.3.0.jar,\
/opt/spark-submit/spark-token-provider-kafka-0-10_2.12-3.3.0.jar,\
/opt/spark-submit/commons-pool2-2.11.1.jar \
        /opt/spark-submit/loadDailyWeather.py
        """
    )

    pokreni_kafka_stream

