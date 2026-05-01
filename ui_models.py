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


# --- YENİ YARDIMCI FONKSİYON: SÜREÇ SİLME ---
def delete_process(process_id):
    execute_db("DELETE FROM modelProcess WHERE id=?", (int(process_id),))
    st.toast("Süreç silindi.", icon="🗑️")
    time.sleep(0.5)
    st.rerun()


def show_model_page(current_user):
    st.header("👕 Model ve Sipariş Yönetimi")

    # --- CSS: SATIR RENKLENDİRME ---
    st.markdown("""
        <style>
        .custom-row {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border: 1px solid #eee;
        }
        .odd-row {
            background-color: #f8f9fa; /* Çok açık gri */
        }
        .even-row {
            background-color: #ffffff; /* Beyaz */
        }
        /* Yazıların hizalanması için */
        .stMarkdown p { margin-bottom: 0px !important; }
        </style>
    """, unsafe_allow_html=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().date()

    # --- VERİLERİ ÇEK ---
    df_customers = run_query("SELECT id, name FROM Customer")
    df_types = run_query("SELECT value FROM parameter WHERE groupCode = 'MODEL_TYPE'")
    df_depts = run_query("SELECT id, name FROM Departmans")
    currencies = ["TRY", "USD", "EUR", "GBP"]

    tab_list, tab_manage = st.tabs(["📋 Model Listesi", "🔧 Yeni Kayıt / Düzenle"])

    # --- LİSTELEME SEKMESİ ---
    with tab_list:
        st.subheader("🔍 Filtreleme")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            f_cust = st.selectbox("Firmaya Göre Filtrele", ["Tümü"] + list(df_customers['name']), key="f_mod_cust")
        with f_col2:
            f_status = st.selectbox("Model Durumu", ["Hepsi", "Sadece Aktifler", "Sadece Kapalılar"], index=1)

        query = """
            SELECT m.id, 
            c.name as [Firma], 
            m.code as [Kod], 
            m.name as [Model Adı], 
            m.type as [Tip], 
            m.siparisAdet as [Adet], 
            m.birimFiyat as [Birim Fiyat], 
            m.birimFiyat * m.siparisAdet as [Toplam Getirisi],
            m.dövizKodu, 
            m.siparisTarihi as [Sipariş Tar.], 
            m.aktif as [Durum]
            FROM Model m
            JOIN Customer c ON m.companyId = c.id
            WHERE 1=1
        """
        params = []
        if f_cust != "Tümü":
            query += " AND c.name = ?"
            params.append(f_cust)
        if f_status == "Sadece Aktifler":
            query += " AND m.aktif = 1"
        elif f_status == "Sadece Kapalılar":
            query += " AND m.aktif = 0"

        df_res = run_query(query + " ORDER BY m.id DESC", params)

        if not df_res.empty:
            #st.write("---")
            tab_list1, tab_list2 = st.tabs(["📋 Liste", "👕 Detay Liste"])
            with tab_list1:
                st.dataframe(
                    df_res,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Birim Fiyat": st.column_config.NumberColumn(
                            "Birim Fiyat",
                            format="%.2f",  # 2 ondalık basamak
                        ),
                        "Toplam Getirisi": st.column_config.NumberColumn(
                            "Toplam Maliyet",
                            format="%,.2f",  # Binlik ayraçsız veya "%.2f" şeklinde
                        )
                    }
                )

            with tab_list2:
                h = st.columns([1, 1, 1, 1, 1, 1, 2, 1, 1, 1])
                cols = ["**Kod**", "**Firma**", "**Model**", "**Tipi**", "**Adet**", "**Birim**", "**Toplam**", "**Durum**",
                        "**Tarih**", "**İşlem**"]
                for col, text in zip(h, cols): col.write(text)
                #st.write("---")

                # SATIR DÖNGÜSÜ
                for i, (idx, row) in enumerate(df_res.iterrows()):
                    # i % 2 kullanarak tek/çift tespiti yapıyoruz
                    row_style = "odd-row" if i % 2 != 0 else "even-row"

                    # HTML div başlangıcı
                    st.markdown(f'<div class="custom-row {row_style}">', unsafe_allow_html=True)

                    birimFiyatFormat = format_tl(row['Birim Fiyat'], row['dövizKodu'])
                    toplamFiyat = format_tl(row['Toplam Getirisi'], row['dövizKodu'])

                    c1, c2, c3, c4, c5, c6, c7, c8, c9, c10 = st.columns([1, 1, 1, 1, 1, 1, 2, 1, 1, 1])
                    c1.write(f"**{row['Kod']}**")
                    c2.write(f"{row['Firma']}")
                    c3.write(f"{row['Model Adı']}")
                    c4.write(f"{row['Tip']}")
                    c5.write(f"{row['Adet']}")
                    c6.write(f"{birimFiyatFormat}")
                    c7.write(f"{toplamFiyat}")
                    durum_icon = "✅ Aktif" if row['Durum'] else "❌ Kapalı"
                    c8.write(durum_icon)
                    c9.write(row['Sipariş Tar.'])

                    if c10.button("🔍", key=f"detay_{row['id']}", help="Model Detaylarını Gör"):
                        st.session_state.selected_model_id = row['id']
                        st.rerun()

                    # HTML div bitişi
                    st.markdown('</div>', unsafe_allow_html=True)

                    with st.expander(f"➕ {row['Kod']} İşlem Fiyat Çizelgesi"):
                        df_proc = run_query("""
                            SELECT mp.id, d.name as Departman, mp.birimFiyat, mp.dovizKodu,
                                   CASE WHEN mp.is_internal = 1 THEN 'İç Üretim' ELSE 'Fason' END as Tip
                            FROM modelProcess mp
                            JOIN Departmans d ON mp.departmanId = d.id
                            WHERE mp.modelId = ?
                        """, (int(row['id']),))

                        if not df_proc.empty:
                            p_h = st.columns([2, 1, 1, 1, 0.5])
                            p_cols = ["**İşlem / Departman**", "**Birim Fiyat**", "**Tip**", "**Döviz**", ""]
                            for p_col, p_text in zip(p_h, p_cols): p_col.write(p_text)
                            for _, p_row in df_proc.iterrows():
                                p_c1, p_c2, p_c3, p_c4, p_c5 = st.columns([2, 1, 1, 1, 0.5])
                                p_c1.write(p_row['Departman'])
                                p_c2.write(f"{p_row['birimFiyat']:,.2f}")
                                p_c3.write(p_row['Tip'])
                                p_c4.write(p_row['dovizKodu'])
                        else:
                            st.info("Süreç tanımlanmamış.")
                    #st.write("---")
                else:
                    st.info("Seçilen filtrelere uygun model bulunamadı.")
            # Alt Toplam Bilgisi
            total_cost = df_res["Toplam Getirisi"].sum()
            st.info(
                    f"Filtrelenen Modellerin Toplam Getiri: **{total_cost:,.2f}** (Döviz kırılımı dikkate alınmamıştır)")

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
            df_all = run_query("SELECT * FROM Model WHERE companyId = ?", (sel_cust_id,))

            if df_all.empty:
                st.warning("Bu firmaya ait model bulunamadı.")
            else:
                sel_id = st.selectbox(
                    "Düzenlenecek Model Seçin",
                    df_all['id'].tolist(),
                    format_func=lambda
                        x: f"{df_all[df_all['id'] == x]['code'].values[0]} - {df_all[df_all['id'] == x]['name'].values[0]}",
                    key="model_selector_edit"
                )
                row = df_all[df_all['id'] == sel_id].iloc[0]

                with st.form("edit_form_dynamic"):
                    st.info(f"Düzenlenen Model: {row['code']}")
                    m_name = st.text_input("Model Adı", value=row['name'])
                    c1, c2, c3 = st.columns(3)
                    m_adet = c1.number_input("Sipariş Adeti", value=int(row['siparisAdet']))
                    m_price = c2.number_input("Birim Fiyat", value=float(row['birimFiyat']))
                    current_curr = row['dövizKodu']
                    curr_index = currencies.index(current_curr) if current_curr in currencies else 0
                    m_curr = c3.selectbox("Döviz", currencies, index=curr_index)
                    d1, d2, d3 = st.columns(3)
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
                        confirm_delete_model(sel_id, row['code'])

                st.write("---")
                st.subheader(f"⚙️ {row['code']} - Üretim Süreçleri ve Maliyet")
                df_proc = run_query("""
                    SELECT mp.id, d.name as Departman, mp.birimFiyat, mp.dovizKodu,
                           CASE WHEN mp.is_internal = 1 THEN 'İç Üretim' ELSE 'Fason' END as Tip
                    FROM modelProcess mp
                    JOIN Departmans d ON mp.departmanId = d.id
                    WHERE mp.modelId = ?
                """, (int(sel_id),))

                if not df_proc.empty:
                    p_h1, p_h2, p_h3, p_h4, p_h5 = st.columns([2, 1, 1, 1, 0.5])
                    p_h1.write("**İşlem / Departman**")
                    p_h2.write("**Birim Fiyat**")
                    p_h3.write("**Tip**")
                    p_h4.write("**Döviz**")
                    for _, p_row in df_proc.iterrows():
                        p_c1, p_c2, p_c3, p_c4, p_c5 = st.columns([2, 1, 1, 1, 0.5])
                        p_c1.write(p_row['Departman'])
                        p_c2.write(f"{p_row['birimFiyat']:,.2f}")
                        p_c3.write(p_row['Tip'])
                        p_c4.write(p_row['dovizKodu'])
                        if p_c5.button("🗑️", key=f"del_proc_{p_row['id']}"):
                            delete_process(p_row['id'])
                else:
                    st.info("Süreç tanımlanmamış.")

                with st.expander("➕ Yeni İşlem/Süreç Tanımla"):
                    with st.form("add_process_form"):
                        col_p1, col_p2 = st.columns(2)
                        if not df_depts.empty:
                            p_dept_name = col_p1.selectbox("Departman", df_depts['name'])
                            p_dept_id = int(df_depts[df_depts['name'] == p_dept_name]['id'].values[0])
                        else:
                            st.warning("Tanımlı departman bulunamadı.")
                        p_type = col_p2.radio("Üretim Tipi", ["İç Üretim", "Fason"], horizontal=True)
                        p_is_internal = 1 if p_type == "İç Üretim" else 0
                        p_col1, p_col2 = st.columns(2)
                        p_birim = p_col1.number_input("İşlem Birim Fiyatı", min_value=0.0, format="%.2f")
                        p_curr = p_col2.selectbox("Döviz", currencies, key="proc_curr")
                        if st.form_submit_button("Süreci Modele Kaydet", use_container_width=True):
                            check_exists = run_query("SELECT id FROM modelProcess WHERE modelId=? AND departmanId=?",
                                                     (int(sel_id), p_dept_id))
                            if not check_exists.empty:
                                st.error(f"Bu modelde {p_dept_name} zaten tanımlı!")
                            else:
                                execute_db("""INSERT INTO modelProcess (companyId, modelId, departmanId, birimFiyat, dovizKodu, is_internal, createUser, createTime)
                                              VALUES (?,?,?,?,?,?,?,?)""",
                                           (sel_cust_id, int(sel_id), p_dept_id, p_birim, p_curr, p_is_internal,
                                            current_user, now))
                                st.success("Süreç eklendi.")
                                time.sleep(0.5)
                                st.rerun()

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
                        st.balloons();
                        st.toast(f"{final_code} başarıyla oluşturuldu!", icon="🚀")
                        time.sleep(1);
                        st.rerun()
                    else:
                        st.error("Model adı boş bırakılamaz!")


def format_tl(value, doviz):
    formatted = "{:,.2f}".format(value)
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".") + " " + doviz