"""Frontend Streamlit — OCR DIAN."""

import json
import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="OCR DIAN — Extracción de Facturas",
    page_icon="📄",
    layout="wide",
)

# --- Session State ---
if "token" not in st.session_state:
    st.session_state.token = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def login_form() -> None:
    """Renderiza el formulario de login."""
    st.title("📄 OCR DIAN")
    st.subheader("Extracción de Datos de Facturas Colombianas")

    with st.form("login_form"):
        username = st.text_input("Usuario", placeholder="admin")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar Sesión")

        if submitted:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/auth/login",
                    json={"username": username, "password": password},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Credenciales inválidas")
            except requests.ConnectionError:
                st.error("No se pudo conectar al servidor. Verifique que la API esté ejecutándose.")
            except Exception as e:
                st.error(f"Error: {e}")


def get_headers() -> dict:
    """Retorna headers con token JWT."""
    return {"Authorization": f"Bearer {st.session_state.token}"}


def extractor_view() -> None:
    """Vista principal del extractor."""
    st.title("📄 Extracción de Factura")

    # Upload de archivo
    uploaded_file = st.file_uploader(
        "Seleccione una factura colombiana (PDF)",
        type=["pdf"],
        help=f"Tamaño máximo: {10}MB",
    )

    if uploaded_file is not None:
        # Validar tamaño
        size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if size_mb > 10:
            st.error(f"Archivo excede el tamaño máximo de 10MB ({size_mb:.1f}MB)")
            return

        if st.button("🔍 Extraer Datos", type="primary"):
            with st.spinner("Procesando factura... Esto puede tomar unos segundos."):
                try:
                    files = {"archivo": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post(
                        f"{API_BASE_URL}/facturas/extraer",
                        files=files,
                        headers=get_headers(),
                        timeout=60,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        display_results(data)
                    elif response.status_code == 401:
                        st.error("Sesión expirada. Inicie sesión nuevamente.")
                        st.session_state.authenticated = False
                        st.session_state.token = None
                        st.rerun()
                    elif response.status_code == 413:
                        st.error("Archivo demasiado grande")
                    elif response.status_code == 422:
                        st.error("Tipo de archivo no válido. Solo se aceptan PDFs.")
                    else:
                        detail = response.json().get("detail", "Error desconocido")
                        st.error(f"Error: {detail}")

                except requests.ConnectionError:
                    st.error("No se pudo conectar al servidor.")
                except requests.Timeout:
                    st.error("Timeout — el procesamiento tardó demasiado.")
                except Exception as e:
                    st.error(f"Error inesperado: {e}")


def display_results(data: dict) -> None:
    """Muestra los resultados de la extracción."""
    st.success("✅ Extracción exitosa")

    datos = data.get("datos", data)

    # Resumen
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Emisor", datos.get("nombre_emisor", "N/A"))
        st.caption(f"NIT: {datos.get('nit_emisor', 'N/A')}")
    with col2:
        st.metric("Receptor", datos.get("nombre_receptor", "N/A"))
        st.caption(f"NIT: {datos.get('nit_receptor', 'N/A')}")
    with col3:
        st.metric("Total", f"${datos.get('total', 0):,.0f} COP")
        st.caption(f"Fecha: {datos.get('fecha_emision', 'N/A')}")

    # Detalles
    with st.expander("📋 Detalles de la Factura", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Número:** {datos.get('numero_factura', 'N/A')}")
            st.write(f"**CUFE:** {datos.get('cufe', 'N/A')}")
            st.write(f"**Método:** {datos.get('metodo_extraccion', 'N/A')}")
        with col2:
            st.write(f"**Subtotal:** ${datos.get('subtotal', 0):,.0f}")
            st.write(f"**IVA Total:** ${datos.get('iva_total', 0):,.0f}")
            confianza = datos.get("confianza", 0)
            color = "green" if confianza >= 0.8 else "orange" if confianza >= 0.5 else "red"
            st.write(f"**Confianza:** :{color}[{confianza:.0%}]")

    # Items
    items = datos.get("items", [])
    if items:
        with st.expander(f"📦 Ítems ({len(items)})"):
            for i, item in enumerate(items, 1):
                st.write(
                    f"**{i}. {item.get('descripcion', 'N/A')}** — "
                    f"Cant: {item.get('cantidad', 0)} × "
                    f"${item.get('precio_unitario', 0):,.0f} = "
                    f"${item.get('cantidad', 0) * item.get('precio_unitario', 0):,.0f} "
                    f"(IVA: ${item.get('iva', 0):,.0f})"
                )

    # JSON
    with st.expander("🔧 JSON Completo"):
        st.code(json.dumps(datos, indent=2, ensure_ascii=False), language="json")


def historial_view() -> None:
    """Vista del historial de extracciones."""
    st.title("📜 Historial de Extracciones")

    try:
        response = requests.get(
            f"{API_BASE_URL}/facturas/historial",
            headers=get_headers(),
            params={"offset": 0, "limit": 50},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            total = data.get("total", 0)

            if not items:
                st.info("No hay extracciones registradas")
                return

            st.caption(f"Total: {total} extracciones")

            for item in items:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    with col1:
                        st.write(f"**{item['nombre_archivo']}**")
                    with col2:
                        st.write(f"NIT: {item['nit_emisor']} — {item['nombre_emisor']}")
                    with col3:
                        st.write(f"${item['total']:,.0f}")
                    with col4:
                        st.write(item["estado"])
                    st.divider()

        elif response.status_code == 401:
            st.error("Sesión expirada")
            st.session_state.authenticated = False
            st.session_state.token = None
            st.rerun()
        else:
            st.error("Error cargando historial")

    except requests.ConnectionError:
        st.error("No se pudo conectar al servidor")


def main() -> None:
    """Función principal de la UI."""
    if not st.session_state.authenticated:
        login_form()
        return

    # Sidebar
    with st.sidebar:
        st.write(f"👤 **{st.session_state.get('username', 'Usuario')}**")
        if st.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            st.session_state.token = None
            st.rerun()
        st.divider()
        page = st.radio("Navegación", ["Extracción", "Historial"], index=0)

    # Contenido principal
    if page == "Extracción":
        extractor_view()
    elif page == "Historial":
        historial_view()


if __name__ == "__main__":
    main()
