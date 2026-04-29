import streamlit as st
from database import run_query
from utils import cfg


def show_login_page():
    # Sayfayı dikeyde biraz ortalamak için boşluk bırakıyoruz
    st.markdown("""
            <style>
                /* Giriş sayfasında en üstteki boşluğu tamamen yok et */
                .main .block-container {
                    padding-top: 0rem !important;
                    margin-top: 0px; /* Daha da yukarı çekmek için */
                }
                /* Form kutusunun üst boşluğunu ayarla */
                [data-testid="stVerticalBlock"] {
                    gap: 0rem;
                }
            </style>
        """, unsafe_allow_html=True)

    # Ekranı 3 sütuna bölerek formu ortaya alıyoruz
    # [1, 1.2, 1] oranı orta sütunu ideal genişlikte tutar
    empty_l, col_main, empty_r = st.columns([1, 1.2, 1])

    with col_main:
        # Formun etrafında bir çerçeve (border) oluşturuyoruz
        with st.container(border=True):
            # Şirket Logosu
            try:
                st.image("image/krc_logo.png", use_container_width=True)
            except:
                st.title("👔")  # Logo dosyası yoksa ikon gösterir

            st.markdown(f"<h3 style='text-align: center; color: #31333F;'>{cfg['company']['full_name']}</h3>",
                        unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>Sisteme erişmek için lütfen giriş yapın.</p>",
                        unsafe_allow_html=True)

            # Giriş Formu
            with st.form("login_form", clear_on_submit=False):
                u_name = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı adınızı giriniz")
                u_pass = st.text_input("Şifre", type="password", placeholder="Şifrenizi giriniz")

                # Butonu tüm genişliğe yayıyoruz
                submit = st.form_submit_button("Giriş Yap", use_container_width=True)

                if submit:
                    if u_name and u_pass:
                        # Veritabanı kontrolü
                        user_check = run_query(
                            "SELECT * FROM Users WHERE userName=? AND password=? AND isActive=1",
                            (u_name, u_pass)
                        )

                        if not user_check.empty:
                            st.session_state.logged_in = True
                            st.session_state.user = u_name
                            st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                            st.rerun()
                        else:
                            st.error("Kullanıcı adı veya şifre hatalı!")
                    else:
                        st.warning("Lütfen tüm alanları doldurun.")


# Eğer kullanıcı yönetimi (Admin Paneli) bu dosyada kalacaksa:
def show_user_management(current_user):
    st.header("👤 Kullanıcı Yönetimi")
    st.info("Kullanıcı ekleme, düzenleme ve yetkilendirme işlemlerini buradan yapabilirsiniz.")
    # CRUD (Create, Read, Update, Delete) kodların buraya eklenebilir.