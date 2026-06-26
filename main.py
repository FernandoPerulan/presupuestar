import streamlit as st
import urllib.parse
from fpdf import FPDF
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# --- INTERFAZ DE STREAMLIT ---
st.set_page_config(page_title="Generador de Presupuestos", layout="wide")

# 1. Conexión con Google Sheets
@st.cache_data(ttl=60)
def cargar_datos_sheets(sheet_name):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet=sheet_name)
    return df

ITEMS_PRECARGADOS = {}

try:
    df_productos = cargar_datos_sheets("Productos")
    df_productos.columns = df_productos.columns.str.strip()
    for _, row in df_productos.iterrows():
        producto_nombre = str(row["Producto"]).strip()
        ITEMS_PRECARGADOS[producto_nombre] = {
            "costo": int(row["Costo"]),
            "pvp": int(row["PVP"]),
            "desc": str(row["Descripcion"])
        }
except Exception as e:
    # Plan de respaldo local por si falla Sheets
    ITEMS_PRECARGADOS = {
        "Desarrollo MVP Web": {"costo": 50000, "pvp": 150000, "desc": "Sitio web básico en React/Python"},
        "Mantenimiento Mensual": {"costo": 10000, "pvp": 35000, "desc": "Soporte técnico y actualizaciones"},
        "Automatización con Bot": {"costo": 30000, "pvp": 90000, "desc": "Bot de WhatsApp/Telegram para turnos"}
    }

# 2. Función para subir el PDF a Google Drive y obtener el link público
def subir_a_drive_y_obtener_link(pdf_bytes, nombre_archivo):
    try:
        # Reutilizamos las credenciales que Streamlit ya tiene configuradas de Google Sheets
        conn = st.connection("gsheets", type=GSheetsConnection)
        creds = conn._client._creds
        
        # Inicializamos el servicio de Google Drive
        service = build('drive', 'v3', credentials=creds)
        
        # Configuramos los metadatos del archivo
        file_metadata = {'name': nombre_archivo, 'mimeType': 'application/pdf'}
        
        # Preparamos el archivo en memoria RAM
        fh = io.BytesIO(pdf_bytes)
        media = MediaIoBaseUpload(fh, mimeType='application/pdf', resumable=True)
        
        # Subimos el archivo a la raíz de tu Drive
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')
        
        # Cambiamos los permisos para que CUALQUIERA con el link lo pueda leer (Público)
        user_permission = {'type': 'anyone', 'role': 'reader'}
        service.permissions().create(fileId=file_id, body=user_permission).execute()
        
        # Construimos el enlace web de visualización directa
        link_publico = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        return link_publico
    except Exception as drive_err:
        st.error(f"Error al subir a Google Drive: {drive_err}")
        return None

# 3. Función para crear el PDF
def generar_presupuesto_pdf(nombre, telefono, items_elegidos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 58, 138) 
    pdf.cell(100, 10, "InnovaSoft", new_x="RIGHT", new_y="TOP")
    
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(80, 10, "PRESUPUESTO", align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(102, 102, 102)
    pdf.cell(100, 6, "Soluciones Digitales Inteligentes", new_x="RIGHT", new_y="TOP")
    
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(80, 6, f"Fecha: {fecha_actual}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(180, 6, "Validez: 15 días", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    y_pos = pdf.get_y()
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(15, y_pos, 85, 28, "F")
    pdf.set_xy(18, y_pos + 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(80, 6, "De nuestra consideración:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(75, 85, 99)
    pdf.set_x(18)
    pdf.cell(80, 5, "InnovaSoft Tech", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(18)
    pdf.cell(80, 5, "Maipú, Mendoza, Argentina", new_x="LMARGIN", new_y="NEXT")
    
    pdf.rect(110, y_pos, 85, 28, "F")
    pdf.set_xy(113, y_pos + 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(2, 132, 199)
    pdf.cell(80, 6, "Preparado para:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(75, 85, 99)
    pdf.set_x(113)
    pdf.cell(80, 5, f"Cliente: {nombre}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(113)
    pdf.cell(80, 5, f"Teléfono: {telefono}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(15, y_pos + 35)
    
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(130, 10, " DESCRIPCIÓN DEL SERVICIO / PRODUCTO", border=0, fill=True)
    pdf.cell(50, 10, "TOTAL ", border=0, fill=True, align="R")
    pdf.ln(10)
    
    pdf.set_text_color(51, 51, 51)
    total_pvp = 0
    toggle_bg = False
    
    for item in items_elegidos:
        desc = ITEMS_PRECARGADOS[item]["desc"]
        pvp = ITEMS_PRECARGADOS[item]["pvp"]
        total_pvp += pvp
        
        if toggle_bg: pdf.set_fill_color(248, 250, 252)
        else: pdf.set_fill_color(255, 255, 255)
            
        x, y = pdf.get_x(), pdf.get_y()
        pdf.rect(x, y, 180, 14, "F")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(130, 6, f" {item}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(x)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(102, 102, 102)
        pdf.cell(130, 6, f"   {desc}")
        
        pdf.set_xy(x + 130, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(51, 51, 51)
        pdf.cell(50, 12, f"${pvp:,} ", border=0, align="R", new_x="LMARGIN", new_y="NEXT")
        
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        toggle_bg = not toggle_bg

    pdf.ln(5)
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_x(110)
    pdf.cell(40, 12, " Total Estimado:", fill=True)
    pdf.cell(45, 12, f"${total_pvp:,} ", fill=True, align="R", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(180, 5, "Gracias por confiar en nosotros.", align="C", new_x="LMARGIN", new_y="NEXT")
    
    return bytes(pdf.output())

# --- CONTROL DE VISTAS ---
st.title("💼 Generador de Presupuestos Inteligente")

tab1, tab2 = st.tabs(["📄 Crear Presupuesto", "📊 Panel de Costos (Dueño)"])

with tab1:
    st.subheader("Datos del Cliente")
    col1, col2 = st.columns(2)
    nombre_cliente = col1.text_input("Nombre del Cliente", placeholder="Ej: Juan Pérez")
    whatsapp = col2.text_input("WhatsApp (ej: 549261XXXXXXX)", placeholder="549...")
    
    items_seleccionados = st.multiselect("Elegí los productos/servicios:", list(ITEMS_PRECARGADOS.keys()))
    
    if items_seleccionados:
        total_pvp = sum(ITEMS_PRECARGADOS[i]["pvp"] for i in items_seleccionados)
        total_costo = sum(ITEMS_PRECARGADOS[i]["costo"] for i in items_seleccionados)
        
        st.markdown(f"## **Total: ${total_pvp:,}**")
        st.write("---")
        
        # 🚀 LA MAGIA: Al tocar este botón se hace todo en background
        if st.button("🚀 Generar y Preparar Envío"):
            with st.spinner("Generando PDF y subiéndolo a tu Drive..."):
                nombre_formateado = nombre_cliente.replace(' ', '_') if nombre_cliente else 'Cliente'
                nombre_archivo_pdf = f"Presupuesto_{nombre_formateado}.pdf"
                
                # 1. Crea el PDF
                pdf_bytes = generar_presupuesto_pdf(nombre_cliente, whatsapp, items_seleccionados)
                
                # 2. Sube a Drive y trae el link
                url_pdf_drive = subir_a_drive_y_obtener_link(pdf_bytes, nombre_archivo_pdf)
                
                if url_pdf_drive:
                    st.success("¡PDF guardado en la nube con éxito!")
                    
                    # 3. Prepara el texto automatizado con el link incluido
                    resumen_texto = "".join([f"- {i}: ${ITEMS_PRECARGADOS[i]['pvp']:,}\n" for i in items_seleccionados])
                    mensaje_ws = (
                        f"¡Hola {nombre_cliente if nombre_cliente else 'Cliente'}! Te adjunto el presupuesto solicitado:\n\n"
                        f"{resumen_texto}\n"
                        f"*Total: ${total_pvp:,}*\n\n"
                        f"📄 Podés ver y descargar tu PDF formal desde Drive acá:\n{url_pdf_drive}\n\n"
                        f"Quedo a tu disposición."
                    )
                    
                    mensaje_encoded = urllib.parse.quote(mensaje_ws)
                    link_whatsapp = f"https://wa.me/{whatsapp}?text={mensaje_encoded}"
                    
                    # Botón dinámico para abrir el chat
                    if whatsapp:
                        st.markdown(f"### [💬 Hacer clic acá para mandar por WhatsApp]({link_whatsapp})")
                    else:
                        st.warning("El PDF se subió a Drive pero te falta cargar el número de WhatsApp para abrir el chat.")

with tab2:
    st.subheader("📈 Análisis de Rentabilidad")
    if items_seleccionados:
        ganancia_neta = total_pvp - total_costo
        margen = (ganancia_neta / total_pvp) * 100 if total_pvp > 0 else 0
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Ingreso Bruto (PVP)", f"${total_pvp:,}")
        col_b.metric("Costo Interno", f"${total_costo:,}", delta_color="inverse")
        col_c.metric("Ganancia Neta", f"${ganancia_neta:,}", f"{margen:.1f}% Margen")
