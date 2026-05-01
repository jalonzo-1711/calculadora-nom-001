import streamlit as st
import math

# --- 1. BASES DE DATOS (NOM-001-SEDE-2012) ---

calibres = ["14", "12", "10", "8", "6", "4", "3", "2", "1", "1/0", "2/0", "3/0", "4/0", "250", "300", "350", "400", "500", "600", "750", "1000"]
index_min_paralelo = calibres.index("1/0")

# Ampacidades Tablas 310-15(b)(16) y (17)
ampacidad_tubo = {
    "14": [15, 20, 25], "12": [20, 25, 30], "10": [30, 35, 40], "8": [40, 50, 55],
    "6": [55, 65, 75], "4": [70, 85, 95], "3": [85, 100, 115], "2": [95, 115, 130],
    "1": [110, 130, 145], "1/0": [125, 150, 170], "2/0": [145, 175, 195], "3/0": [165, 200, 225],
    "4/0": [195, 230, 260], "250": [215, 255, 290], "300": [240, 285, 320], "350": [260, 310, 350],
    "400": [280, 335, 380], "500": [320, 380, 430], "600": [350, 420, 475], "750": [400, 475, 535], "1000": [455, 545, 615]
}

ampacidad_aire = {
    "14": [20, 25, 35], "12": [25, 30, 40], "10": [30, 40, 55], "8": [60, 70, 80],
    "6": [80, 95, 105], "4": [105, 125, 140], "3": [120, 145, 165], "2": [140, 170, 190],
    "1": [165, 195, 220], "1/0": [195, 230, 260], "2/0": [225, 265, 300], "3/0": [260, 310, 350],
    "4/0": [300, 360, 405], "250": [340, 405, 455], "300": [375, 445, 505], "350": [420, 505, 570],
    "400": [455, 545, 615], "500": [515, 620, 700], "600": [575, 690, 780], "750": [655, 785, 885], "1000": [780, 935, 1055]
}

factores_temp_ambiente = {
    "21-25°C": [1.08, 1.05, 1.04], "26-30°C": [1.00, 1.00, 1.00],
    "31-35°C": [0.91, 0.94, 0.96], "36-40°C": [0.82, 0.88, 0.91],
    "41-45°C": [0.71, 0.82, 0.87], "46-50°C": [0.58, 0.75, 0.82],
    "51-55°C": [0.41, 0.67, 0.76], "56-60°C": [0.00, 0.58, 0.71]
}

interruptores_std = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 600, 700, 800, 1000, 1200, 1600, 2000, 2500, 3000, 4000, 5000, 6000]

tierra_por_interruptor = {
    15: "14", 20: "12", 60: "10", 100: "8", 200: "6", 300: "4", 400: "3", 
    500: "2", 600: "1", 800: "1/0", 1000: "2/0", 1200: "3/0", 1600: "4/0", 2000: "250",
    2500: "350", 3000: "400", 4000: "500", 5000: "700", 6000: "800"
}

# --- 2. FUNCIONES LÓGICAS ---
def formato_calibre(calibre_str):
    """Asigna AWG o kcmil automáticamente según el calibre"""
    try:
        if int(calibre_str) >= 250:
            return f"{calibre_str} kcmil"
        else:
            return f"{calibre_str} AWG"
    except ValueError:
        # Para calibres con fracciones como "1/0" que darían error al convertirse a entero
        return f"{calibre_str} AWG"

def obtener_calibre(amp_req, tabla, col_temp):
    for cal in calibres:
        if tabla.get(cal, [0,0,0])[col_temp] >= amp_req:
            return cal
    return None

def seleccionar_interruptor_normativo(corriente_carga_diseno, ampacidad_conductor_corregida):
    it_seleccionado = interruptores_std[-1]
    for it in interruptores_std:
        if it >= corriente_carga_diseno:
            it_seleccionado = it
            break
            
    if it_seleccionado > ampacidad_conductor_corregida:
        idx = interruptores_std.index(it_seleccionado)
        it_inferior = interruptores_std[idx-1] if idx > 0 else it_seleccionado
        if it_inferior > ampacidad_conductor_corregida and ampacidad_conductor_corregida < 800:
             pass 

    return it_seleccionado

def obtener_tierra(interruptor):
    for limite in sorted(tierra_por_interruptor.keys()):
        if interruptor <= limite:
            return tierra_por_interruptor[limite]
    return "800"

def obtener_factor_agrupamiento(n):
    if n <= 3: return 1.00
    elif n <= 6: return 0.80
    elif n <= 9: return 0.70
    elif n <= 20: return 0.50
    elif n <= 30: return 0.45
    elif n <= 40: return 0.40
    else: return 0.35

# --- 3. INTERFAZ GRÁFICA ---
st.set_page_config(page_title="Calculadora Eléctrica NOM", layout="wide")
st.title("⚡ Calculadora de Conductores e Interruptores NOM-001-SEDE")

with st.sidebar:
    st.header("1. Datos de la Carga")
    metodo_entrada = st.radio("Entrada", ["Corriente Directa (A)", "Potencia Aparente (kVA)"])
    
    if metodo_entrada == "Potencia Aparente (kVA)":
        potencia_kva = st.number_input("Potencia (kVA)", min_value=0.1, value=50.0)
        tipo_sistema = st.selectbox("Sistema", ["Monofásico (1F)", "Bifásico (2F)", "Trifásico (3F)"], index=2)
        voltaje = st.number_input("Voltaje (V)", min_value=110, value=220)
        
        if "Monofásico" in tipo_sistema or "Bifásico" in tipo_sistema:
            corriente = (potencia_kva * 1000) / voltaje
            fases_activas_base = 2
        else:
            corriente = (potencia_kva * 1000) / (math.sqrt(3) * voltaje)
            fases_activas_base = 3
        st.info(f"Corriente: {corriente:.2f} A")
    else:
        corriente = st.number_input("Corriente Nominal (A)", min_value=1.0, value=100.0)
        fases_activas_base = st.selectbox("Hilos portadores", [2, 3, 4], index=1)

    factor_utilizacion = st.selectbox("Factor Utilización", [1.0, 0.8], index=1)
    
    st.header("2. Instalación")
    tipo_inst = st.selectbox("Canalización", ["Charola / Tubo Conduit", "Al Aire Libre"])
    temp_aislante = st.selectbox("Aislamiento", ["60°C", "75°C", "90°C"], index=1)
    temp_ambiente_str = st.selectbox("Temp. Ambiente", list(factores_temp_ambiente.keys()), index=2)
    misma_canalizacion = st.checkbox("Agrupar cables paralelos", value=True)
    
    st.header("3. Límites")
    calibre_maximo = st.selectbox("Calibre Máximo", calibres, index=calibres.index("500"))

if st.button("🚀 Calcular Sistema", type="primary", use_container_width=True):
    indice_temp = [60, 75, 90].index(int(temp_aislante[:2]))
    tabla_usar = ampacidad_aire if "Aire" in tipo_inst else ampacidad_tubo
    factor_temp = factores_temp_ambiente[temp_ambiente_str][indice_temp]
    
    corriente_diseno = corriente / factor_utilizacion
    
    cables_fase = 1
    resuelto = False
    
    while cables_fase <= 20:
        total_conductores = (fases_activas_base * cables_fase) if misma_canalizacion else fases_activas_base
        f_agrup = obtener_factor_agrupamiento(total_conductores)
        
        amp_necesaria_por_cable = corriente_diseno / (cables_fase * factor_temp * f_agrup)
        
        cal_cand = obtener_calibre(amp_necesaria_por_cable, tabla_usar, indice_temp)
        
        if cal_cand:
            idx_cand = calibres.index(cal_cand)
            if (cables_fase == 1 or idx_cand >= index_min_paralelo) and idx_cand <= calibres.index(calibre_maximo):
                calibre_final = cal_cand
                f_agrup_final = f_agrup
                resuelto = True
                break
        cables_fase += 1

    if resuelto:
        amp_tabla = tabla_usar[calibre_final][indice_temp]
        amp_corregida_total = amp_tabla * cables_fase * factor_temp * f_agrup_final
        
        interruptor = seleccionar_interruptor_normativo(corriente_diseno, amp_corregida_total)
        tierra = obtener_tierra(interruptor)
        
        # Resultados con el formato correcto (AWG o kcmil)
        st.success(f"### Resultado: {cables_fase}x {formato_calibre(calibre_final)} por fase")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Interruptor ITM", f"{interruptor} A")
        c2.metric("Cable de Tierra", formato_calibre(tierra))
        c3.metric("Ampacidad Corregida", f"{amp_corregida_total:.1f} A")
        
        with st.expander("Ver detalles del cálculo"):
            st.write(f"- **Corriente de carga (ajustada por utilización):** {corriente_diseno:.2f} A")
            st.write(f"- **Factor de agrupamiento detectado ({total_conductores} hilos):** {f_agrup_final}")
            st.write(f"- **Factor de temperatura:** {factor_temp}")
            st.write(f"- **Ampacidad base del cable ({formato_calibre(calibre_final)}):** {amp_tabla} A")
    else:
        st.error("No se encontró una solución. Intenta aumentar el calibre máximo permitido.")