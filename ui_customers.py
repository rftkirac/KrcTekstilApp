import streamlit as st
import pandas as pd
from database import run_query, execute_db, get_next_number
from datetime import datetime
import time

# Silme onay diyaloğu
@st.dialog("⚠️ Firmayı Sil")
def confirm_delete_customer(customer_id, customer_name):
    st.write(f"**{customer_name}** isimli firmayı silmek istediğinize emin misiniz?")
    st.error("Bu işlem geri alınamaz!")

    col1, col2 = st.columns(2)
    if col1.button("Evet, Sil", type="primary", use_container_width=True):
        # Bağımlılık kontrolü
        check_models = run_query("SELECT id FROM Model WHERE companyId = ?", (int(customer_id),))
        if not check_models.empty:
            st.error("Bu firmaya ait modeller var. Önce modelleri silmelisiniz!")
        else:
            execute_db("DELETE FROM Customer WHERE id=?", (int(customer_id),))
            st.success("Firma başarıyla silindi.")
            st.balloons();
            st.toast(f"İşlem başarıyla silindi!", icon="🚀")
            time.sleep(1);
            st.rerun()

    if col2.button("İptal", use_container_width=True):
        st.rerun()


def show_customer_page(current_user):
    st.header("🏢 Firma ve Cari Yönetimi")

    tab_list, tab_manage = st.tabs(["📋 Firma Listesi", "🔧 Yeni Kayıt / Düzenle"])

    # --- 1. SEKME: LİSTELEME (OTOMATİK GELİR) ---
    with tab_list:
        st.subheader("🔍 Firma Arama")
        search_term = st.text_input("Firma Adı veya Kodu ile Filtrele", placeholder="Yazmaya başlayın...")

        # Sorgu her zaman çalışır (Buton gerektirmez)
        query = "SELECT code as [Kod], name as [Firma Adı], contactName as [Yetkili], phone as [Telefon], mail as [E-Posta] FROM Customer"
        params = []
        if search_term:
            query += " WHERE name LIKE ? OR code LIKE ?"
            params = [f"%{search_term}%", f"%{search_term}%"]

        df_res = run_query(query + " ORDER BY id DESC", params)

        if not df_res.empty:
            st.caption(f"Toplam {len(df_res)} kayıt bulundu.")
            st.dataframe(df_res, use_container_width=True, hide_index=True,
                         column_config={
                             "id": None,  # 👈 Bu satır ID kolonunu tamamen gizler
                         },
                         )
        else:
            st.info("Kayıtlı firma bulunamadı.")

    # --- 2. SEKME: YÖNETİM (YENİ / DÜZENLE) ---
    with tab_manage:
        mode = st.radio("İşlem Tipi", ["Yeni Firma Ekle", "Düzenle / Sil"], horizontal=True)
        st.divider()

        if mode == "Düzenle / Sil":
            df_all = run_query("SELECT * FROM Customer")
            if df_all.empty:
                st.warning("Düzenlenecek firma kaydı bulunamadı.")
            else:
                # SEÇİM KUTUSU (FORM DIŞINDA): Seçildiği an bilgileri aşağıya doldurur
                sel_id = st.selectbox(
                    "Düzenlenecek Firmayı Seçin",
                    df_all['id'].tolist(),
                    format_func=lambda
                        x: f"{df_all[df_all['id'] == x]['code'].values[0]} - {df_all[df_all['id'] == x]['name'].values[0]}",
                    key="customer_edit_selector"
                )

                # Seçilen firmanın bilgilerini alıyoruz
                row = df_all[df_all['id'] == sel_id].iloc[0]

                # GÜNCELLEME FORMU
                with st.form(key=f"edit_form_{sel_id}"):
                    st.info(f"Düzenlenen Firma Kodu: **{row['code']}**")
                    c_name = st.text_input("Firma / Ünvan", value=str(row['name']))
                    c_contact = st.text_input("İlgili Kişi (Yetkili)", value=str(row['contactName']))

                    col1, col2 = st.columns(2)
                    c_phone = col1.text_input("Telefon", value=str(row['phone']))
                    c_mail = col2.text_input("E-Posta", value=str(row['mail']))

                    c_address = st.text_area("Adres", value=str(row['address']))

                    if st.form_submit_button("✅ Değişiklikleri Kaydet", use_container_width=True):
                        execute_db("""UPDATE Customer SET name=?, contactName=?, phone=?, mail=?, address=? 
                                      WHERE id=?""",
                                   (c_name, c_contact, c_phone, c_mail, c_address, int(sel_id)))
                        st.success("Bilgiler güncellendi!")
                        st.balloons();
                        st.toast(f"İşlem başarıyla güncellendi!", icon="🚀")
                        time.sleep(1);
                        st.rerun()

                # SİLME İŞLEMİ
                st.write("---")
                if st.button("🗑️ Firmayı Sistemden Tamamen Sil", use_container_width=True, type="secondary"):
                    confirm_delete_customer(sel_id, row['name'])

        else:  # YENİ KAYIT MODU
            with st.form("customer_add_form", clear_on_submit=True):
                # Gelecek kodu göster
                try:
                    res_sayac = run_query("SELECT prefix, last_number FROM sayac WHERE code = 'FIRMA'")
                    next_code = f"{res_sayac['prefix'][0]}{res_sayac['last_number'][0] + 1}"
                    st.info(f"Yeni Oluşturulacak Firma Kodu: **{next_code}**")
                except:
                    st.warning("Sayaç bilgisi alınamadı.")

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
                        st.success(f"{final_code} koduyla yeni firma kaydedildi!")
                        st.balloons();
                        st.toast(f"İşlem başarıyla oluşturuldu!", icon="🚀")
                        time.sleep(1);
                        st.rerun()
                    else:
                        st.error("Firma ünvanı girmek zorunludur!")