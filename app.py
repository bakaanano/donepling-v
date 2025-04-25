import streamlit as st
import os
import pdfplumber
import pandas as pd
import requests
import re

# Fungsi ekstrak teks dari PDF
def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Fungsi ekstrak file ID dari Google Drive link
def extract_drive_id(link):
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", link)
    return match.group(1) if match else None

st.title("🔍 Screening CV Otomatis (PDF dari Spreadsheet + Upload Manual)")

option = st.radio("Pilih sumber CV:", ["Upload Manual", "Ambil dari Spreadsheet Google Drive"])
result = []

if option == "Upload Manual":
    uploaded_files = st.file_uploader("Upload file PDF CV (bisa lebih dari satu)", accept_multiple_files=True, type='pdf')
    if uploaded_files:
        keywords = st.text_input("Masukkan keyword pencarian (pisahkan dengan koma):", "python, UI/UX, data")
        if st.button("Mulai Screening"):
            with st.spinner("🔄 Memproses CV..."):
                for file in uploaded_files:
                    text = extract_text_from_pdf(file)
                    result.append({'filename': file.name, 'text': text})

elif option == "Ambil dari Spreadsheet Google Drive":
    excel_file = st.file_uploader("Upload spreadsheet (.xlsx) yang berisi link Google Drive PDF", type='xlsx')
    if excel_file:
        keywords = st.text_input("Masukkan keyword pencarian (pisahkan dengan koma):", "python, UI/UX, data")
        if st.button("Mulai Screening"):
            with st.spinner("🔄 Mengunduh dan memproses CV..."):
                os.makedirs("downloaded_pdfs", exist_ok=True)
                df_sheet = pd.read_excel(excel_file, dtype=str)  # Baca semua sebagai string biar aman

                for index, row in df_sheet.iterrows():
                    name = f"CV_{index+1}"  # Nama file default: CV_1, CV_2, dst
                    link = row[9]  # Ambil dari kolom ke-9 (kolom I)

                    if pd.isna(link):
                        st.warning(f"⚠️ Tidak ada link pada baris {index+2}")
                        continue

                    file_id = extract_drive_id(link)

                    if not file_id:
                        st.warning(f"❌ Link tidak valid pada baris {index+2}")
                        continue

                    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    file_path = f"downloaded_pdfs/{name}.pdf"

                    try:
                        r = requests.get(download_url)
                        r.raise_for_status()  # Biar kalau gagal download langsung error
                        with open(file_path, "wb") as f:
                            f.write(r.content)

                        text = extract_text_from_pdf(file_path)
                        result.append({'filename': f"{name}.pdf", 'text': text})
                    except Exception as e:
                        st.error(f"❌ Gagal memproses {name}: {e}")

# Screening dan hasil
if result:
    df_result = pd.DataFrame(result)
    keyword_list = [k.strip().lower() for k in keywords.split(",")]
    df_result['match'] = df_result['text'].str.lower().apply(lambda x: any(k in x for k in keyword_list))
    matching_df = df_result[df_result['match']]

    st.success(f"✅ Ditemukan {len(matching_df)} CV yang cocok!")
    st.dataframe(matching_df[['filename']])
    csv = matching_df[['filename', 'text']].to_csv(index=False)
    st.download_button("📥 Download Hasil (CSV)", csv, file_name="hasil_screening.csv", mime='text/csv')
