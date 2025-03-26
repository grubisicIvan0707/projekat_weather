# Projekat Weather Data Pipeline

## NiFi

- GetFile  
- SplitText  
- ExtractText  
- UpdateAttribute  
- InvokeHTTP  
- EvaluateJsonPath  
- SplitJson  
- PutHDFS

## Hue

- Vizuelni interfejs za pregled podataka u HDFS-u

## Spark

- Učitavanje podataka iz HDFS-a  
- Transformacija i čišćenje podataka  
- Upis u PostgreSQL tabelu

## Airflow

- Automatizacija batch Spark poslova  
- Automatizacija kreiranja i punjenja tabela

## Kafka Streaming

- Čitanje podataka iz Kafka topic-a  
- Transformacija u realnom vremenu  
- Upis u PostgreSQL

## Metabase

- Vizualizacija podataka iz PostgreSQL baze
