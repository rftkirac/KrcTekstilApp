import streamlit as st
from database import run_query, execute_db, get_next_number
from datetime import datetime


def show_customer_page(current_user):
    st.header("🏢 Firma ve Cari Yönetimi")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tab_list, tab_manage = st.tabs(["📋 Firma Listesi", "🔧 Yeni Kayıt / Düzenle"])

    # --- LİSTELEME SEKMESİ ---
    with tab_list:
        st.subheader("🔍 Arama")
        search_term = st.text_input("Firma Adı veya Kodu ile Ara")

        if st.button("🔍 Firmaları Listele", type="primary", use_container_width=True):
            query = "SELECT code as [Kod], name as [Firma Adı], contactName as [Yetkili], phone as [Telefon], mail as [E-Posta] FROM Customer"
            params = []

            if search_term:
                query += " WHERE name LIKE ? OR code LIKE ?"
                params = [f"%{search_term}%", f"%{search_term}%"]

            df_res = run_query(query + " ORDER BY id DESC", params)

            if not df_res.empty:
                st.dataframe(df_res, use_container_width=True, hide_index=True)
            else:
                st.info("Kayıtlı Firma bulunamadı.")

    # --- YÖNETİM SEKMESİ (EKLE/SİL/GÜNCELLE) ---
    with tab_manage:
        mode = st.radio("İşlem Tipi", ["Yeni Firma Ekle", "Düzenle / Sil"], horizontal=True)
        st.divider()

        with st.form("customer_form", clear_on_submit=True):
            if mode == "Düzenle / Sil":
                # Düzenleme için Firmaları çek
                df_all = run_query("SELECT * FROM Customer")
                if df_all.empty:
                    st.warning("Düzenlenecek Firma kaydı bulunamadı.")
                    st.form_submit_button("Kapat", disabled=True)
                else:
                    sel_id = st.selectbox(
                        "Düzenlenecek Firma",
                        df_all['id'],
                        format_func=lambda
                            x: f"{df_all[df_all['id'] == x]['code'].values[0]} - {df_all[df_all['id'] == x]['name'].values[0]}"
                    )
                    row = df_all[df_all['id'] == sel_id].iloc[0]

                    c_name = st.text_input("Firma / Ünvan", value=row['name'])
                    c_contact = st.text_input("İlgili Kişi (Yetkili)", value=row['contactName'])

                    col1, col2 = st.columns(2)
                    c_phone = col1.text_input("Telefon", value=row['phone'])
                    c_mail = col2.text_input("E-Posta", value=row['mail'])

                    c_address = st.text_area("Adres", value=row['address'])

                    btn_c1, btn_c2 = st.columns(2)
                    if btn_c1.form_submit_button("✅ Bilgileri Güncelle"):
                        execute_db("""UPDATE Customer SET name=?, contactName=?, phone=?, mail=?, address=? 
                                      WHERE id=?""",
                                   (c_name, c_contact, c_phone, c_mail, c_address, int(sel_id)))
                        st.success("Firma bilgileri güncellendi.")
                        st.rerun()

                    if btn_c2.form_submit_button("🗑️ Firmayı Sil"):
                        # Firmaye ait model var mı kontrolü (Opsiyonel Güvenlik)
                        check_models = run_query("SELECT id FROM Model WHERE companyId = ?", (int(sel_id),))
                        if not check_models.empty:
                            st.error("Bu Firmaye ait modeller var. Önce modelleri silmelisiniz!")
                        else:
                            execute_db("DELETE FROM Customer WHERE id=?", (int(sel_id),))
                            st.warning("Firma sistemden silindi.")
                            st.rerun()

            else:  # Yeni Kayıt Modu
                # Otomatik Kod Önizleme
                res_sayac = run_query("SELECT prefix, last_number FROM sayac WHERE code = 'FIRMA'")
                next_code = f"{res_sayac['prefix'][0]}{res_sayac['last_number'][0] + 1}"

                st.info(f"Oluşturulacak Firma Kodu: **{next_code}**")

                n_name = st.text_input("Firma / Şirket Ünvanı")
                n_contact = st.text_input("İlgili Kişi (Yetkili)")

                col1, col2 = st.columns(2)
                n_phone = col1.text_input("Telefon")
                n_mail = col2.text_input("E-Posta")

                n_address = st.text_area("Adres")

                if st.form_submit_button("➕ Firmayı Kaydet"):
                    if n_name:
                        final_code = get_next_number('FIRMA')
                        execute_db("""INSERT INTO Customer (code, name, contactName, phone, mail, address) 
                                      VALUES (?,?,?,?,?,?)""",
                                   (final_code, n_name, n_contact, n_phone, n_mail, n_address))
                        st.success(f"Firma {final_code} başarıyla oluşturuldu!")
                        st.rerun()
                    else:
                        st.error("Firma ünvanı boş bırakılamaz!")