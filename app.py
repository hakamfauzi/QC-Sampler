import streamlit as st
import pandas as pd
import io # Diperlukan untuk memproses file di memori

# -----------------------------------------------------------------
# Fungsi inti dari skrip Anda, sedikit dimodifikasi
# -----------------------------------------------------------------

def adaptive_sample(x, prop, min_samp):
    """
    Fungsi sampling adaptif.
    Mengambil 'prop' persen dari data, dengan jaminan 'min_samp' baris.
    Tidak akan mengambil lebih banyak dari jumlah baris yang ada.
    """
    n_rows = len(x)
    # Ambil yg lebih besar antara proporsi dan minimal
    n_sample = max(int(n_rows * prop), min_samp)
    # Jangan lebih banyak dari total kategori
    n_sample = min(n_sample, n_rows)
    # Ambil sample dengan random_state tetap agar bisa direproduksi
    return x.sample(n=n_sample, random_state=42)

def process_sampling(df, group_column, proporsi, min_sample):
    """
    Melakukan grouping dan menerapkan fungsi sampling.
    """
    # Terapkan per kategori
    sample_df = (
        df.groupby(group_column, group_keys=False)
        .apply(lambda x: adaptive_sample(x, proporsi, min_sample))
    )
    return sample_df

def process_sampling_sessions(df, group_column, session_column, proporsi, min_sessions):
    """
    Melakukan sampling berbasis sesi per kategori.
    Saat sebuah sesi terpilih, semua baris (bubble) dalam sesi tersebut diikutkan.
    """
    def sample_sessions(group):
        # Daftar sesi unik dalam kategori ini
        unique_sessions = group[session_column].dropna().unique()
        total_sessions = len(unique_sessions)
        # Tentukan jumlah sesi yang diambil berdasarkan proporsi dan minimal
        n_sample = max(int(total_sessions * proporsi), min_sessions)
        n_sample = min(n_sample, total_sessions)
        # Ambil sesi secara reproducible
        if total_sessions == 0 or n_sample == 0:
            return group.iloc[0:0]  # kembalikan empty frame untuk kategori tanpa sesi
        selected = (
            pd.Series(unique_sessions)
            .sample(n=n_sample, random_state=42)
            .tolist()
        )
        return group[group[session_column].isin(selected)]

    sample_df = (
        df.groupby(group_column, group_keys=False)
        .apply(sample_sessions)
    )
    return sample_df

@st.cache_data # Cache data agar tidak perlu konversi ulang saat interaksi
def to_excel(df):
    """
    Mengonversi DataFrame ke file Excel di dalam memori.
    """
    output = io.BytesIO()
    # Gunakan 'with' untuk memastikan writer ditutup dengan benar
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sampled_Data')
    
    processed_data = output.getvalue()
    return processed_data

def compute_sample_size(N, moe, z, p=0.5):
    """
    Menghitung ukuran sampel berdasarkan margin of error (moe),
    nilai Z (tingkat kepercayaan), dan estimasi proporsi populasi p.
    Menggunakan koreksi populasi hingga (Finite Population Correction).
    """
    if N <= 0:
        return 0
    n0 = (z ** 2) * p * (1 - p) / (moe ** 2)
    n = int((N * n0) / (n0 + N - 1))
    return max(1, min(n, N))

# -----------------------------------------------------------------
# Layout Aplikasi Streamlit
# -----------------------------------------------------------------

# Konfigurasi halaman (judul tab dan ikon)
st.set_page_config(page_title="QC Sampler", page_icon="📊")

# Judul Utama Aplikasi
st.title("📊 Aplikasi QC Sampling Generator")
st.write("Unggah file Excel populasi Anda untuk mengambil sampel secara *stratified*.")

# --- Bagian Sidebar untuk Input Parameter ---
st.sidebar.header("⚙️ Parameter Sampling")

# Pilih metode penentuan ukuran sampel
mode = st.sidebar.radio(
    "Metode penentuan sampel",
    ("Proporsi manual", "Margin of Error"),
    index=0
)

# Input 1: Nama kolom untuk stratifikasi
# Menggunakan nilai default dari skrip Anda
group_column = st.sidebar.text_input(
    "Nama Kolom Kategori (Stratifikasi)",
    "Kip - UID MainCategory"
)

# Input 2: Proporsi atau MOE/CL
if mode == "Proporsi manual":
    proporsi = st.sidebar.slider(
        "Proporsi Sample (misal: 0.1 untuk 10%)",
        min_value=0.01,  # 1%
        max_value=1.0,   # 100%
        value=0.1,       # Default 10%
        step=0.01
    )
else:
    margin_of_error = st.sidebar.slider(
        "Margin of Error (E)",
        min_value=0.01,
        max_value=0.20,
        value=0.05,
        step=0.01
    )
    confidence_level = st.sidebar.selectbox(
        "Confidence Level",
        ("90%", "95%", "99%"),
        index=1
    )

# Input kolom sesi (default engine berbasis sesi)
session_column = st.sidebar.text_input(
    "Nama Kolom Session ID",
    "session_id"
)

# Input 3: Sample Minimal (Input Angka)
min_sample = st.sidebar.number_input(
    "Minimal Sesi per Kategori",
    min_value=1,
    value=5  # Default 5
)

# --- Bagian Utama untuk Upload dan Hasil ---

# File Uploader
uploaded_file = st.file_uploader(
    "Unggah file Excel populasi Anda di sini", 
    type=["xlsx", "xls"]
)

if uploaded_file is not None:
    # 1. Baca file yang diunggah
    st.info("Membaca file Excel...")
    try:
        df = pd.read_excel(uploaded_file)
        st.write("**Preview Data Asli (5 baris pertama):**")
        st.dataframe(df.head())

        # Validasi kolom yang diperlukan
        can_sample = True
        missing_cols = []
        if group_column not in df.columns:
            missing_cols.append(group_column)
        if session_column not in df.columns:
            missing_cols.append(session_column)
        if missing_cols:
            can_sample = False
            st.error(f"Kolom berikut tidak ditemukan di file: {', '.join(missing_cols)}")

        # Hitung proporsi efektif berbasis sesi (default engine)
        N_base = df[session_column].nunique() if can_sample else 0

        if mode == "Margin of Error":
            z_lookup = {"90%": 1.645, "95%": 1.96, "99%": 2.576}
            z = z_lookup[confidence_level]
            n_req = compute_sample_size(N_base, margin_of_error, z)
            proporsi_efektif = (n_req / N_base) if N_base > 0 else 0
            st.info(f"Target ukuran sampel: {n_req} dari {N_base} sesi (proporsi {proporsi_efektif:.2%}).")
        else:
            proporsi_efektif = proporsi
            st.info(f"Proporsi sample manual: {proporsi_efektif:.2%} dari {N_base} sesi.")

        # 2. Tombol untuk memulai proses
        if st.button("🚀 Generate Sample"):
            # 3. Lakukan proses dengan spinner
            with st.spinner("Sedang memproses sampling... Mohon tunggu."):
                try:
                    # 4. Panggil fungsi sampling berbasis sesi (default engine)
                    if not can_sample:
                        st.warning("Sampling dibatalkan: periksa kembali kolom yang hilang.")
                        sample_df = df.iloc[0:0]
                    else:
                        sample_df = process_sampling_sessions(df, group_column, session_column, proporsi_efektif, min_sample)
                    
                    st.success("🎉 Sampling Selesai!")
                    
                    # 5. Tampilkan hasil distribusi
                    st.subheader("Distribusi Sampel per Kategori")
                    st.dataframe(sample_df[group_column].value_counts())

                    # 5b. Ringkasan per kategori (Unit: Sesi)
                    if can_sample:
                        def _target_sesi_per_kategori(n_sess):
                            return min(n_sess, max(int(n_sess * proporsi_efektif), min_sample))

                        pop_sess_counts = df.groupby(group_column)[session_column].nunique()
                        pop_sess_df = pop_sess_counts.reset_index()
                        pop_sess_df.columns = ["Kategori", "Populasi Sesi"]
                        pop_sess_df["Target Sesi"] = pop_sess_df["Populasi Sesi"].apply(_target_sesi_per_kategori)

                        actual_sess_counts = sample_df.groupby(group_column)[session_column].nunique()
                        actual_sess_df = actual_sess_counts.reset_index()
                        actual_sess_df.columns = ["Kategori", "Sesi Aktual"]

                        ringkasan_sess_df = pop_sess_df.merge(actual_sess_df, on="Kategori", how="left")
                        ringkasan_sess_df["Sesi Aktual"] = ringkasan_sess_df["Sesi Aktual"].fillna(0).astype(int)

                        st.subheader("Ringkasan Per Kategori (Unit: Sesi)")
                        st.dataframe(ringkasan_sess_df)
                    
                    # 6. Tampilkan preview hasil
                    st.subheader("Preview Data Sampel")
                    st.dataframe(sample_df.head())
                    
                    # 7. Siapkan file untuk di-download
                    excel_data = to_excel(sample_df)
                    
                    # 8. Tampilkan tombol download
                    st.download_button(
                        label="⬇️ Download Data Sample (Excel)",
                        data=excel_data,
                        file_name=f"sample_stratified_min_{min_sample}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                except KeyError:
                    # Penanganan error jika nama kolom tidak ditemukan
                    st.error(f"Error: Kolom '{group_column}' tidak ditemukan di file Excel.")
                    st.warning("Pastikan nama kolom di sidebar sesuai dengan di file Anda.")
                except Exception as e:
                    # Penanganan error umum
                    st.error(f"Terjadi error saat pemrosesan: {e}")

    except Exception as e:
        st.error(f"Gagal membaca file Excel. Error: {e}")