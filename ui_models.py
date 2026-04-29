import streamlit as st
from database import run_query, execute_db, get_next_number
from datetime import datetime
import time


# --- YARDIMCI FONKSİYON: SİLME ONAY PENCERESİ ---
@st.dialog("⚠️ Kaydı Sil")
def confirm_delete_model(model_id, model_code):
    st.warning(f"**{model_code}** kodlu modeli silmek istediğinize emin misiniz?")
    st.write("Bu işlem geri alınamaz ve modele bağlı tüm üretim kayıtları etkilenebilir.")

    col1, col2 = st.columns(2)
    if col1.button("❌ Vazgeç", use_container_width=True):
        st.rerun()

    if col2.button("🗑️ Evet, Sil", type="primary", use_container_width=True):
        execute_db("DELETE FROM Model WHERE id=?", (int(model_id),))
        st.toast(f"{model_code} başarıyla silindi.", icon="🗑️")
        time.sleep(1)
        st.rerun()


def show_model_page(current_user):
    st.header("👕 Model ve Sipariş Yönetimi")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().date()

    # --- VERİLERİ ÇEK ---
    df_customers = run_query("SELECT id, name FROM Customer")
    df_types = run_query("SELECT value FROM parameter WHERE groupCode = 'MODEL_TYPE'")
    currencies = ["TRY", "USD", "EUR", "GBP"]

    tab_list, tab_manage = st.tabs(["📋 Model Listesi", "🔧 Yeni Kayıt / Düzenle"])

    # --- LİSTELEME SEKMESİ ---
    with tab_list:
        st.subheader("🔍 Filtreleme")

        # Filtreleri yan yana koyuyoruz
        f_col1, f_col2 = st.columns(2)

        with f_col1:
            f_cust = st.selectbox("Firmaya Göre Filtrele", ["Tümü"] + list(df_customers['name']), key="f_mod_cust")

        with f_col2:
            # Durum Filtresi: Hepsi, Aktif, Kapalı
            f_status = st.selectbox("Model Durumu", ["Hepsi", "Sadece Aktifler", "Sadece Kapalılar"], index=1)

        query = """
            SELECT m.id, 
            c.name as [Firma], 
            m.code as [Kod], 
            m.type as [Tip], 
            m.name as [Model Adı], 
            m.siparisAdet as [Adet], 
            m.birimFiyat, 
            m.dövizKodu,
            m.siparisTarihi as [Sipariş Tar.], 
            m.aktif as [Durum]
            FROM Model m
            JOIN Customer c ON m.companyId = c.id
            WHERE 1=1
        """
        params = []

        # Firma Filtresi Mantığı
        if f_cust != "Tümü":
            query += " AND c.name = ?"
            params.append(f_cust)

        # Durum Filtresi Mantığı
        if f_status == "Sadece Aktifler":
            query += " AND m.aktif = 1"
        elif f_status == "Sadece Kapalılar":
            query += " AND m.aktif = 0"

        df_res = run_query(query + " ORDER BY m.id DESC", params)

        if not df_res.empty:
            st.write("---")
            h1, h2, h3, h4, h5 = st.columns([1, 2, 2, 1.5, 1])
            h1.write("**Kod**")
            h2.write("**Firma / Model**")
            h3.write("**Sipariş Detay**")
            h4.write("**Durum**")
            h5.write("**İşlem**")
            st.write("---")

            for _, row in df_res.iterrows():
                with st.container():
                    c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 1.5, 1])
                    c1.write(f"**{row['Kod']}**")
                    c2.write(f"{row['Firma']}")
                    c2.caption(f"{row['Tip']} - {row['Model Adı']}")
                    c3.write(f"{row['Adet']} Adet")
                    c3.caption(f"{row['birimFiyat']} {row['dövizKodu']}")

                    # Görsel Durum Belirteci
                    durum_icon = "✅ Aktif" if row['Durum'] else "❌ Kapalı"
                    c4.write(durum_icon)
                    c4.caption(row['Sipariş Tar.'])

                    if c5.button("🔍", key=f"detay_{row['id']}", help="Model Detaylarını Gör"):
                        st.session_state.selected_model_id = row['id']
                        st.rerun()
                st.write("---")
        else:
            st.info("Seçilen filtrelere uygun model bulunamadı.")

    # --- YÖNETİM SEKMESİ ---
    with tab_manage:
        mode = st.radio("İşlem", ["Yeni Model Ekle", "Düzenle / Sil"], horizontal=True)
        st.divider()

        if df_customers.empty:
            st.error("Önce Firma tanımlamalısınız!")
            return

        if mode == "Düzenle / Sil":
            sel_cust_name = st.selectbox("Firma Filtresi", list(df_customers['name']), key="edit_cust_sel")

            sel_cust_id = int(df_customers[df_customers['name'] == sel_cust_name]['id'].values[0])
            # 1. Önce firmaya ait modelleri çekiyoruz
            df_all = run_query("SELECT * FROM Model WHERE companyId = ?", (sel_cust_id,))

            if df_all.empty:
                st.warning("Bu firmaya ait model bulunamadı.")
            else:
                # 2. Model seçme kutusu (Form dışında olması daha stabil çalışmasını sağlar)
                # format_func ile sadece kod ve isim görünecek
                sel_id = st.selectbox(
                    "Düzenlenecek Model Seçin",
                    df_all['id'].tolist(),
                    format_func=lambda
                        x: f"{df_all[df_all['id'] == x]['code'].values[0]} - {df_all[df_all['id'] == x]['name'].values[0]}",
                    key="model_selector_edit"
                )

                # 3. Seçilen modelin verilerini değişkene atıyoruz
                row = df_all[df_all['id'] == sel_id].iloc[0]

                # 4. Formu oluşturuyoruz
                # Formun her model değişiminde "sıfırlanması" için clear_on_submit=False kalmalı
                with st.form("edit_form_dynamic"):
                    st.info(f"Düzenlenen Model: {row['code']}")

                    m_name = st.text_input("Model Adı", value=row['name'])

                    c1, c2, c3 = st.columns(3)
                    # Seçilen satırdaki değerleri doğrudan value kısmına yazıyoruz
                    m_adet = c1.number_input("Sipariş Adeti", value=int(row['siparisAdet']))
                    m_price = c2.number_input("Birim Fiyat", value=float(row['birimFiyat']))

                    # Döviz indeksi hesabı
                    current_curr = row['dövizKodu']
                    curr_index = currencies.index(current_curr) if current_curr in currencies else 0
                    m_curr = c3.selectbox("Döviz", currencies, index=curr_index)

                    d1, d2, d3 = st.columns(3)
                    # Tarihleri string'den date objesine çeviriyoruz
                    m_s_date = d1.date_input("Sipariş Tarihi",
                                             value=datetime.strptime(row['siparisTarihi'], '%Y-%m-%d'))
                    m_b_date = d2.date_input("Başlama Tarihi",
                                             value=datetime.strptime(row['baslamaTarihi'], '%Y-%m-%d') if row[
                                                 'baslamaTarihi'] else today)
                    m_aktif = d3.checkbox("Aktif Model", value=bool(row['aktif']))

                    st.write("---")
                    b1, b2 = st.columns(2)

                    if b1.form_submit_button("✅ Değişiklikleri Kaydet", use_container_width=True):
                        execute_db("""UPDATE Model SET name=?, siparisAdet=?, birimFiyat=?, 
                                      dövizKodu=?, siparisTarihi=?, baslamaTarihi=?, aktif=?, updateUser=?, updateTime=? WHERE id=?""",
                                   (m_name, m_adet, m_price, m_curr, str(m_s_date), str(m_b_date), int(m_aktif),
                                    current_user, now, int(sel_id)))
                        st.success("Güncellendi!")
                        time.sleep(0.5)
                        st.rerun()

                    if b2.form_submit_button("🗑️ Modeli Sil", use_container_width=True):
                        # Silme onay penceresini tetikle
                        confirm_delete_model(sel_id, row['code'])
        else:  # YENİ KAYIT MODU
            with st.form("new_model_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                n_cust_name = col_a.selectbox("Firma / Şirket", list(df_customers['name']))
                n_cust_id = int(df_customers[df_customers['name'] == n_cust_name]['id'].values[0])
                n_type = col_b.selectbox("Model Tipi", list(df_types['value']) if not df_types.empty else ["Diğer"])

                res_sayac = run_query("SELECT prefix, last_number FROM sayac WHERE code = 'MODEL'")
                next_code_p = f"{res_sayac['prefix'][0]}{res_sayac['last_number'][0] + 1}" if not res_sayac.empty else "MOD-1"
                st.info(f"Oluşturulacak Model Kodu: **{next_code_p}**")

                m_name = st.text_input("Model Adı")
                c1, c2, c3 = st.columns(3)
                m_adet = c1.number_input("Sipariş Adeti", min_value=0)
                m_price = c2.number_input("Birim Fiyat", min_value=0.0, format="%.2f")
                m_curr = c3.selectbox("Döviz", currencies, index=0)

                d1, d2 = st.columns(2)
                m_s_date = d1.date_input("Sipariş Tarihi", value=today)
                m_b_date = d2.date_input("Planlanan Başlama", value=today)
                m_aktif = st.checkbox("Aktif Olarak Başlat", value=True)

                if st.form_submit_button("➕ Modeli ve Siparişi Kaydet", use_container_width=True):
                    if m_name:
                        final_code = get_next_number('MODEL')
                        execute_db("""INSERT INTO Model (companyId, code, type, name, siparisAdet, birimFiyat, dövizKodu, 
                                      siparisTarihi, baslamaTarihi, aktif, createUser, createTime) 
                                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                                   (n_cust_id, final_code, n_type, m_name, m_adet, m_price, m_curr, str(m_s_date),
                                    str(m_b_date), int(m_aktif), current_user, now))
                        st.balloons()
                        st.toast(f"{final_code} başarıyla oluşturuldu!", icon="🚀")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Model adı boş bırakılamaz!")