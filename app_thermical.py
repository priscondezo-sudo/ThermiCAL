import streamlit as st
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from rasterio.io import MemoryFile
import datetime

st.set_page_config(page_title="ThermiCAL", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=PT+Serif:wght@400;700&display=swap');
        body { font-family: 'PT Serif', serif; }
        @media (prefers-color-scheme: light) {
            body { background: linear-gradient(to bottom right, #ffffff, #e6e6e6); color: #000000; }
            h2, h3, .stMarkdown { color: #000000; }
        }
        @media (prefers-color-scheme: dark) {
            body { background: linear-gradient(to bottom right, #1e3c72, #2a5298); color: white; }
            h2, h3, .stMarkdown { color: #f0f0f0; }
        }
        .stButton > button, .stDownloadButton > button {
            font-family: 'PT Serif', serif; font-weight: bold;
            border-radius: 10px; padding: 10px 20px;
        }
        .stButton > button { background-color: #ffa500; color: white; }
        .stDownloadButton > button { background-color: #28a745; color: white; }
        .stFileUploader { background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; }
        footer { text-align: center; margin-top: 50px; font-size: 14px; color: #ccc; }
        .eq-box {
            background-color: #e8f5e9;
            color: #1b5e20;
            border-left: 5px solid #2e7d32;
            border-radius: 8px;
            padding: 15px 20px;
            margin-top: 10px;
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between;
         background-color: #005792; padding: 10px 20px; border-radius: 10px;">
        <img src="https://raw.githubusercontent.com/JLHM1998/ThermiCAL_EcosmartRice/master/assets/Escudo.png"
             style="height: 80px;">
        <div style="text-align: center;">
            <h1 style="color: white; margin: 0;">🔥 ThermiCAL_EcosmartRice</h1>
            <p style="margin: 0; font-size: 14px; color: #e0e0e0;">
                Aplicativo Web para el procesamiento y Corrección Radiométrica
            </p>
        </div>
        <img src="https://raw.githubusercontent.com/JLHM1998/ThermiCAL_EcosmartRice/master/assets/logo_TyC.png"
             style="height: 80px;">
    </div>
""", unsafe_allow_html=True)

st.markdown("""
### Bienvenido a la aplicación ThermiCAL
Esta aplicación permite cargar un ortomosaico térmico, aplicar una **ecuación de calibración** y visualizar los resultados.
La calibración indirecta de las imágenes térmicas obtenidas por la cámara H20T se realizó comparándolas con los datos
medidos con un radiómetro Apogee MI-210 en nueve coberturas conocidas.
""")

ecuaciones = {
    # ── Caballito ─────────────────────────────────────────────────────────────
    ("Caballito", "14:30 - 14:50  [18/03/2025]"): ("18/03/2025", 0.907,   6.6052),
    ("Caballito", "11:10 - 11:30  [21/03/2025]"): ("21/03/2025", 1.0042,  5.9539),
    ("Caballito", "09:10 - 09:30  [25/03/2025]"): ("25/03/2025", 1.0203,  8.6858),
    ("Caballito", "12:20 - 12:40  [26/03/2025]"): ("26/03/2025", 0.9538,  8.3405),
    ("Caballito", "10:00 - 10:20  [18/04/2025]"): ("18/04/2025", 1.2333,  9.0813),
    ("Caballito", "09:30 - 09:50  [12/05/2025]"): ("12/05/2025", 0.8892, 17.444),
    ("Caballito", "09:50 - 10:10  [27/05/2025]"): ("27/05/2025", 1.0852,  5.1005),
    ("Caballito", "10:20 - 10:40  [01/06/2025]"): ("01/06/2025", 1.2071, 11.794),
    ("Caballito", "10:30 - 10:50  [07/06/2025]"): ("07/06/2025", 1.1584, 11.198),
    # ── Garcia ────────────────────────────────────────────────────────────────
    ("Garcia",    "12:20 - 12:50  [21/03/2025]"): ("21/03/2025", 1.1135,  0.3147),
    ("Garcia",    "10:10 - 10:20  [25/03/2025]"): ("25/03/2025", 0.932,  10.709),
    ("Garcia",    "10:50 - 11:00  [18/04/2025]"): ("18/04/2025", 1.0166,  8.0256),
    ("Garcia",    "10:40 - 10:50  [12/05/2025]"): ("12/05/2025", 1.0185, 11.074),
    ("Garcia",    "11:00 - 11:20  [27/05/2025]"): ("27/05/2025", 1.2228,  4.5816),
    ("Garcia",    "11:10 - 11:30  [01/06/2025]"): ("01/06/2025", 1.1358,  9.8977),
    ("Garcia",    "11:20 - 11:40  [07/06/2025]"): ("07/06/2025", 1.2435,  4.7453),
    # ── Santa Julia ───────────────────────────────────────────────────────────
    ("Santa Julia", "15:40 - 16:02  [18/03/2025]"): ("18/03/2025", 0.9615,  9.1167),
    ("Santa Julia", "14:20 - 14:40  [21/03/2025]"): ("21/03/2025", 0.8088,  7.8216),
    ("Santa Julia", "12:50 - 13:10  [18/04/2025]"): ("18/04/2025", 1.1907,  1.3478),
    ("Santa Julia", "12:40 - 13:00  [12/05/2025]"): ("12/05/2025", 1.0222,  9.3567),
    ("Santa Julia", "12:40 - 13:00  [27/05/2025]"): ("27/05/2025", 0.9851, 11.359),
    ("Santa Julia", "13:00 - 13:20  [01/06/2025]"): ("01/06/2025", 1.1635,  6.8216),
    ("Santa Julia", "13:00 - 13:20  [07/06/2025]"): ("07/06/2025", 1.0197, 11.609),
    # ── Totora ────────────────────────────────────────────────────────────────
    ("Totora",    "13:20 - 13:40  [21/03/2025]"): ("21/03/2025", 1.0896, -0.3018),
    ("Totora",    "12:10 - 12:20  [25/03/2025]"): ("25/03/2025", 1.2765, -1.7912),
    ("Totora",    "11:50 - 12:10  [18/04/2025]"): ("18/04/2025", 1.2327, -4.3388),
    ("Totora",    "11:40 - 11:50  [12/05/2025]"): ("12/05/2025", 1.0113, 12.322),
    ("Totora",    "11:50 - 12:00  [27/05/2025]"): ("27/05/2025", 0.9042,  9.465),
    ("Totora",    "12:10 - 12:20  [01/06/2025]"): ("01/06/2025", 0.9828, 11.94),
    ("Totora",    "12:10 - 12:30  [07/06/2025]"): ("07/06/2025", 1.2375, 12.387),
    # ── Zapote ────────────────────────────────────────────────────────────────
    ("Zapote",    "14:20 - 14:30  [18/03/2025]"): ("18/03/2025", 0.907,   6.6052),
    ("Zapote",    "10:50 - 11:00  [21/03/2025]"): ("21/03/2025", 1.0042,  5.9539),
    ("Zapote",    "08:50 - 09:00  [25/03/2025]"): ("25/03/2025", 1.0203,  8.6858),
    ("Zapote",    "12:00 - 12:20  [26/03/2025]"): ("26/03/2025", 0.9538,  8.3405),
    ("Zapote",    "09:40 - 09:50  [18/04/2025]"): ("18/04/2025", 1.2333,  9.0813),
    ("Zapote",    "13:50 - 14:00  [19/04/2025]"): ("19/04/2025", 1.468,  -16.973),
    ("Zapote",    "09:10 - 09:30  [12/05/2025]"): ("12/05/2025", 0.8892, 17.444),
    ("Zapote",    "15:20 - 15:40  [13/05/2025]"): ("13/05/2025", 0.8746, 12.76),
    ("Zapote",    "09:30 - 09:40  [27/05/2025]"): ("27/05/2025", 1.0852,  5.1005),
    ("Zapote",    "09:30 - 09:40  [29/05/2025]"): ("29/05/2025", 0.8572, 10.923),
    ("Zapote",    "10:00 - 10:20  [01/06/2025]"): ("01/06/2025", 1.2071, 11.794),
    ("Zapote",    "16:40 - 16:50  [06/06/2025]"): ("06/06/2025", 1.0063,  6.369),
    ("Zapote",    "10:20 - 10:30  [07/06/2025]"): ("07/06/2025", 1.1584, 11.198),
    # ── Carniche ──────────────────────────────────────────────────────────────
    ("Carniche",   "09:00 - 09:10  [19/04/2025]"): ("19/04/2025", 1.1936, 11.022),
    # ── Lambayeque ────────────────────────────────────────────────────────────
    ("Lambayeque", "12:20 - 12:40  [19/04/2025]"): ("19/04/2025", 1.1107,  4.5358),
    # ── Paredones ─────────────────────────────────────────────────────────────
    ("Paredones",  "08:00 - 08:20  [19/04/2025]"): ("19/04/2025", 1.1082,  9.6233),
}

todas_zonas = sorted(set(k[0] for k in ecuaciones))

st.markdown("### 🗺️ Seleccionar información del monitoreo")
col1, col2 = st.columns(2)

with col1:
    zona = st.selectbox("📍 Zona de monitoreo", todas_zonas)

rangos_zona = sorted([k[1] for k in ecuaciones if k[0] == zona], key=lambda r: r[:5])

with col2:
    rango_hora = st.selectbox("🕐 Rango de hora del vuelo", rangos_zona)

registro = ecuaciones.get((zona, rango_hora))

if registro:
    fecha, A, B = registro
    hora_display = rango_hora.split("  [")[0]
    signo = "+" if B >= 0 else "−"
    b_abs = abs(B)
    st.markdown(f"""
        <div class="eq-box">
            <b>Zona:</b> {zona} &nbsp;|&nbsp;
            <b>Fecha:</b> {fecha} &nbsp;|&nbsp;
            <b>Hora del vuelo:</b> {hora_display}<br><br>
            <b>Ecuación de calibración:</b> &nbsp;
            T_cal = <b>{A}</b> × T_raw {signo} <b>{b_abs}</b>
        </div>
    """, unsafe_allow_html=True)
else:
    st.warning("⚠️ No hay ecuación registrada para esta selección.")
    A, B, fecha = None, None, None

st.markdown("### 📂 Subir imagen térmica (GeoTIFF) y descargar corregida")
uploaded_file = st.file_uploader("Selecciona tu archivo TIR (.tif / .tiff):", type=["tif", "tiff"])

if uploaded_file is not None and A is not None:
    with rasterio.open(uploaded_file) as src:
        profile = src.profile.copy()
        image = src.read(1).astype(np.float32)
        nodata = src.nodata

    # Máscara de nodata
    if nodata is not None:
        mask_nodata = (image == nodata)
    else:
        mask_nodata = (image == 0)

    valid = ~mask_nodata

    # ── PASO 1: Si valores válidos > 100 → dividir entre 10 primero
    max_valid = float(np.nanmax(image[valid])) if valid.any() else 0.0
    image_proc = image.copy()
    if max_valid > 100:
        image_proc[valid] = image[valid] / 10.0
        st.warning(f"⚠️ Valores mayores a 100°C detectados (máx: {max_valid:.2f}). "
                   f"Se dividió entre 10 antes de calibrar.")

    # ── PASO 2: Aplicar ecuación de calibración sobre imagen procesada
    calibrated = image_proc.copy()
    calibrated[valid] = A * image_proc[valid] + B

    # Restaurar nodata
    if nodata is not None:
        calibrated[mask_nodata] = nodata
    else:
        calibrated[mask_nodata] = 0

    # Vista previa original (ya dividida si aplica)
    st.markdown("#### 🗾 Imagen Original")
    preview_orig = np.where(valid, image_proc, np.nan)
    vmin, vmax = np.nanpercentile(preview_orig, [2, 98])
    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(preview_orig, cmap='inferno', vmin=vmin, vmax=vmax)
    ax.axis('off')
    fig.colorbar(im, ax=ax, label='Temperatura (°C)')
    st.pyplot(fig)
    st.info(f"**Original** — Min: {np.nanmin(preview_orig):.2f}°C | Max: {np.nanmax(preview_orig):.2f}°C | Media: {np.nanmean(preview_orig):.2f}°C")

    # Vista previa calibrada
    st.markdown("#### 🗾 Imagen Calibrada")
    preview_cal = np.where(valid, calibrated, np.nan)
    vmin2, vmax2 = np.nanpercentile(preview_cal, [2, 98])
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    im2 = ax2.imshow(preview_cal, cmap='inferno', vmin=vmin2, vmax=vmax2)
    ax2.axis('off')
    fig2.colorbar(im2, ax=ax2, label='Temperatura Calibrada (°C)')
    st.pyplot(fig2)
    st.info(f"**Calibrada** — Min: {np.nanmin(preview_cal):.2f}°C | Max: {np.nanmax(preview_cal):.2f}°C | Media: {np.nanmean(preview_cal):.2f}°C")

    # Guardar conservando georreferenciación
    profile.update(dtype=rasterio.float32)
    with MemoryFile() as memfile:
        with memfile.open(**profile) as dst:
            dst.write(calibrated.astype(rasterio.float32), 1)
        mem_bytes = memfile.read()

    hora_fn  = hora_display.replace(":", "").replace(" ", "")
    fecha_fn = fecha.replace("/", "-")
    st.markdown("### 💾 Descargar Imagen Calibrada")
    st.download_button(
        "📥 Descargar TIFF Calibrado",
        data=mem_bytes,
        file_name=f"{zona}_{fecha_fn}_{hora_fn}_calibrada.tif",
        mime="image/tiff"
    )

elif uploaded_file is not None and A is None:
    st.error("Selecciona una combinación zona/hora válida antes de subir la imagen.")
else:
    st.info("Por favor, sube una imagen térmica para comenzar.")

st.markdown("### 📘 Manual de Usuario")
st.markdown("- **Visualizar en línea**: [Abrir manual](https://github.com/JLHM1998/ThermiCAL_EcosmartRice/blob/main/Manual_Usuario_ThermiCAL.pdf)")
try:
    with open("Manual_Usuario_ThermiCAL.pdf", "rb") as manual_file:
        st.download_button(
            label="📥 Descargar Manual de Usuario (PDF)",
            data=manual_file,
            file_name="Manual_Usuario_ThermiCAL.pdf",
            mime="application/pdf"
        )
except FileNotFoundError:
    st.info("El archivo del manual no se encontró en el servidor.")

st.markdown("""
    <div style="margin-top: 30px; padding: 20px;
         background: linear-gradient(to right, #004e92, #000428);
         border-radius: 12px; color: white;">
        <h3 style="margin-top: 0;">💼 Financiamiento</h3>
        <p style="font-size: 15px; line-height: 1.6;">
            Esta aplicación ha sido desarrollada en el marco del proyecto EcosmartRice:
            <strong>"Nuevas herramientas tecnológicas de precisión con sensores remotos para un sistema de producción
            sostenible en arroz, con menor consumo de agua, menor emisión de gases y mayor rendimiento,
            en beneficio de los agricultores de Lambayeque"</strong>,
            financiado por el <strong>PROCIENCIA - CONCYTEC</strong>,
            mediante el <strong>Contrato No. PE501086540-2024-PROCIENCIA</strong>.
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown('<footer>© 2025 Universidad Nacional Agraria La Molina - Todos los derechos reservados.</footer>',
            unsafe_allow_html=True)
