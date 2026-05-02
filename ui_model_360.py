import streamlit as st
from database import run_query


def show_model_360_view():
    model_id = st.session_state.selected_model_id

    if st.button("⬅️ Listeye Dön"):
        st.session_state.selected_model_id = None
        st.rerun()

    # --- MODEL ANA BİLGİLERİ ---
    model_info = run_query("""
        SELECT m.*, c.name as customer_name 
        FROM Model m 
        JOIN Customer c ON m.companyId = c.id 
        WHERE m.id = ?""", (model_id,))

    if model_info.empty:
        st.error("Model bulunamadı!")
        return

    m = model_info.iloc[0]
    st.title(f"📦 Model Özeti: {m['code']}")

    # Üst Bilgi Kartları
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Müşteri", m['customer_name'])
    c2.metric("Sipariş Adedi", f"{m['siparisAdet']:,}")
    c3.metric("Birim Fiyat", f"{m['birimFiyat']} {m['dövizKodu']}")
    c4.metric("Durum", "Aktif" if m['aktif'] else "Kapalı")

    st.divider()

    # --- TABLI GÖRÜNÜM ---
    tab_plan, tab_closing, tab_logs = st.tabs(["📊 Üretim Planı", "🏁 Kapama / Sevkiyat", "📝 İşlem Günlüğü"])

    with tab_plan:
        st.subheader("Günlük Girilen Detaylar (ModelDetay)")
        df_detay = run_query("SELECT renk, beden, adet, createTime FROM ModelDetay WHERE modelId = ?", (model_id,))
        if not df_detay.empty:
            st.dataframe(df_detay, use_container_width=True,
                         column_config={
                             "id": None,  # 👈 Bu satır ID kolonunu tamamen gizler
                         },
                         )
            st.info(f"Toplam Üretilen: {df_detay['adet'].sum()} / Kalan: {m['siparisAdet'] - df_detay['adet'].sum()}")
        else:
            st.warning("Henüz üretim detayı girilmemiş.")

    with tab_closing:
        st.subheader("Kapama ve Yükleme Bilgileri")
        df_kapama = run_query(
            "SELECT yuklemeTarihi, kapamaTarihi, renk, beden, adet, ikinciKaliteAdet FROM modele_kapama WHERE modelId = ?",
            (model_id,))
        if not df_kapama.empty:
            st.table(df_kapama)
        else:
            st.info("Bu model henüz kapatılmamış (Yükleme yapılmamış).")

    with tab_logs:
        st.subheader("Sistem Bilgileri")

        # 1. Departman Listesini Hazırla
        df_depts = run_query("SELECT name FROM Departmans")
        dept_list = ["Tümü"] + list(df_depts['name']) if not df_depts.empty else ["Tümü"]

        # 2. Filtre Alanı (Sadece Selectbox)
        # key ekleyerek seçimin session boyunca korunmasını sağlıyoruz
        sel_log_dept = st.selectbox("Departman Filtresi", dept_list, index=0, key="log_dept_filter_view")

        # 3. Sorguyu Hazırla
        log_query = """
               SELECT m.code as ModelKodu, m.name as ModelAdi,
                p.date as Tarih, d.name as Departman, p.quantity as Adet, p.createUser as [Giren]
               FROM Production p
               JOIN Model m ON p.modelId = m.id
               JOIN Departmans d ON p.departmentId = d.id
               WHERE p.modelId = ?
        """
        log_params = [model_id]

        # Eğer "Tümü" dışında bir şey seçildiyse sorguya ekle
        if sel_log_dept != "Tümü":
            log_query += " AND d.name = ?"
            log_params.append(sel_log_dept)

        log_query += " ORDER BY p.date DESC, p.id DESC"

        # 4. Verileri Çek ve Tabloyu Bas
        df_log = run_query(log_query, tuple(log_params))

        if not df_log.empty:
            st.table(df_log)
        else:
            st.info(f"'{sel_log_dept}' departmanına ait henüz bir işlem kaydı bulunamadı.")