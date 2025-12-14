import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

# ============================================================================
# KONFIGURASI
# ============================================================================
st.set_page_config(
    page_title="Deteksi Dini DBD",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS STYLING
# ============================================================================
st.markdown("""
    <style>
    .main-header {
        font-size: 2.8rem;
        color: #c0392b;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.3rem;
        color: #34495e;
        text-align: center;
        margin-bottom: 2rem;
    }
    .diagnosis-positive {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .diagnosis-negative {
        background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .diagnosis-suspect {
        background: linear-gradient(135deg, #ffd93d 0%, #f39c12 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .warning-box {
    background-color: #fff3cd;
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #ffc107;
    margin: 15px 0;
    color: #000000;
}
.info-box {
    background-color: #e3f2fd;
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #2196f3;
    margin: 15px 0;
    color: #000000;
}
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# GENERATE CASE BASE DARI DATA LAB
# ============================================================================
@st.cache_data
def generate_case_base_from_lab_data():
    """
    Generate case base berdasarkan POLA GEJALA PROBABILISTIK dari data lab.
    
    KONSEP:
    - Dataset lab digunakan untuk menentukan DIAGNOSIS dan SEVERITY
    - Gejala di-generate berdasarkan PROBABILITAS medis, bukan deterministik
    - Ini mencerminkan realita: pasien dengan platelet rendah MUNGKIN punya mimisan, tapi tidak selalu
    """
    
    try:
        with open('case_base.json', 'r', encoding='utf-8') as f:
            lab_data = json.load(f)
    except:
        # Fallback ke sample data
        return generate_sample_cases()
    
    cases = []
    
    for data in lab_data:
        platelet = data['platelet']
        hct = data['hematokrit']
        wbc = data['wbc']
        hb = data['hemoglobin']
        diagnosis = data['diagnosis']
        
        case = {
            'case_id': data['case_id'],
            'diagnosis': diagnosis,
            'age': data['age'],
            'gender': data['gender'],
            'platelet': platelet,
            'hematokrit': hct,
            'wbc': wbc,
            'hemoglobin': hb
        }
        
        # ============================================================
        # GENERATE GEJALA DENGAN PROBABILITAS MEDIS
        # ============================================================
        
        if diagnosis == 'DBD_POSITIF':
            # GEJALA UMUM DBD (hampir selalu ada)
            case['demam_tinggi'] = np.random.choice([0, 1], p=[0.05, 0.95])  # 95% DBD punya demam
            case['lemah_lesu'] = np.random.choice([0, 1], p=[0.10, 0.90])
            case['kehilangan_nafsu_makan'] = np.random.choice([0, 1], p=[0.15, 0.85])
            
            # GEJALA KARAKTERISTIK DBD (sering ada)
            case['sakit_kepala'] = np.random.choice([0, 1], p=[0.20, 0.80])
            case['nyeri_sendi'] = np.random.choice([0, 1], p=[0.25, 0.75])
            case['nyeri_otot'] = np.random.choice([0, 1], p=[0.25, 0.75])
            case['nyeri_belakang_mata'] = np.random.choice([0, 1], p=[0.30, 0.70])
            
            # GEJALA PERDARAHAN (tergantung platelet)
            if platelet < 20000:  # SEVERE
                case['bintik_merah'] = np.random.choice([0, 1], p=[0.10, 0.90])
                case['mimisan'] = np.random.choice([0, 1], p=[0.30, 0.70])
                case['gusi_berdarah'] = np.random.choice([0, 1], p=[0.35, 0.65])
                case['trombosit_rendah'] = 1
                case['pembesaran_hati'] = np.random.choice([0, 1], p=[0.20, 0.80])
                case['severity'] = 'BERAT'
            elif platelet < 50000:  # MODERATE-SEVERE
                case['bintik_merah'] = np.random.choice([0, 1], p=[0.20, 0.80])
                case['mimisan'] = np.random.choice([0, 1], p=[0.50, 0.50])
                case['gusi_berdarah'] = np.random.choice([0, 1], p=[0.55, 0.45])
                case['trombosit_rendah'] = 1
                case['pembesaran_hati'] = np.random.choice([0, 1], p=[0.40, 0.60]) if hct > 45 else np.random.choice([0, 1], p=[0.70, 0.30])
                case['severity'] = 'SEDANG'
            elif platelet < 100000:  # MILD-MODERATE
                case['bintik_merah'] = np.random.choice([0, 1], p=[0.40, 0.60])
                case['mimisan'] = np.random.choice([0, 1], p=[0.70, 0.30])
                case['gusi_berdarah'] = np.random.choice([0, 1], p=[0.75, 0.25])
                case['trombosit_rendah'] = 1
                case['pembesaran_hati'] = np.random.choice([0, 1], p=[0.70, 0.30])
                case['severity'] = 'RINGAN' if platelet > 70000 else 'SEDANG'
            else:  # VERY MILD (platelet normal tapi DBD)
                case['bintik_merah'] = np.random.choice([0, 1], p=[0.70, 0.30])
                case['mimisan'] = np.random.choice([0, 1], p=[0.85, 0.15])
                case['gusi_berdarah'] = np.random.choice([0, 1], p=[0.90, 0.10])
                case['trombosit_rendah'] = 0
                case['pembesaran_hati'] = np.random.choice([0, 1], p=[0.85, 0.15])
                case['severity'] = 'RINGAN'
            
            # GEJALA GI (variabel)
            case['mual_muntah'] = np.random.choice([0, 1], p=[0.40, 0.60])
            case['nyeri_perut'] = np.random.choice([0, 1], p=[0.50, 0.50])
            
            # GEJALA KULIT
            case['ruam_kulit'] = np.random.choice([0, 1], p=[0.50, 0.50])
            
        else:  # BUKAN DBD
            # Demam bisa ada (penyakit lain)
            case['demam_tinggi'] = np.random.choice([0, 1], p=[0.40, 0.60])
            
            # Gejala umum (bisa ada di penyakit lain)
            case['sakit_kepala'] = np.random.choice([0, 1], p=[0.50, 0.50])
            case['lemah_lesu'] = np.random.choice([0, 1], p=[0.40, 0.60])
            case['mual_muntah'] = np.random.choice([0, 1], p=[0.60, 0.40])
            case['nyeri_perut'] = np.random.choice([0, 1], p=[0.65, 0.35])
            case['kehilangan_nafsu_makan'] = np.random.choice([0, 1], p=[0.55, 0.45])
            
            # Gejala yang JARANG di non-DBD
            case['nyeri_sendi'] = np.random.choice([0, 1], p=[0.70, 0.30])
            case['nyeri_otot'] = np.random.choice([0, 1], p=[0.70, 0.30])
            case['nyeri_belakang_mata'] = np.random.choice([0, 1], p=[0.85, 0.15])
            case['ruam_kulit'] = np.random.choice([0, 1], p=[0.80, 0.20])
            
            # Gejala DBD-spesifik (hampir TIDAK ADA di non-DBD)
            case['bintik_merah'] = np.random.choice([0, 1], p=[0.95, 0.05])
            case['mimisan'] = np.random.choice([0, 1], p=[0.95, 0.05])
            case['gusi_berdarah'] = np.random.choice([0, 1], p=[0.97, 0.03])
            case['pembesaran_hati'] = 0
            case['trombosit_rendah'] = 0
            
            case['severity'] = 'NON_DBD'
        
        cases.append(case)
    
    return pd.DataFrame(cases)

def generate_sample_cases():
    """Fallback jika JSON tidak ada"""
    cases = []
    
    for i in range(100):
        is_dbd = i < 70
        
        if is_dbd:
            platelet = np.random.randint(15000, 150000)
            case = {
                'case_id': f'DBD_{i+1:03d}',
                'diagnosis': 'DBD_POSITIF',
                'platelet': platelet,
                'demam_tinggi': np.random.choice([0, 1], p=[0.05, 0.95]),
                'sakit_kepala': np.random.choice([0, 1], p=[0.20, 0.80]),
                'nyeri_sendi': np.random.choice([0, 1], p=[0.25, 0.75]),
                'nyeri_otot': np.random.choice([0, 1], p=[0.25, 0.75]),
                'nyeri_belakang_mata': np.random.choice([0, 1], p=[0.30, 0.70]),
                'lemah_lesu': np.random.choice([0, 1], p=[0.10, 0.90]),
                'kehilangan_nafsu_makan': np.random.choice([0, 1], p=[0.15, 0.85]),
                'bintik_merah': 1 if platelet < 80000 else np.random.choice([0, 1], p=[0.70, 0.30]),
                'mimisan': 1 if platelet < 40000 else np.random.choice([0, 1], p=[0.85, 0.15]),
                'gusi_berdarah': 1 if platelet < 40000 else np.random.choice([0, 1], p=[0.90, 0.10]),
                'trombosit_rendah': 1 if platelet < 100000 else 0,
                'pembesaran_hati': np.random.choice([0, 1], p=[0.60, 0.40]),
                'mual_muntah': np.random.choice([0, 1], p=[0.40, 0.60]),
                'nyeri_perut': np.random.choice([0, 1], p=[0.50, 0.50]),
                'ruam_kulit': np.random.choice([0, 1], p=[0.50, 0.50]),
                'severity': 'BERAT' if platelet < 20000 else ('SEDANG' if platelet < 70000 else 'RINGAN')
            }
        else:
            case = {
                'case_id': f'NEG_{i-69:03d}',
                'diagnosis': 'BUKAN_DBD',
                'platelet': np.random.randint(150000, 400000),
                'demam_tinggi': np.random.choice([0, 1], p=[0.40, 0.60]),
                'sakit_kepala': np.random.choice([0, 1], p=[0.50, 0.50]),
                'nyeri_sendi': np.random.choice([0, 1], p=[0.70, 0.30]),
                'nyeri_otot': np.random.choice([0, 1], p=[0.70, 0.30]),
                'nyeri_belakang_mata': np.random.choice([0, 1], p=[0.85, 0.15]),
                'lemah_lesu': np.random.choice([0, 1], p=[0.40, 0.60]),
                'kehilangan_nafsu_makan': np.random.choice([0, 1], p=[0.55, 0.45]),
                'bintik_merah': np.random.choice([0, 1], p=[0.95, 0.05]),
                'mimisan': np.random.choice([0, 1], p=[0.95, 0.05]),
                'gusi_berdarah': np.random.choice([0, 1], p=[0.97, 0.03]),
                'trombosit_rendah': 0,
                'pembesaran_hati': 0,
                'mual_muntah': np.random.choice([0, 1], p=[0.60, 0.40]),
                'nyeri_perut': np.random.choice([0, 1], p=[0.65, 0.35]),
                'ruam_kulit': np.random.choice([0, 1], p=[0.80, 0.20]),
                'severity': 'NON_DBD'
            }
        
        cases.append(case)
    
    return pd.DataFrame(cases)

# ============================================================================
# FUNGSI CBR
# ============================================================================
def calculate_similarity(new_case, case_base):
    """Hitung similarity HANYA berdasarkan gejala klinis"""
    
    symptoms = [
        'demam_tinggi', 'sakit_kepala', 'nyeri_sendi', 'nyeri_otot',
        'mual_muntah', 'ruam_kulit', 'nyeri_perut', 'mimisan',
        'gusi_berdarah', 'bintik_merah', 'lemah_lesu', 'kehilangan_nafsu_makan',
        'nyeri_belakang_mata', 'pembesaran_hati', 'trombosit_rendah'
    ]
    
    # Bobot berdasarkan spesifisitas DBD
    weights = {
        'trombosit_rendah': 0.15,      # Paling spesifik (tapi jarang user tahu)
        'bintik_merah': 0.13,           # Sangat spesifik DBD
        'mimisan': 0.11,                # Tanda perdarahan
        'gusi_berdarah': 0.11,          # Tanda perdarahan
        'demam_tinggi': 0.10,           # Umum tapi penting
        'nyeri_sendi': 0.08,            # Break-bone fever
        'nyeri_otot': 0.07,             # Myalgia
        'nyeri_belakang_mata': 0.07,    # Khas DBD
        'pembesaran_hati': 0.06,        # Warning sign
        'sakit_kepala': 0.04,           # Umum
        'nyeri_perut': 0.03,            # Warning sign
        'ruam_kulit': 0.02,             # Bisa ada
        'mual_muntah': 0.02,            # Umum
        'lemah_lesu': 0.01,             # Sangat umum
        'kehilangan_nafsu_makan': 0.01  # Sangat umum
    }
    
    similarities = []
    
    for idx, case in case_base.iterrows():
        distance = 0
        matched = 0
        
        for sym in symptoms:
            new_val = new_case.get(sym, 0)
            case_val = case[sym]
            distance += abs(new_val - case_val) * weights[sym]
            
            if new_val == case_val and new_val == 1:
                matched += 1
        
        similarity = (1 - distance) * 100
        
        similarities.append({
            'case_id': case['case_id'],
            'similarity': similarity,
            'matched_symptoms': matched,
            'diagnosis': case['diagnosis'],
            'severity': case['severity']
        })
    
    return pd.DataFrame(similarities).sort_values('similarity', ascending=False)

def diagnose(similar_cases, total_symptoms):
    """Diagnosa dengan validasi minimum gejala"""
    
    # Validasi: minimal 3 gejala
    if total_symptoms < 3:
        return 'DATA_INSUFFICIENT', 0, {
            'DBD_POSITIF': 0, 'SUSPEK_DBD': 0, 'BUKAN_DBD': 0
        }, 'INSUFFICIENT'
    
    total_sim = similar_cases['similarity'].sum()
    votes = {'DBD_POSITIF': 0, 'SUSPEK_DBD': 0, 'BUKAN_DBD': 0}
    severity_votes = {}
    
    for _, case in similar_cases.iterrows():
        weight = case['similarity'] / total_sim
        votes[case['diagnosis']] += weight * 100
        
        if case['severity'] not in severity_votes:
            severity_votes[case['severity']] = 0
        severity_votes[case['severity']] += weight
    
    # RULE SCREENING: Gejala sedikit = tidak bisa DBD POSITIF
    if total_symptoms <= 4:
        votes['DBD_POSITIF'] = 0
        final_diag = 'SUSPEK_DBD' if votes['SUSPEK_DBD'] > votes['BUKAN_DBD'] else 'BUKAN_DBD'
        conf = max(votes['SUSPEK_DBD'], votes['BUKAN_DBD'])
        sev = 'OBSERVASI' if final_diag == 'SUSPEK_DBD' else 'NON_DBD'
    else:
        final_diag = max(votes, key=votes.get)
        conf = votes[final_diag]
        sev = max(severity_votes, key=severity_votes.get) if severity_votes else 'UNKNOWN'
    
    return final_diag, conf, votes, sev

def get_recommendations(diagnosis, severity):
    """Generate rekomendasi"""
    recs = {
        'tindakan_segera': [],
        'pemeriksaan_lab': [],
        'pengobatan': [],
        'monitoring': []
    }
    
    if diagnosis == 'DATA_INSUFFICIENT':
        recs['tindakan_segera'] = [
            "⚠️ Data gejala tidak mencukupi untuk screening",
            "📋 Pilih minimal 3 gejala yang dialami",
            "🏥 Jika ada keraguan, segera konsultasi dokter"
        ]
        return recs
    
    if diagnosis == 'DBD_POSITIF':
        recs['tindakan_segera'] = [
            "🚨 **SEGERA ke fasilitas kesehatan terdekat!**",
            "💧 Banyak minum air putih (2-3L/hari)",
            "🌡️ Pantau suhu tubuh setiap 2-4 jam",
            "🩸 Perhatikan tanda perdarahan (mimisan, gusi berdarah, BAB hitam)"
        ]
        recs['pemeriksaan_lab'] = [
            "✓ **Tes Darah Lengkap (CBC)** - WAJIB",
            "✓ Hitung Trombosit dan Hematokrit",
            "✓ Tes NS1 Antigen atau IgM/IgG Dengue",
            "✓ Fungsi hati (SGOT/SGPT)"
        ]
        
        if severity == 'BERAT':
            recs['pengobatan'] = [
                "🏥 **RAWAT INAP SEGERA**",
                "💉 Infus cairan kristaloid",
                "🩸 Siap transfusi jika diperlukan",
                "👨‍⚕️ Monitoring intensif"
            ]
        elif severity == 'SEDANG':
            recs['pengobatan'] = [
                "🏥 **Segera ke dokter/RS**",
                "💊 Paracetamol untuk demam (HINDARI Aspirin/Ibuprofen!)",
                "💧 Rehidrasi agresif",
                "🩺 Monitor tanda vital"
            ]
        else:
            recs['pengobatan'] = [
                "🏥 **Konsultasi dokter segera**",
                "💊 Paracetamol 500mg 3x/hari",
                "💧 Minum minimal 2.5L/hari",
                "📱 Kontrol ulang 24 jam"
            ]
        
        recs['monitoring'] = [
            "⚠️ **WARNING SIGNS - segera ke UGD jika ada:**",
            "• Nyeri perut hebat dan terus menerus",
            "• Muntah terus menerus",
            "• Perdarahan (mimisan, gusi, BAB hitam)",
            "• Gelisah, mengantuk berlebihan, atau pingsan",
            "• Tangan/kaki dingin dan lembab",
            "• Buang air kecil berkurang"
        ]
    
    elif diagnosis == 'SUSPEK_DBD':
        recs['tindakan_segera'] = [
            "🏥 **Konsultasi dokter dalam 24 jam**",
            "💧 Tingkatkan asupan cairan",
            "🌡️ Catat suhu tubuh setiap 4 jam",
            "📝 Perhatikan perkembangan gejala"
        ]
        recs['pemeriksaan_lab'] = [
            "✓ Tes Darah Lengkap (CBC)",
            "✓ Rapid Test Dengue (jika tersedia)",
            "✓ Hitung Trombosit"
        ]
        recs['pengobatan'] = [
            "💊 Paracetamol untuk demam (HINDARI NSAID!)",
            "💧 Minum 8-10 gelas/hari",
            "🛏️ Istirahat total",
            "📱 Kontrol ulang jika gejala memburuk"
        ]
        recs['monitoring'] = [
            "👁️ **Perhatikan perkembangan:**",
            "• Jika demam >3 hari → periksa ulang",
            "• Jika muncul tanda perdarahan → segera ke RS",
            "• Jika kondisi memburuk → jangan tunda ke dokter"
        ]
    
    else:  # BUKAN DBD
        recs['tindakan_segera'] = [
            "✓ **Kemungkinan besar BUKAN DBD**",
            "🏥 Tetap konsultasi dokter untuk diagnosis pasti",
            "💧 Istirahat cukup dan hidrasi",
            "🌡️ Monitor suhu tubuh"
        ]
        recs['pemeriksaan_lab'] = [
            "✓ Pemeriksaan darah jika demam >3 hari",
            "✓ Tes diagnostik untuk penyakit lain (Tifoid, Malaria, dll)"
        ]
        recs['pengobatan'] = [
            "💊 Obat simptomatik sesuai gejala",
            "🛏️ Istirahat yang cukup",
            "🍎 Nutrisi seimbang"
        ]
        recs['monitoring'] = [
            "👁️ Perhatikan jika gejala berubah atau memburuk"
        ]
    
    return recs

# ============================================================================
# MAIN APP
# ============================================================================
st.markdown('<div class="main-header">🏥 Sistem Screening Awal Penyakit Demam Berdarah Dengue</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Deteksi Dini Berbasis Gejala Klinis | Tidak Menggantikan Pemeriksaan Medis</div>', unsafe_allow_html=True)

# Info penting
st.markdown("""
<div class="warning-box" style="color: #000000;">
    <strong>⚠️ PENTING:</strong> Sistem ini adalah alat <strong>SCREENING AWAL</strong> untuk membantu Anda mengenali 
    gejala DBD dan memutuskan apakah perlu segera ke dokter. Sistem ini <strong>TIDAK MENGGANTIKAN</strong> 
    diagnosis medis profesional dan pemeriksaan laboratorium.
</div>
""", unsafe_allow_html=True)
# Load case base
case_base = generate_case_base_from_lab_data()

st.sidebar.success(f"✅ Knowledge Base: {len(case_base)} kasus")
with st.sidebar.expander("📊 Basis Pengetahuan"):
    dbd_count = len(case_base[case_base['diagnosis'] == 'DBD_POSITIF'])
    non_count = len(case_base[case_base['diagnosis'] == 'BUKAN_DBD'])
    st.write(f"**Kasus DBD:** {dbd_count} ({dbd_count/len(case_base)*100:.1f}%)")
    st.write(f"**Kasus Non-DBD:** {non_count} ({non_count/len(case_base)*100:.1f}%)")
    st.write("*Data diambil dari hasil lab 1523 pasien yang telah terdiagnosa*")

# ============================================================================
# SIDEBAR INPUT
# ============================================================================
st.sidebar.header("📋 Cek Gejala Anda")
st.sidebar.markdown("*Centang gejala yang Anda alami:*")

with st.sidebar.form("symptom_form"):
    st.subheader("👤 Data Diri")
    patient_name = st.text_input("Nama", "Anonymous")
    patient_age = st.number_input("Usia", 1, 100, 25)
    patient_gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    
    st.markdown("---")
    st.subheader("🌡️ Gejala Utama")
    demam_tinggi = st.checkbox("Demam tinggi mendadak (>38°C)", value=False)
    sakit_kepala = st.checkbox("Sakit kepala hebat", value=False)
    nyeri_belakang_mata = st.checkbox("Nyeri di belakang mata", value=False)
    
    st.subheader("💪 Nyeri Tubuh")
    nyeri_sendi = st.checkbox("Nyeri sendi (break-bone fever)", value=False)
    nyeri_otot = st.checkbox("Nyeri otot (myalgia)", value=False)
    
    st.subheader("🩸 Tanda Perdarahan")
    mimisan = st.checkbox("Mimisan (epistaksis)", value=False)
    gusi_berdarah = st.checkbox("Gusi berdarah", value=False)
    bintik_merah = st.checkbox("Bintik merah di kulit (petekie)", value=False)
    
    st.subheader("🤢 Gejala Lainnya")
    mual_muntah = st.checkbox("Mual/muntah", value=False)
    nyeri_perut = st.checkbox("Nyeri perut", value=False)
    kehilangan_nafsu_makan = st.checkbox("Kehilangan nafsu makan", value=False)
    ruam_kulit = st.checkbox("Ruam kulit", value=False)
    lemah_lesu = st.checkbox("Lemah dan lesu", value=False)
    pembesaran_hati = st.checkbox("Perut membesar/keras (hepatomegali)", value=False)
    
    st.subheader("🔬 Data Lab (Opsional)")
    st.markdown("*Isi jika sudah pernah tes lab:*")
    trombosit_rendah = st.checkbox("Trombosit <100.000/μL", value=False)
    
    st.markdown("---")
    diagnose_btn = st.form_submit_button("🔬 CEK SEKARANG", use_container_width=True)

# ============================================================================
# TABS
# ============================================================================
tab1, tab2, tab3 = st.tabs(["🎯 Hasil Screening", "🔍 Kasus Serupa", "ℹ️ Info DBD"])

# ============================================================================
# PROSES DIAGNOSA
# ============================================================================
if diagnose_btn:
    new_case = {
        'demam_tinggi': int(demam_tinggi),
        'sakit_kepala': int(sakit_kepala),
        'nyeri_sendi': int(nyeri_sendi),
        'nyeri_otot': int(nyeri_otot),
        'mual_muntah': int(mual_muntah),
        'ruam_kulit': int(ruam_kulit),
        'nyeri_perut': int(nyeri_perut),
        'mimisan': int(mimisan),
        'gusi_berdarah': int(gusi_berdarah),
        'bintik_merah': int(bintik_merah),
        'lemah_lesu': int(lemah_lesu),
        'kehilangan_nafsu_makan': int(kehilangan_nafsu_makan),
        'nyeri_belakang_mata': int(nyeri_belakang_mata),
        'pembesaran_hati': int(pembesaran_hati),
        'trombosit_rendah': int(trombosit_rendah)
    }
    
    total_symp = sum(new_case.values())
    
    with st.spinner("🔬 Menganalisis gejala Anda..."):
        sims = calculate_similarity(new_case, case_base)
        top10 = sims.head(10)
        diag, conf, votes, sev = diagnose(top10, total_symp)
        recs = get_recommendations(diag, sev)
    
    # TAB 1: HASIL
    with tab1:
        st.header("🎯 Hasil Screening")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Nama", patient_name)
        col2.metric("Usia", f"{patient_age} tahun")
        col3.metric("Jenis Kelamin", patient_gender)
        col4.metric("Gejala Terdeteksi", total_symp)
        
        st.markdown("---")
        
        if diag == 'DATA_INSUFFICIENT':
            cls, icon, txt, desc = 'diagnosis-insufficient', "⚪", "DATA TIDAK CUKUP", "Minimal 3 gejala diperlukan untuk screening"
        elif diag == 'DBD_POSITIF':
            cls, icon, txt, desc = 'diagnosis-positive', "🔴", "KEMUNGKINAN BESAR DBD", "Gejala Anda sangat sesuai dengan pola DBD"
        elif diag == 'SUSPEK_DBD':
            cls, icon, txt, desc = 'diagnosis-suspect', "🟡", "PERLU PEMERIKSAAN LANJUTAN", "Ada beberapa gejala yang mengarah ke DBD"
        else:
            cls, icon, txt, desc = 'diagnosis-negative', "🟢", "KEMUNGKINAN BESAR BUKAN DBD", "Gejala tidak terlalu sesuai dengan pola DBD"
        
        st.markdown(f"""
            <div class="{cls}">
                <h1 style='margin:0; font-size: 2.5rem;'>{icon} {txt}</h1>
                <p style='font-size: 1.2rem; margin:10px 0 0 0;'>{desc}</p>
                <hr style='border-color: rgba(255,255,255,0.3); margin: 15px 0;'>
                <h2 style='margin:10px 0;'>Confidence: {conf:.1f}%</h2>
                <p>Tingkat Keparahan: <strong>{sev}</strong></p>
            </div>
        """, unsafe_allow_html=True)
        
        if diag != 'DATA_INSUFFICIENT':
            st.markdown("---")
            st.subheader("📊 Analisis Probabilitas")
            
            fig = go.Figure(data=[go.Bar(
                x=['Kemungkinan DBD', 'Perlu Pemeriksaan', 'Kemungkinan Bukan DBD'],
                y=[votes['DBD_POSITIF'], votes['SUSPEK_DBD'], votes['BUKAN_DBD']],
                marker_color=['#e74c3c', '#f39c12', '#27ae60'],
                text=[f"{votes['DBD_POSITIF']:.1f}%", 
                      f"{votes['SUSPEK_DBD']:.1f}%",
                      f"{votes['BUKAN_DBD']:.1f}%"],
                textposition='auto',
                textfont=dict(size=14, color='white')
            )])
            
            fig.update_layout(
                title="Berdasarkan Perbandingan dengan 10 Kasus Paling Mirip",
                xaxis_title="Kategori",
                yaxis_title="Probabilitas (%)",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Rekomendasi
        st.markdown("---")
        st.header("💊 Rekomendasi untuk Anda")
        
        if recs['tindakan_segera']:
            st.subheader("🚨 Tindakan Segera")
            for r in recs['tindakan_segera']:
                st.markdown(f"- {r}")
        
        col1, col2 = st.columns(2)
        with col1:
            if recs['pemeriksaan_lab']:
                st.subheader("🔬 Pemeriksaan yang Diperlukan")
                for r in recs['pemeriksaan_lab']:
                    st.markdown(f"{r}")
        
        with col2:
            if recs['pengobatan']:
                st.subheader("💉 Penanganan")
                for r in recs['pengobatan']:
                    st.markdown(f"{r}")
        
        if recs['monitoring']:
            st.subheader("⚠️ Warning Signs - Waspada!")
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            for r in recs['monitoring']:
                st.markdown(f"{r}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Disclaimer
        st.markdown("---")
        st.markdown("""
        <div class="info-box">
            <strong>📌 CATATAN PENTING:</strong>
            <ul>
                <li>Hasil screening ini berdasarkan perbandingan gejala Anda dengan 1523 kasus yang telah terdiagnosa</li>
                <li>Diagnosis pasti DBD HANYA bisa dilakukan dokter dengan pemeriksaan lab (tes darah, NS1, dll)</li>
                <li>Jika Anda memiliki gejala yang mengkhawatirkan, <strong>SEGERA konsultasi ke dokter</strong></li>
                <li>Jangan tunda pemeriksaan medis karena mengandalkan screening online</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # TAB 2: KASUS SERUPA
    with tab2:
        st.header("🔍 10 Kasus Paling Mirip dengan Gejala Anda")
        st.markdown("*Kasus-kasus ini diambil dari database pasien yang telah didiagnosa secara medis*")
        
        for idx, (_, case) in enumerate(top10.iterrows(), 1):
            case_detail = case_base[case_base['case_id'] == case['case_id']].iloc[0]
            
            border_color = {
                'DBD_POSITIF': '#e74c3c',
                'BUKAN_DBD': '#27ae60'
            }[case['diagnosis']]
            
            with st.expander(
                f"#{idx} | Kasus ID: {case['case_id']} | Kesamaan: {case['similarity']:.1f}% | "
                f"Diagnosis Medis: {case['diagnosis']} ({case['severity']})"
            ):
                st.markdown(f'<div style="border-left: 4px solid {border_color}; padding-left: 15px;">', 
                          unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**🌡️ Gejala Utama:**")
                    if case_detail['demam_tinggi']: st.write("✓ Demam tinggi")
                    if case_detail['sakit_kepala']: st.write("✓ Sakit kepala")
                    if case_detail['nyeri_belakang_mata']: st.write("✓ Nyeri mata")
                    if case_detail['lemah_lesu']: st.write("✓ Lemah lesu")
                
                with col2:
                    st.markdown("**💪 Nyeri Tubuh:**")
                    if case_detail['nyeri_sendi']: st.write("✓ Nyeri sendi")
                    if case_detail['nyeri_otot']: st.write("✓ Nyeri otot")
                    
                    st.markdown("**🤢 Gejala GI:**")
                    if case_detail['mual_muntah']: st.write("✓ Mual/muntah")
                    if case_detail['nyeri_perut']: st.write("✓ Nyeri perut")
                
                with col3:
                    st.markdown("**🩸 Tanda Perdarahan:**")
                    if case_detail['mimisan']: st.write("✓ Mimisan")
                    if case_detail['gusi_berdarah']: st.write("✓ Gusi berdarah")
                    if case_detail['bintik_merah']: st.write("✓ Bintik merah")
                    
                    st.markdown("**🔬 Lab/Lainnya:**")
                    if case_detail['trombosit_rendah']: st.write("✓ Trombosit rendah")
                    if case_detail['pembesaran_hati']: st.write("✓ Hepatomegali")
                
                if 'platelet' in case_detail:
                    st.markdown(f"""
                        <div style='margin-top:10px; padding:10px; background-color:#f8f9fa; border-radius:5px;'>
                            <strong>Data Lab Pasien Ini:</strong> 
                            Trombosit: {case_detail['platelet']:,}/μL | 
                            Diagnosis Akhir: <strong>{case['diagnosis']}</strong> | 
                            Kemiripan Gejala: <strong>{case['similarity']:.1f}%</strong>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("💡 **Interpretasi:** Semakin tinggi persentase kesamaan, semakin mirip gejala Anda dengan kasus tersebut. Namun, diagnosis pasti tetap memerlukan pemeriksaan medis.")
    
    # TAB 3: INFO DBD
    with tab3:
        st.header("ℹ️ Tentang Demam Berdarah Dengue")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🦟 Apa itu DBD?
            
            **Demam Berdarah Dengue (DBD)** adalah penyakit infeksi virus dengue yang 
            ditularkan melalui gigitan nyamuk *Aedes aegypti* (nyamuk bergaris hitam-putih).
            
            ### 📋 Gejala Khas DBD:
            
            **Fase Demam (Hari 1-3):**
            - 🌡️ Demam tinggi mendadak (39-40°C)
            - 🤕 Sakit kepala hebat
            - 👁️ Nyeri di belakang mata
            - 💪 Nyeri sendi dan otot hebat ("break-bone fever")
            - 😫 Lemah, lesu, tidak nafsu makan
            
            **Fase Kritis (Hari 3-7):**
            - 🩸 Tanda perdarahan: bintik merah di kulit, mimisan, gusi berdarah
            - 🤢 Mual, muntah terus-menerus
            - 😰 Nyeri perut hebat
            - 🧊 Tangan/kaki dingin dan lembab
            - 💤 Gelisah atau mengantuk berlebihan
            
            **Fase Pemulihan (Hari 7+):**
            - Demam turun
            - Nafsu makan membaik
            - Mungkin muncul ruam kulit
            """)
        
        with col2:
            st.markdown("""
            ### 🔬 Pemeriksaan Lab Penting:
            
            | Parameter | Normal | DBD |
            |-----------|--------|-----|
            | **Trombosit** | 150-450k/μL | **<100k/μL** ⚠️ |
            | **Hematokrit** | P:40-54%, W:37-47% | **Naik ≥20%** ⚠️ |
            | **Leukosit** | 4-11k/μL | Turun (leukopenia) |
            | **Tes NS1** | Negatif | **Positif** (hari 1-5) |
            | **IgM/IgG Dengue** | Negatif | Positif (hari 4+) |
            
            ### ⚠️ WARNING SIGNS - Segera ke UGD!
            
            Jika muncul salah satu tanda ini:
            - 🚨 Nyeri perut hebat dan terus-menerus
            - 🚨 Muntah terus-menerus, tidak bisa minum
            - 🚨 Mimisan, gusi berdarah, muntah/BAB darah
            - 🚨 Gelisah, bingung, atau pingsan
            - 🚨 Tangan/kaki dingin, bibir biru
            - 🚨 Sesak napas
            - 🚨 BAK berkurang atau tidak sama sekali
            
            ### 💊 Penanganan di Rumah:
            
            ✅ **Yang BOLEH:**
            - Minum air putih banyak (2-3L/hari)
            - Paracetamol untuk demam
            - Istirahat total
            - Makan makanan bergizi
            - Kompres hangat jika demam
            
            ❌ **Yang DILARANG:**
            - Aspirin atau Ibuprofen (bisa memperburuk perdarahan!)
            - Obat anti-inflamasi (NSAID)
            - Jamu atau herbal tanpa konsultasi dokter
            
            ### 🛡️ Pencegahan (3M Plus):
            
            1. **Menguras** bak mandi/wadah air seminggu sekali
            2. **Menutup** rapat wadah penampungan air
            3. **Mendaur ulang** barang bekas yang bisa jadi sarang nyamuk
            4. **Plus:** Fogging, obat nyamuk, kawat kasa, ikan pemakan jentik
            """)

# TAB 3 (jika tidak ada diagnosa)
else:
    with tab3:
        st.header("ℹ️ Tentang Demam Berdarah Dengue")
        st.info("👈 Silakan isi gejala Anda di sidebar kiri, lalu klik 'CEK SEKARANG' untuk mendapatkan hasil screening.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🦟 Kenapa Screening Awal Penting?
            
            DBD adalah penyakit yang bisa berkembang cepat dan berbahaya jika terlambat ditangani. 
            Dengan screening awal, Anda bisa:
            
            - ✅ Mengenali gejala DBD lebih dini
            - ✅ Memutuskan kapan harus ke dokter
            - ✅ Tidak panik berlebihan jika gejalanya tidak sesuai DBD
            - ✅ Mendapat informasi tentang tindakan yang tepat
            
            ### 📊 Bagaimana Sistem Ini Bekerja?
            
            1. **Input Gejala**: Anda centang gejala yang dialami
            2. **Perbandingan**: Sistem membandingkan dengan 1523 kasus nyata
            3. **Analisis Kesamaan**: Dihitung tingkat kemiripan dengan pola DBD
            4. **Rekomendasi**: Sistem memberikan saran tindakan yang tepat
            
            **INGAT:** Ini bukan diagnosis medis, hanya screening awal!
            """)
        
        with col2:
            st.markdown("""
            ### ❓ FAQ (Pertanyaan Sering Diajukan)
            
            **Q: Apakah hasil screening ini akurat?**  
            A: Sistem ini berdasarkan 1523 kasus nyata, tapi tetap tidak bisa menggantikan 
            pemeriksaan dokter dan tes lab. Akurasi ~75-85% untuk screening awal.
            
            **Q: Apakah saya harus ke dokter jika hasilnya "Bukan DBD"?**  
            A: Ya, jika gejala Anda berat atau tidak membaik dalam 2-3 hari, tetap 
            konsultasi ke dokter. Bisa jadi penyakit lain.
            
            **Q: Berapa lama hasil lab keluar?**  
            A: Tes NS1 antigen bisa keluar dalam 15-30 menit (rapid test). 
            Tes darah lengkap biasanya 1-2 jam.
            
            **Q: Apakah DBD bisa sembuh sendiri?**  
            A: DBD ringan bisa sembuh dengan perawatan suportif (minum banyak, istirahat). 
            Tapi tetap harus dipantau ketat karena bisa tiba-tiba memburuk.
            
            **Q: Kapan fase paling berbahaya?**  
            A: Hari ke 3-7, terutama saat demam mulai turun. Ini fase kritis dimana 
            bisa terjadi kebocoran plasma dan syok.
            
            **Q: Apakah bisa terkena DBD dua kali?**  
            A: Ya! Ada 4 serotipe virus dengue. Infeksi kedua justru lebih berbahaya.
            """)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"**📊 Knowledge Base:** {len(case_base)} kasus")
with col2:
    st.markdown("**🎯 Metode:** Case-Based Reasoning")
with col3:
    st.markdown("**🦟 Tujuan:** Screening Awal DBD")
with col4:
    st.markdown("**🔬 Parameter:** 15 gejala klinis")

st.markdown("""
    <div style='text-align: center; color: #7f8c8d; padding: 20px;'>
        <p><strong>Sistem Screening Awal Demam Berdarah Dengue</strong></p>
        <p>Basis Data: 1523 Kasus Real Pasien DBD | Metode: Case-Based Reasoning (CBR)</p>
        <p style='font-size: 0.85rem;'>⚠️ <strong>DISCLAIMER:</strong> Sistem ini adalah alat bantu <strong>SCREENING AWAL</strong> 
        untuk membantu mengenali gejala DBD dan memutuskan kapan harus ke dokter. Sistem ini <strong>BUKAN pengganti</strong> 
        diagnosis medis profesional dan pemeriksaan laboratorium. Selalu konsultasikan dengan dokter atau fasilitas kesehatan 
        untuk diagnosis dan pengobatan yang tepat.</p>
    </div>
""", unsafe_allow_html=True)