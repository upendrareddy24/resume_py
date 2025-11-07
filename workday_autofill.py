from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class CandidateProfile:
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "CandidateProfile":
        if not data:
            raise ValueError("autofill.profile is missing or empty")
        required = ["first_name", "last_name", "email", "phone"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            raise ValueError(
                f"autofill.profile missing required fields: {', '.join(missing)}"
            )
        return cls(
            first_name=data.get("first_name", "").strip(),
            last_name=data.get("last_name", "").strip(),
            email=data.get("email", "").strip(),
            phone=data.get("phone", "").strip(),
            address=data.get("address", "").strip(),
            city=data.get("city", "").strip(),
            state=data.get("state", "").strip(),
            postal_code=data.get("postal_code", "").strip(),
            country=data.get("country", "").strip(),
        )

    def as_contact_dict(self) -> dict[str, str]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }


def is_workday_url(url: str | None) -> bool:
    if not url:
        return False
    lower = url.lower()
    patterns = (
        "myworkdayjobs.com",
        ".workdayjobs.com",
        ".workday.com",
        ".myworkday.com",
        "wd1.myworkdayjobs.com",
    )
    return any(pat in lower for pat in patterns)


class WorkdayAutofill:
    APPLY_BUTTON_SELECTORS: tuple[tuple[str, str], ...] = (
        (By.CSS_SELECTOR, "a[data-automation-id='jobPostingActionButton']"),
        (By.CSS_SELECTOR, "button[data-automation-id='jobPostingActionButton']"),
        (By.CSS_SELECTOR, "a[data-automation-id='applyButton']"),
        (By.CSS_SELECTOR, "button[data-automation-id='applyButton']"),
    )
    APPLICATION_IFRAME_SELECTORS: tuple[tuple[str, str], ...] = (
        (By.CSS_SELECTOR, "iframe[data-automation-id='webAppFrame']"),
        (By.CSS_SELECTOR, "iframe[data-automation-id='iframe']"),
        (By.CSS_SELECTOR, "iframe[src*='workdayjobs']"),
    )
    SECTION_TOGGLES: tuple[tuple[str, str], ...] = (
        (By.CSS_SELECTOR, "button[data-automation-id='myInformation']"),
        (By.CSS_SELECTOR, "div[data-automation-id='myInformationSection'] button"),
    )
    LOGIN_FIELD_SELECTORS: tuple[tuple[str, str], ...] = (
        (By.CSS_SELECTOR, "input[name='username']"),
        (By.CSS_SELECTOR, "input[data-automation-id='emailInput']"),
        (By.CSS_SELECTOR, "input[name='password']"),
    )
    TEXT_FIELD_MAP: dict[str, tuple[tuple[str, str], ...]] = {
        "first_name": (
            (By.CSS_SELECTOR, "input[data-automation-id='legalNameSection_firstName']"),
            (By.CSS_SELECTOR, "input[name*='firstName']"),
        ),
        "last_name": (
            (By.CSS_SELECTOR, "input[data-automation-id='legalNameSection_lastName']"),
            (By.CSS_SELECTOR, "input[name*='lastName']"),
        ),
        "email": (
            (By.CSS_SELECTOR, "input[data-automation-id='email']"),
            (By.CSS_SELECTOR, "input[name*='emailAddress']"),
            (By.CSS_SELECTOR, "input[type='email']"),
        ),
        "phone": (
            (By.CSS_SELECTOR, "input[data-automation-id='phoneNumber']"),
            (By.CSS_SELECTOR, "input[name*='phone']"),
        ),
        "address": (
            (By.CSS_SELECTOR, "input[data-automation-id='addressLine1']"),
            (By.CSS_SELECTOR, "input[name*='addressLine1']"),
        ),
        "city": (
            (By.CSS_SELECTOR, "input[data-automation-id='city']"),
            (By.CSS_SELECTOR, "input[name*='city']"),
        ),
        "state": (
            (By.CSS_SELECTOR, "input[data-automation-id='state']"),
            (By.CSS_SELECTOR, "input[name*='state']"),
        ),
        "postal_code": (
            (By.CSS_SELECTOR, "input[data-automation-id='postalCode']"),
            (By.CSS_SELECTOR, "input[name*='zip']"),
        ),
        "country": (
            (By.CSS_SELECTOR, "input[data-automation-id='country']"),
            (By.CSS_SELECTOR, "input[name*='country']"),
        ),
    }
    RESUME_UPLOAD_SELECTORS: tuple[tuple[str, str], ...] = (
        (By.CSS_SELECTOR, "input[type='file'][data-automation-id='resume']"),
        (By.CSS_SELECTOR, "input[type='file'][data-automation-id='resumeUpload']"),
        (By.CSS_SELECTOR, "input[type='file'][data-automation-id*='fileUploadInput']"),
        (By.CSS_SELECTOR, "input[type='file'][data-automation-id*='filePicker']"),
    )
    RESUME_TRIGGER_SELECTORS: tuple[tuple[str, str], ...] = (
        (By.CSS_SELECTOR, "button[data-automation-id='addResume']"),
        (By.CSS_SELECTOR, "div[data-automation-id='fileUploadDecorator'] button"),
    )
    COVER_LETTER_UPLOAD_SELECTORS: tuple[tuple[str, str], ...] = (
        (By.CSS_SELECTOR, "input[type='file'][data-automation-id='coverLetter']"),
        (By.CSS_SELECTOR, "input[type='file'][data-automation-id*='coverLetterUpload']"),
    )
    COVER_LETTER_TEXT_SELECTORS: tuple[tuple[str, str], ...] = (
        (By.CSS_SELECTOR, "textarea[data-automation-id='coverLetter']"),
        (By.CSS_SELECTOR, "textarea[name*='coverLetter']"),
    )

    def __init__(
        self,
        driver_factory: Callable[[], WebDriver | None],
        profile: CandidateProfile,
        wait_seconds: int = 20,
        verbose: bool = True,
    ) -> None:
        self._driver_factory = driver_factory
        self.profile = profile
        self.wait_seconds = wait_seconds
        self.verbose = verbose
        self._driver: WebDriver | None = None

    def __enter__(self) -> "WorkdayAutofill":
        self._ensure_driver()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @property
    def driver(self) -> WebDriver:
        drv = self._ensure_driver()
        if drv is None:
            raise RuntimeError("Selenium driver could not be created")
        return drv

    def close(self) -> None:
        if self._driver:
            with contextlib.suppress(WebDriverException):
                self._driver.quit()
        self._driver = None

    def _ensure_driver(self) -> WebDriver | None:
        if self._driver is None:
            drv = self._driver_factory()
            if drv is None:
                return None
            self._driver = drv
        return self._driver

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"[autofill.workday] {message}")

    def fill_application(
        self,
        job_url: str,
        resume_path: str | None = None,
        cover_letter_path: str | None = None,
    ) -> bool:
        if not job_url:
            raise ValueError("job_url is required for Workday autofill")
        driver = self.driver
        driver.get(job_url)
        time.sleep(2)
        self._wait_for_page_ready(driver)
        if self._login_required(driver):
            raise RuntimeError("Workday page requires account sign-in; manual step needed.")
        self._click_apply_button(driver)
        self._switch_to_latest_window(driver)
        switched = self._enter_application_context(driver)
        if not switched:
            self._log("Application iframe not detected; continuing in current context.")
        self._expand_sections(driver)
        self._fill_contact_information(driver)
        if resume_path:
            self._upload_resume(driver, resume_path)
        if cover_letter_path:
            self._handle_cover_letter(driver, cover_letter_path)
        with contextlib.suppress(WebDriverException):
            driver.switch_to.default_content()
        self._log("Finished autofill run.")
        return True

    def _wait_for_page_ready(self, driver: WebDriver) -> None:
        selectors = self.APPLY_BUTTON_SELECTORS + self.APPLICATION_IFRAME_SELECTORS
        if not self._wait_for_any(driver, selectors, self.wait_seconds):
            self._log("Timed out waiting for Workday page to load; continuing anyway.")

    def _wait_for_any(
        self,
        driver: WebDriver,
        selectors: Iterable[tuple[str, str]],
        timeout: int,
    ) -> bool:
        condition = self._any_present(selectors)
        try:
            WebDriverWait(driver, timeout).until(condition)
            return True
        except TimeoutException:
            return False

    @staticmethod
    def _any_present(selectors: Iterable[tuple[str, str]]):
        def _predicate(driver: WebDriver) -> bool:
            for by, selector in selectors:
                if driver.find_elements(by, selector):
                    return True
            return False

        return _predicate

    def _login_required(self, driver: WebDriver) -> bool:
        for by, selector in self.LOGIN_FIELD_SELECTORS:
            if driver.find_elements(by, selector):
                return True
        return False

    def _click_apply_button(self, driver: WebDriver) -> None:
        for by, selector in self.APPLY_BUTTON_SELECTORS:
            buttons = driver.find_elements(by, selector)
            if not buttons:
                continue
            button = buttons[0]
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            except WebDriverException:
                pass
            try:
                button.click()
                time.sleep(2)
                return
            except WebDriverException:
                continue

    def _switch_to_latest_window(self, driver: WebDriver) -> None:
        try:
            handles = driver.window_handles
        except WebDriverException:
            return
        if len(handles) > 1:
            with contextlib.suppress(WebDriverException):
                driver.switch_to.window(handles[-1])

    def _enter_application_context(self, driver: WebDriver) -> bool:
        for by, selector in self.APPLICATION_IFRAME_SELECTORS:
            frames = driver.find_elements(by, selector)
            if not frames:
                continue
            frame = frames[0]
            try:
                driver.switch_to.frame(frame)
                return True
            except WebDriverException:
                continue
        return False

    def _expand_sections(self, driver: WebDriver) -> None:
        for by, selector in self.SECTION_TOGGLES:
            buttons = driver.find_elements(by, selector)
            for button in buttons:
                try:
                    if button.get_attribute("aria-expanded") == "true":
                        continue
                except WebDriverException:
                    pass
                with contextlib.suppress(WebDriverException):
                    button.click()
                    time.sleep(0.5)

    def _fill_contact_information(self, driver: WebDriver) -> None:
        contact = self.profile.as_contact_dict()
        for key, selectors in self.TEXT_FIELD_MAP.items():
            value = contact.get(key) or ""
            if not value:
                continue
            filled = self._fill_text_field(driver, selectors, value)
            if not filled:
                self._log(f"Field '{key}' could not be located or filled.")

    def _fill_text_field(
        self,
        driver: WebDriver,
        selectors: Iterable[tuple[str, str]],
        value: str,
    ) -> bool:
        for by, selector in selectors:
            try:
                element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((by, selector))
                )
            except TimeoutException:
                continue
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", element
                )
            except WebDriverException:
                pass
            try:
                element.click()
            except WebDriverException:
                pass
            with contextlib.suppress(WebDriverException):
                element.clear()
            try:
                element.send_keys(value)
                element.send_keys(Keys.TAB)
                return True
            except WebDriverException:
                try:
                    driver.execute_script(
                        "arguments[0].value = arguments[1];"
                        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                        element,
                        value,
                    )
                    return True
                except WebDriverException:
                    continue
        return False

    def _upload_resume(self, driver: WebDriver, resume_path: str) -> bool:
        file_path = Path(resume_path).expanduser()
        if not file_path.exists():
            self._log(f"Resume file not found at {file_path}")
            return False
        self._trigger_upload(driver, self.RESUME_TRIGGER_SELECTORS)
        return self._upload_generic(driver, file_path, self.RESUME_UPLOAD_SELECTORS)

    def _handle_cover_letter(self, driver: WebDriver, cover_letter_path: str) -> bool:
        file_path = Path(cover_letter_path).expanduser()
        if not file_path.exists():
            self._log(f"Cover letter path not found at {file_path}")
            return False
        if file_path.suffix.lower() == ".txt":
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as exc:
                self._log(f"Failed to read cover letter text: {exc}")
                return False
            if self._fill_text_field(driver, self.COVER_LETTER_TEXT_SELECTORS, content):
                return True
        return self._upload_generic(driver, file_path, self.COVER_LETTER_UPLOAD_SELECTORS)

    def _trigger_upload(
        self,
        driver: WebDriver,
        selectors: Iterable[tuple[str, str]],
    ) -> None:
        for by, selector in selectors:
            buttons = driver.find_elements(by, selector)
            for button in buttons:
                with contextlib.suppress(WebDriverException):
                    button.click()
                    time.sleep(0.5)

    def _upload_generic(
        self,
        driver: WebDriver,
        path: Path,
        selectors: Iterable[tuple[str, str]],
    ) -> bool:
        for by, selector in selectors:
            inputs = driver.find_elements(by, selector)
            for upload in inputs:
                try:
                    driver.execute_script(
                        "arguments[0].style.display='block'; arguments[0].removeAttribute('hidden');",
                        upload,
                    )
                except WebDriverException:
                    pass
                try:
                    upload.send_keys(str(path))
                    time.sleep(1.5)
                    self._log(f"Uploaded file '{path.name}' via selector {selector}")
                    return True
                except (WebDriverException, StaleElementReferenceException):
                    continue
        self._log(f"No upload field matched for '{path.name}'.")
        return False

