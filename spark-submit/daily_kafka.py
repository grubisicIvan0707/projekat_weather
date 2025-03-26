from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, expr
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType

# Kreiraj Spark session
spark = SparkSession.builder \
    .appName("KafkaToPostgresStreamWeather") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Kafka i PostgreSQL info
kafka_bootstrap_servers = "kafka1:9092"
kafka_topic = "dnevna_prognoza"

postgres_properties = {
    "host": "postgres-db",
    "database": "projekat_baza",
    "user": "POSTGRESS_USER",
    "password": "POSTGRESS_PASSWORD"
}

# Šema za JSON poruke
schema = StructType([
    StructField("location", StructType([
        StructField("name", StringType()),
        StructField("region", StringType()),
        StructField("country", StringType()),
        StructField("localtime", StringType())
    ])),
    StructField("current", StructType([
        StructField("temp_c", DoubleType()),
        StructField("feelslike_c", DoubleType()),
        StructField("humidity", IntegerType()),
        StructField("condition", StructType([
            StructField("text", StringType())
        ]))
    ]))
])

# Čitanje iz Kafka streama
raw_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", kafka_topic) \
    .load()

# Parsiranje JSON poruka
json_df = raw_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select(
        col("data.location.name").alias("grad"),
        col("data.location.region").alias("region"),
        col("data.location.country").alias("drzava"),
        col("data.current.temp_c").alias("temperatura"),
        col("data.current.feelslike_c").alias("osecaj"),
        col("data.current.humidity").alias("vlaznost"),
        col("data.current.condition.text").alias("stanje"),
        to_timestamp(col("data.location.localtime")).alias("lokalno_vreme")
    )

# Dodaj kolonu datum
df = json_df.withColumn("datum", expr("to_date(lokalno_vreme)"))

# Prevod vremenskog stanja
df_translated = df.withColumn("stanje", expr("""
  CASE
    WHEN stanje = 'Sunny' THEN 'Sunčano'
    WHEN stanje = 'Clear' THEN 'Vedro'
    WHEN stanje = 'Partly cloudy' THEN 'Delimično oblačno'
    WHEN stanje = 'Cloudy' THEN 'Oblačno'
    WHEN stanje = 'Overcast' THEN 'Tmurno'
    WHEN stanje = 'Mist' THEN 'Izmaglica'
    WHEN stanje = 'Patchy rain possible' THEN 'Moguća mestimična kiša'
    WHEN stanje = 'Light rain' THEN 'Slaba kiša'
    ELSE stanje
  END
"""))

# Funkcija za UPSERT u PostgreSQL
def write_to_postgres(batch_df, epoch_id):
    batch_df.persist()
    pandas_df = batch_df.toPandas()

    upsert_query = """
    INSERT INTO stream_weather (grad, region, drzava, temperatura, osecaj, vlaznost, stanje, lokalno_vreme, datum)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (grad, datum) DO UPDATE SET
        region = EXCLUDED.region,
        drzava = EXCLUDED.drzava,
        temperatura = EXCLUDED.temperatura,
        osecaj = EXCLUDED.osecaj,
        vlaznost = EXCLUDED.vlaznost,
        stanje = EXCLUDED.stanje,
        lokalno_vreme = EXCLUDED.lokalno_vreme;
    """

    import psycopg2
    conn = psycopg2.connect(**postgres_properties)
    cursor = conn.cursor()

    for index, row in pandas_df.iterrows():
        cursor.execute(upsert_query, (
            row['grad'], row['region'], row['drzava'],
            row['temperatura'], row['osecaj'], row['vlaznost'],
            row['stanje'], row['lokalno_vreme'], row['datum']
        ))

    conn.commit()
    cursor.close()
    conn.close()
    batch_df.unpersist()

# Pokretanje streaminga
query = df_translated.writeStream \
    .foreachBatch(write_to_postgres) \
    .outputMode("update") \
    .start()

query.awaitTermination()

