import streamlit as st
import json
from pathlib import Path
import datetime
import os
import shutil
import zipfile
import io

# --- CONFIGURATION ---
SCENARIOS_FILE = Path("scenarios.json")
CONFIG_FILE = Path("config.json")
# BACKUP_DIR is no longer needed for this approach
# BACKUP_DIR = Path("backups") 

# --- HELPER FUNCTIONS ---

def load_data(file_path: Path):
    """Loads data from a JSON file."""
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(file_path: Path, data):
    """Saves data to a JSON file with pretty printing."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_default_scenario(title="Yeni Senaryo Başlığı"):
    """Returns a dictionary with a default structure for a new scenario."""
    return {
        "title": title,
        "icon": "✨",
        "story": "Buraya krizin hikayesini yazın. **Görev**: Oyuncunun görevini buraya yazın.",
        "advisors": [
            {"name": "Danışman 1 (Örn: Güvenlik)", "text": "Danışman görüşünü buraya yazın."},
            {"name": "Danışman 2 (Örn: Hukuk)", "text": "Danışman görüşünü buraya yazın."},
            {"name": "Danışman 3 (Örn: Siyaset)", "text": "Danışman görüşünü buraya yazın."},
            {"name": "Danışman 4 (Örn: Teknik)", "text": "Danışman görüşünü buraya yazın."}
        ],
        "action_cards": [
            {
                "id": "A", "name": "Aksiyon Kartı A", "cost": 30, "hr_cost": 10, "speed": "fast",
                "security_effect": 40, "freedom_cost": 30, "side_effect_risk": 0.4,
                "safeguard_reduction": 0.5, "tooltip": "Hızlı ama riskli bir seçenek."
            },
            {
                "id": "B", "name": "Aksiyon Kartı B", "cost": 20, "hr_cost": 15, "speed": "medium",
                "security_effect": 30, "freedom_cost": 15, "side_effect_risk": 0.2,
                "safeguard_reduction": 0.7, "tooltip": "Dengeli bir seçenek."
            },
            {
                "id": "C", "name": "Aksiyon Kartı C", "cost": 15, "hr_cost": 20, "speed": "slow",
                "security_effect": 20, "freedom_cost": 5, "side_effect_risk": 0.1,
                "safeguard_reduction": 0.8, "tooltip": "Yavaş ama güvenli bir seçenek."
            }
        ],
        "immediate_text": "Anlık etki metnini buraya yazın. Seçilen aksiyonu göstermek için {} kullanın.",
        "delayed_text": "Gecikmeli etki metnini buraya yazın."
    }

# --- UI SECTIONS ---

def backup_and_restore_ui():
    """Renders the UI for backup and restore operations in the sidebar."""
    st.sidebar.title("🗄️ Yedekleme & Geri Yükleme")

    # --- Create and Download Backup ---
    st.sidebar.subheader("Yedek İndir")
    
    # Create zip in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        if SCENARIOS_FILE.exists():
            zip_file.writestr(SCENARIOS_FILE.name, SCENARIOS_FILE.read_bytes())
        if CONFIG_FILE.exists():
            zip_file.writestr(CONFIG_FILE.name, CONFIG_FILE.read_bytes())
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    st.sidebar.download_button(
        label="Mevcut Yapılandırmayı İndir (.zip)",
        data=zip_buffer.getvalue(),
        file_name=f"cio_game_backup_{timestamp}.zip",
        mime="application/zip",
        use_container_width=True
    )

    # --- Restore from Backup ---
    st.sidebar.subheader("Yedekten Geri Yükle")
    uploaded_file = st.sidebar.file_uploader(
        "Bir yedek (.zip) dosyası yükleyin", type="zip"
    )

    if uploaded_file is not None:
        try:
            with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                # Check for required files in zip
                file_list = zip_ref.namelist()
                has_scenarios = SCENARIOS_FILE.name in file_list
                has_config = CONFIG_FILE.name in file_list

                if not has_scenarios or not has_config:
                    st.sidebar.error("Yüklenen ZIP dosyası 'scenarios.json' ve 'config.json' dosyalarını içermiyor.")
                else:
                    # Extract and save
                    scenarios_data = json.loads(zip_ref.read(SCENARIOS_FILE.name))
                    config_data = json.loads(zip_ref.read(CONFIG_FILE.name))
                    
                    save_data(SCENARIOS_FILE, scenarios_data)
                    save_data(CONFIG_FILE, config_data)
                    
                    st.sidebar.success("Yedek başarıyla geri yüklendi!")
                    st.sidebar.info("Değişiklikleri görmek için sayfayı yenileyin.")
                    # We can't rerun from here as it would re-trigger the upload loop
        except Exception as e:
            st.sidebar.error(f"Geri yükleme sırasında bir hata oluştu: {e}")


def add_scenario_ui(scenarios_data):
    """Renders the UI for adding a new scenario."""
    st.header("➕ Yeni Senaryo Oluştur")
    with st.form(key="new_scenario_form"):
        new_id = st.text_input(
            "Yeni Senaryo ID'si (Benzersiz olmalı, örn: 'cyber_attack')",
            help="Bu, senaryonun JSON dosyasındaki anahtarıdır. Boşluk veya Türkçe karakter kullanmaktan kaçının."
        ).lower().strip().replace(" ", "_")
        
        new_title = st.text_input("Yeni Senaryo Başlığı (Oyunda görünecek isim)")

        submitted = st.form_submit_button("Oluştur ve Kaydet")
        if submitted:
            if not new_id or not new_title:
                st.error("Lütfen hem ID hem de Başlık alanlarını doldurun.")
            elif new_id in scenarios_data:
                st.error(f"'{new_id}' ID'si zaten kullanılıyor. Lütfen benzersiz bir ID girin.")
            else:
                scenarios_data[new_id] = get_default_scenario(new_title)
                save_data(SCENARIOS_FILE, scenarios_data)
                st.session_state.mode = 'edit'
                st.success(f"'{new_title}' senaryosu oluşturuldu! Sayfa yenileniyor...")
                st.rerun()

def delete_scenario_ui(scenarios_data):
    """Renders the UI for deleting an existing scenario."""
    st.header("🗑️ Senaryo Sil")

    if not scenarios_data:
        st.warning("Silinecek senaryo bulunamadı.")
        return

    scenario_titles = {data.get('title', f"ID: {key}"): key for key, data in scenarios_data.items()}
    sorted_titles = sorted(scenario_titles.keys())
    
    selected_title_to_delete = st.selectbox("Silinecek Senaryoyu Seçin", options=sorted_titles)
    
    if selected_title_to_delete:
        st.warning(f"**DİKKAT:** '{selected_title_to_delete}' senaryosunu kalıcı olarak silmek üzeresiniz. Bu işlem geri alınamaz.")
        
        if st.button("Evet, Bu Senaryoyu Sil", type="primary"):
            selected_key_to_delete = scenario_titles[selected_title_to_delete]
            del scenarios_data[selected_key_to_delete]
            save_data(SCENARIOS_FILE, scenarios_data)
            st.success(f"'{selected_title_to_delete}' senaryosu silindi! Sayfa yenileniyor...")
            st.session_state.mode = 'edit'
            st.rerun()

def edit_game_balance(config_data):
    """Renders the UI for editing game balance parameters."""
    st.header("⚙️ Oyun Denge Ayarları")
    balance = config_data.get("game_balance", {})
    
    with st.expander("Denge Parametrelerini Düzenle", expanded=True):
        balance['THREAT_SEVERITY'] = st.slider(
            "Tehdit Şiddeti (Crisis Severity)", 0, 100, balance.get('THREAT_SEVERITY', 80)
        )
        balance['TRUST_BOOST_FOR_TRANSPARENCY'] = st.slider(
            "Şeffaflık için Güven Artışı", 0, 20, balance.get('TRUST_BOOST_FOR_TRANSPARENCY', 10)
        )
        
        c1, c2 = st.columns(2)
        with c1:
            balance['SCOPE_MULTIPLIERS']['targeted'] = st.number_input(
                "Kapsam Çarpanı (Hedefli)", value=balance.get('SCOPE_MULTIPLIERS', {}).get('targeted', 0.7), format="%.2f"
            )
            balance['DURATION_MULTIPLIERS']['short'] = st.number_input(
                "Süre Çarpanı (Kısa)", value=balance.get('DURATION_MULTIPLIERS', {}).get('short', 0.5), format="%.2f"
            )
        with c2:
            balance['SCOPE_MULTIPLIERS']['general'] = st.number_input(
                "Kapsam Çarpanı (Genel)", value=balance.get('SCOPE_MULTIPLIERS', {}).get('general', 1.3), format="%.2f"
            )
            balance['DURATION_MULTIPLIERS']['medium'] = st.number_input(
                "Süre Çarpanı (Orta)", value=balance.get('DURATION_MULTIPLIERS', {}).get('medium', 1.0), format="%.2f"
            )
            balance['DURATION_MULTIPLIERS']['long'] = st.number_input(
                "Süre Çarpanı (Uzun)", value=balance.get('DURATION_MULTIPLIERS', {}).get('long', 1.5), format="%.2f"
            )

    config_data["game_balance"] = balance
    return config_data

def edit_scenarios(scenarios_data):
    """Renders the UI for editing scenarios, advisors, and action cards."""
    st.header("📝 Senaryo Editörü")

    if not scenarios_data:
        st.warning("Hiç senaryo bulunamadı. Lütfen kenar çubuğundan bir tane ekleyin.")
        return {}

    scenario_titles = {data.get('title', f"ID: {key}"): key for key, data in scenarios_data.items()}
    sorted_titles = sorted(scenario_titles.keys())
    selected_title = st.selectbox("Düzenlenecek Senaryoyu Seçin", options=sorted_titles)
    
    if not selected_title:
        return scenarios_data

    selected_key = scenario_titles[selected_title]
    scenario = scenarios_data[selected_key]

    st.subheader(f"'{scenario.get('title', '')}' Senaryosunu Düzenle")
    scenario['title'] = st.text_input("Başlık", value=scenario.get('title', ''), key=f"title_{selected_key}")
    scenario['icon'] = st.text_input("İkon (Emoji)", value=scenario.get('icon', ''), max_chars=2, key=f"icon_{selected_key}")
    scenario['story'] = st.text_area("Hikaye", value=scenario.get('story', ''), height=200, key=f"story_{selected_key}")
    scenario['immediate_text'] = st.text_area("Anlık Etki Metni", value=scenario.get('immediate_text', ''), height=100, key=f"imm_text_{selected_key}")
    scenario['delayed_text'] = st.text_area("Gecikmeli Etki Metni", value=scenario.get('delayed_text', ''), height=100, key=f"del_text_{selected_key}")

    st.subheader("Danışmanlar")
    for i, advisor in enumerate(scenario.get("advisors", [])):
        with st.container(border=True):
            st.markdown(f"**Danışman {i+1}**")
            advisor['name'] = st.text_input("Danışman Adı", value=advisor.get('name', ''), key=f"adv_name_{selected_key}_{i}")
            advisor['text'] = st.text_area("Danışman Metni", value=advisor.get('text', ''), key=f"adv_text_{selected_key}_{i}", height=150)

    st.subheader("Aksiyon Kartları")
    for i, card in enumerate(scenario.get("action_cards", [])):
        with st.container(border=True):
            st.markdown(f"**Aksiyon Kartı {i+1} ({card.get('id', '')})**")
            card['name'] = st.text_input("Kart Adı", value=card.get('name', ''), key=f"card_name_{selected_key}_{i}")
            card['tooltip'] = st.text_area("İpucu Metni", value=card.get('tooltip', ''), key=f"card_tooltip_{selected_key}_{i}")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                card['cost'] = st.number_input("Maliyet (Bütçe)", value=card.get('cost', 0), key=f"card_cost_{selected_key}_{i}")
                card['hr_cost'] = st.number_input("Maliyet (İnsan Kaynağı)", value=card.get('hr_cost', 0), key=f"card_hr_{selected_key}_{i}")
            with c2:
                card['security_effect'] = st.slider("Güvenlik Etkisi", 0, 100, value=card.get('security_effect', 0), key=f"card_sec_{selected_key}_{i}")
                card['freedom_cost'] = st.slider("Özgürlük Maliyeti", 0, 100, value=card.get('freedom_cost', 0), key=f"card_free_{selected_key}_{i}")
            with c3:
                card['side_effect_risk'] = st.slider("Yan Etki Riski", 0.0, 1.0, value=card.get('side_effect_risk', 0.0), format="%.2f", key=f"card_risk_{selected_key}_{i}")
                card['safeguard_reduction'] = st.slider("Güvence Azaltma Etkisi", 0.0, 1.0, value=card.get('safeguard_reduction', 0.0), format="%.2f", key=f"card_safe_{selected_key}_{i}")

    scenarios_data[selected_key] = scenario
    return scenarios_data

# --- MAIN APP ---

def main():
    st.set_page_config(layout="wide", page_title="CIO Oyunu Editörü")
    st.title("🛡️ CIO Kriz Yönetimi Oyunu - İçerik Editörü")
    st.markdown("Bu arayüzü kullanarak `scenarios.json` ve `config.json` dosyalarını güvenli bir şekilde düzenleyebilirsiniz.")

    if 'mode' not in st.session_state:
        st.session_state.mode = 'edit'

    scenarios_data = load_data(SCENARIOS_FILE)
    config_data = load_data(CONFIG_FILE)

    # --- Sidebar for Actions ---
    st.sidebar.title("İşlemler")
    if st.sidebar.button("📝 Senaryoları Düzenle/Görüntüle", use_container_width=True):
        st.session_state.mode = 'edit'
        st.rerun()
    if st.sidebar.button("➕ Yeni Senaryo Ekle", use_container_width=True):
        st.session_state.mode = 'add'
        st.rerun()
    if st.sidebar.button("🗑️ Senaryo Sil", use_container_width=True):
        st.session_state.mode = 'delete'
        st.rerun()
    
    st.sidebar.title("Kaydet")
    if st.sidebar.button("Tüm Değişiklikleri Kaydet", type="primary", use_container_width=True):
        # Save based on the current mode to avoid saving partial data
        if st.session_state.mode == 'edit':
             save_data(SCENARIOS_FILE, scenarios_data)
             save_data(CONFIG_FILE, config_data)
             st.sidebar.success("Tüm veriler başarıyla kaydedildi!")
        else:
            st.sidebar.warning("Kaydetme işlemi sadece 'Düzenle' modunda yapılabilir.")

    # --- Backup and Restore Section ---
    backup_and_restore_ui()

    # --- Main Content Area ---
    if st.session_state.mode == 'add':
        add_scenario_ui(scenarios_data)
    elif st.session_state.mode == 'delete':
        delete_scenario_ui(scenarios_data)
    else: # Default to 'edit'
        col1, col2 = st.columns(2)
        with col1:
            updated_scenarios = edit_scenarios(scenarios_data)
            scenarios_data = updated_scenarios # Store updates
        with col2:
            updated_config = edit_game_balance(config_data)
            config_data = updated_config # Store updates


if __name__ == "__main__":
    main()
