import re
from time import sleep
from threading import Thread, Event

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class BotEngine:
    SERVICES = {
        "followers": {"title": "Followers", "selector": "t-followers-button"},
        "hearts": {"title": "Hearts", "selector": "t-hearts-button"},
        "comments_hearts": {"title": "Comments Hearts", "selector": "t-chearts-button"},
        "views": {"title": "Views", "selector": "t-views-button"},
        "shares": {"title": "Shares", "selector": "t-shares-button"},
        "favorites": {"title": "Favorites", "selector": "t-favorites-button"},
        "live_stream": {"title": "Live Stream", "selector": "t-livesteam-button"},
    }

    def __init__(self):
        self.driver = None
        self.wait = None
        self.running = False
        self.stop_event = Event()
        self.status_message = "Listo"
        self.logs = []
        self.services_status = {}

    def log(self, message: str):
        self.logs.append(message)
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
        self.status_message = message
        print(message)

    def _init_driver(self):
        options = Options()
        options.add_argument("--window-size=900,750")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 20)
        self.log("[+] Chrome iniciado")

    def _wait_for_element(self, by, value):
        try:
            return self.wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            while not self.stop_event.is_set():
                try:
                    return self.driver.find_element(by, value)
                except NoSuchElementException:
                    sleep(1)
            raise Exception("Detenido por el usuario")

    def check_services(self) -> dict:
        """Abre Zefoy, resuelve captcha (manual) y devuelve estado de servicios."""
        try:
            self._init_driver()
            self.driver.get("https://zefoy.com")
            self.log("[~] Completa el captcha en la ventana de Chrome...")

            # Esperar a que el usuario complete el captcha
            self._wait_for_element(By.LINK_TEXT, "Youtube")
            self.log("[+] Captcha resuelto")

            sleep(2)
            self.driver.refresh()
            sleep(2)
            self.driver.refresh()

            statuses = {}
            for key, info in self.SERVICES.items():
                try:
                    button = self.driver.find_element(By.CLASS_NAME, info["selector"])
                    status_text = ""
                    try:
                        parent = button.find_element(
                            By.XPATH,
                            "./ancestor::div[contains(@class,'col-') or contains(@class,'card')][1]"
                        )
                        smalls = parent.find_elements(By.TAG_NAME, "small")
                        for s in smalls:
                            txt = s.text.strip().lower()
                            if txt:
                                status_text = txt
                                break
                    except Exception:
                        pass

                    classes = (button.get_attribute("class") or "").lower()
                    is_disabled = "disabled" in classes or not button.is_enabled()

                    if "soon will be update" in status_text or "soon will be updated" in status_text:
                        statuses[key] = "offline"
                    elif is_disabled:
                        statuses[key] = "offline"
                    else:
                        statuses[key] = "online"
                except NoSuchElementException:
                    statuses[key] = "offline"

            self.services_status = statuses
            self.log("[+] Estados de servicios actualizados")
            return statuses

        except Exception as e:
            self.log(f"[x] Error al comprobar servicios: {e}")
            return {}

    def start_service(self, service_key: str, video_url: str):
        if service_key not in self.SERVICES:
            self.log("[x] Servicio no válido")
            return

        if self.running:
            self.log("[!] Ya hay un proceso en ejecución")
            return

        self.running = True
        self.stop_event.clear()
        thread = Thread(target=self._run_loop, args=(service_key, video_url), daemon=True)
        thread.start()

    def _get_container(self):
        """Obtiene el container activo (re-busca cada vez para evitar stale elements)."""
        return self._wait_for_element(
            By.CSS_SELECTOR, "div.col-sm-5.col-xs-12.p-1.container:not(.nonec)"
        )

    def _run_loop(self, service_key: str, video_url: str):
        try:
            if not self.driver:
                self.check_services()

            info = self.SERVICES[service_key]
            self.log(f"[~] Iniciando servicio: {info['title']}")

            # Click en el tab del servicio
            self._wait_for_element(By.CLASS_NAME, info["selector"]).click()
            sleep(1)

            # Poner la URL en el input — re-buscar container siempre
            container = self._get_container()
            input_element = container.find_element(By.TAG_NAME, "input")
            input_element.clear()
            input_element.send_keys(video_url)
            self.log(f"[+] URL cargada: {video_url[:55]}...")

            while not self.stop_event.is_set():
                try:
                    # Re-buscar container en cada iteración para evitar stale element
                    container = self._get_container()

                    # Click Send
                    container.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()
                    sleep(3)

                    # Re-buscar tras el click
                    container = self._get_container()

                    # Click confirm (btn-dark aparece tras el envío)
                    try:
                        container.find_element(By.CSS_SELECTOR, "button.btn.btn-dark").click()
                        self.log(f"[+] {info['title']} enviado correctamente")
                    except NoSuchElementException:
                        self.log(f"[~] {info['title']} enviado (sin confirmación)")

                    sleep(3)

                    # Re-buscar para leer el timer
                    container = self._get_container()
                    remaining = self._get_remaining_time(container)

                    if remaining:
                        minutes = remaining // 60
                        seconds = remaining % 60
                        self.log(f"[~] Esperando {minutes}m {seconds}s...")
                        for _ in range(remaining):
                            if self.stop_event.is_set():
                                break
                            sleep(1)
                    else:
                        sleep(8)

                except Exception as e:
                    self.log(f"[!] Error en ciclo: {e}")
                    sleep(5)

        except Exception as e:
            self.log(f"[x] Error fatal: {e}")
        finally:
            self.running = False
            self.log("[*] Proceso detenido")

    def _get_remaining_time(self, container):
        try:
            element = container.find_element(By.CSS_SELECTOR, "span.br")
            text = element.text
            if "Please wait" in text or "please wait" in text.lower():
                numbers = re.findall(r"\d+", text)
                if len(numbers) >= 2:
                    return int(numbers[0]) * 60 + int(numbers[1]) + 5
                elif len(numbers) == 1:
                    return int(numbers[0]) + 5
            return None
        except NoSuchElementException:
            return None

    def stop(self):
        self.stop_event.set()
        self.running = False
        self.log("[*] Deteniendo...")

    def close(self):
        self.stop()
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
        self.log("[*] Navegador cerrado")
