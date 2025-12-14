"""
STEP 1: CSV TO JSON CONVERTER
Jalankan file ini SEKALI untuk convert dataset CSV ke format JSON.
Copy hasil JSON ke sistem pakar utama.
"""

import pandas as pd
import json
import numpy as np

def convert_csv_to_embedded_json(csv_path):
    """Convert CSV dataset ke format JSON yang bisa di-embed"""
    
    print("🔄 Loading CSV dataset...")
    df = pd.read_csv(csv_path)
    
    print(f"📊 Total data: {len(df)} kasus")
    print(f"   - DBD Positif: {len(df[df['Result'].str.lower().str.strip() == 'positive'])}")
    print(f"   - Bukan DBD: {len(df[df['Result'].str.lower().str.strip() == 'negative'])}")
    
    cases = []
    
    for idx, row in df.iterrows():
        # Data lab
        platelet = row['Total Platelet Count(/cumm)']
        hct = row['HCT(%)']
        gender = row['Gender'].strip().lower()
        wbc = row['Total WBC count(/cumm)']
        hb = row['Hemoglobin(g/dl)']
        age = row['Age']
        
        result = row['Result'].strip().lower()
        is_dbd = (result == 'positive')
        
        case = {
            'case_id': f'CSV_{idx+1:04d}',
            'diagnosis': 'DBD_POSITIF' if is_dbd else 'BUKAN_DBD',
            'age': int(age),
            'gender': gender,
            'platelet': int(platelet),
            'hematokrit': float(hct),
            'wbc': int(wbc),
            'hemoglobin': float(hb)
        }
        
        # Generate gejala berdasarkan data lab (DETERMINISTIK)
        if is_dbd:
            case['demam_tinggi'] = 1
            case['sakit_kepala'] = 1
            case['nyeri_sendi'] = 1
            case['nyeri_otot'] = 1
            case['lemah_lesu'] = 1
            case['kehilangan_nafsu_makan'] = 1
            
            # Gejala berdasarkan severity
            if platelet < 50000:
                case['bintik_merah'] = 1
                case['mimisan'] = 1 if platelet < 30000 else 0
                case['gusi_berdarah'] = 1 if platelet < 30000 else 0
                case['nyeri_belakang_mata'] = 1
                case['pembesaran_hati'] = 1 if hct > 45 else 0
                case['mual_muntah'] = 1
                case['nyeri_perut'] = 1
                case['ruam_kulit'] = 1
                case['trombosit_rendah'] = 1
                case['severity'] = 'BERAT' if platelet < 20000 else 'SEDANG'
            elif platelet < 100000:
                case['bintik_merah'] = 1
                case['mimisan'] = 0
                case['gusi_berdarah'] = 0
                case['nyeri_belakang_mata'] = 1
                case['pembesaran_hati'] = 0
                case['mual_muntah'] = 1 if platelet < 70000 else 0
                case['nyeri_perut'] = 0
                case['ruam_kulit'] = 1
                case['trombosit_rendah'] = 1
                case['severity'] = 'SEDANG' if platelet < 70000 else 'RINGAN'
            else:
                case['bintik_merah'] = 0
                case['mimisan'] = 0
                case['gusi_berdarah'] = 0
                case['nyeri_belakang_mata'] = 1
                case['pembesaran_hati'] = 0
                case['mual_muntah'] = 0
                case['nyeri_perut'] = 0
                case['ruam_kulit'] = 0
                case['trombosit_rendah'] = 0
                case['severity'] = 'RINGAN'
                
        else:  # BUKAN DBD
            case['demam_tinggi'] = 1 if wbc < 5000 else 0
            case['sakit_kepala'] = 1 if hb < 12 else 0
            case['nyeri_sendi'] = 1 if wbc < 5000 else 0
            case['nyeri_otot'] = 1 if wbc < 5000 else 0
            case['lemah_lesu'] = 1 if hb < 11 else 0
            case['kehilangan_nafsu_makan'] = 1 if hb < 10 else 0
            case['bintik_merah'] = 0
            case['mimisan'] = 0
            case['gusi_berdarah'] = 0
            case['nyeri_belakang_mata'] = 0
            case['pembesaran_hati'] = 0
            case['mual_muntah'] = 0
            case['nyeri_perut'] = 0
            case['ruam_kulit'] = 0
            case['trombosit_rendah'] = 0
            case['severity'] = 'NON_DBD'
        
        cases.append(case)
        
        if (idx + 1) % 100 == 0:
            print(f"   Processed: {idx + 1}/{len(df)} kasus...")
    
    print(f"\n✅ Conversion completed!")
    print(f"📝 Total cases converted: {len(cases)}")
    
    return cases

def save_to_json(cases, output_file='case_base.json'):
    """Save cases to JSON file"""
    with open(output_file, 'w') as f:
        json.dump(cases, f, indent=2)
    print(f"\n💾 Saved to: {output_file}")
    print(f"📦 File size: {len(json.dumps(cases)) / 1024:.2f} KB")

def generate_python_code(cases, output_file='case_base_embedded.py'):
    """Generate Python code with embedded data"""
    
    # Split into chunks untuk readability
    chunk_size = 100
    chunks = [cases[i:i + chunk_size] for i in range(0, len(cases), chunk_size)]
    
    code = "# Auto-generated case base\n"
    code += "# Total cases: {}\n\n".format(len(cases))
    code += "def get_case_base():\n"
    code += "    \"\"\"Return embedded case base\"\"\"\n"
    code += "    cases = [\n"
    
    for case in cases:
        code += "        " + str(case) + ",\n"
    
    code += "    ]\n"
    code += "    return cases\n"
    
    with open(output_file, 'w') as f:
        f.write(code)
    
    print(f"\n🐍 Python code saved to: {output_file}")
    print(f"📦 Code size: {len(code) / 1024:.2f} KB")

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    print("="*70)
    print("DENGUE DATASET CONVERTER - CSV TO EMBEDDED FORMAT")
    print("="*70)
    
    # Path ke CSV Anda
    csv_file = "Dengue Fever Hematological Dataset.csv"
    
    try:
        # Convert
        cases = convert_csv_to_embedded_json(csv_file)
        
        # Save ke JSON
        save_to_json(cases, 'case_base.json')
        
        # Generate Python code
        generate_python_code(cases, 'case_base_embedded.py')
        
        print("\n" + "="*70)
        print("✅ CONVERSION SUCCESSFUL!")
        print("="*70)
        print("\nNext steps:")
        print("1. Open 'case_base_embedded.py'")
        print("2. Copy fungsi get_case_base()")
        print("3. Paste ke sistem pakar utama")
        print("\nOr use 'case_base.json' untuk load dinamis")
        
    except FileNotFoundError:
        print(f"\n❌ ERROR: File '{csv_file}' tidak ditemukan!")
        print("Pastikan file CSV ada di folder yang sama dengan script ini.")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")