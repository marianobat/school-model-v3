
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any

@dataclass
class Params:
    # --- Horizonte y estado inicial ---
    anios: int = 10
    alumnos_inicial_por_grado: int = 20
    demanda_inicial: int = 300
    divisiones_iniciales: int = 1

    # --- Capacidad y aulas ---
    cupo_optimo: int = 25
    cupo_maximo: int = 30
    capex_aula: float = 100000.0
    costo_docente_por_aula: float = 60000.0
    sueldos_no_docentes: float = 120000.0
    mantenimiento_prop: float = 0.03
    trigger_auto_aula: bool = True
    regla_dos_div: bool = True

    # --- Demanda y Marketing ---
    prop_mkt: float = 0.05
    mkt_floor: float = 2000.0
    cac_base: float = 200.0
    k_saturacion: float = 0.5
    k_calidad_candidatos: float = 0.8

    # --- Precio y Retención ---
    cuota_mensual: float = 50.0
    meses_cobro: int = 10
    ref_precio: float = 50.0
    k_bajas_precio: float = 0.08
    k_precio_cac: float = 0.5
    tasa_bajas_base: float = 0.04
    k_bajas_calidad: float = 0.12

    # --- Admisiones ---
    politica_seleccion: float = 0.7
    admitidos_max_abs: int = -1

    # --- Calidad y reputación ---
    calidad_base: float = 0.7
    k_hacinamiento: float = 1.0
    gamma_hacinamiento: float = 1.3
    k_inv_alumno: float = 0.3
    ref_inv_alumno: float = 200.0
    k_inv_infra: float = 0.2
    ref_inv_infra: float = 50000.0
    k_selectividad: float = 0.2
    alpha_calidad: float = 0.4

    # Factores blandos (0..1) y sus pesos
    nivel_articulacion: float = 0.20
    nivel_comunicacion: float = 0.20
    nivel_diferenciacion: float = 0.20
    k_articulacion: float = 0.05
    k_comunicacion: float = 0.05
    k_diferenciacion: float = 0.05

def simulate(par: Params) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    G = np.zeros((par.anios, 12))
    Div = np.zeros((par.anios, 12), dtype=int)
    calidad = np.zeros(par.anios)
    Demanda = np.zeros(par.anios)
    Marketing = np.zeros(par.anios)
    CAC = np.zeros(par.anios)
    admitidos = np.zeros(par.anios)
    admitidos_deseados = np.zeros(par.anios)
    nuevos_candidatos = np.zeros(par.anios)
    candidatos_pago = np.zeros(par.anios)
    candidatos_organico = np.zeros(par.anios)
    tasa_bajas = np.zeros(par.anios)
    inv_infra = np.zeros(par.anios)
    inv_calidad_alumno = np.zeros(par.anios)
    hac_prom_hist = np.zeros(par.anios)
    selectividad_hist = np.zeros(par.anios)
    capacidad_binding = np.zeros(par.anios, dtype=bool)
    demanda_binding = np.zeros(par.anios, dtype=bool)

    G[0, :] = par.alumnos_inicial_por_grado
    Div[0, :] = par.divisiones_iniciales
    calidad[0] = par.calidad_base
    Demanda[0] = max(par.demanda_inicial, G[0, :].sum() + 50)
    fact_prev = G[0, :].sum() * par.cuota_mensual * par.meses_cobro
    Marketing[0] = max(par.mkt_floor, par.prop_mkt * fact_prev)

    for k in range(par.anios):
        alumnos_k = float(G[k, :].sum())
        if k > 0:
            Demanda[k] = max(Demanda[k-1] + 10*calidad[k-1] - 0.05*alumnos_k, alumnos_k + 20)

        saturacion = 0.0 if Demanda[k] <= 0 else (alumnos_k / max(Demanda[k], 1e-9))
        CAC[k] = par.cac_base * (1.0 + par.k_saturacion * saturacion)
        precio_rel = par.cuota_mensual / max(par.ref_precio, 1e-9)
        CAC[k] *= (1.0 + par.k_precio_cac * max(precio_rel - 1.0, 0.0))

        if k > 0:
            fact_prev = G[k-1, :].sum() * par.cuota_mensual * par.meses_cobro
            Marketing[k] = max(par.mkt_floor, par.prop_mkt * fact_prev)

        candidatos_pago[k] = Marketing[k] / max(CAC[k], 1e-9)
        candidatos_organico[k] = par.k_calidad_candidatos * (calidad[k-1] if k > 0 else calidad[0])
        nuevos_candidatos[k] = max(0.0, candidatos_pago[k] + candidatos_organico[k])

        capacidad_g1 = int(Div[k, 0] * par.cupo_maximo)
        gap_demanda = max(Demanda[k] - alumnos_k, 0.0)
        cap_politica = par.politica_seleccion * nuevos_candidatos[k]
        if par.admitidos_max_abs >= 0:
            cap_politica = min(cap_politica, float(par.admitidos_max_abs))
        admitidos_deseados[k] = min(cap_politica, gap_demanda)
        admitidos[k] = min(admitidos_deseados[k], float(capacidad_g1))

        build = False
        if par.trigger_auto_aula:
            exceso_g1 = max(admitidos_deseados[k] - float(capacidad_g1), 0.0)
            if (par.regla_dos_div and admitidos_deseados[k] >= 2 * par.cupo_maximo) or (exceso_g1 > 0):
                build = True
        if build:
            inv_infra[k] += par.capex_aula
            if k < par.anios - 1:
                Div[k, 0] += 1

        div_valid = np.maximum(Div[k, :], 1e-9)
        ratio = G[k, :] / (div_valid * par.cupo_optimo)
        exceso = np.clip(ratio - 1.0, 0.0, None)
        hac_prom = 0.0 if alumnos_k <= 0 else float(np.mean(exceso))
        if par.gamma_hacinamiento != 1.0 and hac_prom > 0:
            hac_prom = hac_prom ** par.gamma_hacinamiento
        hac_prom_hist[k] = hac_prom

        inv_calidad_alumno[k] = 0.5 * Marketing[k]
        inv_alum_norm = 0.0
        if alumnos_k > 0:
            inv_alum_norm = (inv_calidad_alumno[k] / max(alumnos_k, 1e-9)) / max(par.ref_inv_alumno, 1e-9)
        inv_infra_norm = (inv_infra[k] / max(par.ref_inv_infra, 1e-9))

        selectividad = 0.0 if nuevos_candidatos[k] <= 0 else (admitidos[k] / max(nuevos_candidatos[k], 1e-9))
        selectividad = float(np.clip(selectividad, 0.0, 1.0))
        selectividad_hist[k] = selectividad

        articulacion = np.clip(par.nivel_articulacion, 0.0, 1.0)
        comunicacion = np.clip(par.nivel_comunicacion, 0.0, 1.0)
        diferenciacion = np.clip(par.nivel_diferenciacion, 0.0, 1.0)

        calidad_inst = (
            par.calidad_base
            - par.k_hacinamiento * hac_prom
            + par.k_inv_alumno * inv_alum_norm
            + par.k_inv_infra * inv_infra_norm
            - par.k_selectividad * (1.0 - selectividad)
            + par.k_articulacion * articulacion
            + par.k_comunicacion * comunicacion
            + par.k_diferenciacion * diferenciacion
        )
        prev_c = calidad[k-1] if k > 0 else par.calidad_base
        calidad[k] = float(np.clip(prev_c + par.alpha_calidad * (calidad_inst - prev_c), 0.0, 1.0))

        tasa = (
            par.tasa_bajas_base
            + (1.0 - calidad[k]) * par.k_bajas_calidad
            + max(precio_rel - 1.0, 0.0) * par.k_bajas_precio
        )
        tasa = float(np.clip(tasa, 0.0, 0.5))
        tasa_bajas[k] = tasa
        bajas_tot = tasa * alumnos_k

        next_row = np.zeros(12)
        next_row[0] = admitidos[k]
        for gi in range(1, 12):
            base = G[k, gi-1]
            if alumnos_k > 0:
                bajas_prev = (G[k, gi-1] / alumnos_k) * bajas_tot
            else:
                bajas_prev = 0.0
            next_row[gi] = max(base - bajas_prev, 0.0)
        if k < par.anios - 1:
            G[k+1, :] = next_row
            Div[k+1, :] = Div[k, :]

        capacidad_binding[k] = admitidos[k] < admitidos_deseados[k]
        demanda_binding[k] = (G[k, :].sum() >= Demanda[k] - 1e-6)

    alumnos_tot = np.array([G[i, :].sum() for i in range(par.anios)])
    facturacion = alumnos_tot * par.cuota_mensual * par.meses_cobro
    sueldos_docentes = np.sum(Div, axis=1) * par.costo_docente_por_aula
    costos = sueldos_docentes + par.sueldos_no_docentes + par.mantenimiento_prop * facturacion + Marketing
    resultado = facturacion - costos - inv_infra

    df = pd.DataFrame({
        "anio": np.arange(par.anios),
        "alumnos_totales": alumnos_tot,
        "calidad": calidad,
        "tasa_bajas": tasa_bajas,
        "nuevos_candidatos": nuevos_candidatos,
        "candidatos_pago": candidatos_pago,
        "candidatos_organico": candidatos_organico,
        "admitidos_deseados": admitidos_deseados,
        "admitidos": admitidos,
        "Demanda": Demanda,
        "Marketing": Marketing,
        "CAC": CAC,
        "DivG1": Div[:, 0],
        "AulasTotales": Div.sum(axis=1),
        "hacinamiento_prom": hac_prom_hist,
        "selectividad": selectividad_hist,
        "capacidad_binding": capacidad_binding.astype(int),
        "demanda_binding": demanda_binding.astype(int),
        "facturacion": facturacion,
        "sueldos_docentes": sueldos_docentes,
        "costos_totales": costos,
        "resultado": resultado,
    })
    extras = {"G": G, "Div": Div, "params": asdict(par)}
    return df, extras
