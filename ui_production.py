import streamlit as st
from database import run_query, execute_db
from datetime import datetime
import time

def show_production_page(current_user):
    st.header("🚀 Günlük Üretim Takibi")

    now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().date()

    # --- 1. FİLTRELEME VE MODEL SEÇİMİ ---
    with st.container(border=True):
        col_f1, col_f2 = st.columns(2)

        # Firmaları çek
        df_customers = run_query("SELECT id, name FROM Customer")
        if df_customers.empty:
            st.error("Önce Firma tanımlamalısınız!")
            return

        df_depart = run_query("SELECT id,name FROM Departmans order by name")

        d_id = col_f1.selectbox("Departman Seçin", df_depart['id'],
                                      format_func=lambda
                                          x: f"{df_depart[df_depart['id'] == x]['name'].values[0]}")

        sel_cust_name = col_f1.selectbox("Firma Seçin", df_customers['name'])
        sel_cust_id = int(df_customers[df_customers['name'] == sel_cust_name]['id'].values[0])

        # Seçili firmaya ait modelleri çek
        df_models = run_query("SELECT id, code, name, siparisAdet FROM Model WHERE companyId = ?", (sel_cust_id,))


        if df_models.empty:
            st.warning("Bu firmaya ait tanımlı model bulunamadı.")
            return

        sel_model_id = col_f1.selectbox("Model Seçin", df_models['id'],
                                        format_func=lambda
                                            x: f"{df_models[df_models['id'] == x]['code'].values[0]} - {df_models[df_models['id'] == x]['name'].values[0]}")



        # Seçili modelin detaylarını tek satırda göster
        m_info = df_models[df_models['id'] == sel_model_id].iloc[0]

        # Üretim toplamını hesapla (Kalanı görmek için)
        df_prod_sum = run_query("SELECT SUM(quantity) as toplam FROM Production WHERE modelId = ?",
                                (int(sel_model_id),))
        toplam_uretim = df_prod_sum['toplam'][0] if df_prod_sum['toplam'][0] else 0
        kalan = m_info['siparisAdet'] - toplam_uretim

        st.divider()
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        m_c1.metric("Model Kodu", m_info['code'])
        m_c2.metric("Sipariş Adedi", f"{m_info['siparisAdet']:,}")
        m_c3.metric("Toplam Üretilen", f"{toplam_uretim:,}")
        m_c4.metric("Kalan", f"{kalan:,}", delta_color="inverse")

    # --- 2. VERİ GİRİŞİ ---
    st.subheader("📥 Günlük Üretim Girişi")
    depts = run_query("SELECT id, name FROM Departmans")

    with st.form("daily_prod_form", clear_on_submit=True):
        if depts.empty:
            st.error("Lütfen önce Departman tanımlamalarını yapın!")
            st.form_submit_button("Kaydet", disabled=True)
        else:
            col1, col2,  = st.columns([1, 1])
            with col1:
                qty = st.number_input("Üretilen Adet", min_value=1, step=1)
            with col2:
                p_date = st.date_input("İşlem Tarihi", value=today)

            if st.form_submit_button("✅ Üretim Kaydını İşle", use_container_width=True):
                execute_db("""INSERT INTO Production (modelId, departmentId, date, quantity, createTime, createUser) 
                              VALUES (?,?,?,?,?,?)""",
                           (int(sel_model_id), int(d_id), str(p_date), qty, now_ts, current_user))
                st.success(f"Kayıt Eklendi: {qty} adet")
                st.balloons();
                st.toast(f"İşlem başarıyla oluşturuldu!", icon="🚀")
                time.sleep(1);
                st.rerun()

    # --- 3. LİSTELEME VE DÜZENLEME ---
    st.subheader(f"📝 ({m_info['code']} - {m_info['name']}) Modeline Ait Kayıtlar")

    # Sadece seçili modele ait raporu çek
    raw_report = run_query("""
        SELECT 
            p.id,  
            p.date as Tarih, 
            d.name as Departman, 
            p.quantity as Adet, 
            p.createUser as [Giren]
        FROM Production p
        JOIN Departmans d ON p.departmentId = d.id
        WHERE p.modelId = ? and p.departmentId = ?
        ORDER BY p.date DESC, p.id DESC
    """, (int(sel_model_id),int(d_id),))

    gosterilecek_kolonlar = ["ModelAdi", "Tarih", "Departman", "Adet", "Giren"]

    if not raw_report.empty:
        st.dataframe(raw_report, use_container_width=True, hide_index=True,
                     column_config={
                         "id": None,  # 👈 Bu satır ID kolonunu tamamen gizler
                     },
                     )
        #st.dataframe(raw_report[gosterilecek_kolonlar], use_container_width=True, hide_index=True)

        st.divider()
        with st.expander("🛠️ Seçili Kaydı Düzenle veya Sil"):
            sel_edit_id = st.selectbox("İşlem yapılacak Kayıt ID (Tablodan bakınız)", raw_report['id'])

            # Seçili kaydın mevcut adedini getir
            current_qty = int(raw_report[raw_report['id'] == sel_edit_id]['Adet'].values[0])

            e_c1, e_c2 = st.columns(2)
            with e_c1:
                new_qty = st.number_input("Adedi Güncelle", min_value=1, value=current_qty)
                if st.button("🔢 Adedi Güncelle", use_container_width=True):
                    execute_db("UPDATE Production SET quantity=? WHERE id=?", (new_qty, int(sel_edit_id)))
                    st.toast(f"ID {sel_edit_id} güncellendi.")
                    st.balloons();
                    st.toast(f"İşlem başarıyla oluşturuldu!", icon="🚀")
                    time.sleep(1);
                    st.rerun()

            with e_c2:
                if st.button("🗑️ Kaydı Tamamen Sil", use_container_width=True, type="secondary"):
                    execute_db("DELETE FROM Production WHERE id=?", (int(sel_edit_id),))
                    st.warning("Kayıt veritabanından silindi.")
                    st.balloons();
                    st.toast(f"İşlem başarıyla silindi!", icon="🚀")
                    time.sleep(1);
                    st.rerun()
    else:
        st.info("Bu model için henüz bir üretim girişi yapılmamış.")