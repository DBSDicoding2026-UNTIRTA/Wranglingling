# Dashboard Analisis Sampah Daur Ulang

Aplikasi ini berisi hasil proses data wrangling, exploratory data analysis, explanatory analysis, dan dashboard interaktif Streamlit untuk klasifikasi sampah daur ulang.

## Ringkasan Proyek

Proyek ini menggabungkan beberapa tahapan utama:
- Gathering data dari dataset publik Kaggle.
- Assessing data untuk mengecek kualitas, struktur, duplikasi, dan kelengkapan.
- Cleaning data untuk menghasilkan metadata final yang siap dianalisis dan dipakai modeling.
- EDA dan explanatory analysis untuk menjawab pertanyaan bisnis.
- Visualisasi data dan dashboard interaktif menggunakan Streamlit.
- Data dictionary sebagai referensi kolom dan tipe data.

## Struktur Final Data

Struktur data final yang dipakai saat ini:
- Folder gambar final: [images](images)
- Metadata final: [clean_sampah_metadata_updated.csv](clean_sampah_metadata_updated.csv)
- Data dictionary: [DATA_DICTIONARY.md](DATA_DICTIONARY.md)
- Dashboard Streamlit: [dashboard.py](dashboard.py)

Folder [images](images) berisi subfolder kelas:
- `Clothes`
- `Kaca`
- `Kardus`
- `Kertas`
- `Logam`
- `Organik`
- `Plastik`
- `Residu`

## Hasil Utama

- Distribusi data antar kelas sudah dianalisis untuk melihat imbalance.
- Dataset final sudah memuat kelas tambahan `Clothes` dan `Organik`.
- Dashboard menampilkan ringkasan statistik, distribusi kelas, korelasi numerik, insight, dan contoh gambar per kelas.
- Data final sudah disiapkan agar lebih siap diproses oleh model.

## Menjalankan Dashboard

1. Pastikan Python 3.9+ tersedia.
2. Install dependency:

```bash
pip install -r requirements.txt
```

3. Jalankan Streamlit:

```bash
streamlit run dashboard.py
```

## Notebook Analisis

Notebook utama ada di [Analisis Data Tahap 1.ipynb](Analisis%20Data%20Tahap%201.ipynb).
Di notebook tersebut terdapat:
- proses gathering data,
- assessment data,
- cleaning data,
- EDA,
- visualisasi,
- explanatory analysis,
- ringkasan kesiapan data untuk modeling.

## Catatan

- File metadata lama yang tidak dipakai lagi sudah dihapus.
- Folder sementara seperti `clean_images/`, `clean_images_new/`, `clean_images_filtered/`, dan `clean_images_merged/` tidak dipakai lagi dalam workflow final.
- Jika ingin memperbarui notebook atau data final, gunakan `clean_sampah_metadata_updated.csv` dan folder [images](images) sebagai sumber utama.
