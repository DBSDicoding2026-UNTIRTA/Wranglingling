# Dashboard Analisis Sampah Daur Ulang

Deskripsi singkat
- Aplikasi Streamlit untuk menampilkan analisis metadata dan contoh gambar bersih sampah daur ulang.

Perubahan yang dilakukan
- Kolom `file_path` dihapus dari data hasil wrangling untuk alasan privasi dan agar tidak ikut tersimpan di CSV akhir maupun tampil di dashboard.
- Hasil wrangling sekarang juga disalin ke folder `clean_images/` per kategori, sehingga output akhirnya tetap berupa gambar yang sudah lolos validasi.
- Menambahkan bagian "Contoh Gambar per Kategori" di dashboard:
  - Aplikasi akan mencari gambar hasil wrangling di folder `clean_images/` terlebih dahulu.
  - Jika gambar bersih tidak ditemukan, aplikasi tetap bisa mengambil contoh dari dataset asli atau memakai placeholder sederhana.

Isi data akhir
- File `clean_sampah_metadata.csv` hanya menyimpan metadata gambar yang dipakai untuk analisis, seperti kategori, nama file, ekstensi, dimensi, rasio aspek, jumlah piksel, ukuran file, dan mode warna.
- Kolom jalur file mentah tidak disertakan lagi di snapshot wrangled terbaru.
- Folder `clean_images/` berisi salinan gambar yang lolos proses cleaning, tersusun per kategori.

Menjalankan
1. Pastikan Python 3.9+ terpasang.
2. Instal dependensi:

```bash
pip install -r requirements.txt
```

3. Jalankan Streamlit:

```bash
streamlit run dashboard.py
```

Menambahkan gambar kategori sampah
- Jalankan notebook wrangling sampai selesai agar folder `clean_images/` terisi otomatis.
- Jika ingin menggunakan gambar contoh manual, letakkan file gambar per kategori di folder yang sesuai dengan nama kategori.
- Format yang didukung: PNG/JPG. Jika ada gambar, aplikasi akan menampilkannya sebagai contoh untuk tiap kategori.


