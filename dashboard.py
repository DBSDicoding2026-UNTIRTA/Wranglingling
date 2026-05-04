import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sns.set_theme(style="whitegrid")

DATASET_CANDIDATES = ["main_data.csv", "clean_sampah_metadata.csv"]
DATE_KEYWORDS = ("date", "tanggal", "time", "waktu")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def slugify_category(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value.lower()).strip("_")


def find_dataset_path() -> Path | None:
    for filename in DATASET_CANDIDATES:
        candidate = Path(filename)
        if candidate.exists():
            return candidate
    return None


@st.cache_data(show_spinner=False)
def load_dataset(path_str: str) -> pd.DataFrame:
    return pd.read_csv(path_str)


def find_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def find_dataset_image_root() -> Path | None:
    local_candidates = [
        Path("clean_images"),
        Path("sampah-daur-ulang"),
        Path("dataset"),
        Path("data"),
        Path.home() / ".cache" / "kagglehub" / "datasets" / "fathurrahmanalfarizy" / "sampah-daur-ulang" / "versions" / "5" / "DATASETS",
    ]

    for candidate in local_candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    kaggle_cache_root = Path.home() / ".cache" / "kagglehub" / "datasets"
    if kaggle_cache_root.exists():
        matches = sorted(
            kaggle_cache_root.glob("**/sampah-daur-ulang/versions/*/DATASETS"),
            reverse=True,
        )
        for match in matches:
            if match.is_dir():
                return match

    return None


def find_category_sample_image(category: str, image_root: Path | None) -> Path | None:
    if image_root is None:
        return None

    candidate_dirs = [image_root / category]
    slug = slugify_category(category)
    if slug and slug != category:
        candidate_dirs.append(image_root / slug)

    for class_dir in candidate_dirs:
        if not class_dir.exists() or not class_dir.is_dir():
            continue

        for image_path in sorted(class_dir.rglob("*")):
            if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS:
                return image_path

    return None


def preprocess_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    data = df.copy()

    rename_map = {
        "class_label": "kategori",
        "file_name": "nama_file",
        "file_ext": "ekstensi_file",
        "file_size_kb": "ukuran_file_kb",
        "aspect_ratio": "rasio_aspek",
        "pixels": "jumlah_piksel",
        "color_mode": "mode_warna",
        "file_path": "lokasi_file",
        "width": "lebar",
        "height": "tinggi",
    }
    data = data.rename(columns={k: v for k, v in rename_map.items() if k in data.columns})

    # Remove file path column for privacy / display reasons
    if "lokasi_file" in data.columns:
        data = data.drop(columns=["lokasi_file"])

    date_cols: list[str] = []
    for col in data.columns:
        if any(keyword in col.lower() for keyword in DATE_KEYWORDS):
            converted = pd.to_datetime(data[col], errors="coerce")
            if converted.notna().any():
                data[col] = converted
                date_cols.append(col)

    data = data.drop_duplicates()

    for col in data.columns:
        if pd.api.types.is_datetime64_any_dtype(data[col]):
            continue

        if pd.api.types.is_numeric_dtype(data[col]):
            if data[col].isna().any():
                data[col] = data[col].fillna(data[col].median())
        else:
            if data[col].isna().any():
                mode_series = data[col].mode(dropna=True)
                fallback = mode_series.iloc[0] if not mode_series.empty else "Tidak diketahui"
                data[col] = data[col].fillna(fallback)

    return data, date_cols


def sidebar_filters(
    df: pd.DataFrame,
    category_col: str | None,
    date_cols: list[str],
) -> tuple[pd.DataFrame, str | None]:
    filtered = df.copy()
    selected_date_col: str | None = None

    st.sidebar.header("Filter Data")

    if category_col:
        category_options = sorted(filtered[category_col].dropna().astype(str).unique().tolist())
        selected_categories = st.sidebar.multiselect(
            "Pilih kategori",
            options=category_options,
            default=category_options,
        )

        if selected_categories:
            filtered = filtered[filtered[category_col].astype(str).isin(selected_categories)]
        else:
            filtered = filtered.iloc[0:0]

    if date_cols:
        selected_date_col = st.sidebar.selectbox("Pilih kolom tanggal", options=date_cols)
        valid_dates = filtered[selected_date_col].dropna()

        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            date_input = st.sidebar.date_input(
                "Pilih rentang tanggal",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )

            if isinstance(date_input, tuple) and len(date_input) == 2:
                start_date, end_date = date_input
            else:
                start_date = date_input
                end_date = date_input

            start_ts = pd.to_datetime(start_date)
            end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            filtered = filtered[filtered[selected_date_col].between(start_ts, end_ts)]

    numeric_cols = filtered.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        selected_numeric_col = st.sidebar.selectbox("Pilih kolom numerik", options=numeric_cols)
        min_val = float(filtered[selected_numeric_col].min())
        max_val = float(filtered[selected_numeric_col].max())

        if min_val < max_val:
            value_range = st.sidebar.slider(
                "Pilih rentang nilai",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
            )
            filtered = filtered[filtered[selected_numeric_col].between(value_range[0], value_range[1])]
        else:
            st.sidebar.caption("Kolom numerik terpilih memiliki nilai konstan.")

    return filtered, selected_date_col


def build_insights(
    df: pd.DataFrame,
    category_col: str | None,
    size_col: str | None,
    pixel_col: str | None,
) -> list[str]:
    insights: list[str] = []

    if category_col and not df.empty:
        class_counts = df[category_col].value_counts()
        total = class_counts.sum()
        if total > 0 and not class_counts.empty:
            imbalance_ratio = class_counts.max() / max(class_counts.min(), 1)
            under_15 = class_counts[(class_counts / total * 100) < 15].index.tolist()
            insights.append(
                f"Distribusi kategori menunjukkan imbalance ratio sekitar {imbalance_ratio:.2f}x antara kelas terbesar dan terkecil."
            )
            if under_15:
                insights.append(
                    f"Kategori dengan porsi di bawah 15%: {', '.join(map(str, under_15))}. Kategori ini layak diprioritaskan untuk augmentasi data."
                )

    if category_col and size_col and not df.empty:
        grouped_size = df.groupby(category_col)[size_col].median().sort_values(ascending=False)
        overall_median = df[size_col].median()
        if pd.notna(overall_median) and overall_median != 0:
            deviating = grouped_size[
                ((grouped_size - overall_median).abs() / overall_median * 100) >= 20
            ].index.tolist()
            if deviating:
                insights.append(
                    "Terdapat kategori dengan deviasi median ukuran file >=20% terhadap median keseluruhan: "
                    + ", ".join(map(str, deviating))
                    + "."
                )

    if category_col and size_col and not df.empty:
        outlier_classes: list[str] = []
        for category, series in df.groupby(category_col)[size_col]:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_rate = ((series < lower) | (series > upper)).mean() * 100
            if outlier_rate >= 5:
                outlier_classes.append(f"{category} ({outlier_rate:.1f}%)")

        if outlier_classes:
            insights.append(
                "Outlier ukuran file (metode IQR) yang perlu quality check tambahan: "
                + ", ".join(outlier_classes)
                + "."
            )

    if pixel_col and size_col and not df.empty:
        corr_value = df[[pixel_col, size_col]].corr().iloc[0, 1]
        if pd.notna(corr_value):
            insights.append(
                f"Korelasi antara jumlah piksel dan ukuran file berada di sekitar {corr_value:.2f}, menunjukkan hubungan teknis antar fitur gambar."
            )

    if not insights:
        insights.append("Data hasil filter belum cukup untuk menghasilkan insight yang stabil.")

    return insights


def create_placeholder_image(label: str) -> Image.Image:
    w, h = 640, 420
    image = Image.new("RGB", (w, h), color=(240, 240, 240))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    bbox = draw.textbbox((0, 0), label, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(
        ((w - text_width) / 2, (h - text_height) / 2),
        label,
        fill=(30, 30, 30),
        font=font,
    )
    return image


def main() -> None:
    st.set_page_config(
        page_title="Dashboard Analisis Sampah Daur Ulang",
        layout="wide",
    )

    st.title("Dashboard Analisis Klasifikasi Sampah Daur Ulang")
    st.markdown(
        "Dashboard ini menampilkan hasil analisis distribusi kategori, karakteristik gambar, "
        "dan indikasi kebutuhan preprocessing berdasarkan data hasil olahan notebook."
    )

    dataset_path = find_dataset_path()
    if dataset_path is None:
        st.error(
            "File dataset tidak ditemukan. Letakkan main_data.csv atau clean_sampah_metadata.csv di folder proyek."
        )
        st.stop()

    raw_df = load_dataset(str(dataset_path))
    clean_df, date_cols = preprocess_data(raw_df)

    category_col = find_existing_column(clean_df, ["kategori", "class_label", "category"])
    size_col = find_existing_column(clean_df, ["ukuran_file_kb", "file_size_kb"])
    pixel_col = find_existing_column(clean_df, ["jumlah_piksel", "pixels"])

    st.caption(f"Sumber data aktif: {dataset_path.name}")

    filtered_df, selected_date_col = sidebar_filters(clean_df, category_col, date_cols)

    with st.container():
        st.subheader("Data")
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.dataframe(filtered_df, use_container_width=True, height=340)

        with col_right:
            st.markdown("### Ringkasan")
            st.metric("Jumlah baris", f"{len(filtered_df):,}")
            if category_col and not filtered_df.empty:
                st.metric("Jumlah kategori", filtered_df[category_col].nunique())
            if size_col and not filtered_df.empty:
                st.metric("Median ukuran file (KB)", f"{filtered_df[size_col].median():.2f}")

    with st.container():
        st.subheader("Ringkasan Statistik")
        numeric_df = filtered_df.select_dtypes(include="number")
        if numeric_df.empty:
            st.info("Tidak ada kolom numerik untuk ditampilkan dalam ringkasan statistik.")
        else:
            st.dataframe(numeric_df.describe().T, use_container_width=True)

    with st.container():
        st.subheader("Visualisasi Data")
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            if category_col and not filtered_df.empty:
                class_dist = (
                    filtered_df[category_col]
                    .value_counts()
                    .rename_axis("kategori")
                    .reset_index(name="jumlah_data")
                )
                fig1, ax1 = plt.subplots(figsize=(8, 4.5))
                sns.barplot(data=class_dist, x="kategori", y="jumlah_data", palette="viridis", ax=ax1)
                ax1.set_title("Distribusi Jumlah Data per Kategori")
                ax1.set_xlabel("Kategori")
                ax1.set_ylabel("Jumlah Data")
                ax1.tick_params(axis="x", rotation=25)
                st.pyplot(fig1)

                if not class_dist.empty:
                    top_row = class_dist.iloc[0]
                    bottom_row = class_dist.iloc[-1]
                    imbalance_ratio = top_row["jumlah_data"] / max(bottom_row["jumlah_data"], 1)
                    below_15 = (
                        class_dist["jumlah_data"] / class_dist["jumlah_data"].sum() * 100 < 15
                    )
                    low_classes = class_dist.loc[below_15, "kategori"].tolist()
                    st.markdown(
                        f"**Insight:** Kategori dengan data terbanyak adalah **{top_row['kategori']}** dan yang paling sedikit **{bottom_row['kategori']}** dengan rasio sekitar **{imbalance_ratio:.2f}x**. "
                        + (
                            f"Kategori di bawah 15% total data: {', '.join(map(str, low_classes))}."
                            if low_classes
                            else "Tidak ada kategori yang berada di bawah 15% total data."
                        )
                    )
            else:
                st.info("Kolom kategori tidak ditemukan untuk membuat bar chart.")

        with chart_col2:
            fig2, ax2 = plt.subplots(figsize=(8, 4.5))
            line_chart_rendered = False

            if selected_date_col and not filtered_df.empty:
                trend_df = (
                    filtered_df.dropna(subset=[selected_date_col])
                    .set_index(selected_date_col)
                    .resample("D")
                    .size()
                    .rename("jumlah_data")
                    .reset_index()
                )
                if not trend_df.empty:
                    sns.lineplot(data=trend_df, x=selected_date_col, y="jumlah_data", marker="o", ax=ax2)
                    ax2.set_title("Tren Jumlah Data per Hari")
                    ax2.set_xlabel("Tanggal")
                    ax2.set_ylabel("Jumlah Data")
                    line_chart_rendered = True

            if not line_chart_rendered and category_col and size_col and not filtered_df.empty:
                trend_alt = (
                    filtered_df.groupby(category_col)[size_col]
                    .median()
                    .sort_values(ascending=False)
                    .reset_index()
                )
                sns.lineplot(data=trend_alt, x=category_col, y=size_col, marker="o", ax=ax2)
                ax2.set_title("Perbandingan Median Ukuran File per Kategori")
                ax2.set_xlabel("Kategori")
                ax2.set_ylabel("Median Ukuran File (KB)")
                ax2.tick_params(axis="x", rotation=25)
                line_chart_rendered = True

            if line_chart_rendered:
                st.pyplot(fig2)

                if selected_date_col and not trend_df.empty:
                    peak_row = trend_df.loc[trend_df["jumlah_data"].idxmax()]
                    st.markdown(
                        f"**Insight:** Aktivitas data paling padat terjadi pada **{peak_row[selected_date_col].date()}** dengan **{int(peak_row['jumlah_data'])}** data. "
                        f"Pola ini membantu melihat apakah ada lonjakan pengumpulan data pada periode tertentu."
                    )
                elif category_col and size_col and not filtered_df.empty:
                    highest_row = trend_alt.iloc[0]
                    lowest_row = trend_alt.iloc[-1]
                    st.markdown(
                        f"**Insight:** Median ukuran file tertinggi ada pada **{highest_row[category_col]}** dan terendah pada **{lowest_row[category_col]}**. "
                        "Ini menandakan karakteristik file antar kategori tidak seragam dan layak diperlakukan berbeda saat preprocessing."
                    )
            else:
                st.info("Line chart belum dapat ditampilkan karena kolom pendukung tidak tersedia.")

        numeric_for_corr = filtered_df.select_dtypes(include="number")
        if numeric_for_corr.shape[1] >= 2:
            fig3, ax3 = plt.subplots(figsize=(10, 5))
            corr_matrix = numeric_for_corr.corr(numeric_only=True)
            sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="YlGnBu", ax=ax3)
            ax3.set_title("Heatmap Korelasi Fitur Numerik")
            st.pyplot(fig3)

            corr_no_diag = corr_matrix.abs().where(~pd.DataFrame(
                np.eye(corr_matrix.shape[0], dtype=bool),
                index=corr_matrix.index,
                columns=corr_matrix.columns,
            ))
            if corr_no_diag.notna().any().any():
                strongest_pair = corr_no_diag.stack().idxmax()
                strongest_value = corr_matrix.loc[strongest_pair[0], strongest_pair[1]]
                st.markdown(
                    f"**Insight:** Korelasi paling kuat terlihat antara **{strongest_pair[0]}** dan **{strongest_pair[1]}** dengan nilai **{strongest_value:.2f}**. "
                    "Pola ini penting untuk melihat fitur mana yang saling berkaitan dan berpotensi redundant."
                )
        else:
            st.info("Heatmap korelasi membutuhkan minimal dua kolom numerik.")

    with st.container():
        st.subheader("Insight")
        for insight in build_insights(filtered_df, category_col, size_col, pixel_col):
            st.markdown(f"- {insight}")

    with st.container():
        st.subheader("Contoh Gambar per Kategori")
        if category_col and not filtered_df.empty:
            image_root = find_dataset_image_root()
            categories = sorted(filtered_df[category_col].dropna().astype(str).unique())
            if not categories:
                st.info("Tidak ada kategori untuk ditampilkan gambar.")
            elif image_root is None:
                st.warning("Folder dataset gambar tidak ditemukan di cache lokal, jadi gambar contoh tidak bisa diambil dari dataset asli.")
            else:
                cols = st.columns(min(3, len(categories)))
                real_image_count = 0
                missing_categories: list[str] = []

                for i, cat in enumerate(categories):
                    img_path = find_category_sample_image(cat, image_root)
                    col = cols[i % len(cols)]

                    with col:
                        if img_path is not None:
                            st.image(Image.open(img_path), width="stretch", caption=str(cat))
                            real_image_count += 1
                        else:
                            st.image(create_placeholder_image(str(cat)), width="stretch", caption=str(cat))
                            missing_categories.append(str(cat))

                st.markdown(
                    f"**Insight:** Ada **{real_image_count}** kategori yang berhasil diambil langsung dari file gambar dataset asli di cache lokal. "
                    + (
                        f"Kategori tanpa file contoh yang cocok: {', '.join(missing_categories)}."
                        if missing_categories
                        else "Semua kategori yang sedang difilter sudah punya contoh gambar asli dari dataset."
                    )
                )

    with st.container():
        st.subheader("Kesimpulan")
        st.markdown(
            "- Distribusi data antar kategori masih perlu dipantau untuk mencegah bias model pada kelas mayoritas.\n"
            "- Perbedaan karakteristik ukuran file dan resolusi antar kategori menguatkan kebutuhan preprocessing yang konsisten sekaligus adaptif.\n"
            "- Dashboard interaktif ini dapat digunakan untuk menentukan prioritas augmentasi data, class weight, dan quality control sebelum tahap modeling."
        )


if __name__ == "__main__":
    main()
