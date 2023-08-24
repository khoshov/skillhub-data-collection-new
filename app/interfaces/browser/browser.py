"""
интерфейс для работы с веб-драйвером
"""
import os
import time
from typing import Union

import psutil
import undetected_chromedriver as uc
from selenium.common import ElementClickInterceptedException
from selenium.common.exceptions import (JavascriptException,
                                        NoSuchElementException,
                                        TimeoutException, WebDriverException)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from app.config import logger
from app.interfaces.browser.exceptions import (BrowserNotFound,
                                               RaiseDriverException,
                                               ReadlonlyFileSystemException)
from app.interfaces.browser.scripts import scrolling_page_script

PAGE_LOAD_TIMEOUT_SEC = 30
MAXIMUM_RESTART_ATTEMPS = 10


class BrowserInterface:
    """Chrome-интерфейс для работы с JS-сайтами"""

    def __init__(
        self,
        driver_path: str = None,
        logger_client=logger,
    ):
        self.driver = self._downloads_cnt = self._chrome_pid = self._wait = None
        self._logger = logger_client
        self._driver_path = driver_path
        # запускаем браузер
        try:
            self.launch_browser()
        except WebDriverException as error:
            self._logger.error(f"Ошибка запуска driver: {str(error)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self.driver:
            self.driver.close()
            self.driver.quit()

    def get_driver(self):
        """Инициализирует вебдрайвер"""
        if self._driver_path:
            driver = uc.Chrome(
                driver_executable_path=self._driver_path,
                headless=True,
                use_subprocess=False,
            )
        else:
            service = Service(executable_path=ChromeDriverManager().install())
            driver = uc.Chrome(
                headless=True,
                driver_executable_path=service.path,
                use_subprocess=False,
            )
        return driver

    def launch_browser(
        self, max_attemps=MAXIMUM_RESTART_ATTEMPS, previous_error=None
    ) -> None:
        """Запускает WebDriver"""
        if previous_error:
            self._logger.info(f"driver launch attemp failed{previous_error}")
        if max_attemps < 1:
            raise WebDriverException(
                f"Chrome failed to start after {MAXIMUM_RESTART_ATTEMPS} attemps {previous_error}"
            )
        self._downloads_cnt = 0
        try:
            driver = self.get_driver()

        except WebDriverException as error:
            exception_text = str(error)
            if "Chrome failed to start" in str(error):
                if "cannot create temp dir for user data dir" in str(error):
                    raise ReadlonlyFileSystemException(error) from error
                return self.launch_browser(
                    max_attemps=max_attemps - 1, previous_error=str(error)
                )

            if "cannot find Chrome binary" in str(error):
                self._logger.info(
                    f"Не найден браузер Chrome: {exception_text}")
                raise BrowserNotFound(
                    f"Не найден браузер Chrome: {exception_text}"
                ) from error
            raise WebDriverException(error) from error
        except Exception as error:
            common_exception_text = str(error)
            self._logger.error(
                f"необработанная ошибка драйвера: {common_exception_text}"
            )
            raise RaiseDriverException(
                f"необработанная ошибка драйвера: {common_exception_text}"
            ) from error
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SEC)
        if hasattr(driver, "service"):
            self._chrome_pid = driver.service.process.pid
        self.driver = driver
        self._wait = WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT_SEC)

    def relaunch_browser(self) -> None:
        """Перезапускает браузер"""
        if hasattr(self.driver, "service"):
            self.kill_chrome()
        self.driver.quit()
        try:
            self.launch_browser()
        except WebDriverException as error:
            self._logger.error(f"Ошибка запуска браузера:{error}")

    def scroll_down(self, wait: int = 1) -> None:
        """Плавно скроллит вниз, чтобы зацепить все JS-триггеры"""
        for item in ("1/2", "2/2"):
            script = scrolling_page_script.format(
                direction="top", offset=f"{item}*h"
            )

            try:
                self.driver.execute_script(script)
            except JavascriptException as jserr:
                self._logger.error(
                    "Ошибка плавной прокрутки JS вниз: " + str(jserr)
                )
            time.sleep(wait)

    def scroll_up(self, wait: int = 1) -> None:
        """Плавно скроллит вверх"""
        for item in ("1/2", "2/2"):
            script = scrolling_page_script.format(
                direction="top", offset=f"-{item}*h"
            )

            try:
                self.driver.execute_script(script)
            except JavascriptException as jserr:
                self._logger.error(
                    "Ошибка плавной прокрутки JS вверх: " + str(jserr)
                )
            time.sleep(wait)

    def find_by_xpath(self, value: str) -> WebElement:
        """Получение элемента через XPATH."""
        return self.driver.find_element(By.XPATH, value)

    def find_elements_by_xpath(self, value: str) -> WebElement:
        """Получение списка элементов через XPATH."""
        return self.driver.find_elements(By.XPATH, value)

    def wait_clickable_element(self, xpath: str) -> WebElement:
        """Ожидание появления элемента"""
        return self._wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

    async def click_actions(self, xpath: str) -> None:
        """
        Для имитации действий пользователя наводит курсор браузера на элемент
        и кликает по нему
        """
        try:
            button = self.wait_clickable_element(xpath)
            actions = ActionChains(self.driver)
            actions.move_to_element(button)
            actions.click(button)
            actions.perform()
        except (NoSuchElementException, TimeoutException) as error:
            raise error
        except ElementClickInterceptedException as error:
            raise error
        except WebDriverException as error:
            raise error

    def _find_element(self, selector: str) -> Union[WebElement, None]:
        """Находит элемент по CSS-селектору"""
        return self._find_element_by(By.CSS_SELECTOR, selector)

    def _find_element_by(
        self, by_type: By, selector: str
    ) -> WebElement | None:
        """Находит элемент по типу выбора By Selenium пр:By.CSS_SELECTOR"""
        try:
            element = self.driver.find_element(by_type, selector)
        except TimeoutException:
            self._logger.error(f"Элемент {selector} не найден")
            return None
        except NoSuchElementException:
            return None
        return element

    def close(self):
        """Закрывает WebDriver"""
        if self.driver:
            self.driver.close()
            self.driver.quit()

    def kill_chrome(self):
        """Находит и гасит процессы текущего Chrome"""
        try:
            parent = psutil.Process(self._chrome_pid)
        except psutil.NoSuchProcess:  # процесса уже нет
            return
        for child in parent.children(recursive=True):
            try:
                os.kill(child.pid, 9)
            except ProcessLookupError:
                pass
            self._logger.debug("Процессы BROWSER Chrome были убиты")

    def __del__(self):
        if self.driver:
            self.driver.quit()

        if self._chrome_pid:
            self.kill_chrome()
