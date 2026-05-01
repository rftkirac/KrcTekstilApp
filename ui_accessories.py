import streamlit as st
import pandas as pd
from database import run_query, execute_db
from datetime import datetime


def show_accessory_page(current_user):
    st.header("🎀 Model Aksesuar Yönetimi")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- VERİ ÇEKME ---
    models = run_query("SELECT id, (code || ' - ' || name) as display, companyId FROM Model")
    customers = run_query("SELECT id, name FROM Customer")
    types = run_query("SELECT value FROM parameter WHERE groupCode = 'AKS_TYPE'")

    tab_list, tab_manage = st.tabs(["📋 Aksesuar Listesi", "🛠️ Ekle / Güncelle / Sil"])

    with tab_list:
        st.subheader("🔍 Filtreleme")
        f1, f2 = st.columns(2)

        # 1. Firma Filtresi
        customer_options = ["Tümü"] + customers["name"].tolist()
        selected_customer = f1.selectbox("Firma Filtresi", customer_options)

        # 2. Model Filtresi (Firmaya Bağımlı)
        if selected_customer != "Tümü":
            # Seçilen firmanın ID'sini al
            cust_id = customers[customers["name"] == selected_customer]["id"].iloc[0]
            # Sadece o firmaya ait modelleri filtrele
            filtered_models = models[models["companyId"] == cust_id]
            model_options = ["Tümü"] + filtered_models["display"].tolist()
        else:
            model_options = ["Tümü"] + models["display"].tolist()

        selected_model_display = f2.selectbox("Model Filtresi", model_options)

        # --- SQL SORGUSU (Filtrelere Göre) ---
        query = """
            SELECT 
                a.id as [ID],
                c.name as [Firma],
                m.code as [Model Kodu],
                m.name as [Model Adı],
                a.name as [Aksesuar],
                a.type as [Tür],
                a.adet as [Adet],
                a.birim as [Birim],
                a.birimFiyat as [Birim Fiyat],
                a.dövizKodu as [Döviz],
                (a.adet * a.birimFiyat) as [Toplam Maliyet]
            FROM aksesuar a 
            JOIN Model m ON a.modelId = m.id
            JOIN Customer c ON m.companyId = c.id
            WHERE 1=1
        """
        params = []

        if selected_customer != "Tümü":
            query += " AND c.name = ?"
            params.append(selected_customer)

        if selected_model_display != "Tümü":
            # Display formatından (Kod - İsim) kodu ayıklayalım
            m_code = selected_model_display.split(" - ")[0]
            query += " AND m.code = ?"
            params.append(m_code)

        df_acc_filtered = run_query(query, tuple(params))

        if not df_acc_filtered.empty:
            st.dataframe(
                df_acc_filtered,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Birim Fiyat": st.column_config.NumberColumn(
                        "Birim Fiyat",
                        format="%.2f",  # 2 ondalık basamak
                    ),
                    "Toplam Maliyet": st.column_config.NumberColumn(
                        "Toplam Maliyet",
                        format="%,.2f",  # Binlik ayraçsız veya "%.2f" şeklinde
                    )
                }
            )
            #st.dataframe(df_acc_filtered, use_container_width=True, hide_index=True)

            # Alt Toplam Bilgisi
            total_cost = df_acc_filtered["Toplam Maliyet"].sum()
            st.info(
                f"Filtrelenen Aksesuarların Toplam Maliyeti: **{total_cost:,.2f}** (Döviz kırılımı dikkate alınmamıştır)")
        else:
            st.warning("Aradığınız kriterlere uygun aksesuar kaydı bulunamadı.")

    with tab_manage:
        if models.empty:
            st.error("Önce model tanımlamalısınız!")
            return

        mode = st.radio("İşlem Tipi", ["Yeni Aksesuar", "Güncelle / Sil"], horizontal=True)

        # Tüm aksesuarları güncelleme listesi için çek (JOIN'li hali)
        all_acc = run_query("""
            SELECT a.*, (m.code || ' - ' || m.name) as model_display 
            FROM aksesuar a 
            JOIN Model m ON a.modelId = m.id
            ORDER BY a.id DESC
        """)

        with st.form("acc_form", clear_on_submit=True):
            if mode == "Güncelle / Sil" and not all_acc.empty:
                # Selectbox'ta gösterimi iyileştirelim
                acc_options = all_acc.apply(lambda x: f"{x['model_display']} | {x['name']}", axis=1).tolist()
                sel_acc_label = st.selectbox("Düzenlenecek Aksesuar", acc_options)

                # Seçilen etiketten gerçek ID'yi bulalım
                sel_acc_id = all_acc.iloc[acc_options.index(sel_acc_label)]['id']
                row = all_acc[all_acc['id'] == sel_acc_id].iloc[0]

                m_id = st.selectbox("Model", models['id'], index=list(models['id']).index(row['modelId']),
                                    format_func=lambda x: models[models['id'] == x]['display'].values[0])
                acc_name = st.text_input("Aksesuar Adı", value=row['name'])
                acc_type = st.selectbox("Tür", types['value'].tolist() if not types.empty else ["Tanımsız"],
                                        index=list(types['value']).index(row['type']) if not types.empty and row[
                                            'type'] in list(types['value']) else 0)
                qty = st.number_input("Adet", value=float(row['adet']))
                unit = st.selectbox("Birim", ["Adet", "Metre", "Kg", "Set"],
                                    index=["Adet", "Metre", "Kg", "Set"].index(row['birim']))
                price = st.number_input("Birim Fiyat", value=float(row['birimFiyat']))
                currency = st.selectbox("Döviz", ["TRY", "USD", "EUR", "GBP"],
                                        index=["TRY", "USD", "EUR", "GBP"].index(row['dövizKodu']))

                c1, c2 = st.columns(2)
                if c1.form_submit_button("Değişiklikleri Kaydet"):
                    execute_db("""UPDATE aksesuar SET modelId=?, name=?, type=?, adet=?, birim=?, birimFiyat=?, 
                                  dövizKodu=?, updateUser=?, updateTime=? WHERE id=?""",
                               (int(m_id), acc_name, acc_type, qty, unit, price, currency, current_user, now,
                                int(sel_acc_id)))
                    st.rerun()
                if c2.form_submit_button("Aksesuarı Sil"):
                    execute_db("DELETE FROM aksesuar WHERE id=?", (int(sel_acc_id),))
                    st.rerun()
            else:
                m_id = st.selectbox("Model", models['id'],
                                    format_func=lambda x: models[models['id'] == x]['display'].values[0])
                acc_name = st.text_input("Aksesuar Adı")
                acc_type = st.selectbox("Tür", types['value'].tolist() if not types.empty else ["Tanımsız"])
                qty = st.number_input("Adet", min_value=0.0)
                unit = st.selectbox("Birim", ["Adet", "Metre", "Kg", "Set"])
                price = st.number_input("Birim Fiyat", min_value=0.0)
                currency = st.selectbox("Döviz", ["TRY", "USD", "EUR", "GBP"])

                if st.form_submit_button("Aksesuar Ekle"):
                    execute_db("""INSERT INTO aksesuar (modelId, name, type, adet, birim, birimFiyat, dövizKodu, creataUser, CreateTime) 
                                  VALUES (?,?,?,?,?,?,?,?,?)""",
                               (int(m_id), acc_name, acc_type, qty, unit, price, currency, current_user, now))
                    st.rerun()