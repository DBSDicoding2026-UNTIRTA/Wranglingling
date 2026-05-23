import pandas as pd
import os

# Convert CSV to Parquet (lebih kecil & lebih cepat)
csv_file = 'clean_sampah_metadata_updated.csv'
parquet_file = 'clean_sampah_metadata_updated.parquet'

print(f"Loading {csv_file}...")
df = pd.read_csv(csv_file)

print(f"Converting to Parquet...")
df.to_parquet(parquet_file, compression='snappy')

# Check file sizes
csv_size = os.path.getsize(csv_file) / 1024
parquet_size = os.path.getsize(parquet_file) / 1024
reduction = (1 - parquet_size/csv_size) * 100

print(f"\n✓ Selesai!")
print(f"CSV: {csv_size:.0f}KB → Parquet: {parquet_size:.0f}KB")
print(f"Ukuran berkurang: {reduction:.1f}%")
