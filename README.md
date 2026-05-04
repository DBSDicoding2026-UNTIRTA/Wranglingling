# Dashboard Analisis Sampah Daur Ulang

Deskripsi singkat
- Aplikasi Streamlit untuk menampilkan analisis metadata gambar sampah daur ulang.

Perubahan yang dilakukan
- Kolom `file_path` dihapus dari data hasil wrangling untuk alasan privasi dan agar tidak ikut tersimpan di CSV akhir maupun tampil di dashboard.
- Menambahkan bagian "Contoh Gambar per Kategori" di dashboard:
  - Aplikasi akan mencari gambar di folder `images/` dengan nama file berformat `{slug_kategori}.png` (slug: huruf kecil, non-alfanumerik diganti underscore).
  - Jika gambar tidak ditemukan, aplikasi membuat placeholder sederhana otomatis dan menyimpannya di `images/`.

Isi data akhir
- File `clean_sampah_metadata.csv` hanya menyimpan metadata gambar yang dipakai untuk analisis, seperti kategori, nama file, ekstensi, dimensi, rasio aspek, jumlah piksel, ukuran file, dan mode warna.
- Kolom jalur file mentah tidak disertakan lagi di snapshot wrangled terbaru.

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
- Buat folder `images` di direktori proyek (opsional; aplikasi akan membuatnya otomatis jika belum ada).
- Simpan satu gambar untuk setiap kategori dengan nama file mengikuti slug kategori, misal `plastik_botol.png`, `kertas.png`, dll.
- Format yang didukung: PNG/JPG. Jika ada gambar, aplikasi akan menampilkannya sebagai contoh untuk tiap kategori.


