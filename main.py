import streamlit as st
import urllib.parse
from fpdf import FPDF
from datetime import datetime
from supabase import create_client, Client
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador de Presupuestos", layout="wide")

# --- CONEXIÓN DE SUPABASE ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Cargar catálogo desde la tabla "productos" en Supabase
@st.cache_data(ttl=60)
def cargar_datos_supabase():
    try:
        # Trae todas las filas de la tabla 'productos'
        response = supabase.table("productos").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error al conectar con la base de datos de Supabase: {e}")
        return None

ITEMS_PRECARGADOS = {}
datos_db = cargar_datos_supabase()

if datos_db:
    for row in datos_db:
        # Ajustá los nombres de las columnas en minúscula/mayúscula según los creaste en Supabase
        producto_nombre = str(row.get("producto", row.get("Producto", ""))).strip()
        ITEMS_PRECARGADOS[producto_nombre] = {
            "costo": int(row.get("costo", row.get("Costo", 0))),
            "pvp": int(row.get("pvp", row.get("PVP", 0))),
            "desc": str(row.get("descripcion", row.get("Descripcion", "")))
        }
else:
    # Respaldo automático si la base de datos no devuelve datos o está vacía
    ITEMS_PRECARGADOS = {
        "Desarrollo MVP Web": {"costo": 50000, "pvp": 150000, "desc": "Sitio web básico en React/Python"},
        "Mantenimiento Mensual": {"costo": 10000, "pvp": 35000, "desc": "Soporte técnico y actualizaciones"},
        "Automatización con Bot": {"costo": 30000, "pvp": 90000, "desc": "Bot de WhatsApp/Telegram para turnos"}
    }

# 2. Función para subir el PDF al Storage Bucket y obtener la URL pública
def subir_pdf_a_supabase_storage(pdf_bytes, nombre_archivo):
    try:
        bucket_name = "presupuestos"  # Asegurate de crear este bucket como 'Público' en el panel de Supabase
        
        # Subir el archivo binario
        supabase.storage.from_(bucket_name).upload(
            path=nombre_archivo,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf", "x-upsert": "true"} # x-upsert sobreescribe si se llama igual
        )
        
        # Obtener y retornar el enlace público definitivo
        url_publica = supabase.storage.from_(bucket_name).get_public_url(nombre_archivo)
        return url_publica
    except Exception as storage_err:
        st.error(f"Error al subir el archivo al almacenamiento: {storage_err}")
        return None

# 3. Función para crear el PDF (Mantiene tu estructura FPDF2 exacta)
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
st.title("💼 Generador de Presupuestos Automatizado")

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
        
        nombre_formateado = nombre_cliente.replace(' ', '_') if nombre_cliente else 'Cliente'
        nombre_archivo_pdf = f"Presupuesto_{nombre_formateado}_{datetime.now().strftime('%d%m%Y_%H%M')}.pdf"
        
        # Generar el PDF en memoria una sola vez al seleccionar items
        try:
            pdf_bytes = generar_presupuesto_pdf(nombre_cliente, whatsapp, items_seleccionados)
        except Exception as e:
            st.error(f"Error al estructurar PDF: {e}")
            pdf_bytes = None

        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if pdf_bytes:
                st.download_button(
                    label="📥 Descargar copia local (Opcional)",
                    data=pdf_bytes,
                    file_name=nombre_archivo_pdf,
                    mime="application/pdf"
                )
                
        with col_btn2:
            if pdf_bytes and st.button("🔗 Generar Enlace y Preparar WhatsApp"):
                with st.spinner("Subiendo PDF de forma segura a Supabase..."):
                    url_pdf = subir_pdf_a_supabase_storage(pdf_bytes, nombre_archivo_pdf)
                    
                    if url_pdf:
                        resumen_texto = "".join([f"- {i}: ${ITEMS_PRECARGADOS[i]['pvp']:,}\n" for i in items_seleccionados])
                        mensaje_ws = (
                            f"💼 *InnovaSoft Tech — Presupuesto*\n\n"
                            f"¡Hola {nombre_cliente if nombre_cliente else 'Cliente'}! "
                            f"Te adjunto el detalle de la solución digital solicitada:\n\n"
                            f"{resumen_texto}\n"  # Acá cada ítem puede arrancar con 🔹 o 🖥️
                            f"💰 *Total Estimado: ${total_pvp:,}*\n"
                            f"📅 _Validez del presupuesto: 15 días_\n\n"
                            f"📄 Podés ver y descargar el documento formal completo desde acá:\n"
                            f"{url_pdf}\n\n"
                            f"🤝 Quedo a tu disposición para cualquier consulta."
                        )
                        mensaje_encoded = urllib.parse.quote(mensaje_ws)
                        link_whatsapp = f"https://wa.me/{whatsapp}?text={mensaje_encoded}"
                        
                        if whatsapp:
                            st.success("¡Enlace generado exitosamente!")
                            st.markdown(f"### [💬 Hacer clic para enviar por WhatsApp]({link_whatsapp})")
                        else:
                            st.warning("El PDF se subió con éxito, pero necesitás ingresar el número de WhatsApp para abrir el chat.")

with tab2:
    st.subheader("📈 Análisis de Rentabilidad")
    if items_seleccionados:
        ganancia_neta = total_pvp - total_costo
        margen = (ganancia_neta / total_pvp) * 100 if total_pvp > 0 else 0
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Ingreso Bruto (PVP)", f"${total_pvp:,}")
        col_b.metric("Costo Interno", f"${total_costo:,}", delta_color="inverse")
        col_c.metric("Ganancia Neta", f"${ganancia_neta:,}", f"{margen:.1f}% Margen")
