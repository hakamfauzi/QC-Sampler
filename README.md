# QC Sampling Generator (Streamlit)

Aplikasi Streamlit untuk melakukan sampling terstratifikasi (stratified sampling) dari data populasi berbasis Excel. Mendukung dua metode penentuan ukuran sampel: proporsi manual dan perhitungan berdasarkan Margin of Error (MOE) serta Confidence Level (CL) dengan koreksi populasi hingga (Finite Population Correction).

## Fitur
- Unggah file Excel (`.xlsx`, `.xls`) sebagai populasi.
- Stratifikasi berdasarkan kolom kategori yang dapat diatur.
- Metode penentuan sampel:
  - Proporsi manual: slider 1%–100% (default 10%).
  - Margin of Error: slider MOE 0.01–0.20 (default 0.05) dan pilihan CL (90%, 95%, 99%) dengan konversi ke nilai `z`.
- Minimal sampel per kategori (default 5) dengan batas maksimum tidak melebihi populasi kategori.
- Sampling reproducible menggunakan `random_state=42`.
- Preview data asli, distribusi sampel per kategori, dan tabel ringkasan per kategori (Populasi, Target Sampel, Sampel Aktual).
- Unduh hasil sampel sebagai file Excel.

## Prasyarat
- Python 3.9+ (disarankan).
- Paket yang diperlukan tercantum di `requirements.txt`:
  - `pandas`
  - `streamlit`
  - `openpyxl`

## Instalasi
1. Clone atau salin proyek ini ke mesin lokal.
2. (Opsional tapi disarankan) Buat virtual environment:
   - Windows: `python -m venv venv` lalu `venv\Scripts\activate`
3. Instal dependensi:
   - `pip install -r requirements.txt`

## Menjalankan Aplikasi
- Cara umum: `streamlit run app.py`
- Jika menggunakan virtual environment lokal: `python -m streamlit run app.py`
- Jika ingin memakai venv yang ada di folder (Windows): `.\n+  venv\Scripts\python.exe -m streamlit run app.py`

Setelah berjalan, buka URL lokal yang ditampilkan (biasanya `http://localhost:8501`).

## Cara Penggunaan
1. Atur parameter di sidebar:
   - `Nama Kolom Kategori (Stratifikasi)`: nama kolom kategori di dataset (default `Kip - UID MainCategory`).
   - `Metode penentuan sampel`:
     - `Proporsi manual`: pilih proporsi melalui slider (0.01–1.0; default 0.1).
     - `Margin of Error`: atur `E` (0.01–0.20; default 0.05) dan pilih `Tingkat Kepercayaan` (90%, 95%, 99%).
   - `Minimal Sample per Kategori`: jumlah minimum per kategori (default 5).
2. Unggah file Excel populasi (`.xlsx` atau `.xls`).
3. Tekan tombol `Generate Sample` untuk memulai proses sampling.
4. Tinjau hasil:
   - Info target ukuran sampel dan proporsi efektif (jika memakai MOE/CL).
   - Distribusi sampel per kategori.
   - Tabel ringkasan per kategori berisi `Populasi`, `Target Sampel`, dan `Sampel Aktual`.
5. Unduh hasil sampel (Excel) melalui tombol download yang tersedia.

## Perhitungan Ukuran Sampel (MOE/CL)
Perhitungan ukuran sampel menggunakan rumus dengan koreksi populasi hingga (Finite Population Correction, FPC):

- `n0 = (z^2 * p * (1 - p)) / (E^2)`
- `n = (N * n0) / (n0 + N - 1)`

Keterangan:
- `N`: ukuran populasi (jumlah baris data).
- `E`: Margin of Error (dalam proporsi, mis. 0.05 = 5%).
- `z`: nilai z-score berdasarkan tingkat kepercayaan (90%→1.645, 95%→1.96, 99%→2.576).
- `p`: estimasi proporsi populasi (default 0.5 untuk skenario terburuk).

Proporsi efektif yang digunakan untuk sampling terstratifikasi dihitung sebagai `proporsi_efektif = n / N`.

## Struktur Data Masukan
- File Excel akan dibaca ke `DataFrame` menggunakan `pandas.read_excel`.
- Secara default, sheet pertama digunakan jika tidak ditentukan.
- Pastikan kolom kategori (`group_column`) ada di data yang diunggah.

## Output
- Hasil sampling ditampilkan sebagai preview di aplikasi.
- Ringkasan per kategori ditampilkan dalam tabel (`Kategori`, `Populasi`, `Target Sampel`, `Sampel Aktual`).
- File hasil dapat diunduh sebagai Excel melalui tombol `Download Data Sample (Excel)`.

## Catatan & Tips
- Jika kolom kategori tidak ditemukan, aplikasi menampilkan pesan kesalahan; pastikan nama kolom di sidebar sesuai dengan data.
- Sampling bersifat reproducible karena menggunakan `random_state=42`.
- Kategori dengan populasi kecil akan tetap mendapatkan minimal sampel sesuai pengaturan, namun tidak melebihi populasi kategori tersebut.

## Struktur Proyek
```
sample_generator_mbaRum/
├── app.py
├── requirements.txt
└── venv/  (opsional; jika ada, Anda bisa memakai atau membuat venv baru)
```

## Kustomisasi
- Nilai `p` dalam perhitungan MOE saat ini diset `0.5`. Jika perlu, dapat ditambahkan sebagai input di sidebar.
- Anda dapat menyesuaikan nama kolom default untuk stratifikasi di `app.py`.

## Kontribusi
Silakan ajukan issue atau pull request untuk perbaikan, fitur tambahan, atau dokumentasi.