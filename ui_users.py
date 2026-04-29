import streamlit as st
from database import run_query, execute_db
from datetime import datetime


def show_user_page(current_user):
    st.header("👤 Kullanıcı Yönetimi")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Tabloyu çek (Şifreyi güvenlik için listede göstermiyoruz)
    df_users = run_query("SELECT id, userName, name, surname, isActive, createTime, createUser FROM Users")

    tab_list, tab_manage = st.tabs(["📋 Kullanıcı Listesi", "🔧 Kullanıcı İşlemleri"])

    with tab_manage:
        mode = st.radio("İşlem Tipi", ["Yeni Kullanıcı Kaydı", "Düzenle / Sil"], horizontal=True)
        st.divider()

        with st.form("user_form", clear_on_submit=True):
            if mode == "Düzenle / Sil":
                if df_users.empty:
                    st.info("Sistemde kayıtlı kullanıcı bulunamadı.")
                else:
                    sel_id = st.selectbox(
                        "İşlem Yapılacak Kullanıcı",
                        df_users['id'],
                        format_func=lambda
                            x: f"{df_users[df_users['id'] == x]['userName'].values[0]} ({df_users[df_users['id'] == x]['name'].values[0]} {df_users[df_users['id'] == x]['surname'].values[0]})"
                    )

                    # Seçili veriyi bul
                    row = df_users[df_users['id'] == sel_id].iloc[0]

                    u_username = st.text_input("Kullanıcı Adı (Giriş Adı)", value=row['userName'])
                    u_name = st.text_input("Ad", value=row['name'])
                    u_surname = st.text_input("Soyad", value=row['surname'])
                    u_pass = st.text_input("Şifre (Değiştirmek istemiyorsanız boş bırakın)", type="password")
                    u_active = st.checkbox("Aktif mi?", value=bool(row['isActive']))

                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("💾 Bilgileri Güncelle"):
                        if u_pass:  # Şifre doluysa şifreyi de güncelle
                            execute_db("""UPDATE Users SET userName=?, name=?, surname=?, isActive=?, password=? 
                                          WHERE id=?""",
                                       (u_username, u_name, u_surname, int(u_active), u_pass, int(sel_id)))
                        else:  # Şifre boşsa eski şifreyi koru
                            execute_db("""UPDATE Users SET userName=?, name=?, surname=?, isActive=? 
                                          WHERE id=?""",
                                       (u_username, u_name, u_surname, int(u_active), int(sel_id)))
                        st.success("Kullanıcı güncellendi!")
                        st.rerun()

                    if c2.form_submit_button("🗑️ Kullanıcıyı Sil"):
                        if u_username == current_user:
                            st.error("Kendi kullanıcınızı silemezsiniz!")
                        else:
                            execute_db("DELETE FROM Users WHERE id=?", (int(sel_id),))
                            st.warning("Kullanıcı sistemden silindi!")
                            st.rerun()

            else:  # Yeni Kullanıcı Modu
                col1, col2 = st.columns(2)
                new_username = col1.text_input("Kullanıcı Adı")
                new_pass = col2.text_input("Şifre", type="password")
                new_name = col1.text_input("Ad")
                new_surname = col2.text_input("Soyad")
                new_active = st.checkbox("Aktif Kullanıcı", value=True)

                if st.form_submit_button("➕ Kullanıcıyı Sisteme Tanımla"):
                    if new_username and new_pass and new_name:
                        # Çakışma kontrolü
                        check = run_query("SELECT id FROM Users WHERE userName = ?", (new_username,))
                        if not check.empty:
                            st.error("Bu Kullanıcı Adı zaten kullanımda!")
                        else:
                            execute_db("""INSERT INTO Users (userName, name, surname, isActive, password, createTime, createUser) 
                                          VALUES (?,?,?,?,?,?,?)""",
                                       (new_username, new_name, new_surname, int(new_active), new_pass, now,
                                        current_user))
                            st.success(f"{new_username} kullanıcısı başarıyla oluşturuldu.")
                            st.rerun()
                    else:
                        st.error("Lütfen zorunlu alanları (Kullanıcı adı, Şifre, Ad) doldurun!")

    with tab_list:
        if df_users.empty:
            st.warning("Görüntülenecek kullanıcı yok.")
        else:
            # isActive kolonunu daha anlaşılır yapalım (0/1 yerine ikon)
            df_display = df_users.copy()
            df_display['Durum'] = df_display['isActive'].apply(lambda x: "✅ Aktif" if x == 1 else "❌ Pasif")

            st.dataframe(
                df_display[['id', 'userName', 'name', 'surname', 'Durum', 'createTime', 'createUser']],
                use_container_width=True,
                hide_index=True
            )