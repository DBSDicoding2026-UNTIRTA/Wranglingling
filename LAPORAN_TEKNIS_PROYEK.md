# Laporan Teknis Proyek: Klasifikasi Sampah Daur Ulang

## 1. Ringkasan Eksekutif

Proyek ini membangun alur analisis data untuk dataset gambar sampah daur ulang, mulai dari problem discovery, pengumpulan data, data assessment, cleaning, exploratory data analysis, explanatory analysis, hingga penyajian hasil dalam dashboard interaktif Streamlit.

Hasil akhir proyek menunjukkan bahwa dataset final sudah jauh lebih siap untuk tahap modeling. Metadata final berisi 13.324 gambar, 8 kelas, tanpa nilai null, dan sudah dilengkapi struktur folder gambar final di [images](images), metadata final di [clean_sampah_metadata_updated.csv](clean_sampah_metadata_updated.csv), data dictionary di [DATA_DICTIONARY.md](DATA_DICTIONARY.md), serta dashboard di [dashboard.py](dashboard.py).

## 2. Problem Discovery

Masalah utama yang ingin diselesaikan adalah menyiapkan dataset klasifikasi sampah yang layak untuk dianalisis dan dipakai sebagai dasar model machine learning. Pada tahap awal, dataset mentah masih memiliki keterbatasan jumlah kelas, ketidakseimbangan distribusi, dan kebutuhan validasi kualitas file gambar.

Snapshot awal yang dibahas di notebook menunjukkan metadata mentah berjumlah 7.014 baris dengan 6 kelas. Dari sini muncul kebutuhan untuk:

- menilai distribusi kelas dan tingkat imbalance,
- memeriksa kualitas gambar berdasarkan ukuran file dan resolusi,
- menyiapkan data yang konsisten untuk preprocessing dan modeling,
- memperluas cakupan kelas agar representasi sampah lebih lengkap.

## 3. Tujuan Analisis

Analisis ini difokuskan pada dua pertanyaan bisnis utama:

1. Bagaimana distribusi jumlah gambar per kategori pada snapshot final, kategori mana yang porsinya di bawah 15%, dan berapa imbalance ratio antara kelas terbesar dan terkecil?
2. Kategori mana yang memiliki median ukuran file dan median resolusi yang menyimpang minimal 20% dari median keseluruhan, serta berapa outlier rate ukuran file per kategori dengan metode IQR?

Tujuan praktis dari pertanyaan tersebut adalah menentukan prioritas augmentasi data, class weighting, standardisasi preprocessing, dan quality control sebelum tahap modeling.

## 4. Sumber Data dan Struktur Final

Dataset final yang digunakan berasal dari hasil wrangling data gambar sampah daur ulang. Struktur akhirnya adalah:

- metadata final: [clean_sampah_metadata_updated.csv](clean_sampah_metadata_updated.csv)
- folder gambar final: [images](images)
- referensi kolom: [DATA_DICTIONARY.md](DATA_DICTIONARY.md)

Karakteristik metadata final:

- total baris: 13.324
- jumlah kelas: 8
- jumlah kolom: 9
- tidak ada nilai null

Kolom yang tersimpan adalah `class_label`, `file_name`, `file_ext`, `width`, `height`, `aspect_ratio`, `pixels`, `file_size_kb`, dan `color_mode`.

## 5. Tahap Data Wrangling

Tahap wrangling dilakukan untuk mengubah data mentah menjadi dataset final yang stabil dan siap dianalisis. Langkah utamanya adalah:

- pengambilan data dari sumber publik,
- pengecekan struktur metadata,
- penyatuan data akhir ke format yang konsisten,
- penghapusan duplikasi yang tidak diperlukan,
- standarisasi nama kolom agar lebih jelas,
- penghapusan kolom jalur file untuk alasan privasi,
- pembersihan nilai kosong dengan strategi yang sesuai,
- verifikasi ulang jumlah kelas dan kualitas metadata.

Hasil wrangling menghasilkan dataset yang lebih rapi, konsisten, dan siap masuk ke tahap analisis eksploratif serta persiapan modeling.

## 6. Hasil Analisis Deskriptif

### 6.1 Distribusi Kelas

Distribusi kelas pada dataset final adalah sebagai berikut:

| Kelas | Jumlah | Persentase |
|---|---:|---:|
| Clothes | 5.325 | 39,97% |
| Kertas | 1.807 | 13,56% |
| Plastik | 1.257 | 9,43% |
| Logam | 1.210 | 9,08% |
| Kaca | 1.110 | 8,33% |
| Residu | 1.006 | 7,55% |
| Organik | 985 | 7,39% |
| Kardus | 624 | 4,68% |

Temuan utamanya:

- kelas terbesar adalah Clothes,
- kelas terkecil adalah Kardus,
- imbalance ratio mencapai 8,53x,
- ada 7 kelas yang memiliki porsi di bawah 15%.

Artinya, dataset final masih cukup imbalanced dan memerlukan strategi mitigasi saat modeling.

### 6.2 Karakteristik Ukuran File dan Resolusi

Statistik pusat keseluruhan menunjukkan:

- median ukuran file: 12,48 KB
- median jumlah piksel: 50.625
- median width: 299 px
- median height: 250 px

Interpretasi pentingnya adalah resolusi dasar antar kelas relatif seragam pada sebagian besar kelas, tetapi ukuran file masih bervariasi cukup jauh. Ini biasanya mengindikasikan adanya perbedaan kompresi, detail visual, atau karakteristik visual objek pada masing-masing kelas.

### 6.3 Kelas dengan Deviasi Signifikan

Perbandingan terhadap median keseluruhan menunjukkan bahwa Clothes adalah kelas yang paling berbeda secara teknis:

- median ukuran file Clothes: 25,05 KB, atau +100,72% dari median keseluruhan,
- median jumlah piksel Clothes: 213.200, atau +321,14% dari median keseluruhan.

Kelas lain cenderung memiliki median jumlah piksel yang sangat dekat dengan keseluruhan, sehingga perbedaan utama ada pada ukuran file, bukan pada resolusi dasar. Residu menonjol karena ukuran file median relatif lebih kecil dibanding median keseluruhan dan memiliki outlier rate tertinggi.

### 6.4 Outlier Ukuran File

Outlier rate ukuran file dihitung dengan metode IQR. Hasilnya:

| Kelas | Outlier Rate |
|---|---:|
| Clothes | 2,93% |
| Kaca | 2,43% |
| Kardus | 4,65% |
| Kertas | 0,39% |
| Logam | 3,31% |
| Organik | 0,71% |
| Plastik | 4,22% |
| Residu | 8,35% |

Residu menjadi kelas dengan outlier rate tertinggi, sehingga layak menjadi prioritas quality check tambahan.

## 7. Explanatory Analysis dan Implikasi Bisnis

Analisis eksploratif tidak hanya menjelaskan distribusi data, tetapi juga memberi dampak langsung ke keputusan pra-modeling:

- kelas minoritas perlu diprioritaskan untuk augmentasi data,
- class weighting direkomendasikan untuk mengurangi bias ke kelas mayoritas,
- preprocessing gambar harus konsisten, terutama resize dan normalisasi,
- kelas dengan outlier rate tinggi perlu quality control tambahan,
- Clothes perlu perlakuan khusus karena karakteristiknya paling berbeda dari kelas lain.

Secara teknis, korelasi antara jumlah piksel dan ukuran file berada pada kisaran positif sedang hingga kuat, yang mendukung interpretasi bahwa ukuran file memang berkaitan dengan kompleksitas visual dan resolusi gambar.

## 8. Dashboard Interaktif

Dashboard Streamlit pada [dashboard.py](dashboard.py) disusun untuk menampilkan hasil analisis secara interaktif. Fitur utamanya mencakup:

- ringkasan statistik dataset,
- distribusi jumlah data per kategori,
- heatmap korelasi fitur numerik,
- distribusi ukuran file,
- analisis deviasi dan outlier,
- distribusi jumlah piksel,
- contoh gambar per kategori,
- insight otomatis dari data yang sedang difilter,
- kesimpulan ringkas untuk pengambilan keputusan.

Dashboard ini berfungsi sebagai jembatan antara hasil analisis teknis dan kebutuhan pengguna non-teknis yang perlu memahami kondisi dataset dengan cepat.

## 9. Hasil Akhir Proyek

Hasil akhir yang berhasil dicapai adalah:

- dataset final yang sudah dibersihkan dan distandarkan,
- struktur kelas menjadi 8 kategori,
- metadata final tanpa missing value,
- dokumentasi struktur data melalui data dictionary,
- dashboard interaktif untuk eksplorasi hasil analisis,
- rekomendasi siap pakai untuk tahap modeling.

Secara keseluruhan, proyek ini menghasilkan dataset yang lebih matang untuk proses machine learning, walaupun masih memerlukan perhatian pada imbalance kelas dan perbedaan karakteristik visual antar kategori.

## 10. Rekomendasi Tahap Berikutnya

Sebelum masuk ke modeling, langkah yang paling masuk akal adalah:

1. menggunakan stratified split untuk train, validation, dan test,
2. menerapkan class weight atau balanced sampler,
3. melakukan augmentasi terarah pada kelas minoritas,
4. melakukan resize dan normalisasi yang konsisten,
5. mengecek ulang gambar dengan outlier tinggi atau resolusi yang sangat berbeda,
6. memulai baseline model CNN seperti ResNet50 atau EfficientNet.

## 11. Kesimpulan

Proyek ini berhasil menyelesaikan alur analisis end-to-end dari problem discovery hingga hasil akhir dataset dan dashboard. Temuan utama menunjukkan bahwa dataset final sudah siap untuk modeling, tetapi masih memiliki imbalance yang cukup tinggi dan perbedaan karakteristik file antar kelas yang harus diakomodasi pada tahap preprocessing dan training.

Dengan kata lain, nilai utama dari proyek ini bukan hanya pada dashboard yang dihasilkan, tetapi juga pada kesiapan data final sebagai fondasi proses klasifikasi sampah daur ulang yang lebih akurat dan lebih stabil.