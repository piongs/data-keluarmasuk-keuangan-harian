import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="Keuangan Pribadi",
    page_icon="💰",
    layout="wide"
)

# ===================== DATABASE =====================
conn = sqlite3.connect("keuangan.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transaksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal TEXT,
    jenis TEXT,
    jumlah INTEGER,
    keterangan TEXT
)
""")
conn.commit()

# ===================== CSS =====================
st.markdown("""
<style>
.main {
    background: linear-gradient(135deg, #e0f2fe, #f8fafc);
    font-family: 'Inter', system-ui, sans-serif;
}
.header {
    background: linear-gradient(135deg, #2563eb, #1e40af);
    color: white;
    padding: 36px;
    border-radius: 26px;
    text-align: center;
    box-shadow: 0 25px 50px rgba(37,99,235,0.45);
    margin-bottom: 35px;
}
.card {
    background: rgba(255,255,255,0.78);
    backdrop-filter: blur(18px);
    border-radius: 24px;
    padding: 26px;
    box-shadow: 0 18px 45px rgba(0,0,0,0.12);
    margin-bottom: 30px;
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.85);
    padding: 22px;
    border-radius: 22px;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e3a8a, #1e40af);
}
section[data-testid="stSidebar"] * {
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ===================== HEADER =====================
st.markdown("""
<div class="header">
    <h1>💰 Keuangan Pribadi</h1>
    <p>Catat uang masuk & keluar • Saldo otomatis • Data aman</p>
</div>
""", unsafe_allow_html=True)

# ===================== SIDEBAR =====================
menu = st.sidebar.radio(
    "📌 Menu",
    ["➕ Tambah Transaksi", "📊 Dashboard", "📜 Riwayat"]
)

# ===================== TAMBAH TRANSAKSI =====================
if menu == "➕ Tambah Transaksi":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("➕ Tambah Transaksi")

    tanggal = st.date_input("Tanggal", date.today())
    jenis = st.selectbox("Jenis", ["Uang Masuk", "Uang Keluar"])
    jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000)
    keterangan = st.text_input("Keterangan")

    if st.button("💾 Simpan"):
        cursor.execute(
            "INSERT INTO transaksi (tanggal, jenis, jumlah, keterangan) VALUES (?,?,?,?)",
            (tanggal, jenis, jumlah, keterangan)
        )
        conn.commit()
        st.success("Transaksi tersimpan")

    st.markdown("</div>", unsafe_allow_html=True)

# ===================== DASHBOARD =====================
if menu == "📊 Dashboard":
    df = pd.read_sql("SELECT * FROM transaksi", conn)

    total_masuk = df[df["jenis"] == "Uang Masuk"]["jumlah"].sum()
    total_keluar = df[df["jenis"] == "Uang Keluar"]["jumlah"].sum()
    saldo = total_masuk - total_keluar

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Masuk", f"Rp {total_masuk:,.0f}")
    col2.metric("Total Keluar", f"Rp {total_keluar:,.0f}")
    col3.metric("Saldo Akhir", f"Rp {saldo:,.0f}")

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if not df.empty:
        df["nilai"] = df.apply(
            lambda x: x["jumlah"] if x["jenis"] == "Uang Masuk" else -x["jumlah"],
            axis=1
        )
        df["saldo"] = df["nilai"].cumsum()
        st.line_chart(df["saldo"])
    st.markdown("</div>", unsafe_allow_html=True)

# ===================== RIWAYAT + EDIT + DELETE =====================
if menu == "📜 Riwayat":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📜 Riwayat Transaksi")

    df = pd.read_sql("SELECT * FROM transaksi ORDER BY tanggal DESC", conn)

    if df.empty:
        st.info("Belum ada transaksi")
    else:
        st.dataframe(df, use_container_width=True)

        st.divider()
        st.subheader("✏️ Edit / 🗑️ Hapus Transaksi")

        id_pilih = st.selectbox(
            "Pilih ID Transaksi",
            df["id"]
        )

        data = df[df["id"] == id_pilih].iloc[0]

        tgl_edit = st.date_input("Tanggal", pd.to_datetime(data["tanggal"]))
        jenis_edit = st.selectbox(
            "Jenis",
            ["Uang Masuk", "Uang Keluar"],
            index=0 if data["jenis"] == "Uang Masuk" else 1
        )
        jumlah_edit = st.number_input(
            "Jumlah (Rp)",
            min_value=0,
            step=1000,
            value=int(data["jumlah"])
        )
        ket_edit = st.text_input(
            "Keterangan",
            value=data["keterangan"]
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Update"):
                cursor.execute("""
                    UPDATE transaksi
                    SET tanggal=?, jenis=?, jumlah=?, keterangan=?
                    WHERE id=?
                """, (tgl_edit, jenis_edit, jumlah_edit, ket_edit, id_pilih))
                conn.commit()
                st.success("Transaksi berhasil diupdate")
                st.rerun()

        with col2:
            if st.button("🗑️ Hapus"):
                cursor.execute(
                    "DELETE FROM transaksi WHERE id=?",
                    (id_pilih,)
                )
                conn.commit()
                st.warning("Transaksi dihapus")
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
