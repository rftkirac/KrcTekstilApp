import streamlit as st
from database import run_query
import pandas as pd


def show_advanced_report_page():
    st.header("📊 Detaylı Üretim Analizi")

    # --- SESSION STATE FİLTRE YÖNETİMİ ---
    if 'filter_customer' not in st.session_state: st.session_state.filter_customer = "Tümü"
    if 'filter_model' not in st.session_state: st.session_state.filter_model = "Tümü"
    if 'filter_dept' not in st.session_state: st.session_state.filter_dept = "Tümü"
    if 'filter_date' not in st.session_state:
        st.session_state.filter_date = [pd.to_datetime("today").replace(day=1), pd.to_datetime("today")]

    def reset_filters():
        st.session_state.filter_customer = "Tümü"
        st.session_state.filter_model = "Tümü"
        st.session_state.filter_dept = "Tümü"
        st.session_state.filter_date = [pd.to_datetime("today").replace(day=1), pd.to_datetime("today")]

    # --- FİLTRELEME ALANI (ÜST TARAF) ---
    with st.container():
        # İlk satır filtreleri
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.write("**Tarih Aralığı**")
            d_range = st.date_input("Aralık Seçin", value=st.session_state.filter_date, key="filter_date",
                                    label_visibility="collapsed")

        with row1_col2:
            st.write("**Firma / Firma**")
            customers = run_query("SELECT id, name FROM Customer")
            customer_list = ["Tümü"] + list(customers['name'])
            selected_cust = st.selectbox("Firma Seçin", customer_list, key="filter_customer",
                                         label_visibility="collapsed")

        # İkinci satır filtreleri
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.write("**Model (Firmaya Özel)**")
            if selected_cust != "Tümü":
                c_id_res = customers[customers['name'] == selected_cust]
                c_id = c_id_res['id'].values[0] if not c_id_res.empty else 0
                models_df = run_query("SELECT code FROM Model WHERE companyId = ?", (int(c_id),))
            else:
                models_df = run_query("SELECT code FROM Model")

            model_list = ["Tümü"] + list(models_df['code'])
            selected_model = st.selectbox("Model Seçin", model_list, key="filter_model", label_visibility="collapsed")

        with row2_col2:
            st.write("**Departman**")
            depts = run_query("SELECT name FROM Departmans")
            dept_list = ["Tümü"] + list(depts['name'])
            selected_dept = st.selectbox("Departman Seçin", dept_list, key="filter_dept", label_visibility="collapsed")

        # Butonlar
        btn_col1, btn_col2 = st.columns([4, 1])
        with btn_col1:
            list_btn = st.button("🔍 Verileri Listele", use_container_width=True, type="primary")
        with btn_col2:
            st.button("Sweep Temizle", use_container_width=True, on_click=reset_filters)

    # --- LİSTELEME MANTIĞI ---
    if list_btn:
        query = """
            SELECT 
                p.date as [Tarih],
                c.name as [Firma],
                m.code as [Model_Code],
                 m.name as [Model],
                d.name as [Departman],
                p.quantity as [Adet]
            FROM Production p
            JOIN Model m ON p.modelId = m.id
            JOIN Customer c ON m.companyId = c.id
            JOIN Departmans d ON p.departmentId = d.id
            WHERE p.date BETWEEN ? AND ?
        """

        start_d = d_range[0] if len(d_range) > 0 else pd.to_datetime("today")
        end_d = d_range[1] if len(d_range) > 1 else start_d
        params = [str(start_d), str(end_d)]

        if selected_cust != "Tümü":
            query += " AND c.name = ?"
            params.append(selected_cust)

        if selected_model != "Tümü":
            query += " AND m.code = ?"
            params.append(selected_model)

        if selected_dept != "Tümü":
            query += " AND d.name = ?"
            params.append(selected_dept)

        query += " ORDER BY p.date DESC"
        df_result = run_query(query, params)

        if df_result.empty:
            st.warning("Seçilen kriterlere uygun kayıt bulunamadı.")
        else:
            st.divider()

            # 1. Özet Metrikler
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Üretim", f"{df_result['Adet'].sum():,}")
            m2.metric("Kayıt Sayısı", len(df_result))
            m3.metric("Ortalama/Kayıt", f"{int(df_result['Adet'].mean())}")

            # 2. Veri Tablosu
            st.subheader("📋 Sonuç Listesi")
            st.dataframe(df_result, use_container_width=True, hide_index=True,
                         column_config={
                             "id": None,  # 👈 Bu satır ID kolonunu tamamen gizler
                         },
                         )

            st.divider()

            # 3. Grafikler (Sayfanın Sonunda)
            st.subheader("📈 Görsel Analiz")
            g_col1, g_col2 = st.columns(2)

            with g_col1:
                st.write("**Departman Dağılımı**")
                dept_sum = df_result.groupby('Departman')['Adet'].sum()
                st.bar_chart(dept_sum)

            with g_col2:
                st.write("**Model Dağılımı**")
                model_sum = df_result.groupby('Model')['Adet'].sum()
                st.area_chart(model_sum)