from pyspark.sql import SparkSession
from pyspark.sql.functions import col, max, min, first
import psycopg2

spark = SparkSession.builder \
    .appName("AgregacijaNajToplijiNajHladniji") \
    .config("spark.jars", "/opt/spark-submit/postgresql-42.3.5.jar") \
    .getOrCreate()

# Učitaj podatke iz PostgreSQL
df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://postgres-db:5432/projekat_baza2") \
    .option("dbtable", "daily_weather") \
    .option("user", "POSTGRESS_USER") \
    .option("password", "POSTGRESS_PASSWORD") \
    .option("driver", "org.postgresql.Driver") \
    .load()

# Filtriraj relevantne države
df = df.filter(col("drzava").isin("Srbija", "Hrvatska", "BiH", "Severna Makedonija"))

# Najtopliji gradovi
window_topli = df.groupBy("datum", "drzava").agg(
    max("temperatura").alias("max_temperatura")
).join(df, ["datum", "drzava"]).filter(
    col("temperatura") == col("max_temperatura")
).groupBy("datum", "drzava").agg(
    first("grad").alias("najtopliji_grad"),
    first("max_temperatura").alias("max_temperatura"),
    first("stanje").alias("stanje_najtoplijeg")
)

# Najhladniji gradovi
window_hladni = df.groupBy("datum", "drzava").agg(
    min("temperatura").alias("min_temperatura")
).join(df, ["datum", "drzava"]).filter(
    col("temperatura") == col("min_temperatura")
).groupBy("datum", "drzava").agg(
    first("grad").alias("najhladniji_grad"),
    first("min_temperatura").alias("min_temperatura"),
    first("stanje").alias("stanje_najhladnijeg")
)

# Spoji u jednu tabelu
final_df = window_topli.join(window_hladni, ["datum", "drzava"])

# Privremeni prikaz u pandas DataFrame
pdf = final_df.toPandas()

# Upsert u PostgreSQL
conn = psycopg2.connect(
    host="postgres-db",
    database="projekat_baza",
    user="POSTGRESS_USER",
    password="POSTGRESS_PASSWORD"
)
cursor = conn.cursor()

for index, row in pdf.iterrows():
    cursor.execute("""
        INSERT INTO weather_agregacija (
            datum, drzava, najtopliji_grad, max_temperatura, stanje_najtoplijeg,
            najhladniji_grad, min_temperatura, stanje_najhladnijeg
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (datum, drzava) DO UPDATE SET
            najtopliji_grad = EXCLUDED.najtopliji_grad,
            max_temperatura = EXCLUDED.max_temperatura,
            stanje_najtoplijeg = EXCLUDED.stanje_najtoplijeg,
            najhladniji_grad = EXCLUDED.najhladniji_grad,
            min_temperatura = EXCLUDED.min_temperatura,
            stanje_najhladnijeg = EXCLUDED.stanje_najhladnijeg;
    """, (
        row["datum"], row["drzava"], row["najtopliji_grad"], row["max_temperatura"],
        row["stanje_najtoplijeg"], row["najhladniji_grad"], row["min_temperatura"],
        row["stanje_najhladnijeg"]
    ))

conn.commit()
cursor.close()
conn.close()

print("✅ Tabela 'weather_agregacija' uspešno ažurirana bez dupliranja.")

spark.stop()

