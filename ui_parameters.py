import streamlit as st
from database import run_query, execute_db
import time

def show_parameter_page():
    st.header("⚙️ Sistem Parametreleri")

    df_params = run_query("SELECT * FROM parameter")

    tab1, tab2 = st.tabs(["📋 Parametre Listesi", "🔧 Yönetim"])

    with tab2:
        mode = st.radio("İşlem", ["Yeni Parametre", "Düzenle / Sil"], horizontal=True)

        with st.form("param_form", clear_on_submit=True):
            if mode == "Düzenle / Sil" and not df_params.empty:
                sel_id = st.selectbox("Parametre Seç (ID)", df_params['id'])
                row = df_params[df_params['id'] == sel_id].iloc[0]

                g_code = st.text_input("Grup Kodu (Örn: AKS_TYPE)", value=row['groupCode'])
                p_code = st.text_input("Kod", value=row['code'])
                p_val = st.text_input("Değer / Açıklama", value=row['value'])

                c1, c2 = st.columns(2)
                if c1.form_submit_button("Güncelle"):
                    execute_db("UPDATE parameter SET groupCode=?, code=?, value=? WHERE id=?",
                               (g_code, p_code, p_val, int(sel_id)))
                    st.balloons();
                    st.toast(f"İşlem başarıyla güncellendi!", icon="🚀")
                    time.sleep(1);
                    st.rerun()
                if c2.form_submit_button("Sil"):
                    execute_db("DELETE FROM parameter WHERE id=?", (int(sel_id),))
                    st.balloons();
                    st.toast(f"İşlem başarıyla silindi!", icon="🚀")
                    time.sleep(1);
                    st.rerun()
            else:
                g_code = st.text_input("Grup Kodu (Örn: AKS_TYPE)")
                p_code = st.text_input("Kod")
                p_val = st.text_input("Değer / Açıklama")

                if st.form_submit_button("Kaydet"):
                    execute_db("INSERT INTO parameter (groupCode, code, value) VALUES (?,?,?)",
                               (g_code, p_code, p_val))
                    st.balloons();
                    st.toast(f"İşlem başarıyla oluşturuldu!", icon="🚀")
                    time.sleep(1);
                    st.rerun()

    with tab1:
        st.dataframe(df_params, use_container_width=True,
                     column_config={
                         "id": None,  # 👈 Bu satır ID kolonunu tamamen gizler
                     },
                     )