import streamlit as st
import urllib.parse
from fpdf import FPDF
from datetime import datetime

# 1. Base de datos simulada (Ítems precargados con Costo y PVP)
ITEMS_PRECARGADOS = {}
# ITEMS_PRECARGADOS = {
#   "Desarrollo MVP Web": {"costo": 50000, "pvp": 150000, "desc": "Sitio web básico en React/Python"},
#    "Mantenimiento Mensual": {"costo": 10000, "pvp": 35000, "desc": "Soporte técnico y actualizaciones"},
#    "Automatización con Bot": {"costo": 30000, "pvp": 90000, "desc": "Bot de WhatsApp/Telegram para turnos"},
#    "Consultoría Tecnológica (Hora)": {"costo": 5000, "pvp": 15000, "desc": "Asesoramiento personalizado"}
#}

# 2. Función para crear el PDF en base a los datos cargados
def generar_presupuesto_pdf(nombre, telefono, items_elegidos):
    pdf = FPDF()
    pdf.add_page()
    
    # Configuración de página y márgenes
    pdf.set_margins(15, 15, 15)
    
    # --- ENCABEZADO ---
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 58, 138) # Color azul premium (#1e3a8a)
    pdf.cell(100, 10, "InnovaSoft", ln=0)
    
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(80, 10, "PRESUPUESTO", ln=1, align="R")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(102, 102, 102)
    pdf.cell(100, 6, "Soluciones Digitales Inteligentes", ln=0)
    
    # Datos del documento (derecha)
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(80, 6, f"Fecha: {fecha_actual}", ln=1, align="R")
    pdf.cell(180, 6, "Validez: 15 días", ln=1, align="R")
    
    pdf.ln(10)
    
    # --- INFORMACIÓN DE CONTACTO Y CLIENTE ---
    # Guardamos la posición actual para hacer dos columnas manuales
    y_pos = pdf.get_y()
    
    # Columna Izquierda (Empresa)
    pdf.set_fill_color(248, 250, 252) # Gris claro (#f8fafc)
    pdf.rect(15, y_pos, 85, 28, "F")
    pdf.set_xy(18, y_pos + 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(80, 6, "De nuestra consideración:", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(75, 85, 99)
    pdf.set_x(18)
    pdf.cell(80, 5, "InnovaSoft Tech", ln=1)
    pdf.set_x(18)
    pdf.cell(80, 5, "Maipú, Mendoza, Argentina", ln=1)
    
    # Columna Derecha (Cliente)
    pdf.rect(110, y_pos, 85, 28, "F")
    pdf.set_xy(113, y_pos + 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(2, 132, 199) # Celeste (#0284c7)
    pdf.cell(80, 6, "Preparado para:", ln=1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(75, 85, 99)
    pdf.set_x(113)
    pdf.cell(80, 5, f"Cliente: {nombre}", ln=1)
    pdf.set_x(113)
    pdf.cell(80, 5, f"Teléfono: {telefono}", ln=1)
    
    pdf.set_xy(15, y_pos + 35)
    
    # --- TABLA DE ÍTEMS ---
    # Encabezados de tabla
    pdf.set_fill_color(30, 58, 138) # Azul oscuro
    pdf.set_text_color(255, 255, 255) # Blanco
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(130, 10, " DESCRIPCIÓN DEL SERVICIO / PRODUCTO", border=0, fill=True)
    pdf.cell(50, 10, "TOTAL ", border=0, fill=True, align="R")
    pdf.ln(10)
    
    # Filas de ítems
    pdf.set_text_color(51, 51, 51)
    total_pvp = 0
    toggle_bg = False # Para hacer filas alternas gris/blanco
    
    for item in items_elegidos:
        desc = ITEMS_PRECARGADOS[item]["desc"]
        pvp = ITEMS_PRECARGADOS[item]["pvp"]
        total_pvp += pvp
        
        # Fondo alterno
        if toggle_bg:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)
            
        # Dibujamos la celda de descripción (Multicell para que no se desborde el texto)
        x = pdf.get_x()
        y = pdf.get_y()
        
        # Estructura del ítem
        pdf.rect(x, y, 180, 14, "F") # Fondo
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(130, 6, f" {item}", ln=1)
        pdf.set_x(x)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(102, 102, 102)
        pdf.cell(130, 6, f"   {desc}")
        
        # Volvemos arriba para poner el precio a la derecha
        pdf.set_xy(x + 130, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(51, 51, 51)
        pdf.cell(50, 12, f"${pvp:,} ", border=0, align="R", ln=1)
        
        # Línea de separación sutil
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        toggle_bg = not toggle_bg

    pdf.ln(5)
    
    # --- TOTAL ---
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_x(110)
    pdf.cell(40, 12, " Total Estimado:", fill=True)
    pdf.cell(45, 12, f"${total_pvp:,} ", fill=True, align="R", ln=1)
    
    # --- FOOTER ---
    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(180, 5, "Gracias por confiar en nosotros para la optimización de su negocio.", ln=1, align="C")
    pdf.cell(180, 5, "InnovaSoft © 2026 - Mendoza, Argentina", ln=1, align="C")
    
    # Retornar el PDF como un string de bytes listo para descargar
    return bytes(pdf.output())

# --- INTERFAZ DE STREAMLIT ---
st.set_page_config(page_title="Generador de Presupuestos", layout="wide")
st.title("💼 Generador de Presupuestos Express")

tab1, tab2 = st.tabs(["📄 Crear Presupuesto", "📊 Panel de Costos (Dueño)"])

with tab1:
    st.subheader("Datos del Cliente")
    col1, col2 = st.columns(2)
    with col1:
        nombre_cliente = st.text_input("Nombre del Cliente", placeholder="Ej: Juan Pérez")
    with col2:
        whatsapp = st.text_input("WhatsApp (Con código de área, ej: 549261XXXXXXX)", placeholder="549...")
    
    st.subheader("Selección de Ítems")
    items_seleccionados = st.multiselect("Elegí los productos/servicios a presupuestar:", list(ITEMS_PRECARGADOS.keys()))
    
    if items_seleccionados:
        st.write("### Vista Previa en Pantalla")
        total_pvp = 0
        total_costo = 0
        resumen_texto = ""
        
        for item in items_seleccionados:
            pvp = ITEMS_PRECARGADOS[item]["pvp"]
            costo = ITEMS_PRECARGADOS[item]["costo"]
            st.write(f"• **{item}** | **${pvp:,}**")
            total_pvp += pvp
            total_costo += costo
            resumen_texto += f"- {item}: ${pvp:,}\n"
            
        st.markdown(f"## **Total: ${total_pvp:,}**")
        
        st.write("---")
        st.subheader("🚀 Acciones de Envío")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            # 3. GENERACIÓN EN TIEMPO REAL DEL PDF EN MEMORIA
            # Usamos latin-1 para evitar problemas con caracteres o símbolos de moneda en FPDF
            pdf_bytes = generar_presupuesto_pdf(nombre_cliente, whatsapp, items_seleccionados)
            
            st.download_button(
                label="📥 Descargar Presupuesto PDF Profesional",
                data=pdf_bytes,
                file_name=f"Presupuesto_{nombre_cliente.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            st.caption("Descargá el archivo formal para adjuntarlo en tus mensajes.")
            
        with col_btn2:
            mensaje_ws = f"¡Hola {nombre_cliente}! Te adjunto el presupuesto solicitado:\n\n{resumen_texto}\n*Total: ${total_pvp:,}*\n\nCualquier duda me avisás."
            mensaje_encoded = urllib.parse.quote(mensaje_ws)
            link_whatsapp = f"https://wa.me/{whatsapp}?text={mensaje_encoded}"
            
            if whatsapp:
                st.markdown(f"[💬 Abrir Chat de WhatsApp]({link_whatsapp})")
                st.caption("Abre el chat con el texto pre-armado listo para enviar.")
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
    else:
        st.info("Cargá ítems en la pestaña anterior para ver el análisis de costos.")


