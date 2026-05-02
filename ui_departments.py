import streamlit as st
from database import run_query, execute_db
from datetime import datetime
import time

def show_department_page(current_user):
    st.header("🏭 Departman Yönetimi")

    df_depts = run_query("SELECT * FROM Departmans")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tab1, tab2 = st.tabs(["📋 Departman Listesi", "⚙️ Yönetim"])

    with tab2:
        mode = st.toggle("Düzenleme Modunu Aç")

        with st.form("dept_form", clear_on_submit=True):
            if mode and not df_depts.empty:
                # GÜNCELLEME / SİLME
                sel_dept = st.selectbox("Düzenlenecek Departman", df_depts['name'])
                row = df_depts[df_depts['name'] == sel_dept].iloc[0]

                new_name = st.text_input("Departman Adı", value=row['name'])

                c1, c2 = st.columns(2)
                if c1.form_submit_button("🔄 Güncelle"):
                    execute_db("""UPDATE Departmans SET name=?, updateTime=?, updateUser=? 
                                  WHERE id=?""", (new_name, now, current_user, int(row['id'])))
                    st.success("Departman güncellendi!")
                    st.balloons();
                    st.toast(f"İşlem başarıyla güncellendi!", icon="🚀")
                    time.sleep(1);
                    st.rerun()

                if c2.form_submit_button("🗑️ Sil"):
                    execute_db("DELETE FROM Production WHERE departmentId=?",
                               (int(row['id']),))  # Önce bağlı üretimleri temizle
                    execute_db("DELETE FROM Departmans WHERE id=?", (int(row['id']),))
                    st.warning("Departman silindi!")
                    st.balloons();
                    st.toast(f"İşlem başarıyla silindi!", icon="🚀")
                    time.sleep(1);
                    st.rerun()
            else:
                # YENİ KAYIT
                new_name = st.text_input("Yeni Departman Adı")
                if st.form_submit_button("💾 Kaydet"):
                    execute_db("""INSERT INTO Departmans (name, createTime, createUser) 
                                  VALUES (?,?,?)""", (new_name, now, current_user))
                    st.success("Departman başarıyla eklendi.")
                    st.balloons();
                    st.toast(f"İşlem başarıyla oluşturuldu!", icon="🚀")
                    time.sleep(1);
                    st.rerun()

    with tab1:
        st.dataframe(df_depts, use_container_width=True,
                     column_config={
                         "id": None,  # 👈 Bu satır ID kolonunu tamamen gizler
                     },
                     )