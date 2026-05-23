import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Lazy load heavy libraries - only when needed
def get_matplotlib_pyplot():
    import matplotlib.pyplot as plt
    return plt

def get_seaborn():
    import seaborn as sns
    return sns

DATASET_CANDIDATES = [
    "clean_sampah_metadata_updated.parquet",  # Faster & smaller (use if available)
    "clean_sampah_metadata_updated.csv",
]
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
    if path_str.endswith('.parquet'):
        return pd.read_parquet(path_str)
    else:
        return pd.read_csv(path_str)


def find_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def find_dataset_image_roots() -> list[Path]:
    image_root = Path("images")
    return [image_root] if image_root.exists() and image_root.is_dir() else []


def find_category_sample_image(category: str, image_roots: list[Path]) -> Path | None:
    if not image_roots:
        return None

    slug = slugify_category(category)
    for image_root in image_roots:
        candidate_dirs = [image_root / category]
        if slug and slug != category:
            candidate_dirs.append(image_root / slug)

        for class_dir in candidate_dirs:
            if not class_dir.exists() or not class_dir.is_dir():
                continue

            for image_path in sorted(class_dir.rglob("*")):
                if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS:
                    return image_path

    return None


def prioritize_categories(categories: list[str]) -> list[str]:
    preferred = ["Clothes", "Organik"]
    ordered = []
    seen = set()

    for item in preferred:
        if item in categories and item not in seen:
            ordered.append(item)
            seen.add(item)

    for item in categories:
        if item not in seen:
            ordered.append(item)
            seen.add(item)

    return ordered


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


@st.cache_data(show_spinner=False)
def count_images_in_root(image_root: Path) -> int:
    return sum(
        1
        for image_path in image_root.rglob("*")
        if image_path.is_file() and image_path.suffix.lower() in IMAGE_EXTENSIONS
    )


@st.cache_data(show_spinner=False)
def find_category_sample_image_cached(category: str, image_root_paths: tuple[str, ...]) -> str | None:
    image_roots = [Path(root) for root in image_root_paths]
    sample = find_category_sample_image(category, image_roots)
    return str(sample) if sample is not None else None


def compute_iqr_outlier_rate(series: pd.Series) -> float:
    if series.empty:
        return 0.0

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0.0

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return float(((series < lower) | (series > upper)).mean() * 100)


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
            "File dataset tidak ditemukan. Letakkan clean_sampah_metadata_updated.csv di folder proyek."
        )
        st.stop()

    clean_df, date_cols = load_and_preprocess_dataset(str(dataset_path))

    category_col = find_existing_column(clean_df, ["kategori", "class_label", "category"])
    size_col = find_existing_column(clean_df, ["ukuran_file_kb", "file_size_kb"])
    pixel_col = find_existing_column(clean_df, ["jumlah_piksel", "pixels"])

    st.caption(f"Sumber data aktif: {dataset_path.name}")

    filtered_df, selected_date_col = sidebar_filters(clean_df, category_col, date_cols)

    raw_images_root = Path("images")
    curated_images_root = Path("clean_images_filtered")
    raw_image_count = count_images_in_root(raw_images_root) if raw_images_root.exists() else 0
    curated_image_count = count_images_in_root(curated_images_root) if curated_images_root.exists() else 0
    available_image_roots = [
        root for root in (raw_images_root, curated_images_root)
        if root.exists() and root.is_dir()
    ]
    preferred_root = raw_images_root if raw_images_root.exists() and raw_images_root.is_dir() else None
    if preferred_root is None and curated_images_root.exists() and curated_images_root.is_dir():
        preferred_root = curated_images_root

    with st.container():
        st.subheader("Data")
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.dataframe(filtered_df, use_container_width=True, height=340)

        with col_right:
            st.markdown("### Ringkasan")
            st.metric("Jumlah Data", f"{raw_image_count:,}")
            st.metric("Jumlah Data Clean", f"{curated_image_count:,}")
            if size_col and not clean_df.empty:
                st.metric("Rata-rata ukuran file (KB)", f"{clean_df[size_col].mean():.2f}")
            if category_col and not clean_df.empty:
                st.metric("Jumlah kategori", clean_df[category_col].nunique())

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
                class_dist["persen"] = class_dist["jumlah_data"] / class_dist["jumlah_data"].sum() * 100
                fig1, ax1 = plt.subplots(figsize=(8, 4.5))
                sns.barplot(data=class_dist, x="kategori", y="jumlah_data", palette="viridis", ax=ax1)
                ax1.set_title("Distribusi Jumlah Data per Kategori")
                ax1.set_xlabel("Kategori")
                ax1.set_ylabel("Jumlah Data")
                ax1.tick_params(axis="x", rotation=25)
                # annotate percent on bars
                for p, pct in zip(ax1.patches, class_dist["persen"]):
                    height = p.get_height()
                    ax1.annotate(f"{pct:.1f}%", (p.get_x() + p.get_width() / 2, height),
                                 ha="center", va="bottom", fontsize=9)
                st.pyplot(fig1)

                if not class_dist.empty:
                    top_row = class_dist.iloc[0]
                    bottom_row = class_dist.iloc[-1]
                    imbalance_ratio = top_row["jumlah_data"] / max(bottom_row["jumlah_data"], 1)
                    low_classes = class_dist.loc[class_dist["persen"] < 15, "kategori"].tolist()
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
        st.subheader("Distribusi Ukuran File")
        size_col1, size_col2 = st.columns(2)

        with size_col1:
            if size_col and not filtered_df.empty:
                fig_size_hist, ax_size_hist = plt.subplots(figsize=(8, 4.5))
                sns.histplot(filtered_df[size_col], bins=40, kde=True, color="#1b4965", ax=ax_size_hist)
                ax_size_hist.set_title("Histogram Ukuran File (KB)")
                ax_size_hist.set_xlabel("Ukuran File (KB)")
                ax_size_hist.set_ylabel("Jumlah Gambar")
                st.pyplot(fig_size_hist)

                skewness = float(filtered_df[size_col].skew())
                tail_note = "condong ke kanan" if skewness > 0.5 else "cukup seimbang"
                st.markdown(
                    f"**Insight:** Distribusi ukuran file {tail_note} (skewness {skewness:.2f}). "
                    "Ini membantu menentukan apakah perlu normalisasi atau kompresi tambahan."
                )
            else:
                st.info("Kolom ukuran file belum tersedia untuk histogram.")

        with size_col2:
            if category_col and size_col and not filtered_df.empty:
                fig_size_box, ax_size_box = plt.subplots(figsize=(8, 4.5))
                sns.boxplot(
                    data=filtered_df,
                    x=category_col,
                    y=size_col,
                    palette="Set2",
                    ax=ax_size_box,
                )
                ax_size_box.set_title("Boxplot Ukuran File per Kategori")
                ax_size_box.set_xlabel("Kategori")
                ax_size_box.set_ylabel("Ukuran File (KB)")
                ax_size_box.tick_params(axis="x", rotation=25)
                st.pyplot(fig_size_box)

                medians = filtered_df.groupby(category_col)[size_col].median().sort_values(ascending=False)
                if not medians.empty:
                    st.markdown(
                        f"**Insight:** Median ukuran file tertinggi berada pada **{medians.index[0]}** "
                        f"dan terendah pada **{medians.index[-1]}**, menandakan perbedaan karakteristik visual antar kategori."
                    )
            else:
                st.info("Boxplot ukuran file membutuhkan kolom kategori dan ukuran file.")

    with st.container():
        st.subheader("Deviasi dan Outlier Ukuran File")
        dev_col1, dev_col2 = st.columns(2)

        with dev_col1:
            if category_col and size_col and not filtered_df.empty:
                overall_median = filtered_df[size_col].median()
                median_by_class = filtered_df.groupby(category_col)[size_col].median()
                deviation_pct = ((median_by_class - overall_median).abs() / overall_median * 100).sort_values(ascending=False)

                dev_df = deviation_pct.reset_index()
                dev_df.columns = ["kategori", "deviasi_persen"]

                fig_dev, ax_dev = plt.subplots(figsize=(8, 4.5))
                sns.barplot(data=dev_df, x="kategori", y="deviasi_persen", palette="crest", ax=ax_dev)
                ax_dev.set_title("Deviasi Median Ukuran File per Kategori")
                ax_dev.set_xlabel("Kategori")
                ax_dev.set_ylabel("Deviasi (%)")
                ax_dev.tick_params(axis="x", rotation=25)
                st.pyplot(fig_dev)

                top_dev = dev_df.head(2)["kategori"].tolist()
                if top_dev:
                    st.markdown(
                        f"**Insight:** Deviasi median terbesar berasal dari kategori {', '.join(top_dev)}. "
                        "Kategori ini perlu perhatian khusus saat standarisasi ukuran input."
                    )
            else:
                st.info("Deviasi median membutuhkan kolom kategori dan ukuran file.")

        with dev_col2:
            if category_col and size_col and not filtered_df.empty:
                outlier_rates = (
                    filtered_df.groupby(category_col)[size_col]
                    .apply(compute_iqr_outlier_rate)
                    .sort_values(ascending=False)
                )
                outlier_df = outlier_rates.reset_index()
                outlier_df.columns = ["kategori", "outlier_rate"]

                fig_outlier, ax_outlier = plt.subplots(figsize=(8, 4.5))
                sns.barplot(data=outlier_df, x="kategori", y="outlier_rate", palette="flare", ax=ax_outlier)
                ax_outlier.set_title("Outlier Rate Ukuran File (IQR)")
                ax_outlier.set_xlabel("Kategori")
                ax_outlier.set_ylabel("Outlier Rate (%)")
                ax_outlier.tick_params(axis="x", rotation=25)
                st.pyplot(fig_outlier)

                high_outliers = outlier_df[outlier_df["outlier_rate"] >= 5]["kategori"].tolist()
                if high_outliers:
                    st.markdown(
                        "**Insight:** Outlier ukuran file >=5% muncul pada kategori: "
                        + ", ".join(high_outliers)
                        + ". Ini menandakan perlunya QC tambahan atau trimming." 
                    )
                else:
                    st.markdown("**Insight:** Tidak ada kategori dengan outlier rate di atas 5%.")
            else:
                st.info("Outlier rate membutuhkan kolom kategori dan ukuran file.")

    with st.container():
        st.subheader("Distribusi Jumlah Piksel")
        if category_col and pixel_col and not filtered_df.empty:
            fig_px, ax_px = plt.subplots(figsize=(10, 5))
            sns.violinplot(
                data=filtered_df,
                x=category_col,
                y=pixel_col,
                palette="muted",
                ax=ax_px,
            )
            ax_px.set_title("Violin Plot Jumlah Piksel per Kategori")
            ax_px.set_xlabel("Kategori")
            ax_px.set_ylabel("Jumlah Piksel")
            ax_px.tick_params(axis="x", rotation=25)
            st.pyplot(fig_px)

            pixel_medians = filtered_df.groupby(category_col)[pixel_col].median().sort_values(ascending=False)
            if not pixel_medians.empty:
                st.markdown(
                    f"**Insight:** Median jumlah piksel tertinggi berada pada **{pixel_medians.index[0]}**, "
                    "mengindikasikan resolusi rata-rata lebih besar pada kategori tersebut."
                )
        else:
            st.info("Violin plot jumlah piksel membutuhkan kolom kategori dan jumlah piksel.")

    with st.container():
        st.subheader("Insight")
        for insight in build_insights(filtered_df, category_col, size_col, pixel_col):
            st.markdown(f"- {insight}")

    with st.container():
        st.subheader("Contoh Gambar per Kategori")
        if category_col and not filtered_df.empty:
            image_roots = available_image_roots
            categories = prioritize_categories(sorted(filtered_df[category_col].dropna().astype(str).unique()))
            if not categories:
                st.info("Tidak ada kategori untuk ditampilkan gambar.")
            elif not image_roots:
                st.warning(
                    "Folder dataset gambar tidak ditemukan. Pastikan folder final 'images' tersedia.\n"
                    "Gunakan placeholder; pastikan folder gambar tersedia jika ingin melihat contoh asli."
                )
                cols = st.columns(min(8, len(categories)))
                for i, cat in enumerate(categories):
                    col = cols[i % len(cols)]
                    with col:
                        st.image(create_placeholder_image(str(cat)), width="stretch", caption=str(cat))
            else:
                # prefer explicit `images` when available
                if preferred_root is not None:
                    st.info(f"Menggunakan sumber gambar: {preferred_root}")
                    search_roots = [preferred_root]
                else:
                    root_options = ["Gabungan (semua)"] + [str(p) for p in image_roots]
                    default_idx = 0
                    chosen = st.selectbox(
                        "Pilih folder gambar (sumber)", options=root_options, index=default_idx
                    )
                    if chosen == "Gabungan (semua)":
                        search_roots = image_roots
                    else:
                        from pathlib import Path as _P

                        search_roots = [_P(chosen)]

                cols = st.columns(min(8, len(categories)))
                real_image_count = 0
                missing_categories: list[str] = []
                selected_preview_categories = [cat for cat in ["Clothes", "Organik"] if cat in categories]
                selected_preview_categories += [cat for cat in categories if cat not in selected_preview_categories][: max(0, 8 - len(selected_preview_categories))]

                for i, cat in enumerate(selected_preview_categories):
                    img_path_str = find_category_sample_image_cached(cat, tuple(str(root) for root in search_roots))
                    img_path = Path(img_path_str) if img_path_str else None
                    col = cols[i % len(cols)]

                    with col:
                        if img_path is not None:
                            try:
                                st.image(Image.open(img_path), width="stretch", caption=str(cat))
                                real_image_count += 1
                            except Exception:
                                st.image(create_placeholder_image(str(cat)), width="stretch", caption=str(cat))
                                missing_categories.append(str(cat))
                        else:
                            st.image(create_placeholder_image(str(cat)), width="stretch", caption=str(cat))
                            missing_categories.append(str(cat))

                st.markdown(
                    f"**Insight:** Ada **{real_image_count}** kategori yang berhasil diambil langsung dari file gambar di sumber terpilih. "
                    + (
                        f"Kategori tanpa file contoh yang cocok: {', '.join(missing_categories)}."
                        if missing_categories
                        else "Semua kategori yang sedang difilter punya contoh gambar dari sumber terpilih."
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
