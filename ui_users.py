import streamlit as st
import pandas as pd
from database import run_query, execute_db
from datetime import datetime
import time


def show_user_page(current_user):
    st.header("👤 Kullanıcı Yönetimi")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- 1. VERİ ÇEKME ---
    try:
        df_roles = run_query("SELECT id, roleName FROM Roles")
    except Exception as e:
        st.error(f"Roles tablosu okunurken hata oluştu: {e}")
        df_roles = pd.DataFrame(columns=['id', 'roleName'])

    try:
        query_users = """
            SELECT u.*, 
            r.roleName 
            FROM Users u
            LEFT JOIN Roles r ON u.roleId = r.id
        """
        df_users = run_query(query_users)
    except Exception as e:
        st.error(f"Kullanıcı listesi çekilemedi: {e}")
        df_users = pd.DataFrame()

    tab_list, tab_manage = st.tabs(["📋 Kullanıcı Listesi", "🔧 Kullanıcı İşlemleri"])

    with tab_list:
        if df_users.empty:
            st.warning("Görüntülenecek kullanıcı bulunamadı.")
        else:
            df_display = df_users.copy()
            df_display['Durum'] = df_display['isActive'].apply(lambda x: "✅ Aktif" if x == 1 else "❌ Pasif")
            cols = ['id', 'userName', 'name', 'surname', 'roleName', 'Durum', 'createTime', 'createUser']
            st.dataframe(df_display[[c for c in cols if c in df_display.columns]], use_container_width=True,
                         hide_index=True,
                         column_config={
                             "id": None,  # 👈 Bu satır ID kolonunu tamamen gizler
                         },
                         )

    with tab_manage:
        mode = st.radio("İşlem Seçiniz", ["Yeni Kullanıcı Kaydı", "Düzenle / Sil"], horizontal=True)
        st.divider()

        if mode == "Düzenle / Sil":
            if df_users.empty:
                st.info("Düzenlenecek kullanıcı yok.")
            else:
                # --- KRİTİK DEĞİŞİKLİK: SELECTBOX FORM DIŞINDA ---
                # Bu sayede seçim yapıldığı an sayfa yenilenir ve 'row' değişkeni güncellenir.
                sel_id = st.selectbox(
                    "İşlem Yapılacak Kullanıcıyı Seçin",
                    df_users['id'].tolist(),
                    format_func=lambda
                        x: f"{df_users[df_users['id'] == x]['userName'].values[0]} ({df_users[df_users['id'] == x]['name'].values[0]})",
                    key="user_selector"
                )

                # Seçilen kullanıcının bilgilerini al
                row = df_users[df_users['id'] == sel_id].iloc[0]

                # Bilgileri formun içinde göster
                with st.form("edit_user_form"):
                    u_username = st.text_input("Kullanıcı Adı", value=str(row['userName']))
                    u_name = st.text_input("Ad", value=str(row['name']))
                    u_surname = st.text_input("Soyad", value=str(row['surname']))

                    # Rol seçimi index hesaplama
                    role_list = df_roles['id'].tolist()
                    current_role_id = row['roleId']
                    role_index = role_list.index(current_role_id) if current_role_id in role_list else 0

                    u_role_id = st.selectbox(
                        "Yetki Rolü",
                        options=role_list,
                        index=role_index,
                        format_func=lambda x: df_roles[df_roles['id'] == x]['roleName'].values[0]
                    )

                    u_pass = st.text_input("Yeni Şifre (Değişmesin istiyorsanız boş bırakın)", type="password")
                    u_active = st.checkbox("Hesap Aktif", value=bool(row['isActive']))

                    col_btn1, col_btn2 = st.columns(2)

                    if col_btn1.form_submit_button("💾 Değişiklikleri Kaydet"):
                        if u_pass:
                            execute_db("""UPDATE Users SET userName=?, name=?, surname=?, isActive=?, roleId=?, password=? 
                                          WHERE id=?""",
                                       (u_username, u_name, u_surname, int(u_active), int(u_role_id), u_pass,
                                        int(sel_id)))
                        else:
                            execute_db("""UPDATE Users SET userName=?, name=?, surname=?, isActive=?, roleId=? 
                                          WHERE id=?""",
                                       (u_username, u_name, u_surname, int(u_active), int(u_role_id), int(sel_id)))
                        st.success("Kullanıcı başarıyla güncellendi.")
                        st.balloons();
                        st.toast(f"İşlem başarıyla güncellendi!", icon="🚀")
                        time.sleep(1);
                        st.rerun()

                    if col_btn2.form_submit_button("🗑️ Kullanıcıyı Sil"):
                        if u_username == current_user:
                            st.error("Kendi hesabınızı silemezsiniz!")
                        else:
                            execute_db("DELETE FROM Users WHERE id=?", (int(sel_id),))
                            st.warning("Kullanıcı silindi.")
                            st.balloons();
                            st.toast(f"İşlem başarıyla Silindi!", icon="🚀")
                            time.sleep(1);
                            st.rerun()

        else:  # YENİ KULLANICI KAYDI
            with st.form("new_user_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                new_username = c1.text_input("Giriş Adı (userName)")
                new_pass = c2.text_input("Şifre", type="password")
                new_name = c1.text_input("Ad")
                new_surname = c2.text_input("Soyad")

                new_role_id = st.selectbox(
                    "Yetki Rolü Atayın",
                    options=df_roles['id'].tolist() if not df_roles.empty else [0],
                    format_func=lambda x: df_roles[df_roles['id'] == x]['roleName'].values[
                        0] if not df_roles.empty else "Rol Yok"
                )

                new_active = st.checkbox("Aktif Kullanıcı Olarak Tanımla", value=True)

                if st.form_submit_button("➕ Kullanıcıyı Oluştur"):
                    if new_username and new_pass and new_name:
                        check = run_query("SELECT id FROM Users WHERE userName = ?", (new_username,))
                        if not check.empty:
                            st.error("Bu kullanıcı adı zaten alınmış!")
                        else:
                            execute_db("""INSERT INTO Users (userName, name, surname, isActive, roleId, password, createTime, createUser) 
                                          VALUES (?,?,?,?,?,?,?,?)""",
                                       (new_username, new_name, new_surname, int(new_active), int(new_role_id),
                                        new_pass, now, current_user))
                            st.success(f"{new_username} başarıyla eklendi.")
                            st.balloons();
                            st.toast(f"İşlem başarıyla oluşturuldu!", icon="🚀")
                            time.sleep(1);
                            st.rerun()
                    else:
                        st.error("Lütfen zorunlu alanları doldurun!")