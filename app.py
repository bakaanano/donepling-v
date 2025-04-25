import streamlit as st
import os
import pdfplumber
import pandas as pd

# Fungsi ekstrak teks dari PDF
def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

st.title("🔍 Screening CV PDF Otomatis")

uploaded_files = st.file_uploader("Upload file PDF CV (bisa lebih dari satu)", accept_multiple_files=True, type='pdf')

if uploaded_files:
    keywords = st.text_input("Masukkan keyword pencarian (pisahkan dengan koma):", "python, UI/UX, data")
    if st.button("Mulai Screening"):
        result = []
        with st.spinner("🔄 Memproses CV..."):
            for file in uploaded_files:
                text = extract_text_from_pdf(file)
                result.append({'filename': file.name, 'text': text})

        df = pd.DataFrame(result)

        # Keyword search
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        df['match'] = df['text'].str.lower().apply(lambda x: any(k in x for k in keyword_list))
        matching_df = df[df['match']]

        st.success(f"✅ Ditemukan {len(matching_df)} CV yang cocok!")
        st.dataframe(matching_df[['filename']])
        csv = matching_df[['filename', 'text']].to_csv(index=False)
        st.download_button("📥 Download Hasil (CSV)", csv, file_name="hasil_screening.csv", mime='text/csv')
