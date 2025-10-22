
# School Sim — Simulador de Sistema Escolar

Simulador de dinámica de sistemas para colegios: calidad, demanda, admisiones, capacidad e inversión.

## 🚀 Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app_case.py
```

## 🧠 Modelo (resumen)

- **Calidad** = base − f(hacinamiento)^γ + f(inv/alumno) + f(inv/infra) − f(1−selectividad) + (articulación+comunicación+diferenciación), con **suavizado exponencial**.
- **Precio** → sube **bajas** y encarece **CAC**.
- **Marketing** = % de facturación anterior (con mínimo).
- **Aulas**: construcción endógena si `admitidos_deseados` > capacidad G1 o si aplica la “regla de dos divisiones”.

## 📁 Estructura

```
.
├── app_case.py            # Interfaz Streamlit con parámetros agrupados en expanders
├── simulate_case.py       # Modelo ajustado
├── requirements.txt
└── README.md
```

## ☁️ Streamlit Cloud

1) Subí a GitHub. 2) Crea app apuntando a `app_case.py`. 3) Deploy automático con cada push.
