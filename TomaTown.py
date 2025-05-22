import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import re
import io

# CSS: Ubah tampilan berdasarkan status login
if 'login' in st.session_state and st.session_state.login:
    # Saat sudah login - warna halaman & sidebar
    st.markdown("""
        <style>
        .stApp {
            background-color: #B1CBA6;  /* Hijau */
        }
        section[data-testid="stSidebar"] {
            background-color: #E74C3C;  /* Sidebar tomato */
        }
        </style>
    """, unsafe_allow_html=True)
else:
    # Saat belum login (halaman login)
    st.markdown("""
        <style>
        .stApp {
            background-color: #B1CBA6;  /* Hijau */
        }
        </style>
    """, unsafe_allow_html=True)

# ---------- Login ---------- #
def cek_login(user, pw):
    return user == "admin" and pw == "admin123"

if 'login' not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.image("Background.png", width=800)
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if cek_login(username, password):
            st.session_state.login = True
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Username atau Password salah")

else:
    st.sidebar.title("TomaTown🍅")
    halaman = st.sidebar.radio("Pilih Halaman", ["Persediaan Tomat", "Penjualan", "Modal", "Laporan Laba/Rugi", "Akhiri Periode Panen"])
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.login = False
        st.rerun()

# ---------- Inisialisasi Database ---------- #
    def init_db():
        conn = sqlite3.connect("TomaTown_DataBase.db")
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS stok (
                kode TEXT PRIMARY KEY,
                jenis TEXT,
                jumlah REAL,
                harga REAL
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS modal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keterangan TEXT,
                kuantitas TEXT,
                harga REAL,
                jumlah REAL
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS penjualan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                waktu TEXT,
                kode TEXT,
                jumlah_terjual INTEGER,
                total_penjualan REAL
            )
        """)

        conn.commit()
        conn.close()

    init_db()

     # ---------- Fungsi Utility ---------- #
    def load_data(query, params=()):
        conn = sqlite3.connect("TomaTown_DataBase.db")
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def execute_query(query, params=()):
        conn = sqlite3.connect("TomaTown_DataBase.db")
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        conn.close()

# ----------------- Persediaan Tomat ----------------- #
    if halaman == "Persediaan Tomat":
        st.title("Selamat Datang!")
        st.image("Logo TomaTown.png", width=500)
        st.header("📦 Persediaan Tomat Saat Ini")
        data_stok = load_data("SELECT * FROM stok")
        st.dataframe(data_stok)

        with st.form("form_tambah"):
            kode = st.text_input("Kode")
            jenis = st.text_input("Jenis")
            jumlah = st.number_input("Jumlah (Kg)", min_value=0)
            harga = st.number_input("Harga (per Kg)", min_value=0.0)
            tambah = st.form_submit_button("Tambah")

            if tambah:
                if kode and jenis:
                    existing = load_data("SELECT * FROM stok WHERE kode = ?", (kode,))
                    if not existing.empty:
                        st.error("Kode sudah ada!")
                    else:
                        execute_query("INSERT INTO stok VALUES (?, ?, ?, ?)", (kode, jenis, jumlah, harga))
                        st.success("Data berhasil ditambahkan!")
                        st.rerun()
                else:
                    st.warning("Kode dan Jenis wajib diisi.")

        st.header("📦 Tambah Stok Tomat")
        with st.form("form_update"):
            kode_update = st.text_input("Kode Tomat")
            jumlah_tambah = st.number_input("Kuantitas", min_value=0)
            update = st.form_submit_button("Tambah")

            if update:
                if kode_update:
                    existing = load_data("SELECT * FROM stok WHERE kode = ?", (kode_update,))
                    if not existing.empty:
                        execute_query(
                            "UPDATE stok SET jumlah = jumlah + ? WHERE kode = ?",
                            (jumlah_tambah, kode_update)
                        )
                        st.success("Stok berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.error("Kode tidak ditemukan.")
                else:
                    st.warning("Silakan masukkan Kode Tomat.")

        st.header("📦 Hapus Stok Tomat")
        with st.form("form_hapus"):
            kode_hapus = st.text_input("Kode Tomat")
            jumlah_hapus = st.number_input("Kuantitas", min_value=0.0)
            hapus = st.form_submit_button("Hapus")

            if hapus:
                if kode_hapus:
                    existing = load_data("SELECT * FROM stok WHERE kode = ?", (kode_hapus,))
                    if not existing.empty:
                        stok_saat_ini = existing.iloc[0]["jumlah"]
                        if jumlah_hapus >= stok_saat_ini:
                            # Jika kuantitas yang dikurangkan lebih dari atau sama dengan stok, hapus seluruh baris
                            execute_query("DELETE FROM stok WHERE kode = ?", (kode_hapus,))
                            st.success("Stok habis. Pencatatan stok telah dihapus.")
                            st.rerun()
                        else:
                            # Kurangi stok
                            execute_query(
                                "UPDATE stok SET jumlah = jumlah - ? WHERE kode = ?",
                                (jumlah_hapus, kode_hapus)
                            )
                            st.success("Stok berhasil dikurangi!")
                            st.rerun()
                    else:
                        st.error("Kode tidak ditemukan.")
                else:
                    st.warning("Silakan masukkan Kode Tomat.")


# ----------------- Penjualan ----------------- #
    elif halaman == "Penjualan":
        st.header("🛒 Penjualan Tomat")
        penjualan = load_data("SELECT * FROM penjualan")
        penjualan = penjualan.rename(columns={
        "jumlah_terjual": "jumlah terjual",
        "total_penjualan": "total penjualan"
         })
        st.dataframe(penjualan, use_container_width=True)

        with st.form("form_jual"):
            kode_jual = st.text_input("Kode Tomat yang Dijual")
            jumlah_jual = st.number_input("Jumlah Terjual", min_value=0, step=1)
            jual = st.form_submit_button("Jual")

            if jual:
                stok = load_data("SELECT * FROM stok WHERE kode = ?", (kode_jual,))
                if not stok.empty:
                    available = stok.at[0, "jumlah"]
                    harga_satuan = stok.at[0, "harga"]
                    if jumlah_jual <= available:
                        total = jumlah_jual * harga_satuan
                        execute_query("UPDATE stok SET jumlah = jumlah - ? WHERE kode = ?", (jumlah_jual, kode_jual))
                        execute_query("INSERT INTO penjualan (waktu, kode, jumlah_terjual, total_penjualan) VALUES (?, ?, ?, ?)",
                                      (datetime.now().isoformat(), kode_jual, jumlah_jual, total))
                        st.success(f"Berhasil menjual {jumlah_jual} item. Total: Rp{total:,.0f}")
                        st.rerun()
                    else:
                        st.warning("Stok tidak mencukupi!")
                else:
                    st.error("Kode tidak ditemukan.")

        st.write("### Hapus Riwayat Penjualan")
        for i, row in penjualan.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
            col1.write(row["waktu"])
            col2.write(row["kode"])
            col3.write(f"{row['jumlah terjual']} Kg")
            col4.write(f"Rp{row['total penjualan']:,.0f}")
            if col5.button("🗑", key=f"hapus_penjualan_{i}"):
                execute_query("DELETE FROM penjualan WHERE id = ?", (row["id"],))
                st.rerun()

# ----------------- Modal ----------------- #
    elif halaman == "Modal":
        st.header("💼 Manajemen Modal")
        modal = load_data("SELECT * FROM modal")
        st.dataframe(modal)

        with st.form("form_modal"):
            ket_modal = st.text_input("Keterangan Modal")
            kuantitas_modal = st.text_input("Kuantitas (misal: 2 kg)")
            harga_modal = st.number_input("Harga per unit (Rp)", min_value=0, step=1000)

            jumlah_modal = 0
            if kuantitas_modal:
                match = re.match(r"(\d+(?:\.\d+)?)", kuantitas_modal)
                if match:
                    jumlah_unit = float(match.group(1))
                    jumlah_modal = jumlah_unit * harga_modal
            st.write(f"*Jumlah (Rp):* Rp {jumlah_modal:,.0f}")

            tambah_modal = st.form_submit_button("Tambah Modal")
            if tambah_modal:
                if ket_modal and kuantitas_modal and harga_modal > 0:
                    execute_query("INSERT INTO modal (keterangan, kuantitas, harga, jumlah) VALUES (?, ?, ?, ?)",
                                  (ket_modal, kuantitas_modal, harga_modal, jumlah_modal))
                    st.success("Modal berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.warning("Isi semua data terlebih dahulu.")

        st.write("### Hapus Pencatatan Modal")
        for i, row in modal.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
            col1.write(row["keterangan"])
            col2.write(row["kuantitas"])
            col3.write(f"Rp{row['harga']:,.0f}")
            col4.write(f"Rp{row['jumlah']:,.0f}")
            if col5.button("🗑", key=f"hapus_modal_{i}"):
                execute_query("DELETE FROM modal WHERE id = ?", (row["id"],))
                st.rerun()

# ----------------- Laporan Laba Rugi ----------------- #
    elif halaman == "Laporan Laba/Rugi":
        st.header("📊 Laporan Laba / Rugi")

        total_modal = load_data("SELECT SUM(jumlah) as total FROM modal").at[0, "total"] or 0
        total_penjualan = load_data("SELECT SUM(total_penjualan) as total FROM penjualan").at[0, "total"] or 0
        laba = total_penjualan - total_modal

        st.metric("Total Modal", f"Rp{total_modal:,.0f}")
        st.metric("Total Penjualan", f"Rp{total_penjualan:,.0f}")
        st.metric("Laba / Rugi", f"Rp{laba:,.0f}", delta=laba)
        
# ----------------- Akhiri Periode Panen ----------------- #
    elif halaman == "Akhiri Periode Panen":
        st.header("⚠ Akhiri Periode Panen - Reset Semua Data")

        st.warning("Semua data pencatatan (stok, modal, penjualan) akan dihapus PERMANEN setelah mengunduh backup.")

        # Ambil data
        df_stok = load_data("SELECT * FROM stok")
        df_modal = load_data("SELECT * FROM modal")
        df_penjualan = load_data("SELECT * FROM penjualan")

        # Simpan ke file Excel (multi-sheet)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_stok.to_excel(writer, index=False, sheet_name="Stok")
            df_modal.to_excel(writer, index=False, sheet_name="Modal")
            df_penjualan.to_excel(writer, index=False, sheet_name="Penjualan")
        output.seek(0)

        # Tombol download
        st.download_button(
            label="📥 Unduh Data (Excel)",
            data=output,
            file_name=f"TomaTown_{datetime.now()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Konfirmasi dan Hapus
        konfirmasi = st.checkbox("Saya sudah mengunduh backup data dan siap menghapus semua data.")
        if konfirmasi:
            if st.button("Akhiri Periode Panen dan Hapus Semua Data"):
                execute_query("DELETE FROM stok")
                execute_query("DELETE FROM modal")
                execute_query("DELETE FROM penjualan")
                st.success("Periode Panen saat ini berhasil diakhiri. Semua data telah dihapus.")
                st.rerun()