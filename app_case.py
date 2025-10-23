
import streamlit as st
import pandas as pd
import numpy as np
from simulate_case import Params, simulate

st.set_page_config(page_title="Simulador Escolar – Calidad Dinámica", layout="wide")

st.title("Simulador de Sistema Escolar • Calidad, Demanda y Capacidad")

with st.sidebar:
    st.markdown("### 🎛️ Presets de escenarios")
    preset = st.selectbox("Elegí un escenario", [
        "Personalizado",
        "Exitoso",
        "Estable",
        "Pérdida por precio alto",
        "Pérdida por baja calidad"
    ])
    
    st.header("Parámetros")
    with st.expander("⏳ Horizonte y Estado inicial", expanded=True):
        anios = st.number_input("Años a simular", 3, 30, 10, 1)
        alumnos_inicial_por_grado = st.slider("Alumnos iniciales por grado", 0, 50, 25, 1)
        demanda_inicial = st.slider("Demanda inicial (pool familias)", 0, 3000, 800, 50)
        divisiones_iniciales = st.slider("Divisiones iniciales por grado", 1, 5, 2, 1)

    with st.expander("🏫 Capacidad e Infraestructura", expanded=False):
        cupo_optimo = st.slider("Cupo óptimo por aula", 15, 35, 25, 1)
        cupo_maximo = st.slider("Cupo MÁXIMO por aula", 20, 40, 30, 1)
        capex_aula = st.number_input("CAPEX por aula nueva", 10000.0, 500000.0, 100000.0, 1000.0)
        costo_docente_por_aula = st.number_input("Costo docente anual por aula", 10000.0, 200000.0, 60000.0, 1000.0)
        sueldos_no_docentes = st.number_input("Sueldos NO docentes (anual)", 0.0, 500000.0, 120000.0, 1000.0)
        mantenimiento_prop = st.slider("Mantenimiento (% facturación)", 0.0, 0.2, 0.03, 0.01)
        trigger_auto_aula = st.checkbox("Construcción endógena de aulas", True)
        regla_dos_div = st.checkbox("Disparar si admitidos deseados ≥ 2*cupo_max", True)
        beta_demanda_calidad = st.slider("Δ Demanda por punto de calidad", 0.0, 30.0, 10.0, 0.5)
        delta_demanda_saturacion = st.slider("Caída de Demanda por alumno actual", 0.0, 0.2, 0.05, 0.01)
        piso_demanda_gap = st.slider("Piso de Demanda sobre matrícula (gap)", 0, 200, 20, 5)

    with st.expander("📣 Demanda y Marketing", expanded=False):
        prop_mkt = st.slider("Proporción de marketing sobre facturación", 0.0, 0.2, 0.05, 0.01)
        mkt_floor = st.number_input("MKT mínimo anual", 0.0, 100000.0, 2000.0, 100.0)
        cac_base = st.number_input("CAC base", 10.0, 2000.0, 200.0, 10.0)
        k_saturacion = st.slider("Sensibilidad CAC a saturación", 0.0, 2.0, 0.5, 0.1)
        k_calidad_candidatos = st.slider("Efecto de calidad en orgánico", 0.0, 2.0, 0.8, 0.1)

    with st.expander("💵 Precio y Retención", expanded=False):
        cuota_mensual = st.number_input("Cuota mensual", 0.0, 1000.0, 250.0, 1.0)
        meses_cobro = st.slider("Meses de cobro/año", 1, 12, 10, 1)
        ref_precio = st.number_input("Precio de referencia", 1.0, 2000.0, 300.0, 1.0)
        k_bajas_precio = st.slider("Sensibilidad bajas al precio", 0.0, 0.5, 0.08, 0.01)
        k_precio_cac = st.slider("Sensibilidad CAC al precio", 0.0, 1.0, 0.5, 0.05)
        tasa_bajas_base = st.slider("Tasa de bajas base", 0.0, 0.2, 0.04, 0.01)
        k_bajas_calidad = st.slider("Sensibilidad bajas a baja calidad", 0.0, 0.5, 0.12, 0.01)

    with st.expander("🌟 Calidad y Reputación (blandos)", expanded=False):
        calidad_base = st.slider("Calidad base", 0.0, 1.0, 0.7, 0.01)
        k_hacinamiento = st.slider("Castigo por hacinamiento", 0.0, 2.0, 1.0, 0.05)
        gamma_hacinamiento = st.slider("No linealidad de hacinamiento", 1.0, 2.0, 1.3, 0.05)
        k_inv_alumno = st.slider("Rendimiento de inversión por alumno", 0.0, 1.0, 0.3, 0.05)
        ref_inv_alumno = st.number_input("Ref. inversión por alumno (anual)", 1.0, 5000.0, 200.0, 10.0)
        k_inv_infra = st.slider("Rendimiento de inversión en infraestructura", 0.0, 1.0, 0.2, 0.05)
        ref_inv_infra = st.number_input("Ref. inversión en infraestructura (anual)", 1000.0, 200000.0, 50000.0, 1000.0)
        k_selectividad = st.slider("Efecto de selectividad", 0.0, 1.0, 0.2, 0.05)
        alpha_calidad = st.slider("Suavizado de calidad (inercia)", 0.0, 1.0, 0.4, 0.05)
        nivel_articulacion = st.slider("Nivel de articulación", 0.0, 1.0, 0.2, 0.05)
        nivel_comunicacion = st.slider("Nivel de comunicación", 0.0, 1.0, 0.2, 0.05)
        nivel_diferenciacion = st.slider("Nivel de diferenciación", 0.0, 1.0, 0.2, 0.05)
        k_articulacion = st.slider("Peso articulación", 0.0, 0.5, 0.05, 0.01)
        k_comunicacion = st.slider("Peso comunicación", 0.0, 0.5, 0.05, 0.01)
        k_diferenciacion = st.slider("Peso diferenciación", 0.0, 0.5, 0.05, 0.01)

    with st.expander("📝 Admisiones", expanded=False):
        politica_seleccion = st.slider("Política de selección (admitidos/candidatos)", 0.0, 1.0, 0.7, 0.05)
        admitidos_max_abs = st.number_input("Tope absoluto de admitidos (-1 desactiva)", -1, 2000, -1, 1)
        st.caption("Admisiones solo en Kinder (K3-K5) y 1° grado. Ajustá el reparto de candidatos:")
        colA, colB = st.columns(2)
        with colA:
            prop_cand_k3 = st.slider("Prop. cand. a K3", 0.0, 1.0, 0.25, 0.05)
            prop_cand_k4 = st.slider("Prop. cand. a K4", 0.0, 1.0, 0.25, 0.05)
        with colB:
            prop_cand_k5 = st.slider("Prop. cand. a K5", 0.0, 1.0, 0.25, 0.05)
            prop_cand_g1 = st.slider("Prop. cand. a G1", 0.0, 1.0, 0.25, 0.05)
        
        tasa_cont_k_to_g1 = st.slider("Tasa de continuidad K5 → 1°", 0.0, 1.0, 0.95, 0.01)

    with st.expander("🧱 Crecimiento de Aulas (manual)", expanded=False):
        manual_crecimiento = st.checkbox("Habilitar crecimiento manual", False)
        solo_manual = st.checkbox("Usar SOLO plan manual (apaga trigger automático)", False)
        colm1, colm2 = st.columns(2)
        with colm1:
            extra_div_k3_per_year = st.number_input("Aulas extra por año en K3", 0, 20, 0, 1)
            extra_div_k4_per_year = st.number_input("Aulas extra por año en K4", 0, 20, 0, 1)
        with colm2:
            extra_div_k5_per_year = st.number_input("Aulas extra por año en K5", 0, 20, 0, 1)
            extra_div_g1_per_year = st.number_input("Aulas extra por año en G1", 0, 20, 0, 1)

# ---- Aplicar preset (sobrescribe variables leídas de sliders) ----
if preset == "Exitoso":
    prop_mkt = 0.10
    k_calidad_candidatos = 1.0
    cuota_mensual = ref_precio * 1.0
    k_precio_cac = 0.3
    tasa_bajas_base = 0.03
    k_bajas_calidad = 0.10
    calidad_base = 0.8
    k_hacinamiento = 1.2
    gamma_hacinamiento = 1.3
    cupo_optimo = 25
    cupo_maximo = 30
    trigger_auto_aula = True
    politica_seleccion = 0.7
    beta_demanda_calidad = 15.0
    delta_demanda_saturacion = 0.03

elif preset == "Estable":
    prop_mkt = 0.05
    k_calidad_candidatos = 0.8
    cuota_mensual = ref_precio * 1.0
    k_precio_cac = 0.5
    tasa_bajas_base = 0.04
    k_bajas_calidad = 0.12
    calidad_base = 0.7
    k_hacinamiento = 1.0
    gamma_hacinamiento = 1.3
    cupo_optimo = 25
    cupo_maximo = 30
    trigger_auto_aula = True
    politica_seleccion = 0.7
    beta_demanda_calidad = 10.0
    delta_demanda_saturacion = 0.05

elif preset == "Pérdida por precio alto":
    prop_mkt = 0.04
    k_calidad_candidatos = 0.6
    cuota_mensual = ref_precio * 1.4
    k_precio_cac = 0.8
    tasa_bajas_base = 0.05
    k_bajas_calidad = 0.14
    calidad_base = 0.65
    k_hacinamiento = 0.9
    gamma_hacinamiento = 1.3
    cupo_optimo = 25
    cupo_maximo = 30
    trigger_auto_aula = False
    politica_seleccion = 0.8
    beta_demanda_calidad = 8.0
    delta_demanda_saturacion = 0.08

elif preset == "Pérdida por baja calidad":
    prop_mkt = 0.03
    k_calidad_candidatos = 0.4
    cuota_mensual = ref_precio * 0.95
    k_precio_cac = 0.4
    tasa_bajas_base = 0.06
    k_bajas_calidad = 0.20
    calidad_base = 0.5
    k_hacinamiento = 1.4
    gamma_hacinamiento = 1.5
    cupo_optimo = 22
    cupo_maximo = 28
    trigger_auto_aula = False
    politica_seleccion = 0.9
    beta_demanda_calidad = 6.0
    delta_demanda_saturacion = 0.10


p = Params(
    anios=anios, alumnos_inicial_por_grado=alumnos_inicial_por_grado,
    demanda_inicial=demanda_inicial, divisiones_iniciales=divisiones_iniciales,
    cupo_optimo=cupo_optimo, cupo_maximo=cupo_maximo, capex_aula=capex_aula,
    costo_docente_por_aula=costo_docente_por_aula, sueldos_no_docentes=sueldos_no_docentes,
    mantenimiento_prop=mantenimiento_prop, trigger_auto_aula=trigger_auto_aula, regla_dos_div=regla_dos_div,
    prop_mkt=prop_mkt, mkt_floor=mkt_floor, cac_base=cac_base, k_saturacion=k_saturacion,
    k_calidad_candidatos=k_calidad_candidatos,
    cuota_mensual=cuota_mensual, meses_cobro=meses_cobro, ref_precio=ref_precio,
    k_bajas_precio=k_bajas_precio, k_precio_cac=k_precio_cac, tasa_bajas_base=tasa_bajas_base, k_bajas_calidad=k_bajas_calidad,
    calidad_base=calidad_base, k_hacinamiento=k_hacinamiento, gamma_hacinamiento=gamma_hacinamiento,
    k_inv_alumno=k_inv_alumno, ref_inv_alumno=ref_inv_alumno, k_inv_infra=k_inv_infra, ref_inv_infra=ref_inv_infra,
    k_selectividad=k_selectividad, alpha_calidad=alpha_calidad,
    nivel_articulacion=nivel_articulacion, nivel_comunicacion=nivel_comunicacion, nivel_diferenciacion=nivel_diferenciacion,
    k_articulacion=k_articulacion, k_comunicacion=k_comunicacion, k_diferenciacion=k_diferenciacion,
    politica_seleccion=politica_seleccion, admitidos_max_abs=admitidos_max_abs, beta_demanda_calidad=beta_demanda_calidad, 
    delta_demanda_saturacion=delta_demanda_saturacion, piso_demanda_gap=piso_demanda_gap,
    prop_cand_k3=prop_cand_k3, prop_cand_k4=prop_cand_k4, 
    prop_cand_k5=prop_cand_k5, prop_cand_g1=prop_cand_g1, 
    tasa_cont_k_to_g1=tasa_cont_k_to_g1,
    manual_crecimiento=manual_crecimiento, solo_manual=solo_manual,
    extra_div_k3_per_year=extra_div_k3_per_year, extra_div_k4_per_year=extra_div_k4_per_year,
    extra_div_k5_per_year=extra_div_k5_per_year, extra_div_g1_per_year=extra_div_g1_per_year,
)

df, extras = simulate(p)

# --- BLOQUE NUEVO: pestañas de visualización ---
tabs = st.tabs([
    "📈 Evolución general",
    "💰 Finanzas",
    "🎓 Distribución por curso"
])

# --- 📈 TAB 1: Evolución general ---
with tabs[0]:
    # --- KPIs con delta ---
    alum_ini, alum_fin = int(df["alumnos_totales"].iloc[0]), int(df["alumnos_totales"].iloc[-1])
    cal_ini, cal_fin = float(df["calidad"].iloc[0]), float(df["calidad"].iloc[-1])
    aulas_ini, aulas_fin = int(df["AulasTotales"].iloc[0]), int(df["AulasTotales"].iloc[-1])
    margen_series = df["facturacion"] - df["costos_totales"]
    marg_ini, marg_fin = float(margen_series.iloc[0]), float(margen_series.iloc[-1])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Alumnos (último año)", f"{alum_fin}", delta=f"{alum_fin - alum_ini:+d}")
    c2.metric("Calidad (último año)", f"{cal_fin:.2f}", delta=f"{(cal_fin - cal_ini):+.2f}")
    c3.metric("Aulas totales", f"{aulas_fin}", delta=f"{aulas_fin - aulas_ini:+d}")
    c4.metric("Margen (último año)", f"{marg_fin:,.0f}", delta=f"{(marg_fin - marg_ini):+,.0f}")

    st.subheader("Evolución de alumnos")
    st.line_chart(df.set_index("anio")[["alumnos_totales"]])

    st.subheader("Calidad vs Tasa de bajas")
    st.line_chart(df.set_index("anio")[["calidad","tasa_bajas"]])
    
    st.subheader("Demanda, candidatos, aceptados y bajas")
    cand_total = df["nuevos_candidatos"]
    plot_df = (
        pd.DataFrame({
            "anio": df["anio"],
            "Demanda potencial": df["Demanda"],
            "Candidatos": cand_total,
            "Aceptados": df["admitidos"],
            "Bajas": df["bajas_totales"],   # 👈 agregamos esta línea
        })
        .set_index("anio")
    )
    st.line_chart(plot_df)


# --- 💰 TAB 2: Finanzas ---
with tabs[1]:
    st.subheader("Facturación, costos fijos y margen de gestión")
    costos_fijos = df["sueldos_docentes"] + extras["params"]["sueldos_no_docentes"]
    margen_gestion = df["facturacion"] - df["costos_totales"]

    fin_df = (
        pd.DataFrame({
            "anio": df["anio"],
            "Facturación": df["facturacion"],
            "Costos fijos": costos_fijos,
            "Margen de gestión": margen_gestion
        })
        .set_index("anio")
    )

    st.line_chart(fin_df)


# --- 🎓 TAB 3: Distribución de alumnos por curso (heatmap con etiquetas + total por año) ---
with tabs[2]:
    import altair as alt

    st.subheader("Distribución de alumnos por curso")

    # Orden deseado de cursos (de abajo a arriba)
    ideal_grades = ["K3", "K4", "K5"] + [f"G{g}" for g in range(1, 13)]

    # Tomar nombres reales desde el modelo (si vienen) o inferir por ancho de G
    grade_names = extras.get("grade_names", None)
    if grade_names is None:
        ncols = extras["G"].shape[1]
        grade_names = ideal_grades[:] if ncols == 15 else [f"G{g}" for g in range(1, 13)]

    # Mantener sólo los grados disponibles, en el orden correcto
    ordered = [g for g in ideal_grades if g in grade_names]

    # Construir DataFrame largo
    G = extras["G"]  # (anios x N_GRADES), ya redondeado a enteros si aplicaste el patch de modelo
    heat_df = pd.DataFrame(G, columns=grade_names).reindex(columns=ordered)
    heat_df["Año"] = df["anio"]
    long_df = heat_df.melt(id_vars="Año", var_name="Curso", value_name="Alumnos")
    # Forzar orden en eje Y invertido (K3 abajo, G12 arriba)
    long_df["Curso"] = pd.Categorical(long_df["Curso"], categories=ordered, ordered=True)

    # Dominio explícito de años para alinear heatmap y totalizador
    years_domain = list(df["anio"].tolist())

    # Toggle para mostrar/ocultar números en cada celda (por si hay muchos)
    show_numbers = st.checkbox("Mostrar números en cada celda", value=True)

    # --- HEATMAP ---
    heat = (
        alt.Chart(long_df)
        .mark_rect()
        .encode(
            x=alt.X("Año:O", title="Año", sort=years_domain, scale=alt.Scale(domain=years_domain)),
            y=alt.Y("Curso:O", title="Curso", sort=ordered[::-1]),  # invertido: kinder abajo
            color=alt.Color("Alumnos:Q", title="Alumnos"),
            tooltip=["Año", "Curso", "Alumnos"]
        )
        .properties(height=420)
    )

    # Capa de etiquetas (números por celda)
    labels = (
        alt.Chart(long_df)
        .mark_text(baseline="middle", align="center", fontSize=11)
        .encode(
            x=alt.X("Año:O", sort=years_domain),
            y=alt.Y("Curso:O", sort=ordered[::-1]),
            text=alt.Text("Alumnos:Q", format=".0f"),
            # Si querés contraste dinámico, podés condicionar el color según 'Alumnos'
            color=alt.value("black"),
            tooltip=["Año", "Curso", "Alumnos"]
        )
    )

    heatmap_chart = heat + (labels if show_numbers else alt.Chart())

    # --- TOTALIZADOR POR COLUMNA (suma de todos los cursos por año) ---
    totals_df = (
        long_df.groupby("Año", as_index=False)["Alumnos"].sum()
        .rename(columns={"Alumnos": "Total alumnos"})
    )

    bars = (
        alt.Chart(totals_df)
        .mark_bar()
        .encode(
            x=alt.X("Año:O", sort=years_domain, scale=alt.Scale(domain=years_domain)),
            y=alt.Y("Total alumnos:Q", title="Total alumnos"),
            tooltip=["Año", "Total alumnos"]
        )
        .properties(height=160)
    )

    bars_labels = (
        alt.Chart(totals_df)
        .mark_text(dy=-8, fontSize=11)
        .encode(
            x=alt.X("Año:O", sort=years_domain),
            y="Total alumnos:Q",
            text=alt.Text("Total alumnos:Q", format=".0f")
        )
    )

    totalizer_chart = bars + bars_labels

    # --- Mostrar verticalmente: heatmap arriba + totalizador abajo ---
    st.altair_chart(alt.vconcat(heatmap_chart, totalizer_chart).resolve_scale(x='shared'), use_container_width=True)
    

with st.expander("📊 Ver tabla completa"):
    st.dataframe(df)

st.caption("Consejo: si 'Admitidos < Admitidos deseados' y la capacidad está limitando, activa 'Construcción endógena' o sube el cupo/DivG1 para ver el efecto.")
