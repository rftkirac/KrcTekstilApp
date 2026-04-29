import streamlit as st
from database import run_query, execute_db
from datetime import datetime


def show_accessory_page(current_user):
    st.header("🎀 Model Aksesuar Yönetimi")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    models = run_query("SELECT id, (code || ' - ' || name) as display FROM Model")
    # Parametre tablosundan aksesuar türlerini getir
    types = run_query("SELECT value FROM parameter WHERE groupCode = 'AKS_TYPE'")

    tab_list, tab_manage = st.tabs(["📋 Aksesuar Listesi", "🛠️ Ekle / Güncelle / Sil"])

    with tab_manage:
        if models.empty:
            st.error("Önce model tanımlamalısınız!")
            return

        mode = st.radio("İşlem Tipi", ["Yeni Aksesuar", "Güncelle / Sil"], horizontal=True)

        # Mevcut aksesuarları çek (Güncelleme modu için)
        all_acc = run_query("""
            SELECT a.*, (m.code || ' - ' || m.name) as model_display 
            FROM aksesuar a 
            JOIN Model m ON a.modelId = m.id
        """)

        with st.form("acc_form", clear_on_submit=True):
            if mode == "Güncelle / Sil" and not all_acc.empty:
                sel_acc_id = st.selectbox("Düzenlenecek Aksesuar", all_acc['id'],
                                          format_func=lambda
                                              x: f"ID: {x} - {all_acc[all_acc['id'] == x]['name'].values[0]}")
                row = all_acc[all_acc['id'] == sel_acc_id].iloc[0]

                m_id = st.selectbox("Model", models['id'], index=list(models['id']).index(row['modelId']),
                                    format_func=lambda x: models[models['id'] == x]['display'].values[0])
                acc_name = st.text_input("Aksesuar Adı", value=row['name'])
                acc_type = st.selectbox("Tür", types['value'],
                                        index=list(types['value']).index(row['type']) if row['type'] in list(
                                            types['value']) else 0)
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
                acc_type = st.selectbox("Tür", types['value'] if not types.empty else ["Tanımsız"])
                qty = st.number_input("Adet", min_value=0.0)
                unit = st.selectbox("Birim", ["Adet", "Metre", "Kg", "Set"])
                price = st.number_input("Birim Fiyat", min_value=0.0)
                currency = st.selectbox("Döviz", ["TRY", "USD", "EUR", "GBP"])

                if st.form_submit_button("Aksesuar Ekle"):
                    execute_db("""INSERT INTO aksesuar (modelId, name, type, adet, birim, birimFiyat, dövizKodu, creataUser, CreateTime) 
                                  VALUES (?,?,?,?,?,?,?,?,?)""",
                               (int(m_id), acc_name, acc_type, qty, unit, price, currency, current_user, now))
                    st.rerun()

    with tab_list:
        st.dataframe(all_acc, use_container_width=True)