import streamlit as st
import pandas as pd

# Upload clean_sampah_metadata_updated.parquet ke Google Drive
# 1. Go ke https://drive.google.com
# 2. Upload file .parquet
# 3. Right-click → Share → Siapa saja dengan link
# 4. Copy ID dari URL: https://drive.google.com/file/d/[ID_INI]/view
# 5. Ganti FILE_ID di bawah ini

FILE_ID = "YOUR_GOOGLE_DRIVE_FILE_ID"
URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

@st.cache_data(show_spinner=False)
def load_dataset_from_cloud() -> pd.DataFrame:
    try:
        df = pd.read_parquet(URL)
        return df
    except:
        st.error("Data not found. Check Google Drive FILE_ID in code.")
        return None

# Usage: df = load_dataset_from_cloud()
