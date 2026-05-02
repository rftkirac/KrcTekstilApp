import streamlit as st
from database import run_query, execute_db
from datetime import datetime


def show_model_details_page(current_user):
    st.header("🧵 Model Renk ve Beden Dağılımı")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- VERİLERİ ÖN HAZIRLIK ---
    df_customers = run_query("SELECT id, name FROM Customer")
    df_colors = run_query("SELECT value FROM parameter WHERE groupCode = 'RENK'")
    df_sizes = run_query("SELECT value FROM parameter WHERE groupCode = 'BEDEN'")

    tab_list, tab_manage = st.tabs(["📋 Detay Listesi", "🔧 Kayıt ve Düzenleme"])

    # --- LİSTELEME SEKMESİ ---
    with tab_list:
        st.subheader("🔍 Arama ve Filtreleme")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            f_cust = st.selectbox("Firma", ["Tümü"] + list(df_customers['name']), key="filter_cust")

        with c2:
            # Seçilen Firmaye göre model listesini dinamik daralt
            if f_cust != "Tümü":
                df_f_models = run_query(
                    "SELECT code FROM Model WHERE companyId = (SELECT id FROM Customer WHERE name = ?)", (f_cust,))
                f_model = st.selectbox("Model", ["Tümü"] + list(df_f_models['code']), key="filter_mod")
            else:
                f_model = st.selectbox("Model", ["Tümü"], disabled=True, help="Önce Firma seçin")

        with c3:
            f_color = st.selectbox("Renk", ["Tümü"] + list(df_colors['value']), key="filter_color")

        with c4:
            f_size = st.selectbox("Beden", ["Tümü"] + list(df_sizes['value']), key="filter_size")

        # LİSTELE BUTONU
        list_btn = st.button("🔍 Verileri Listele", use_container_width=True, type="primary")

        if list_btn:
            query = """
                SELECT md.id, c.name as [Firma], (m.code || ' - ' || m.name) as [Model], 
                       md.renk as [Renk], md.beden as [Beden], md.adet as [Adet]
                FROM ModelDetay md
                JOIN Customer c ON md.companyId = c.id
                JOIN Model m ON md.modelId = m.id
                WHERE 1=1
            """
            params = []

            if f_cust != "Tümü":
                query += " AND c.name = ?"
                params.append(f_cust)
            if f_model != "Tümü" and f_cust != "Tümü":
                query += " AND m.code = ?"
                params.append(f_model)
            if f_color != "Tümü":
                query += " AND md.renk = ?"
                params.append(f_color)
            if f_size != "Tümü":
                query += " AND md.beden = ?"
                params.append(f_size)

            df_display = run_query(query + " ORDER BY md.id DESC", params)

            if not df_display.empty:
                st.divider()
                st.metric("Toplam Planlanan Adet", f"{df_display['Adet'].sum():,} Adet")
                st.dataframe(df_display,
                             use_container_width=True,
                             column_config={
                                 "id": None,  # 👈 Bu satır ID kolonunu tamamen gizler
                             },
                             hide_index=True)
            else:
                st.warning("Aranan kriterlere uygun kayıt bulunamadı.")

    # --- YÖNETİM SEKMESİ (EKLE/SİL/GÜNCELLE) ---
    with tab_manage:
        mode = st.radio("İşlem Tipi", ["Yeni Detay Ekle", "Güncelle / Sil"], horizontal=True)
        st.divider()

        with st.form("details_form", clear_on_submit=True):
            if df_customers.empty:
                st.error("Sistemde Firma bulunamadı.")
                return

            # Firma ve Model Seçimi
            sel_cust_name = st.selectbox("Firma", list(df_customers['name']))
            sel_cust_id = df_customers[df_customers['name'] == sel_cust_name]['id'].values[0]

            df_models = run_query("SELECT id, code, name FROM Model WHERE companyId = ?", (int(sel_cust_id),))
            model_options = {f"{r['code']} - {r['name']}": r['id'] for _, r in df_models.iterrows()}

            if mode == "Güncelle / Sil":
                all_raw = run_query("SELECT id, renk, beden, adet FROM ModelDetay")
                if all_raw.empty:
                    st.info("Kayıt yok.")
                else:
                    sel_id = st.selectbox("Düzenlenecek ID", all_raw['id'])
                    row = all_raw[all_raw['id'] == sel_id].iloc[0]

                    u_model = st.selectbox("Model", list(model_options.keys()))
                    u_renk = st.selectbox("Renk", list(df_colors['value']),
                                          index=list(df_colors['value']).index(row['renk']) if row['renk'] in list(
                                              df_colors['value']) else 0)
                    u_beden = st.selectbox("Beden", list(df_sizes['value']),
                                           index=list(df_sizes['value']).index(row['beden']) if row['beden'] in list(
                                               df_sizes['value']) else 0)
                    u_adet = st.number_input("Adet", value=int(row['adet']))

                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("✅ Güncelle"):
                        execute_db(
                            "UPDATE ModelDetay SET companyId=?, modelId=?, renk=?, beden=?, adet=?, updateUser=?, updateTime=? WHERE id=?",
                            (int(sel_cust_id), model_options[u_model], u_renk, u_beden, u_adet, current_user, now,
                             int(sel_id)))
                        st.rerun()
                    if c2.form_submit_button("🗑️ Sil"):
                        execute_db("DELETE FROM ModelDetay WHERE id=?", (int(sel_id),))
                        st.rerun()

            else:  # Yeni Kayıt
                sel_model = st.selectbox("Model", list(model_options.keys()) if model_options else ["Model Yok"])
                n_renk = st.selectbox("Renk",
                                      list(df_colors['value']) if not df_colors.empty else ["RENK Parametresi Girin"])
                n_beden = st.selectbox("Beden",
                                       list(df_sizes['value']) if not df_sizes.empty else ["BEDEN Parametresi Girin"])
                n_adet = st.number_input("Adet", min_value=0)

                if st.form_submit_button("➕ Detayı Kaydet"):
                    if model_options and not df_colors.empty:
                        execute_db("""INSERT INTO ModelDetay (companyId, modelId, renk, beden, adet, createUser, createTime) 
                                      VALUES (?,?,?,?,?,?,?)""",
                                   (int(sel_cust_id), model_options[sel_model], n_renk, n_beden, n_adet, current_user,
                                    now))
                        st.success("Kaydedildi.")
                        st.rerun()