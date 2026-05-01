import streamlit as st
import pandas as pd
from database import run_query
from datetime import datetime, timedelta


def show_daily_financial_report():
    st.header("📊 Detaylı Departman Kazanç ve Üretim Raporu")

    # --- VERİ ÇEKME (FİLTRELER İÇİN) ---
    df_depts = run_query("SELECT name FROM Departmans")
    dept_list = ["Tümü"] + df_depts["name"].tolist() if not df_depts.empty else ["Tümü"]

    # --- FİLTRELEME ALANI ---
    with st.expander("🔍 Filtreleme Seçenekleri", expanded=True):
        col1, col2, col3 = st.columns(3)
        start_date = col1.date_input("Başlangıç Tarihi", datetime.now() - timedelta(days=7))
        end_date = col2.date_input("Bitiş Tarihi", datetime.now())
        selected_dept = col3.selectbox("Departman Seçin", dept_list)

    # --- SQL SORGUSU (GÜNCELLENDİ) ---
    # mp.is_internal bilgisi eklendi (1=İç Üretim, 0=Fason)
    query = """
        SELECT 
            p.date as [Tarih],
            d.name as [Departman],
            m.code as [Model],
            p.quantity as [Üretilen Adet],
            mp.birimFiyat as [Birim Fiyat],
            (p.quantity * mp.birimFiyat) as [Toplam Kazanç],
            mp.dovizKodu as [Döviz],
            CASE WHEN mp.is_internal = 1 THEN '🏠 İç Üretim' ELSE '🚚 Fason' END as [Üretim Tipi]
        FROM Production p
        JOIN Model m ON p.modelId = m.id
        JOIN Departmans d ON p.departmentId = d.id
        JOIN modelProcess mp ON mp.modelId = m.id AND mp.departmanId = d.id
        WHERE date(p.date) BETWEEN date(?) AND date(?)
    """

    params = [str(start_date), str(end_date)]

    if selected_dept != "Tümü":
        query += " AND d.name = ?"
        params.append(selected_dept)

    query += " ORDER BY p.date DESC"

    df_report = run_query(query, tuple(params))

    if not df_report.empty:
        # --- ÖZET METRİKLER ---
        st.subheader("📌 Genel Durum")
        m1, m2, m3, m4 = st.columns(4)

        total_qty = df_report["Üretilen Adet"].sum()
        total_earning = df_report["Toplam Kazanç"].sum()  # Basit toplam

        # İç/Fason adetlerini ayır
        internal_qty = df_report[df_report["Üretim Tipi"] == '🏠 İç Üretim']["Üretilen Adet"].sum()
        fason_qty = df_report[df_report["Üretim Tipi"] == '🚚 Fason']["Üretilen Adet"].sum()

        m1.metric("Toplam Üretim", f"{total_qty:,}")
        m2.metric("İç Üretim", f"{internal_qty:,}")
        m3.metric("Fason Üretim", f"{fason_qty:,}")
        m4.metric("Toplam Hakediş", f"{total_earning:,.2f}")

        st.divider()

        # --- TABLOLAR ---

        # 1. Departman ve Üretim Tipi Bazlı Özet
        st.subheader("🏢 Departman & Tip Analizi")
        df_summary = df_report.groupby(["Departman", "Üretim Tipi"]).agg({
            "Üretilen Adet": "sum",
            "Toplam Kazanç": "sum"
        }).reset_index()

        st.dataframe(df_summary, use_container_width=True, hide_index=True)

        # 2. Tüm Detaylı Liste
        st.subheader("📄 Detaylı İşlem Kayıtları")

        # Görünümü güzelleştirmek için sütunları yeniden sıralayalım
        display_df = df_report[[
            "Tarih", "Departman", "Model", "Üretim Tipi",
            "Üretilen Adet", "Birim Fiyat", "Döviz", "Toplam Kazanç"
        ]]

        st.dataframe(
            display_df.style.highlight_max(axis=0, subset=["Toplam Kazanç"], color='#e6fffa'),
            use_container_width=True,
            hide_index=True
        )

        # İndirme Butonu
        csv = df_report.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Raporu Excel (CSV) Olarak İndir", csv, "finansal_uretim_raporu.csv", "text/csv")

    else:
        st.warning("Belirtilen kriterlerde veri bulunamadı.")