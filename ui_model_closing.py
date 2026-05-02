import streamlit as st
from database import run_query, execute_db
from datetime import datetime
import time

def show_model_closing_page(current_user):
    st.header("🏁 Model Kapama ve Yükleme İşlemleri")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().date()

    # --- VERİ HAZIRLIĞI ---
    df_customers = run_query("SELECT id, name FROM Customer")
    # Filtreler ve Seçimler için "Seçilmedi" opsiyonu ekliyoruz
    df_colors = ["Belirtilmedi"] + list(run_query("SELECT value FROM parameter WHERE groupCode = 'RENK'")['value'])
    df_sizes = ["Belirtilmedi"] + list(run_query("SELECT value FROM parameter WHERE groupCode = 'BEDEN'")['value'])

    tab_list, tab_manage = st.tabs(["📋 Kapama Listesi", "🔧 Yeni Kapama / Düzenle"])

    # --- LİSTELEME SEKMESİ ---
    with tab_list:
        st.subheader("🔍 Filtrele ve Sorgula")
        c1, c2, c3 = st.columns(3)

        f_cust = c1.selectbox("Firma", ["Tümü"] + list(df_customers['name']), key="cls_f_cust")

        if f_cust != "Tümü":
            df_f_models = run_query(
                "SELECT id, code FROM Model WHERE companyId = (SELECT id FROM Customer WHERE name = ?)", (f_cust,))
            f_model = c2.selectbox("Model", ["Tümü"] + list(df_f_models['code']), key="cls_f_mod")
        else:
            f_model = c2.selectbox("Model", ["Tümü"], disabled=True)


        if st.button("🔍 Kayıtları Listele", use_container_width=True, type="primary"):
            query = """
                SELECT mk.id, c.name as [Firma], m.code as [Model], 
                       mk.renk as [Renk], mk.beden as [Beden], 
                       mk.adet as [Yüklenen], mk.ikinciKaliteAdet as [2. Kalite],
                       mk.yuklemeTarihi as [Yükleme Tar.], mk.kapamaTarihi as [Kapama Tar.]
                FROM modele_kapama mk
                JOIN Customer c ON mk.companyId = c.id
                JOIN Model m ON mk.modelId = m.id
                WHERE 1=1
            """
            params = []
            if f_cust != "Tümü":
                query += " AND c.name = ?";
                params.append(f_cust)
            if f_model != "Tümü" and f_cust != "Tümü":
                query += " AND m.code = ?";
                params.append(f_model)

            df_res = run_query(query + " ORDER BY mk.id DESC", params)

            if not df_res.empty:
                st.divider()
                st.dataframe(df_res, use_container_width=True, hide_index=True,
                             column_config={
                                 "id": None,  # 👈 Bu satır ID kolonunu tamamen gizler
                             },
                             )
            else:
                st.info("Kayıt bulunamadı.")

    # --- YÖNETİM SEKMESİ ---
    with tab_manage:
        mode = st.radio("İşlem", ["Yeni Kapama Ekle", "Güncelle / Sil"], horizontal=True)
        st.divider()

        with st.form("closing_form", clear_on_submit=True):
            if df_customers.empty:
                st.error("Firma bulunamadı.")
                return

            sel_cust_name = st.selectbox("Firma", list(df_customers['name']))
            sel_cust_id = int(df_customers[df_customers['name'] == sel_cust_name]['id'].values[0])

            df_models = run_query("SELECT id, code, name FROM Model WHERE companyId = ?", (sel_cust_id,))
            model_map = {f"{r['code']} - {r['name']}": r['id'] for _, r in df_models.iterrows()}

            if mode == "Güncelle / Sil":
                raw_data = run_query("SELECT id, renk, beden, adet, ikinciKaliteAdet FROM modele_kapama")
                if raw_data.empty:
                    st.warning("Düzenlenecek kayıt yok.")
                    st.form_submit_button("Formu Kapat", disabled=True)
                else:
                    sel_id = st.selectbox("Düzenlenecek Kayıt ID", raw_data['id'])
                    curr = raw_data[raw_data['id'] == sel_id].iloc[0]

                    u_model = st.selectbox("Model", list(model_map.keys()))
                    u_y_date = st.date_input("Yükleme Tarihi")
                    u_k_date = st.date_input("Kapama Tarihi")

                    col1, col2 = st.columns(2)
                    # Mevcut değer listede yoksa (eskiden zorunlu değilse) default Belirtilmedi gelsin
                    u_renk = col1.selectbox("Renk (Opsiyonel)", df_colors,
                                            index=df_colors.index(curr['renk']) if curr['renk'] in df_colors else 0)
                    u_beden = col2.selectbox("Beden (Opsiyonel)", df_sizes,
                                             index=df_sizes.index(curr['beden']) if curr['beden'] in df_sizes else 0)

                    u_adet = col1.number_input("Yüklenen Adet", value=int(curr['adet']))
                    u_2_adet = col2.number_input("2. Kalite Adet", value=int(curr['ikinciKaliteAdet']))

                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("✅ Değişiklikleri Kaydet"):
                        execute_db("""UPDATE modele_kapama SET companyId=?, modelId=?, kapamaTarihi=?, yuklemeTarihi=?, 
                                      renk=?, beden=?, adet=?, ikinciKaliteAdet=?, updateUser=?, updateTime=? WHERE id=?""",
                                   (sel_cust_id, model_map[u_model], str(u_k_date), str(u_y_date), u_renk, u_beden,
                                    u_adet, u_2_adet, current_user, now, int(sel_id)))
                        st.balloons();
                        st.toast(f"İşlem başarıyla güncellendi!", icon="🚀")
                        time.sleep(1);
                        st.rerun()
                    if c2.form_submit_button("🗑️ Kaydı Sil"):
                        execute_db("DELETE FROM modele_kapama WHERE id=?", (int(sel_id),))
                        st.balloons();
                        st.toast(f"İşlem başarıyla siliindi!", icon="🚀")
                        time.sleep(1);
                        st.rerun()

            else:  # Yeni Kayıt
                sel_m = st.selectbox("Model", list(model_map.keys()) if model_map else ["Model Yok"])

                d1, d2 = st.columns(2)
                n_y_date = d1.date_input("Yükleme Tarihi", value=today)
                n_k_date = d2.date_input("Kapama Tarihi", value=today)

                col1, col2 = st.columns(2)
                n_renk = col1.selectbox("Renk (Opsiyonel)", df_colors)
                n_beden = col2.selectbox("Beden (Opsiyonel)", df_sizes)

                n_adet = col1.number_input("Yüklenen Adet", min_value=0)
                n_2_adet = col2.number_input("2. Kalite Adet", min_value=0)

                if st.form_submit_button("➕ Kapama Kaydını Tamamla"):
                    if model_map:
                        execute_db("""INSERT INTO modele_kapama (companyId, modelId, kapamaTarihi, yuklemeTarihi, beden, renk, adet, ikinciKaliteAdet, createUser, createTime) 
                                      VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                   (sel_cust_id, model_map[sel_m], str(n_k_date), str(n_y_date), n_beden, n_renk,
                                    n_adet, n_2_adet, current_user, now))
                        execute_db("UPDATE Model SET aktif = 0, updateTime = ? WHERE id = ?",
                                       (now, int(model_map[sel_m])))
                        st.success("Kayıt tamamlandı.")
                        st.balloons();
                        st.toast(f"İşlem başarıyla oluşturuldu!", icon="🚀")
                        time.sleep(1);
                        st.rerun()
                    else:
                        st.error("Lütfen bir model seçin!")