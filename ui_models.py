import streamlit as st
from database import run_query, execute_db, get_next_number
from datetime import datetime
import time


# --- YARDIMCI FONKSİYONLAR ---
def format_tl(value, doviz):
    """Para birimini formatlar."""
    try:
        return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".") + " " + doviz
    except:
        return f"{value} {doviz}"


@st.dialog("⚠️ Kaydı Sil")
def confirm_delete_model(model_id, model_code):
    st.warning(f"**{model_code}** kodlu modeli silmek istediğinize emin misiniz?")
    st.write("Bu işlem geri alınamaz ve modele bağlı tüm üretim/varyant kayıtları silinecektir.")
    col1, col2 = st.columns(2)
    if col1.button("❌ Vazgeç", use_container_width=True): st.rerun()
    if col2.button("🗑️ Evet, Sil", type="primary", use_container_width=True):
        execute_db("DELETE FROM Model WHERE id=?", (int(model_id),))
        execute_db("DELETE FROM modelProcess WHERE modelId=?", (int(model_id),))
        execute_db("DELETE FROM ModelDetay WHERE modelId=?", (int(model_id),))
        st.toast(f"{model_code} ve bağlı tüm veriler silindi.")
        time.sleep(1)
        st.rerun()


def show_model_page(current_user):
    st.header("👕 Model Tasarım ve Sipariş Yönetimi")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    currencies = ["TRY", "USD", "EUR", "GBP"]

    # Verileri Çek
    df_customers = run_query("SELECT id, name FROM Customer")
    df_depts = run_query("SELECT id, name FROM Departmans")
    df_colors = run_query("SELECT value FROM parameter WHERE groupCode = 'RENK'")
    df_sizes = run_query("SELECT value FROM parameter WHERE groupCode = 'BEDEN'")
    df_types = run_query("SELECT value FROM parameter WHERE groupCode = 'MODEL_TYPE'")

    tab_list, tab_manage = st.tabs(["📋 Model Listesi", "🔧 Yeni Kayıt ve Düzenleme"])

    # --- 1. LİSTELEME SEKMESİ ---
    with tab_list:
        st.subheader("🔍 Filtreleme")
        f_col1, f_col2 = st.columns(2)
        f_cust = f_col1.selectbox("Firma Filtresi", ["Tümü"] + list(df_customers['name']), key="list_f_cust")
        f_status = f_col2.selectbox("Durum", ["Hepsi", "Aktifler", "Kapalılar"], index=1)

        query = """
            SELECT 
            m.id, c.name as [Firma], 
            m.code as [Kod], 
            m.name as [Model Adı], 
            m.type as Tip ,
            m.siparisTarihi as [Sipariş Tar.],
            m.birimFiyat as [Birim Fiyat], 
            m.siparisAdet as [Adet], 
            (m.siparisAdet * m.birimFiyat) as [Toplam Getiri], 
            m.dövizKodu, m.description as [Açıklama], 
            m.aktif as [Durum]
            FROM Model m JOIN Customer c ON m.companyId = c.id WHERE 1=1
        """
        params = []
        if f_cust != "Tümü":
            query += " AND c.name = ?";
            params.append(f_cust)
        if f_status == "Aktifler":
            query += " AND m.aktif = 1"
        elif f_status == "Kapalılar":
            query += " AND m.aktif = 0"

        df_res = run_query(query + " ORDER BY m.id DESC", params)

        if not df_res.empty:
            tab_list1, tab_list2 = st.tabs(["📋 Liste", "📝 Detay Liste"])
            with tab_list1:
                # 1. Veriyi kopyala ve 1/0 değerlerini değiştir
                df_display = df_res.copy()

                # "Durum" kolonundaki 1'leri "✅ Aktif", 0'ları "❌ Kapalı" yap
                df_display["Durum"] = df_display["Durum"].map({1: "✅ Aktif", 0: "❌ Kapalı"})

                # 2. Tabloyu ekrana bas
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": None,  # 👈 Bu satır ID kolonunu tamamen gizler
                        "Birim Fiyat": st.column_config.NumberColumn("Birim Fiyat", format="%.2f"),
                        "Toplam Getiri": st.column_config.NumberColumn("Toplam Getiri", format="%,.2f"),
                        "Durum": st.column_config.TextColumn(
                            "Durum",
                            help="Modelin güncel üretim durumu"
                        )
                    }
                )
            with tab_list2:
                # Başlıklar
                h = st.columns([1, 1.5, 1.5, 1, 1, 1.5, 2, 1, 1, 1])
                cols = ["**Kod**", "**Firma**", "**Model**", "**Tip**", "**Adet**", "**Birim Fiyat**", "**Toplam**",
                        "**Durum**",
                        "**Tarih**", "**İşlem**"]
                for col, text in zip(h, cols): col.write(text)
                for i, (idx, row) in enumerate(df_res.iterrows()):
                    c1, c2, c3, c4, c5, c6, c7, c8, c9, c10 = st.columns([1, 1.5, 1.5, 1, 1, 1.5, 2, 1, 1, 1])
                    c1.write(f"**{row['Kod']}**")
                    c2.write(row['Firma'])
                    c3.write(row['Model Adı'])
                    c4.write(row['Tip'])
                    c5.write(str(row['Adet']))
                    c6.write(format_tl(row['Birim Fiyat'], row['dövizKodu']))
                    c7.write(format_tl(row['Toplam Getiri'], row['dövizKodu']))
                    c8.write("✅" if row['Durum'] else "❌")
                    c9.write(row['Sipariş Tar.'])

                    if c10.button("🔍", key=f"detay_{row['id']}"):
                        st.session_state.selected_model_id = row['id']
                        st.toast("Model detayına yönlendiriliyor...")

                    st.markdown('</div>', unsafe_allow_html=True)

                total_val = df_res["Toplam Getiri"].sum()
                st.info(f"Filtrelenen Modellerin Toplam Brüt Getirisi: **{total_val:,.2f}**")



        else:
            st.info("Kayıt bulunamadı.")

    # --- 2. YÖNETİM SEKMESİ (EKLE / DÜZENLE) ---
    with tab_manage:
        mode = st.radio("İşlem Tipi", ["Yeni Model Ekle", "Düzenle / Detay Yönetimi"], horizontal=True)
        st.divider()

        if mode == "Yeni Model Ekle":
            if df_customers.empty:
                st.error("Lütfen önce Firma tanımlayın.");
                return

            with st.form("new_model_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                n_cust = c1.selectbox("Firma", df_customers['name'])
                n_type = c2.selectbox("Model Tipi", df_types['value'] if not df_types.empty else ["Standart"])

                m_name = st.text_input("Model İsmi")
                m_desc = st.text_area("Model Açıklaması / Özel Notlar", help="Kumaş bilgisi, aksesuar detayları vb.")

                c3, c4, c5 = st.columns(3)
                m_adet = c3.number_input("Sipariş Adeti", min_value=1)
                m_price = c4.number_input("Satış Birim Fiyatı", min_value=0.0)
                m_curr = c5.selectbox("Döviz", currencies)

                if st.form_submit_button("➕ Modeli Kaydet", use_container_width=True):
                    if m_name:
                        cid = int(df_customers[df_customers['name'] == n_cust]['id'].values[0])
                        new_code = get_next_number('MODEL')
                        execute_db("""INSERT INTO Model (companyId, code, type, name, description, siparisAdet, birimFiyat, dövizKodu, aktif, createUser, createTime) 
                                      VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                                   (cid, new_code, n_type, m_name, m_desc, m_adet, m_price, m_curr, 1, current_user,
                                    now))
                        st.success(f"{new_code} başarıyla oluşturuldu!");
                        time.sleep(1);
                        st.rerun()
                    else:
                        st.error("Model ismi boş olamaz.")

        else:  # DÜZENLEME VE DETAY YÖNETİMİ
            sel_cust = st.selectbox("Firma Seç", df_customers['name'], key="edit_sel_cust")
            cid = int(df_customers[df_customers['name'] == sel_cust]['id'].values[0])
            df_models = run_query("SELECT * FROM Model WHERE companyId = ?", (cid,))

            if df_models.empty:
                st.warning("Bu firmaya ait model bulunamadı.")
            else:
                sel_m_id = st.selectbox("Model Seçin", df_models['id'].tolist(),
                                        format_func=lambda
                                            x: f"{df_models[df_models['id'] == x]['code'].values[0]} - {df_models[df_models['id'] == x]['name'].values[0]}")
                row = df_models[df_models['id'] == sel_m_id].iloc[0]

                # --- BÖLÜM 1: ANA BİLGİ GÜNCELLEME ---
                with st.expander("📝 Model Ana Bilgileri ve Notları Düzenle", expanded=True):
                    with st.form("edit_base_form"):
                        u_name = st.text_input("Model Adı", value=row['name'])
                        # description sütunu veritabanında yoksa boş string döner
                        u_desc = st.text_area("Açıklama / Notlar",
                                              value=row['description'] if 'description' in row and row[
                                                  'description'] else "")

                        col1, col2, col3 = st.columns(3)
                        u_adet = col1.number_input("Adet", value=int(row['siparisAdet']))
                        u_price = col2.number_input("Birim Fiyat", value=float(row['birimFiyat']))
                        u_aktif = col3.checkbox("Model Aktif", value=bool(row['aktif']))

                        if st.form_submit_button("✅ Değişiklikleri Kaydet", use_container_width=True):
                            execute_db(
                                "UPDATE Model SET name=?, description=?, siparisAdet=?, birimFiyat=?, aktif=? WHERE id=?",
                                (u_name, u_desc, u_adet, u_price, int(u_aktif), row['id']))
                            st.success("Bilgiler güncellendi!");
                            time.sleep(0.5);
                            st.rerun()

                # --- BÖLÜM 2: SÜREÇ VE MALİYET ---
                st.subheader("⚙️ Üretim Süreçleri ve Maliyet")
                df_proc = run_query("""
                    SELECT mp.id, d.name as Departman, mp.birimFiyat, mp.dovizKodu, mp.is_internal
                    FROM modelProcess mp JOIN Departmans d ON mp.departmanId = d.id WHERE mp.modelId = ?
                """, (int(sel_m_id),))

                if not df_proc.empty:
                    for _, p in df_proc.iterrows():
                        c_p = st.columns([3, 2, 2, 1])
                        c_p[0].write(f"🔹 {p['Departman']}")
                        c_p[1].write(format_tl(p['birimFiyat'], p['dovizKodu']))
                        c_p[2].write("İç Üretim" if p['is_internal'] else "Fason")
                        if c_p[3].button("🗑️", key=f"del_p_{p['id']}"):
                            execute_db("DELETE FROM modelProcess WHERE id=?", (p['id'],))
                            st.rerun()

                with st.expander("➕ Yeni Süreç Ekle"):
                    with st.form("add_p_form"):
                        p_dept = st.selectbox("Departman", df_depts['name'])
                        p_prc = st.number_input("İşlem Maliyeti", min_value=0.0)
                        p_int = st.radio("Tip", ["İç Üretim", "Fason"], horizontal=True)
                        if st.form_submit_button("Süreci Kaydet"):
                            did = int(df_depts[df_depts['name'] == p_dept]['id'].values[0])
                            execute_db(
                                "INSERT INTO modelProcess (companyId, modelId, departmanId, birimFiyat, dovizKodu, is_internal) VALUES (?,?,?,?,?,?)",
                                (cid, int(sel_m_id), did, p_prc, row['dövizKodu'], 1 if p_int == "İç Üretim" else 0))
                            st.rerun()

                # --- BÖLÜM 3: RENK VE BEDEN DAĞILIMI ---
                st.subheader("🎨 Renk ve Beden Dağılımı")
                df_detay = run_query("SELECT id, renk, beden, adet FROM ModelDetay WHERE modelId = ?", (int(sel_m_id),))

                if not df_detay.empty:
                    st.dataframe(df_detay[['renk', 'beden', 'adet']], use_container_width=True, hide_index=True)
                    st.info(f"Varyant Toplamı: **{df_detay['adet'].sum():,}** / Sipariş: **{row['siparisAdet']:,}**")

                    d_sel = st.selectbox("Silinecek Varyant", df_detay['id'].tolist(),
                                         format_func=lambda
                                             x: f"{df_detay[df_detay['id'] == x]['renk'].values[0]} - {df_detay[df_detay['id'] == x]['beden'].values[0]}")
                    if st.button("❌ Seçili Varyantı Sil"):
                        execute_db("DELETE FROM ModelDetay WHERE id=?", (int(d_sel),))
                        st.rerun()

                with st.expander("➕ Yeni Renk/Beden Ekle"):
                    with st.form("add_v_form"):
                        v_c1, v_c2, v_c3 = st.columns(3)
                        v_r = v_c1.selectbox("Renk", df_colors['value'] if not df_colors.empty else ["-"])
                        v_b = v_c2.selectbox("Beden", df_sizes['value'] if not df_sizes.empty else ["-"])
                        v_a = v_c3.number_input("Adet", min_value=1)
                        if st.form_submit_button("Varyantı Kaydet"):
                            execute_db(
                                "INSERT INTO ModelDetay (companyId, modelId, renk, beden, adet) VALUES (?,?,?,?,?)",
                                (cid, int(sel_m_id), v_r, v_b, v_a))
                            st.rerun()

                st.divider()
                if st.button("🗑️ TÜM MODELİ SİL", use_container_width=True, type="secondary"):
                    confirm_delete_model(sel_m_id, row['code'])