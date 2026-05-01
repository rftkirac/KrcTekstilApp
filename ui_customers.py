import streamlit as st
from database import run_query, execute_db, get_next_number
from datetime import datetime


# Silme onay diyaloğu
@st.dialog("⚠️ Firmayı Sil")
def confirm_delete_customer(customer_id, customer_name):
    st.write(f"**{customer_name}** isimli firmayı silmek istediğinize emin misiniz?")
    st.error("Bu işlem geri alınamaz!")

    col1, col2 = st.columns(2)
    if col1.button("Evet, Sil", type="primary", use_container_width=True):
        check_models = run_query("SELECT id FROM Model WHERE companyId = ?", (int(customer_id),))
        if not check_models.empty:
            st.error("Bu firmaya ait modeller var. Önce modelleri silmelisiniz!")
        else:
            execute_db("DELETE FROM Customer WHERE id=?", (int(customer_id),))
            st.success("Firma başarıyla silindi.")
            st.rerun()

    if col2.button("İptal", use_container_width=True):
        st.rerun()


def show_customer_page(current_user):
    st.header("🏢 Firma ve Cari Yönetimi")

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

    # --- YÖNETİM SEKMESİ ---
    with tab_manage:
        mode = st.radio("İşlem Tipi", ["Yeni Firma Ekle", "Düzenle / Sil"], horizontal=True)
        st.divider()

        if mode == "Düzenle / Sil":
            df_all = run_query("SELECT * FROM Customer")
            if df_all.empty:
                st.warning("Düzenlenecek Firma kaydı bulunamadı.")
            else:
                # KRİTİK: Selectbox form dışında olmalı
                sel_id = st.selectbox(
                    "Düzenlenecek Firma Seçin",
                    df_all['id'].tolist(),
                    format_func=lambda
                        x: f"{df_all[df_all['id'] == x]['code'].values[0]} - {df_all[df_all['id'] == x]['name'].values[0]}",
                    key="customer_edit_selector"
                )

                # Seçilen firmanın bilgilerini alıyoruz
                row = df_all[df_all['id'] == sel_id].iloc[0]

                # --- GÜNCELLEME FORMU ---
                # Formun ID'sini dinamik yaparak (key) her seçimde yenilenmesini sağlayabilirsin
                with st.form(key=f"edit_form_{sel_id}"):
                    st.info(f"Düzenlenen: {row['code']}")
                    c_name = st.text_input("Firma / Ünvan", value=row['name'])
                    c_contact = st.text_input("İlgili Kişi (Yetkili)", value=row['contactName'])

                    col1, col2 = st.columns(2)
                    c_phone = col1.text_input("Telefon", value=row['phone'])
                    c_mail = col2.text_input("E-Posta", value=row['mail'])

                    c_address = st.text_area("Adres", value=row['address'])

                    if st.form_submit_button("✅ Bilgileri Güncelle", use_container_width=True):
                        execute_db("""UPDATE Customer SET name=?, contactName=?, phone=?, mail=?, address=? 
                                      WHERE id=?""",
                                   (c_name, c_contact, c_phone, c_mail, c_address, int(sel_id)))
                        st.success("Firma bilgileri güncellendi.")
                        st.rerun()

                # --- SİLME BUTONU (FORM DIŞINDA) ---
                st.write("---")
                if st.button("🗑️ Firmayı Sistemden Sil", use_container_width=True, type="secondary"):
                    confirm_delete_customer(sel_id, row['name'])

        else:  # Yeni Kayıt Modu
            with st.form("customer_add_form", clear_on_submit=True):
                res_sayac = run_query("SELECT prefix, last_number FROM sayac WHERE code = 'FIRMA'")
                next_code = f"{res_sayac['prefix'][0]}{res_sayac['last_number'][0] + 1}"
                st.info(f"Oluşturulacak Firma Kodu: **{next_code}**")

                n_name = st.text_input("Firma / Şirket Ünvanı")
                n_contact = st.text_input("İlgili Kişi (Yetkili)")
                col1, col2 = st.columns(2)
                n_phone = col1.text_input("Telefon")
                n_mail = col2.text_input("E-Posta")
                n_address = st.text_area("Adres")

                if st.form_submit_button("➕ Firmayı Kaydet", use_container_width=True):
                    if n_name:
                        final_code = get_next_number('FIRMA')
                        execute_db("""INSERT INTO Customer (code, name, contactName, phone, mail, address) 
                                      VALUES (?,?,?,?,?,?)""",
                                   (final_code, n_name, n_contact, n_phone, n_mail, n_address))
                        st.success(f"Firma {final_code} başarıyla oluşturuldu!")
                        st.rerun()
                    else:
                        st.error("Firma ünvanı boş bırakılamaz!")