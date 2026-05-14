# Data Dictionary

Dokumen ini menjelaskan struktur metadata final yang digunakan pada proyek klasifikasi sampah daur ulang.

## Ringkasan Dataset

- Sumber metadata final: [clean_sampah_metadata_updated.csv](clean_sampah_metadata_updated.csv)
- Folder gambar final: [images](images)
- Jumlah baris metadata: 13.324
- Jumlah kelas: 8
- Kelas final: Clothes, Kaca, Kardus, Kertas, Logam, Organik, Plastik, Residu

## Skema Data

| Column | Dtype | Non-null | Null | Unique | Contoh Nilai | Deskripsi |
|---|---:|---:|---:|---:|---|---|
| class_label | object | 13324 | 0 | 8 | Clothes, Kaca, Kardus, Kertas, Logam | Label kelas sampah pada gambar. |
| file_name | object | 13324 | 0 | 13296 | R_3850.jpg, clothes1.jpg, biologic... | Nama file gambar asli. |
| file_ext | object | 13324 | 0 | 1 | .jpg | Ekstensi file gambar. |
| width | int64 | 13324 | 0 | 516 | 225, 183, 194, 259, 88 | Lebar gambar dalam piksel. |
| height | int64 | 13324 | 0 | 578 | 225, 275, 259, 194, 222 | Tinggi gambar dalam piksel. |
| aspect_ratio | float64 | 13324 | 0 | 1142 | 1.0, 0.6655, 0.749, 1.3351, 0.3964 | Rasio lebar terhadap tinggi gambar. |
| pixels | int64 | 13324 | 0 | 945 | 50625, 50325, 50246, 19536, 50396 | Jumlah total piksel gambar ($width \times height$). |
| file_size_kb | float64 | 13324 | 0 | 4282 | 2.6, 4.86, 2.65, 3.83, 3.16 | Ukuran file gambar dalam KB. |
| color_mode | object | 13324 | 0 | 3 | RGB, P, L | Mode warna gambar saat dibaca. |

## Penjelasan Kolom

- `class_label` dipakai sebagai target klasifikasi.
- `file_name` membantu pelacakan gambar per kategori.
- `file_ext` menunjukkan format file yang diproses.
- `width`, `height`, dan `pixels` dipakai untuk analisis resolusi.
- `aspect_ratio` dipakai untuk melihat perbedaan proporsi gambar antar kelas.
- `file_size_kb` dipakai untuk melihat perbedaan ukuran file dan quality check.
- `color_mode` membantu mengecek konsistensi channel dan format gambar.

## Catatan Kualitas Data

- Data sudah dibersihkan dari kolom jalur file mentah untuk alasan privasi.
- Duplikasi file yang tidak diperlukan sudah dikurangi pada tahap wrangling.
- Dataset final sudah disiapkan agar siap dipakai untuk analisis lanjutan dan preprocessing model.
- Folder sementara seperti `clean_images/`, `clean_images_new/`, `clean_images_filtered/`, dan `clean_images_merged/` tidak dipakai lagi dalam workflow final.

## Referensi Penggunaan

- Dashboard interaktif: [dashboard.py](dashboard.py)
- Notebook analisis: [Analisis Data Tahap 1.ipynb](Analisis%20Data%20Tahap%201.ipynb)
- Data final untuk dashboard dan analisis: [clean_sampah_metadata_updated.csv](clean_sampah_metadata_updated.csv)
