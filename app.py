import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# KONFIGURASI APLIKASI
# ============================================================================
st.set_page_config(
    page_title="Sistem Pakar Diagnosa DBD",
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
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
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
    .symptom-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin: 10px 0;
    }
    .case-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin: 15px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin: 15px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNGSI 1: MEMBUAT CASE BASE (DATABASE KASUS)
# ============================================================================
@st.cache_data
def load_csv_case_base(file_path=None, uploaded_file=None):
    """
    Load dan preprocess dataset DBD dari CSV.
    Dataset berisi data hematologi pasien DBD.
    
    Args:
        file_path: Path ke file CSV (jika ada di local)
        uploaded_file: File yang diupload via Streamlit
    
    Returns:
        DataFrame: Case base yang sudah dipreprocess
    """
    
    # Load CSV
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    elif file_path is not None:
        df = pd.read_csv(file_path)
    else:
        st.error("Tidak ada file yang di-load!")
        return None
    
    # Mapping kolom dari dataset ke format yang kita butuhkan
    # Berdasarkan screenshot, dataset punya kolom:
    # Gender, Age, Hemoglobin(g/dl), Neutrophils(%), Lymphocytes(%), 
    # Monocytes(%), Eosinophils(%), RBC, HCT(%), MCV(fl), MCH(pg), 
    # MCHC(g/dl), RDW-CV(%), Total Platelet Count(/cumm), MPV(fl), 
    # PDW(%), PCT(%), Total WBC count(/cumm), Result (positive/negative)
    
    processed_cases = []
    
    for idx, row in df.iterrows():
        case = {}
        case['case_id'] = f'CSV_{idx+1:03d}'
        
        # === EXTRACT FEATURES DARI DATA HEMATOLOGI ===
        
        # 1. DEMAM TINGGI - asumsi semua pasien dalam dataset punya demam
        case['demam_tinggi'] = 1
        
        # 2. TROMBOSIT RENDAH (<100,000/μL = indikator kuat DBD)
        platelet = row['Total Platelet Count(/cumm)']
        case['trombosit_rendah'] = 1 if platelet < 100000 else 0
        
        # 3. HEMATOKRIT TINGGI (Hemokonsentrasi - tanda DBD)
        # Normal: Pria 40-54%, Wanita 37-47%
        hct = row['HCT(%)']
        gender = row['Gender']
        if gender.lower() == 'male':
            case['hematokrit_tinggi'] = 1 if hct > 54 else 0
        else:
            case['hematokrit_tinggi'] = 1 if hct > 47 else 0
        
        # 4. LEUKOSIT RENDAH (Leukopenia - tanda DBD)
        # Normal: 4,000-11,000/μL
        wbc = row['Total WBC count(/cumm)']
        case['leukosit_rendah'] = 1 if wbc < 4000 else 0
        
        # 5. HEMOGLOBIN (untuk severity assessment)
        hb = row['Hemoglobin(g/dl)']
        case['hemoglobin_rendah'] = 1 if hb < 12 else 0
        
        # 6. NEUTROFIL (tinggi bisa indikasi infeksi bakteri, bukan DBD)
        neutro = row['Neutrophils(%)']
        case['neutrofil_tinggi'] = 1 if neutro > 70 else 0
        
        # 7. LIMFOSIT (relatif meningkat di DBD)
        lympho = row['Lymphocytes(%)']
        case['limfosit_tinggi'] = 1 if lympho > 40 else 0
        
        # === DERIVE GEJALA KLINIS DARI DATA LAB ===
        
        # Jika trombosit sangat rendah → kemungkinan ada perdarahan
        case['bintik_merah'] = 1 if platelet < 50000 else 0
        case['mimisan'] = 1 if platelet < 30000 else 0
        case['gusi_berdarah'] = 1 if platelet < 30000 else 0
        
        # Jika HCT tinggi + platelet rendah → khas DBD
        if case['hematokrit_tinggi'] == 1 and case['trombosit_rendah'] == 1:
            case['nyeri_sendi'] = 1
            case['nyeri_otot'] = 1
            case['sakit_kepala'] = 1
            case['nyeri_belakang_mata'] = 1
        else:
            # Random dengan probabilitas rendah
            case['nyeri_sendi'] = np.random.choice([0, 1], p=[0.6, 0.4])
            case['nyeri_otot'] = np.random.choice([0, 1], p=[0.6, 0.4])
            case['sakit_kepala'] = np.random.choice([0, 1], p=[0.5, 0.5])
            case['nyeri_belakang_mata'] = np.random.choice([0, 1], p=[0.7, 0.3])
        
        # Gejala umum
        case['lemah_lesu'] = 1 if hb < 11 else np.random.choice([0, 1], p=[0.3, 0.7])
        case['mual_muntah'] = np.random.choice([0, 1], p=[0.5, 0.5])
        case['nyeri_perut'] = np.random.choice([0, 1], p=[0.6, 0.4])
        case['ruam_kulit'] = np.random.choice([0, 1], p=[0.6, 0.4])
        case['kehilangan_nafsu_makan'] = np.random.choice([0, 1], p=[0.4, 0.6])
        
        # Hepatomegali (pembesaran hati) - biasa di DBD sedang-berat
        if platelet < 50000 and hct > 45:
            case['pembesaran_hati'] = 1
        else:
            case['pembesaran_hati'] = np.random.choice([0, 1], p=[0.7, 0.3])
        
        # === DIAGNOSIS BERDASARKAN RESULT COLUMN ===
        result = row['Result'].strip().lower()
        
        if result == 'positive':
            case['diagnosis'] = 'DBD_POSITIF'
            # Tentukan severity berdasarkan nilai lab
            if platelet < 20000 or (hct > 50 and platelet < 50000):
                case['severity'] = 'BERAT'
            elif platelet < 50000 or (hct > 45 and platelet < 100000):
                case['severity'] = 'SEDANG'
            else:
                case['severity'] = 'RINGAN'
        else:
            case['diagnosis'] = 'BUKAN_DBD'
            case['severity'] = 'NON_DBD'
        
        # Simpan data lab untuk referensi
        case['platelet_count'] = platelet
        case['hematokrit'] = hct
        case['wbc_count'] = wbc
        case['hemoglobin'] = hb
        case['age'] = row['Age']
        case['gender'] = gender
        
        processed_cases.append(case)
    
    df_case_base = pd.DataFrame(processed_cases)
    
    return df_case_base

@st.cache_data
def create_medical_case_base():
    """Membuat dataset simulasi DBD untuk fallback jika tidak ada CSV."""
    symptoms = [
        'demam_tinggi', 'sakit_kepala', 'nyeri_sendi', 'nyeri_otot',
        'mual_muntah', 'ruam_kulit', 'nyeri_perut', 'mimisan',
        'gusi_berdarah', 'bintik_merah', 'lemah_lesu', 'kehilangan_nafsu_makan',
        'nyeri_belakang_mata', 'pembesaran_hati', 'trombosit_rendah'
    ]
    
    cases = []
    case_id = 1
    
    # 40 Kasus DBD Positif
    for i in range(40):
        case = {'case_id': f'DBD_{case_id:03d}'}
        case['demam_tinggi'] = 1
        case['sakit_kepala'] = np.random.choice([0, 1], p=[0.1, 0.9])
        case['nyeri_sendi'] = np.random.choice([0, 1], p=[0.2, 0.8])
        case['nyeri_otot'] = np.random.choice([0, 1], p=[0.2, 0.8])
        case['nyeri_belakang_mata'] = np.random.choice([0, 1], p=[0.3, 0.7])
        case['mimisan'] = np.random.choice([0, 1], p=[0.5, 0.5])
        case['gusi_berdarah'] = np.random.choice([0, 1], p=[0.6, 0.4])
        case['bintik_merah'] = np.random.choice([0, 1], p=[0.3, 0.7])
        case['ruam_kulit'] = np.random.choice([0, 1], p=[0.4, 0.6])
        case['mual_muntah'] = np.random.choice([0, 1], p=[0.4, 0.6])
        case['nyeri_perut'] = np.random.choice([0, 1], p=[0.5, 0.5])
        case['lemah_lesu'] = np.random.choice([0, 1], p=[0.2, 0.8])
        case['kehilangan_nafsu_makan'] = np.random.choice([0, 1], p=[0.3, 0.7])
        case['pembesaran_hati'] = np.random.choice([0, 1], p=[0.7, 0.3])
        case['trombosit_rendah'] = np.random.choice([0, 1], p=[0.2, 0.8])
        case['diagnosis'] = 'DBD_POSITIF'
        case['severity'] = np.random.choice(['RINGAN', 'SEDANG', 'BERAT'], p=[0.5, 0.35, 0.15])
        cases.append(case)
        case_id += 1
    
    # 30 Kasus Suspek
    for i in range(30):
        case = {'case_id': f'SUS_{case_id:03d}'}
        case['demam_tinggi'] = 1
        case['sakit_kepala'] = np.random.choice([0, 1], p=[0.3, 0.7])
        case['nyeri_sendi'] = np.random.choice([0, 1], p=[0.5, 0.5])
        case['nyeri_otot'] = np.random.choice([0, 1], p=[0.5, 0.5])
        case['nyeri_belakang_mata'] = np.random.choice([0, 1], p=[0.6, 0.4])
        case['mimisan'] = np.random.choice([0, 1], p=[0.9, 0.1])
        case['gusi_berdarah'] = np.random.choice([0, 1], p=[0.9, 0.1])
        case['bintik_merah'] = np.random.choice([0, 1], p=[0.8, 0.2])
        case['ruam_kulit'] = np.random.choice([0, 1], p=[0.7, 0.3])
        case['mual_muntah'] = np.random.choice([0, 1], p=[0.6, 0.4])
        case['nyeri_perut'] = np.random.choice([0, 1], p=[0.8, 0.2])
        case['lemah_lesu'] = np.random.choice([0, 1], p=[0.4, 0.6])
        case['kehilangan_nafsu_makan'] = np.random.choice([0, 1], p=[0.5, 0.5])
        case['pembesaran_hati'] = np.random.choice([0, 1], p=[0.9, 0.1])
        case['trombosit_rendah'] = np.random.choice([0, 1], p=[0.7, 0.3])
        case['diagnosis'] = 'SUSPEK_DBD'
        case['severity'] = 'OBSERVASI'
        cases.append(case)
        case_id += 1
    
    # 20 Kasus Negatif
    for i in range(20):
        case = {'case_id': f'NEG_{case_id:03d}'}
        case['demam_tinggi'] = np.random.choice([0, 1], p=[0.3, 0.7])
        case['sakit_kepala'] = np.random.choice([0, 1], p=[0.4, 0.6])
        case['nyeri_sendi'] = np.random.choice([0, 1], p=[0.7, 0.3])
        case['nyeri_otot'] = np.random.choice([0, 1], p=[0.7, 0.3])
        case['nyeri_belakang_mata'] = np.random.choice([0, 1], p=[0.8, 0.2])
        case['mimisan'] = 0
        case['gusi_berdarah'] = 0
        case['bintik_merah'] = 0
        case['ruam_kulit'] = np.random.choice([0, 1], p=[0.8, 0.2])
        case['mual_muntah'] = np.random.choice([0, 1], p=[0.5, 0.5])
        case['nyeri_perut'] = np.random.choice([0, 1], p=[0.7, 0.3])
        case['lemah_lesu'] = np.random.choice([0, 1], p=[0.4, 0.6])
        case['kehilangan_nafsu_makan'] = np.random.choice([0, 1], p=[0.6, 0.4])
        case['pembesaran_hati'] = 0
        case['trombosit_rendah'] = 0
        case['diagnosis'] = 'BUKAN_DBD'
        case['severity'] = 'NON_DBD'
        cases.append(case)
        case_id += 1
    
    return pd.DataFrame(cases)    
# ============================================================================
# FUNGSI 2: MENGHITUNG SIMILARITY (KESAMAAN KASUS)
# ============================================================================
def calculate_case_similarity_with_lab(new_case, case_base):
    """
    Menghitung similarity dengan mempertimbangkan data lab.
    
    Args:
        new_case: Dictionary berisi gejala + data lab pasien baru
        case_base: DataFrame case base
    
    Returns:
        DataFrame: Similarity scores
    """
    
    # Fitur gejala klinis
    symptom_features = [
        'demam_tinggi', 'sakit_kepala', 'nyeri_sendi', 'nyeri_otot',
        'mual_muntah', 'ruam_kulit', 'nyeri_perut', 'mimisan',
        'gusi_berdarah', 'bintik_merah', 'lemah_lesu', 'kehilangan_nafsu_makan',
        'nyeri_belakang_mata', 'pembesaran_hati', 'trombosit_rendah'
    ]
    
    # Fitur lab tambahan (jika ada)
    lab_features = ['hematokrit_tinggi', 'leukosit_rendah', 'hemoglobin_rendah']
    
    # Bobot gejala (total untuk gejala = 0.7)
    symptom_weights = {
        'demam_tinggi': 0.08,
        'trombosit_rendah': 0.10,
        'bintik_merah': 0.08,
        'mimisan': 0.07,
        'gusi_berdarah': 0.07,
        'nyeri_sendi': 0.06,
        'nyeri_otot': 0.06,
        'nyeri_belakang_mata': 0.05,
        'pembesaran_hati': 0.04,
        'sakit_kepala': 0.03,
        'ruam_kulit': 0.03,
        'nyeri_perut': 0.03,
        'mual_muntah': 0.02,
        'lemah_lesu': 0.01,
        'kehilangan_nafsu_makan': 0.01
    }
    
    # Bobot lab (total = 0.3)
    lab_weights = {
        'hematokrit_tinggi': 0.12,
        'leukosit_rendah': 0.10,
        'hemoglobin_rendah': 0.08
    }
    
    similarities = []
    
    for idx, case in case_base.iterrows():
        total_distance = 0
        matched_symptoms = 0
        
        # Hitung distance untuk gejala
        for symptom in symptom_features:
            if symptom in new_case:
                new_val = new_case[symptom]
                case_val = case[symptom]
                
                distance = abs(new_val - case_val)
                weighted_distance = distance * symptom_weights.get(symptom, 0.01)
                total_distance += weighted_distance
                
                if new_val == case_val and new_val == 1:
                    matched_symptoms += 1
        
        # Hitung distance untuk data lab (jika ada)
        for lab in lab_features:
            if lab in new_case and lab in case:
                new_val = new_case[lab]
                case_val = case[lab]
                
                distance = abs(new_val - case_val)
                weighted_distance = distance * lab_weights.get(lab, 0.01)
                total_distance += weighted_distance
        
        # Similarity score
        similarity = 1 - total_distance
        
        similarities.append({
            'case_id': case['case_id'],
            'similarity': similarity * 100,
            'matched_symptoms': matched_symptoms,
            'diagnosis': case['diagnosis'],
            'severity': case['severity'],
            'platelet': case.get('platelet_count', 0),
            'hematokrit': case.get('hematokrit', 0)
        })
    
    df_similarity = pd.DataFrame(similarities)
    return df_similarity.sort_values('similarity', ascending=False)

def calculate_case_similarity(new_case, case_base):
    """Hitung similarity tanpa data lab"""
    symptom_features = [
        'demam_tinggi', 'sakit_kepala', 'nyeri_sendi', 'nyeri_otot',
        'mual_muntah', 'ruam_kulit', 'nyeri_perut', 'mimisan',
        'gusi_berdarah', 'bintik_merah', 'lemah_lesu', 'kehilangan_nafsu_makan',
        'nyeri_belakang_mata', 'pembesaran_hati', 'trombosit_rendah'
    ]
    
    weights = {
        'demam_tinggi': 0.12, 'trombosit_rendah': 0.12, 'bintik_merah': 0.10,
        'mimisan': 0.09, 'gusi_berdarah': 0.09, 'nyeri_sendi': 0.08,
        'nyeri_otot': 0.08, 'nyeri_belakang_mata': 0.07, 'pembesaran_hati': 0.06,
        'sakit_kepala': 0.05, 'ruam_kulit': 0.04, 'nyeri_perut': 0.04,
        'mual_muntah': 0.03, 'lemah_lesu': 0.02, 'kehilangan_nafsu_makan': 0.01
    }
    
    similarities = []
    for idx, case in case_base.iterrows():
        total_distance = 0
        matched_symptoms = 0
        
        for symptom in symptom_features:
            new_val = new_case.get(symptom, 0)
            case_val = case[symptom]
            distance = abs(new_val - case_val)
            weighted_distance = distance * weights[symptom]
            total_distance += weighted_distance
            
            if new_val == case_val and new_val == 1:
                matched_symptoms += 1
        
        similarity = 1 - total_distance
        
        similarities.append({
            'case_id': case['case_id'],
            'similarity': similarity * 100,
            'matched_symptoms': matched_symptoms,
            'diagnosis': case['diagnosis'],
            'severity': case['severity']
        })
    
    return pd.DataFrame(similarities).sort_values('similarity', ascending=False)
# ============================================================================
# FUNGSI 3: RETRIEVE - AMBIL KASUS YANG PALING MIRIP
# ============================================================================
def retrieve_similar_cases(similarities_df, k=10):
    """
    Mengambil k kasus yang paling mirip dari hasil perhitungan similarity.
    
    Args:
        similarities_df (DataFrame): Hasil perhitungan similarity
        k (int): Jumlah kasus yang akan diambil
    
    Returns:
        DataFrame: Top k kasus paling mirip
    """
    return similarities_df.head(k)

# ============================================================================
# FUNGSI 4: REUSE - BUAT DIAGNOSA BERDASARKAN KASUS MIRIP
# ============================================================================
def diagnose_from_similar_cases(similar_cases):
    """
    Membuat diagnosa berdasarkan kasus-kasus yang mirip.
    Menggunakan weighted voting berdasarkan similarity score.
    
    Args:
        similar_cases (DataFrame): Kasus-kasus yang mirip
    
    Returns:
        tuple: (diagnosis, confidence, vote_distribution, severity)
    """
    
    # Hitung total similarity
    total_similarity = similar_cases['similarity'].sum()
    
    # Hitung weighted vote untuk setiap diagnosis
    diagnosis_votes = {
        'DBD_POSITIF': 0,
        'SUSPEK_DBD': 0,
        'BUKAN_DBD': 0
    }
    
    severity_votes = {}
    
    for _, case in similar_cases.iterrows():
        weight = case['similarity'] / total_similarity
        diagnosis_votes[case['diagnosis']] += weight * 100
        
        if case['severity'] not in severity_votes:
            severity_votes[case['severity']] = 0
        severity_votes[case['severity']] += weight
    
    # Tentukan diagnosis final
    final_diagnosis = max(diagnosis_votes, key=diagnosis_votes.get)
    confidence = diagnosis_votes[final_diagnosis]
    
    # Tentukan severity
    final_severity = max(severity_votes, key=severity_votes.get) if severity_votes else 'UNKNOWN'
    
    return final_diagnosis, confidence, diagnosis_votes, final_severity

# ============================================================================
# FUNGSI 5: REVISE - MEMBERIKAN REKOMENDASI MEDIS
# ============================================================================
def get_medical_recommendations(diagnosis, severity, matched_symptoms):
    """
    Memberikan rekomendasi medis berdasarkan hasil diagnosa.
    
    Args:
        diagnosis (str): Hasil diagnosa
        severity (str): Tingkat keparahan
        matched_symptoms (int): Jumlah gejala yang cocok
    
    Returns:
        dict: Rekomendasi tindakan medis
    """
    
    recommendations = {
        'tindakan_segera': [],
        'pemeriksaan_lab': [],
        'pengobatan': [],
        'monitoring': [],
        'pencegahan': []
    }
    
    if diagnosis == 'DBD_POSITIF':
        recommendations['tindakan_segera'] = [
            "🚨 SEGERA bawa pasien ke fasilitas kesehatan terdekat",
            "💧 Berikan banyak cairan oral (air putih, oralit, jus buah)",
            "🌡️ Pantau suhu tubuh setiap 2-4 jam",
            "🩸 Perhatikan tanda-tanda perdarahan (mimisan, gusi berdarah, BAB hitam)"
        ]
        
        recommendations['pemeriksaan_lab'] = [
            "✓ Hitung trombosit (setiap 4-6 jam jika <100.000/μL)",
            "✓ Hematokrit untuk deteksi hemokonsentrasi",
            "✓ Tes NS1 Antigen atau IgM/IgG Dengue",
            "✓ Fungsi hati (SGOT/SGPT)",
            "✓ Elektrolit dan fungsi ginjal"
        ]
        
        if severity == 'BERAT':
            recommendations['pengobatan'] = [
                "🏥 RAWAT INAP segera (risiko Dengue Shock Syndrome)",
                "💉 Infus kristaloid (RL atau NaCl 0.9%)",
                "🩸 Transfusi trombosit jika <20.000/μL dengan perdarahan",
                "👨‍⚕️ Monitoring ketat di ICU jika diperlukan"
            ]
        elif severity == 'SEDANG':
            recommendations['pengobatan'] = [
                "🏥 Rawat inap atau observasi 24 jam",
                "💊 Paracetamol untuk demam (HINDARI aspirin/ibuprofen)",
                "💧 Rehidrasi oral agresif 2-3 L/hari",
                "🩺 Monitor tanda vital setiap 4 jam"
            ]
        else:
            recommendations['pengobatan'] = [
                "🏠 Rawat jalan dengan kontrol ketat",
                "💊 Paracetamol 500mg 3x sehari untuk demam",
                "💧 Minum minimal 2.5 L cairan per hari",
                "📱 Kontrol ke dokter setiap hari"
            ]
        
        recommendations['monitoring'] = [
            "⚠️ WARNING SIGNS yang harus diwaspadai:",
            "• Nyeri perut hebat dan terus menerus",
            "• Muntah terus menerus",
            "• Perdarahan mukosa (hidung, gusi)",
            "• Gelisah atau letargi",
            "• Pembesaran hati >2cm",
            "• Penurunan trombosit drastis + peningkatan hematokrit"
        ]
        
    elif diagnosis == 'SUSPEK_DBD':
        recommendations['tindakan_segera'] = [
            "🏥 Kunjungi dokter/puskesmas untuk pemeriksaan lengkap",
            "💧 Tingkatkan asupan cairan",
            "🌡️ Monitor suhu tubuh",
            "📝 Catat perkembangan gejala"
        ]
        
        recommendations['pemeriksaan_lab'] = [
            "✓ Tes darah lengkap (CBC)",
            "✓ Tes NS1 Antigen atau Rapid Test Dengue",
            "✓ Hitung trombosit dan hematokrit"
        ]
        
        recommendations['pengobatan'] = [
            "💊 Paracetamol untuk demam (HINDARI NSAID)",
            "💧 Minum 8-10 gelas per hari",
            "🛏️ Istirahat total",
            "📱 Kontrol ulang 24-48 jam kemudian"
        ]
        
        recommendations['monitoring'] = [
            "👁️ Perhatikan perkembangan gejala:",
            "• Jika demam berlanjut >3 hari → periksa ulang",
            "• Jika muncul tanda perdarahan → segera ke RS",
            "• Jika kondisi memburuk → jangan tunda ke RS"
        ]
    
    else:  # BUKAN_DBD
        recommendations['tindakan_segera'] = [
            "✓ Kemungkinan besar BUKAN DBD",
            "🏥 Tetap konsultasi dengan dokter untuk diagnosa pasti",
            "💧 Istirahat cukup dan minum banyak air",
            "🌡️ Monitor suhu tubuh"
        ]
        
        recommendations['pemeriksaan_lab'] = [
            "✓ Pemeriksaan darah rutin jika demam >3 hari",
            "✓ Tes diagnostik untuk kemungkinan penyakit lain (Tifoid, Malaria, dll)"
        ]
        
        recommendations['pengobatan'] = [
            "💊 Obat simptomatik sesuai gejala",
            "🛏️ Istirahat yang cukup",
            "🍎 Nutrisi seimbang"
        ]
    
    # Pencegahan umum DBD
    recommendations['pencegahan'] = [
        "🦟 Lakukan 3M Plus:",
        "• Menguras tempat penampungan air seminggu sekali",
        "• Menutup rapat tempat penampungan air",
        "• Mendaur ulang barang bekas",
        "• Plus: Gunakan obat anti nyamuk, pasang kawat kasa, dll",
        "🏠 Fogging lingkungan jika ada kasus DBD di area tersebut",
        "👕 Gunakan pakaian tertutup saat beraktivitas"
    ]
    
    return recommendations

def add_csv_upload_section():
    """
    Menambahkan section untuk upload CSV di aplikasi.
    """
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Load Dataset CSV")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload file CSV dataset DBD",
        type=['csv'],
        help="Upload file CSV dengan format sesuai dataset hematologi DBD"
    )
    
    if uploaded_file is not None:
        try:
            case_base = load_csv_case_base(uploaded_file=uploaded_file)
            
            if case_base is not None:
                st.sidebar.success(f"✅ Berhasil load {len(case_base)} kasus dari CSV!")
                
                # Preview data
                with st.sidebar.expander("👁️ Preview Data"):
                    st.write(f"Total kasus: {len(case_base)}")
                    st.write(f"DBD Positif: {len(case_base[case_base['diagnosis']=='DBD_POSITIF'])}")
                    st.write(f"Bukan DBD: {len(case_base[case_base['diagnosis']=='BUKAN_DBD'])}")
                
                return case_base
        except Exception as e:
            st.sidebar.error(f"❌ Error loading CSV: {str(e)}")
            return None
    
    return None
# ============================================================================
# MAIN APPLICATION
# ============================================================================

# Header
st.markdown('<div class="main-header">🏥 Sistem Pakar Diagnosa Demam Berdarah Dengue</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Menggunakan Metode Case-Based Reasoning (CBR)</div>', unsafe_allow_html=True)

# Load case base
# Load case base - cek apakah ada CSV yang diupload
csv_case_base = add_csv_upload_section()

if csv_case_base is not None:
    case_base = csv_case_base
    use_lab_similarity = True
    st.info(f"📊 Menggunakan dataset dari CSV: {len(case_base)} kasus")
else:
    case_base = create_medical_case_base()
    use_lab_similarity = False
    st.info("📊 Menggunakan dataset simulasi: 90 kasus")
# ============================================================================
# SIDEBAR - INPUT GEJALA PASIEN
# ============================================================================
st.sidebar.header("📋 Input Data Pasien")
st.sidebar.markdown("Pilih gejala yang dialami pasien:")

with st.sidebar.form("symptom_form"):
    st.subheader("👤 Data Identitas")
    patient_name = st.text_input("Nama Pasien", "Anonymous")
    patient_age = st.number_input("Usia", 1, 100, 25)
    patient_gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    
    st.markdown("---")
    st.subheader("🌡️ Gejala Utama")
    
    demam_tinggi = st.checkbox("Demam tinggi (>38°C) mendadak", value=False)
    sakit_kepala = st.checkbox("Sakit kepala hebat", value=False)
    nyeri_belakang_mata = st.checkbox("Nyeri di belakang mata", value=False)
    
    st.subheader("💪 Gejala Muskuloskeletal")
    nyeri_sendi = st.checkbox("Nyeri sendi (break-bone fever)", value=False)
    nyeri_otot = st.checkbox("Nyeri otot (myalgia)", value=False)
    
    st.subheader("🩸 Tanda Perdarahan")
    mimisan = st.checkbox("Mimisan (epistaksis)", value=False)
    gusi_berdarah = st.checkbox("Gusi berdarah", value=False)
    bintik_merah = st.checkbox("Bintik merah di kulit (petekie)", value=False)
    
    st.subheader("🤢 Gejala Gastrointestinal")
    mual_muntah = st.checkbox("Mual dan muntah", value=False)
    nyeri_perut = st.checkbox("Nyeri perut", value=False)
    kehilangan_nafsu_makan = st.checkbox("Kehilangan nafsu makan", value=False)
    
    st.subheader("👁️ Gejala Lainnya")
    ruam_kulit = st.checkbox("Ruam kulit (rash)", value=False)
    lemah_lesu = st.checkbox("Lemah dan lesu", value=False)
    pembesaran_hati = st.checkbox("Pembesaran hati (hepatomegali)", value=False)
    trombosit_rendah = st.checkbox("Trombosit rendah (<100.000/μL)", value=False)
    
    st.markdown("---")
    diagnose_button = st.form_submit_button("🔬 DIAGNOSA SEKARANG", use_container_width=True)

# ============================================================================
# TABS UNTUK BERBAGAI FITUR
# ============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Hasil Diagnosa", 
    "🔍 Kasus Mirip", 
    "📊 Analisis Similarity", 
    "📚 Tentang CBR",
    "ℹ️ Informasi DBD"
])

# ============================================================================
# PROSES DIAGNOSA
# ============================================================================
if diagnose_button:
    # Buat dictionary kasus baru dari input
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
    
    # Hitung jumlah gejala
    total_symptoms = sum(new_case.values())
    
    # Proses CBR
    with st.spinner("🔬 Menganalisis gejala dan membandingkan dengan case base..."):
        # RETRIEVE: Cari kasus yang mirip
        # RETRIEVE: Cari kasus yang mirip
        if use_lab_similarity:
            similarities = calculate_case_similarity_with_lab(new_case, case_base)
        else:
            similarities = calculate_case_similarity(new_case, case_base)
        similar_cases = retrieve_similar_cases(similarities, k=10)
        
        # REUSE: Buat diagnosa dari kasus mirip
        diagnosis, confidence, vote_dist, severity = diagnose_from_similar_cases(similar_cases)
        
        # REVISE: Dapatkan rekomendasi
        recommendations = get_medical_recommendations(diagnosis, severity, total_symptoms)
    
    # ========================================================================
    # TAB 1: HASIL DIAGNOSA
    # ========================================================================
    with tab1:
        st.header("🎯 Hasil Diagnosa")
        
        # Info Pasien
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Nama", patient_name)
        col2.metric("Usia", f"{patient_age} tahun")
        col3.metric("Jenis Kelamin", patient_gender)
        col4.metric("Jumlah Gejala", total_symptoms)
        
        st.markdown("---")
        
        # Tampilkan hasil diagnosa dengan style sesuai hasil
        if diagnosis == 'DBD_POSITIF':
            diagnosis_class = 'diagnosis-positive'
            diagnosis_icon = "🔴"
            diagnosis_text = "POSITIF DBD"
            diagnosis_desc = "Pasien menunjukkan gejala yang sangat konsisten dengan Demam Berdarah Dengue"
        elif diagnosis == 'SUSPEK_DBD':
            diagnosis_class = 'diagnosis-suspect'
            diagnosis_icon = "🟡"
            diagnosis_text = "SUSPEK DBD"
            diagnosis_desc = "Pasien menunjukkan beberapa gejala DBD, perlu pemeriksaan laboratorium lanjutan"
        else:
            diagnosis_class = 'diagnosis-negative'
            diagnosis_icon = "🟢"
            diagnosis_text = "KEMUNGKINAN BUKAN DBD"
            diagnosis_desc = "Gejala yang ditunjukkan tidak konsisten dengan pola DBD"
        
        st.markdown(f"""
            <div class="{diagnosis_class}">
                <h1 style='margin:0; font-size: 2.5rem;'>{diagnosis_icon} {diagnosis_text}</h1>
                <p style='font-size: 1.2rem; margin:10px 0 0 0; opacity: 0.95;'>{diagnosis_desc}</p>
                <hr style='border-color: rgba(255,255,255,0.3); margin: 15px 0;'>
                <h2 style='margin:10px 0;'>Confidence Level: {confidence:.1f}%</h2>
                <p style='font-size: 1rem; margin:5px 0;'>Tingkat Keparahan: <strong>{severity}</strong></p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Grafik distribusi diagnosis
        st.subheader("📊 Distribusi Probabilitas Diagnosis")
        
        fig_diagnosis = go.Figure(data=[
            go.Bar(
                x=['DBD Positif', 'Suspek DBD', 'Bukan DBD'],
                y=[vote_dist['DBD_POSITIF'], vote_dist['SUSPEK_DBD'], vote_dist['BUKAN_DBD']],
                marker_color=['#e74c3c', '#f39c12', '#27ae60'],
                text=[f"{vote_dist['DBD_POSITIF']:.1f}%", 
                      f"{vote_dist['SUSPEK_DBD']:.1f}%",
                      f"{vote_dist['BUKAN_DBD']:.1f}%"],
                textposition='auto',
                textfont=dict(size=14, color='white')
            )
        ])
        
        fig_diagnosis.update_layout(
            title="Voting dari 10 Kasus Paling Mirip",
            xaxis_title="Kategori Diagnosis",
            yaxis_title="Probabilitas (%)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_diagnosis, use_container_width=True)
        
        # Rekomendasi Medis
        st.markdown("---")
        st.header("💊 Rekomendasi Tindakan Medis")
        
        # Tindakan Segera
        if recommendations['tindakan_segera']:
            st.subheader("🚨 Tindakan Segera")
            for action in recommendations['tindakan_segera']:
                st.markdown(f"- {action}")
        
        col1, col2 = st.columns(2)
        
        # Pemeriksaan Lab
        with col1:
            if recommendations['pemeriksaan_lab']:
                st.subheader("🔬 Pemeriksaan Laboratorium")
                for lab in recommendations['pemeriksaan_lab']:
                    st.markdown(f"{lab}")
        
        # Pengobatan
        with col2:
            if recommendations['pengobatan']:
                st.subheader("💉 Pengobatan")
                for treatment in recommendations['pengobatan']:
                    st.markdown(f"{treatment}")
        
        # Monitoring
        if recommendations['monitoring']:
            st.subheader("⚠️ Monitoring & Warning Signs")
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            for monitor in recommendations['monitoring']:
                st.markdown(f"{monitor}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Pencegahan
        if recommendations['pencegahan']:
            st.subheader("🛡️ Pencegahan")
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            for prevent in recommendations['pencegahan']:
                st.markdown(f"{prevent}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ========================================================================
    # TAB 2: KASUS MIRIP
    # ========================================================================
    with tab2:
        st.header("🔍 Kasus Historis yang Paling Mirip")
        st.markdown(f"Menampilkan **10 kasus paling mirip** dari **{len(case_base)} kasus** dalam database")
        
        for idx, (_, case) in enumerate(similar_cases.iterrows(), 1):
            # Ambil detail kasus dari case base
            case_detail = case_base[case_base['case_id'] == case['case_id']].iloc[0]
            
            # Tentukan warna border berdasarkan diagnosis
            border_color = {
                'DBD_POSITIF': '#e74c3c',
                'SUSPEK_DBD': '#f39c12',
                'BUKAN_DBD': '#27ae60'
            }[case['diagnosis']]
            
            with st.expander(
                f"#{idx} | ID: {case['case_id']} | Similarity: {case['similarity']:.2f}% | "
                f"Diagnosis: {case['diagnosis']} | Matched: {case['matched_symptoms']} gejala"
            ):
                st.markdown(f'<div style="border-left: 4px solid {border_color}; padding-left: 15px;">', 
                          unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**🌡️ Gejala Utama:**")
                    if case_detail['demam_tinggi']: st.write("✓ Demam tinggi")
                    if case_detail['sakit_kepala']: st.write("✓ Sakit kepala")
                    if case_detail['nyeri_belakang_mata']: st.write("✓ Nyeri belakang mata")
                    if case_detail['lemah_lesu']: st.write("✓ Lemah lesu")
                
                with col2:
                    st.markdown("**💪 Gejala Muskuloskeletal:**")
                    if case_detail['nyeri_sendi']: st.write("✓ Nyeri sendi")
                    if case_detail['nyeri_otot']: st.write("✓ Nyeri otot")
                    
                    st.markdown("**🤢 Gejala GI:**")
                    if case_detail['mual_muntah']: st.write("✓ Mual/muntah")
                    if case_detail['nyeri_perut']: st.write("✓ Nyeri perut")
                    if case_detail['kehilangan_nafsu_makan']: st.write("✓ Hilang nafsu makan")
                
                with col3:
                    st.markdown("**🩸 Tanda Perdarahan:**")
                    if case_detail['mimisan']: st.write("✓ Mimisan")
                    if case_detail['gusi_berdarah']: st.write("✓ Gusi berdarah")
                    if case_detail['bintik_merah']: st.write("✓ Bintik merah")
                    
                    st.markdown("**🔬 Tanda Lain:**")
                    if case_detail['ruam_kulit']: st.write("✓ Ruam kulit")
                    if case_detail['pembesaran_hati']: st.write("✓ Hepatomegali")
                    if case_detail['trombosit_rendah']: st.write("✓ Trombosit rendah")
                
                st.markdown(f"""
                    <div style='margin-top:10px; padding:10px; background-color:#f8f9fa; border-radius:5px;'>
                        <strong>Diagnosis:</strong> {case['diagnosis']} | 
                        <strong>Severity:</strong> {case['severity']} | 
                        <strong>Similarity Score:</strong> {case['similarity']:.2f}%
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # ========================================================================
    # TAB 3: ANALISIS SIMILARITY
    # ========================================================================
    with tab3:
        st.header("📊 Analisis Kesamaan Kasus")
        
        # Scatter plot similarity
        st.subheader("Distribusi Similarity Score")
        
        fig_scatter = px.scatter(
            similarities.head(30),
            x=range(30),
            y='similarity',
            color='diagnosis',
            size='similarity',
            hover_data=['case_id', 'matched_symptoms'],
            title='Top 30 Kasus dengan Similarity Tertinggi',
            labels={'x': 'Ranking', 'similarity': 'Similarity Score (%)'},
            color_discrete_map={
                'DBD_POSITIF': '#e74c3c',
                'SUSPEK_DBD': '#f39c12',
                'BUKAN_DBD': '#27ae60'
            }
        )
        
        fig_scatter.update_layout(height=450)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Statistik similarity
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Similarity Tertinggi",
                f"{similarities.iloc[0]['similarity']:.2f}%",
                delta=f"{similarities.iloc[0]['matched_symptoms']} gejala cocok"
            )
        
        with col2:
            avg_similarity = similar_cases['similarity'].mean()
            st.metric(
                "Rata-rata Similarity (Top 10)",
                f"{avg_similarity:.2f}%"
            )
        
        with col3:
            total_matched = similar_cases['matched_symptoms'].sum()
            st.metric(
                "Total Gejala Cocok (Top 10)",
                f"{total_matched} gejala"
            )
        
        # Gejala yang diinput
        st.markdown("---")
        st.subheader("📋 Gejala yang Diinputkan")
        
        active_symptoms = [k.replace('_', ' ').title() for k, v in new_case.items() if v == 1]
        
        if active_symptoms:
            cols = st.columns(3)
            for i, symptom in enumerate(active_symptoms):
                cols[i % 3].markdown(f"✓ {symptom}")
        else:
            st.warning("Tidak ada gejala yang dipilih")

# ========================================================================
# TAB 4: TENTANG CBR
# ========================================================================
with tab4:
    st.header("📚 Tentang Case-Based Reasoning (CBR)")
    
    st.markdown("""
    ### Apa itu Case-Based Reasoning?
    
    **Case-Based Reasoning (CBR)** adalah metode pemecahan masalah dalam kecerdasan buatan yang 
    menyelesaikan masalah baru dengan menggunakan pengalaman dari kasus-kasus serupa yang pernah 
    terjadi sebelumnya.
    
    ### 🔄 Siklus CBR dalam Sistem Ini:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 1️⃣ RETRIEVE (Pencarian)
        - Mencari kasus-kasus dari database yang paling mirip dengan gejala pasien
        - Menggunakan **Weighted Euclidean Distance**
        - Mempertimbangkan 15 gejala klinis dengan bobot berbeda
        - Mengurutkan berdasarkan similarity score
        
        #### 2️⃣ REUSE (Penggunaan Ulang)
        - Mengambil 10 kasus paling mirip
        - Melakukan **weighted voting** berdasarkan similarity
        - Menghitung probabilitas untuk setiap diagnosis
        - Menentukan diagnosis dengan confidence level
        """)
    
    with col2:
        st.markdown("""
        #### 3️⃣ REVISE (Revisi)
        - Menyesuaikan diagnosis dengan konteks spesifik
        - Menentukan tingkat keparahan (severity)
        - Memberikan rekomendasi medis yang tepat
        - Menyediakan warning signs untuk monitoring
        
        #### 4️⃣ RETAIN (Penyimpanan)
        - Menyimpan kasus baru ke case base
        - Meningkatkan akurasi sistem dari waktu ke waktu
        - Database terus berkembang dengan kasus baru
        """)
    
    st.markdown("---")
    st.subheader("⚖️ Bobot Gejala dalam Perhitungan Similarity")
    
    weights_data = {
        'Gejala': [
            'Demam Tinggi', 'Trombosit Rendah', 'Bintik Merah (Petekie)',
            'Mimisan', 'Gusi Berdarah', 'Nyeri Sendi', 'Nyeri Otot',
            'Nyeri Belakang Mata', 'Pembesaran Hati', 'Sakit Kepala',
            'Ruam Kulit', 'Nyeri Perut', 'Mual/Muntah', 'Lemah Lesu',
            'Kehilangan Nafsu Makan'
        ],
        'Bobot': [0.12, 0.12, 0.10, 0.09, 0.09, 0.08, 0.08, 0.07, 0.06, 
                  0.05, 0.04, 0.04, 0.03, 0.02, 0.01],
        'Keterangan': [
            'Gejala utama DBD', 'Indikator lab penting', 'Tanda perdarahan khas',
            'Tanda perdarahan', 'Tanda perdarahan', 'Break-bone fever',
            'Myalgia', 'Gejala khas DBD', 'Hepatomegali', 'Gejala umum',
            'Rash', 'Warning sign', 'Gejala GI', 'Gejala umum', 'Gejala umum'
        ]
    }
    
    df_weights = pd.DataFrame(weights_data)
    
    fig_weights = px.bar(
        df_weights,
        x='Gejala',
        y='Bobot',
        color='Bobot',
        color_continuous_scale='Reds',
        title='Distribusi Bobot untuk Setiap Gejala',
        hover_data=['Keterangan']
    )
    
    fig_weights.update_layout(height=500, xaxis_tickangle=-45)
    st.plotly_chart(fig_weights, use_container_width=True)
    
    st.markdown("""
    ### 🎯 Keunggulan Sistem CBR untuk Diagnosa DBD:
    
    - ✅ **Berbasis Pengalaman**: Menggunakan 90 kasus historis dengan pola gejala yang beragam
    - ✅ **Interpretable**: Dapat melihat kasus-kasus yang menjadi dasar diagnosa
    - ✅ **Adaptive**: Case base dapat terus diperbarui dengan kasus baru
    - ✅ **Context-Aware**: Mempertimbangkan kombinasi gejala dan tingkat keparahan
    - ✅ **Transparent**: Menampilkan similarity score dan reasoning process
    - ✅ **Weighted**: Gejala yang lebih spesifik diberi bobot lebih tinggi
    
    ### ⚠️ Disclaimer:
    
    Sistem ini adalah **alat bantu keputusan** untuk tenaga medis dan **BUKAN pengganti**:
    - Penilaian klinis dokter
    - Pemeriksaan fisik langsung
    - Pemeriksaan laboratorium
    - Pencitraan medis
    
    Selalu konsultasikan dengan dokter atau fasilitas kesehatan untuk diagnosa dan pengobatan yang tepat.
    """)

# ========================================================================
# TAB 5: INFORMASI DBD
# ========================================================================
with tab5:
    st.header("ℹ️ Informasi Demam Berdarah Dengue (DBD)")
    
    st.markdown("""
    ### 🦟 Apa itu Demam Berdarah Dengue?
    
    **Demam Berdarah Dengue (DBD)** atau Dengue Hemorrhagic Fever adalah penyakit infeksi yang 
    disebabkan oleh virus dengue dan ditularkan melalui gigitan nyamuk *Aedes aegypti* dan 
    *Aedes albopictus*.
    
    ### 📋 Gejala Klinis DBD
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### Gejala Utama:
        - 🌡️ **Demam tinggi mendadak** (39-40°C) selama 2-7 hari
        - 🤕 **Sakit kepala hebat**
        - 👁️ **Nyeri di belakang mata**
        - 💪 **Nyeri sendi dan otot** (break-bone fever)
        - 😫 **Lemah dan lesu**
        
        #### Tanda Perdarahan:
        - 🩸 **Mimisan** (epistaksis)
        - 🩸 **Gusi berdarah**
        - 🔴 **Bintik merah** di kulit (petekie)
        - 🩸 **Muntah darah**
        - 🩸 **BAB hitam** (melena)
        """)
    
    with col2:
        st.markdown("""
        #### Warning Signs (Tanda Bahaya):
        - ⚠️ **Nyeri perut hebat** dan terus menerus
        - ⚠️ **Muntah terus menerus**
        - ⚠️ **Perdarahan mukosa**
        - ⚠️ **Gelisah atau letargi**
        - ⚠️ **Pembesaran hati** >2cm
        - ⚠️ **Penurunan trombosit** + peningkatan hematokrit
        
        #### Gejala Lain:
        - 🤢 Mual dan muntah
        - 🍽️ Kehilangan nafsu makan
        - 🟥 Ruam kulit (muncul hari ke 3-5)
        """)
    
    st.markdown("---")
    st.subheader("🔬 Pemeriksaan Laboratorium")
    
    st.markdown("""
    | Parameter | Nilai Normal | Indikasi DBD |
    |-----------|--------------|--------------|
    | **Trombosit** | 150.000 - 450.000/μL | **< 100.000/μL** |
    | **Hematokrit** | Pria: 40-54%, Wanita: 37-47% | **Meningkat ≥20%** |
    | **Leukosit** | 4.000 - 11.000/μL | Menurun (leukopenia) |
    | **NS1 Antigen** | Negatif | **Positif (hari 1-5)** |
    | **IgM Dengue** | Negatif | **Positif (hari 4-5 dst)** |
    | **IgG Dengue** | Negatif | Positif (infeksi sekunder) |
    """)
    
    st.markdown("---")
    st.subheader("🏥 Klasifikasi WHO untuk DBD")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### Dengue Fever (DF):
        - Demam akut 2-7 hari
        - Minimal 2 gejala: sakit kepala, nyeri retro-orbital, nyeri otot/sendi, ruam
        - Tidak ada tanda perdarahan spontan
        """)
        
        st.markdown("""
        #### Dengue Hemorrhagic Fever (DHF):
        **Kriteria WHO:**
        1. Demam tinggi 2-7 hari
        2. Manifestasi perdarahan
        3. Trombositopenia (≤100.000/μL)
        4. Hemokonsentrasi (Ht ↑ ≥20%)
        """)
    
    with col2:
        st.markdown("""
        #### Grading DHF:
        - **Grade I**: Demam + manifestasi perdarahan (uji tourniquet +)
        - **Grade II**: Grade I + perdarahan spontan
        - **Grade III**: Kegagalan sirkulasi (nadi lemah, hipotensi)
        - **Grade IV**: Syok berat (DSS - Dengue Shock Syndrome)
        """)
        
        st.markdown("""
        #### Dengue Shock Syndrome (DSS):
        - DHF Grade III atau IV
        - Tekanan nadi ≤20 mmHg
        - Hipotensi
        - Kulit dingin, lembab
        - Gelisah
        """)
    
    st.markdown("---")
    st.subheader("💊 Penatalaksanaan DBD")
    
    st.markdown("""
    #### Terapi Suportif:
    - **Hidrasi**: Cairan oral 2-3 L/hari atau IV jika diperlukan
    - **Antipiretik**: Paracetamol (HINDARI Aspirin/NSAID)
    - **Monitoring ketat**: Tanda vital, trombosit, hematokrit
    - **Tirah baring**: Istirahat total
    
    #### Indikasi Rawat Inap:
    - Trombosit <100.000/μL dengan gejala perdarahan
    - Hematokrit meningkat ≥20%
    - Tanda warning signs
    - Muntah terus menerus
    - Tidak bisa makan/minum
    - Kondisi memburuk
    
    #### Indikasi Transfusi:
    - **Trombosit**: Jika <20.000/μL dengan perdarahan aktif
    - **PRC**: Jika Hb turun drastis dengan perdarahan masif
    - **FFP**: Jika ada koagulopati
    """)
    
    st.markdown("---")
    st.subheader("🛡️ Pencegahan DBD (3M Plus)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 3M:
        1. **Menguras**
           - Bak mandi
           - Tempat penampungan air
           - Seminggu sekali
        
        2. **Menutup**
           - Tempat penampungan air
           - Rapat-rapat
        """)
    
    with col2:
        st.markdown("""
        3. **Mendaur ulang**
           - Barang bekas
           - Wadah yang bisa menampung air
           - Hindari genangan air
        """)
    
    with col3:
        st.markdown("""
        #### Plus:
        - Fogging/pengasapan
        - Obat anti nyamuk
        - Kawat kasa
        - Ikan pemakan jentik
        - Tanaman anti nyamuk
        - Pakaian tertutup
        """)

# ========================================================================
# FOOTER
# ========================================================================
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**📊 Case Base:** 90 kasus")
with col2:
    st.markdown("**🎯 Metode:** CBR")
with col3:
    st.markdown("**🦟 Domain:** Diagnosa DBD")
with col4:
    st.markdown("**🔬 Gejala:** 15 parameter")

st.markdown("""
    <div style='text-align: center; color: #7f8c8d; padding: 20px;'>
        <p><strong>Sistem Pakar Diagnosa Demam Berdarah Dengue</strong></p>
        <p>Menggunakan Metode Case-Based Reasoning | © 2024</p>
        <p style='font-size: 0.85rem;'>⚠️ Disclaimer: Sistem ini adalah alat bantu dan bukan pengganti konsultasi medis profesional</p>
    </div>
""", unsafe_allow_html=True)