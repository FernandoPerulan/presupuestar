import streamlit as st
import urllib.parse
from fpdf import FPDF
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador de Presupuestos", layout="wide")

# 1. Conexión con Google Sheets para el Catálogo
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
    # Respaldo automático si el Sheets está offline o cargando
    ITEMS_PRECARGADOS = {
        "Desarrollo MVP Web": {"costo": 50000, "pvp": 150000, "desc": "Sitio web básico en React/Python"},
        "Mantenimiento Mensual": {"costo": 10000, "pvp": 35000, "desc": "Soporte técnico y actualizaciones"},
        "Automatización con Bot": {"costo": 30000, "pvp": 90000, "desc": "Bot de WhatsApp/Telegram para turnos"}
    }

# 2. Función para crear el PDF (Estructura Moderna FPDF2)
def generar_presupuesto_pdf(nombre, telefono, items_elegidos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    # Encabezado
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
    
    # Bloques de datos
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
    pdf.cell(80, 5, f"Teléfono: {telefono}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_xy(15, y_pos + 35)
    
    # Tabla de precios
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

# --- INTERFAZ ---
st.title("💼 Generador de Presupuestos Express")

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
        st.subheader("🚀 Acciones de Envío")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            try:
                pdf_bytes = generar_presupuesto_pdf(nombre_cliente, whatsapp, items_seleccionados)
                st.download_button(
                    label="📥 1. Descargar Presupuesto PDF",
                    data=pdf_bytes,
                    file_name=f"Presupuesto_{nombre_cliente.replace(' ', '_') if nombre_cliente else 'Cliente'}.pdf",
                    mime="application/pdf"
                )
                st.caption("Guardá el archivo formal en tu dispositivo.")
            except Exception as pdf_err:
                st.error(f"Error generando el PDF: {pdf_err}")
                
        with col_btn2:
            resumen_texto = "".join([f"- {i}: ${ITEMS_PRECARGADOS[i]['pvp']:,}\n" for i in items_seleccionados])
            mensaje_ws = (
                f"¡Hola {nombre_cliente if nombre_cliente else 'Cliente'}! Te adjunto el detalle del presupuesto solicitado:\n\n"
                f"{resumen_texto}\n"
                f"*Total: ${total_pvp:,}*\n\n"
                f"*(Te adjunto el documento PDF formal por este medio)*"
            )
            mensaje_encoded = urllib.parse.quote(mensaje_ws)
            link_whatsapp = f"https://wa.me/{whatsapp}?text={mensaje_encoded}"
            
            if whatsapp:
                st.markdown(f"### [💬 2. Abrir WhatsApp y Adjuntar]({link_whatsapp})")
                st.caption("Abre el chat con el texto listo. Solo tocás el clip y arrastrás el PDF descargado.")
            else:
                st.warning("Falta cargar el número de WhatsApp.")

with tab2:
    st.subheader("📈 Análisis de Rentabilidad")
    if items_seleccionados:
        ganancia_neta = total_pvp - total_costo
        margen = (ganancia_neta / total_pvp) * 100 if total_pvp > 0 else 0
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Ingreso Bruto (PVP)", f"${total_pvp:,}")
        col_b.metric("Costo Interno", f"${total_costo:,}", delta_color="inverse")
        col_c.metric("Ganancia Neta", f"${ganancia_neta:,}", f"{margen:.1f}% Margen")
