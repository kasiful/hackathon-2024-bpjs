import streamlit as st
import pandas as pd
import openai
import math

# Inisiasi API Key OpenAI (ganti dengan API Key Anda)
openai.api_key = "YOUR_OPENAI_API_KEY"

st.set_page_config(layout="wide")

# Fungsi untuk mendapatkan kode ICD-10 dari API OpenAI dalam satu kueri untuk batch
def get_icd_10_bulk(data_batch):
    # Membuat prompt dengan seluruh diagnosis dan gejala
    prompt = "Berikut adalah diagnosis dan gejala dari beberapa pasien. Berikan kode ICD-10 yang sesuai untuk setiap diagnosis.\n\nData:\n"
    
    for idx, row in enumerate(data_batch, start=1):
        prompt += f"{idx}. Diagnosis: {row['Diagnosis']}, Gejala: {row['Gejala']}\n"

    prompt += "\nKeluaran yang diharapkan:\n"

    st.write("Prompt yang akan dikirim ke API OpenAI:")
    st.code(prompt)  # Menampilkan prompt dengan format code block
    
    # Mengirim prompt ke OpenAI API dalam satu kali pemanggilan
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500,
        temperature=0.5
    )

    # Mendapatkan output dari API
    hasil = response['choices'][0]['text'].strip().split("\n")

    # Ekstrak kode ICD-10 dari hasil
    icd_10_codes = [line.split(":")[1].strip() for line in hasil if "ICD-10" in line]
    return icd_10_codes

# Fungsi untuk membagi data menjadi batch
def process_in_batches(data, batch_size=50):
    num_batches = math.ceil(len(data) / batch_size)
    all_icd_10_codes = []
    
    for batch_num in range(num_batches):
        # Tentukan batas batch
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(data))
        
        # Ambil data untuk batch ini
        data_batch = data[start_idx:end_idx]
        
        # Panggil API untuk batch ini
        icd_10_codes = get_icd_10_bulk(data_batch)
        
        # Gabungkan hasil
        all_icd_10_codes.extend(icd_10_codes)
    
    return all_icd_10_codes

# Tampilan utama Streamlit
st.title("ICD-10 Coding Tool")

# Upload file Excel
uploaded_file = st.file_uploader("Upload File", type=["xlsx"])

if uploaded_file:
    # Membaca file Excel ke dalam DataFrame
    df = pd.read_excel(uploaded_file)

    # Menampilkan list kolom yang tersedia untuk pilihan
    st.subheader("List Variabel")
    id_bpjs_col = st.selectbox("ID BPJS", df.columns)
    diagnosis_col = st.selectbox("Diagnosis", df.columns)
    symptoms_col = st.selectbox("Gejala", df.columns)

    # Menampilkan data sesuai dengan kolom yang dipilih
    st.subheader("Review Data")
    selected_data = df[[id_bpjs_col, diagnosis_col, symptoms_col]].copy()
    st.dataframe(selected_data)

    # Tombol untuk melakukan coding ICD-10
    if st.button("Lakukan Coding ICD-10"):
        # Siapkan data untuk kueri dalam bentuk list of dicts
        data = selected_data.to_dict(orient="records")
        
        # Panggil API OpenAI secara batch jika lebih dari 50 baris
        icd_10_codes = process_in_batches(data)

        # Masukkan kode ICD-10 ke dalam kolom DataFrame
        selected_data['ICD-10'] = icd_10_codes

        # Tampilkan hasil dengan ICD-10 di tabel bawah
        st.subheader("Hasil Coding ICD-10")
        st.dataframe(selected_data)

        # Tombol untuk download hasil sebagai file Excel
        def convert_df_to_excel(df):
            return df.to_excel(index=False)

        st.download_button(
            label="Download",
            data=convert_df_to_excel(selected_data),
            file_name="hasil_icd_10.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
