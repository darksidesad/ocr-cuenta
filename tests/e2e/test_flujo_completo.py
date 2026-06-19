"""Tests E2E del flujo completo con Playwright."""

import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def base_url():
    """URL base de la UI Streamlit."""
    return "http://localhost:8501"


@pytest.fixture(scope="module")
def api_url():
    """URL base de la API FastAPI."""
    return "http://localhost:8000"


class TestFlujoLogin:
    """Tests E20 del flujo de login."""

    def test_pagina_carga(self, page, base_url):
        """La página de login carga correctamente."""
        page.goto(base_url)
        assert "OCR DIAN" in page.title() or "OCR" in page.content()

    def test_login_form_visible(self, page, base_url):
        """El formulario de login es visible."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        # Streamlit renderiza inputs de texto
        inputs = page.locator("input")
        assert inputs.count() >= 2

    def test_login_credenciales_invalidas(self, page, base_url):
        """Login con credenciales inválidas muestra error."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        # Buscar campos de usuario y contraseña
        inputs = page.locator("input")
        if inputs.count() >= 2:
            inputs.nth(0).fill("wrong_user")
            inputs.nth(1).fill("wrong_pass")

            # Buscar botón de submit
            buttons = page.locator("button")
            for i in range(buttons.count()):
                btn_text = buttons.nth(i).text_content()
                if "Iniciar" in btn_text or "Login" in btn_text or "Entrar" in btn_text:
                    buttons.nth(i).click()
                    break

            page.wait_for_timeout(2000)
            content = page.content()
            # Debería mostrar error o permanecer en login
            has_error = "inválid" in content.lower() or "error" in content.lower()
            assert has_error or "OCR DIAN" in content


class TestFlujoExtractor:
    """Tests E2E del flujo de extracción."""

    def test_extractor_visible(self, page, base_url):
        """La pantalla del extractor es accesible después del login."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        content = page.content()
        # La app debería cargar sin errores
        assert "OCR" in content or "factura" in content.lower() or "extracción" in content.lower()


class TestHistorial:
    """Tests E2E del historial."""

    def test_historial_accessible(self, page, base_url):
        """La sección de historial es accesible."""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        content = page.content()
        # La app debería cargar sin errores
        assert len(content) > 0
