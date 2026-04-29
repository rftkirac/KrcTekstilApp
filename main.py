import streamlit as st
from database import init_db
from ui_auth import show_login_page
from ui_customers import show_customer_page
from ui_departments import show_department_page
from ui_models import show_model_page
from ui_model_360 import show_model_360_view
from ui_model_details import show_model_details_page
from ui_production import show_production_page
from ui_reports import show_advanced_report_page
from ui_accessories import show_accessory_page  # Yeni
from ui_parameters import show_parameter_page    # Yeni
from ui_users import show_user_page
from ui_model_closing import show_model_closing_page
import streamlit as st
from database import init_db
from utils import cfg  # Hazırladığımız config objesini import et
from datetime import datetime

# ... (Diğer importlar aynı kalsın)

# --- UYGULAMA AYARLARI ---
# Şirket adını başlıklarda kullanma

#st.set_page_config(page_title=cfg['company']['name'],layout="wide", page_icon="👔")

st.set_page_config(
    page_title=cfg['company']['name'],
    layout="wide",
    page_icon="👔",
    initial_sidebar_state="expanded" # Sidebar'ın her zaman açık başlamasını sağlar
)


#st.set_page_config(page_title="KRC Tekstil", layout="wide", page_icon="👔")

# --- STİL AYARLARI ---

st.markdown("""
    <style>
        /* Ana içerik üst boşluğunu daralt */
        .block-container {
            padding-top: 3rem;
            padding-bottom: 0rem;
        }
        
        /* Sidebar en üst boşluğu sıfırla */
        [data-testid="stSidebarContent"] {
            padding-top: 0rem !important;
        }

        /* OK SİMGESİNİ GÖRÜNÜR YAPMAK İÇİN: */
        /* Header'ı tamamen gizlemek yerine sadece arka planını şeffaf yapıyoruz */
        header {
            background-color: rgba(0,0,0,0); /* Şeffaf arka plan */
            height: 3rem; /* Oku görecek kadar yükseklik */
        }

        /* Sidebar içindeki logonun üst boşluğunu hafifçe ayarla */
        [data-testid="stSidebar"] img {
            margin-top: 0px;
        }
    </style>
""", unsafe_allow_html=True)

init_db()

# --- OTURUM YÖNETİMİ ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "Modeller"  # Varsayılan açılış sayfası
if "selected_model_id" not in st.session_state:
    st.session_state.selected_model_id = None


if not st.session_state.logged_in:
    show_login_page()
else:
    # --- SOL YAN MENÜ (SIDEBAR) ---
    with st.sidebar:
        try:
            # Logonun dosya yolunu buraya yaz (örneğin logo.png)
            st.image("image/krc_logo.png", use_container_width=True)
            # Logo ile altındaki metin arasındaki mesafeyi sen belirle
            st.markdown("<div style='margin-top: -10px;'></div>", unsafe_allow_html=True)
        except:
            # Logo dosyası bulunamazsa şirket ismini yazdırır
            st.title(cfg['company']['name'])
       # st.image("https://via.placeholder.com/150", width=100)  # Varsa logonuz
        #st.title(cfg['company']['name'])
        #st.write(f"Hoş geldin, **{st.session_state.user}**")
        #st.markdown("---")


        # Menü Butonları
        def nav_button(label, icon):
            if st.button(f"{icon} {label}", use_container_width=True,
                         type="secondary" if st.session_state.page != label else "primary"):
                st.session_state.page = label
                st.rerun()



        nav_button("Modeller", "👕")
        nav_button("Model Günlük İş Giriş", "🚀")
        nav_button("Model Detay", "🧵")
        nav_button("Model Kapama", "🏁")
        nav_button("Aksesuarlar", "🎀")

        nav_button("Raporlar", "📊")
        nav_button("Firmalar", "👥")

        # Admin Paneli Ayırıcı
        is_admin = st.session_state.get('user') == 'admin'
        if is_admin:
            st.markdown("---")
            st.caption("Sistem Yönetimi")
            nav_button("Departmanlar", "🏭")
            nav_button("Parametreler", "⚙️")
            nav_button("Kullanıcılar", "👤")

        st.markdown("---")
        if st.button("🚪 Güvenli Çıkış", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    if st.session_state.logged_in:
        tarih = datetime.now().strftime("%d %B %Y")
        # Sayfanın en üstünde sağa yaslı hoş geldin mesajı
        col1, col2 = st.columns([8, 2])  # 8:2 oranıyla sağda küçük bir alan ayırıyoruz
        with col2:
            st.markdown(
                f"""
                <div style='text-align: right; color: #666; font-size: 0.9rem; line-height: 1.2;'>
                    <div>📅 {tarih} / <span style='color: #1f77b4; font-weight: bold;'>{st.session_state.user}</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )
        #st.markdown("---")  # İçerik ile başlık arasına ince bir çizgi

    # --- SAYFA YÖNLENDİRME MANTIĞI ---
    page = st.session_state.page

    if st.session_state.selected_model_id:
        # Eğer bir model seçilmişse direkt detay ekranını göster (Menüden bağımsız)
        from ui_model_360 import show_model_360_view
        show_model_360_view()
        #st.session_state.selected_model_id = None
    else:
        if page == "Firmalar":
            show_customer_page(st.session_state.user)
        elif page == "Departmanlar":
            show_department_page(st.session_state.user)
        elif page == "Modeller":
            show_model_page(st.session_state.user)
        elif page == "Model Detay":
            show_model_details_page(st.session_state.user)
        elif page == "Model Kapama":
            show_model_closing_page(st.session_state.user)
        elif page == "Aksesuarlar":
            show_accessory_page(st.session_state.user)
        elif page == "Model Günlük İş Giriş":
            show_production_page(st.session_state.user)
        elif page == "Raporlar":
            show_advanced_report_page()
        elif page == "Parametreler":
            show_parameter_page()
        elif page == "Kullanıcılar":
            show_user_page(True)