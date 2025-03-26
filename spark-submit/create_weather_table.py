from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, to_date
from pyspark.sql.types import StructType, StringType, DoubleType, IntegerType, TimestampType, DateType

# SparkSession
spark = SparkSession.builder \
    .appName("KafkaToPostgresWeather") \
    .getOrCreate()

# Kafka topic i bootstrap server
kafka_topic = "dnevna_prognoza"
kafka_bootstrap_servers = "kafka1:9092"

# Šema podataka (prevedena)
schema = StructType() \
    .add("grad", StringType()) \
    .add("region", StringType()) \
    .add("drzava", StringType()) \
    .add("temperatura", DoubleType()) \
    .add("osecaj", DoubleType()) \
    .add("vlaznost", IntegerType()) \
    .add("stanje", StringType()) \
    .add("lokalno_vreme", StringType()) \
    .add("datum", StringType())

# Čitanje iz Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", kafka_topic) \
    .option("startingOffsets", "earliest") \
    .load()

# Parsiranje JSON vrednosti
json_df = df.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("lokalno_vreme", to_timestamp("lokalno_vreme")) \
    .withColumn("datum", to_date("datum"))

# Funkcija za upis u PostgreSQL
def write_to_postgres(batch_df, batch_id):
    db_url = "jdbc:postgresql://postgres-db:5432/projekat_baza"
    db_properties = {
        "user": "POSTGRES_USER",
        "password": "POSTGRES_PASSWORD",
        "driver": "org.postgresql.Driver"
    }
    batch_df.write.jdbc(
        url=db_url,
        table="daily_weather",
        mode="append",
        properties=db_properties
    )

# Upis u bazu pomoću foreachBatch
query = json_df.writeStream \
    .foreachBatch(write_to_postgres) \
    .outputMode("append") \
    .start()

query.awaitTermination()

