from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List, Callable
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
import time
import sys
from enum import Enum, auto
import time

# Configure logging with more detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_execution.log')
    ]
)
logger = logging.getLogger(__name__)

class TestResult(Enum):
    """Enumeration for test results"""
    PASSED = auto()
    FAILED = auto()
    SKIPPED = auto()

@dataclass
class TestStep:
    """Data class for test steps"""
    name: str
    function: Callable
    description: str

class WebDriverFactory:
    """Factory class for creating WebDriver instances"""
    
    @staticmethod
    def create_chrome_driver(headless: bool = False) -> webdriver.Chrome:
        """Create and configure a Chrome WebDriver instance"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--start-maximized')

        driver = webdriver.Remote(
            command_executor='http://chrome:4444/wd/hub',
            desired_capabilities=DesiredCapabilities.CHROME,
            options=chrome_options
        )
        return driver
    
class BasePage:
    """Enhanced base class for all page objects"""
    
    def __init__(self, driver: webdriver.Chrome, timeout: int = 20):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.timeout = timeout
    
    def find_element(self, by: By, locator: str, timeout: Optional[int] = None) -> webdriver.Remote:
        """Wait for and return an element with custom timeout"""
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        return wait.until(EC.presence_of_element_located((by, locator)))
    
    def find_clickable(self, by: By, locator: str, timeout: Optional[int] = None) -> webdriver.Remote:
        """Wait for and return a clickable element with custom timeout"""
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        return wait.until(EC.element_to_be_clickable((by, locator)))
        
    
    def safe_click(self, element: webdriver.Remote, retry_attempts: int = 10, retry_delay: float = 1.0) -> bool:
        """Enhanced safe click with configurable retry delay"""
        for attempt in range(retry_attempts):
            try:
                if attempt > 0:
                    time.sleep(retry_delay)
                element.click()
                return True
            except ElementClickInterceptedException:
                logger.warning(f"Click intercepted, attempt {attempt + 1}/{retry_attempts}")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            except Exception as e:
                logger.error(f"Click failed: {str(e)}, attempt {attempt + 1}/{retry_attempts}")
                if attempt == retry_attempts - 1:
                    raise
        return False
    
    def is_element_visible(self, by: By, locator: str, timeout: Optional[int] = None) -> bool:
        """Check if element is visible"""
        try:
            wait = WebDriverWait(self.driver, timeout or self.timeout)
            wait.until(EC.visibility_of_element_located((by, locator)))
            return True
        except TimeoutException:
            return False

    def wait_for_url_contains(self, partial_url: str, timeout: Optional[int] = None) -> bool:
        """Wait for URL to contain specific text"""
        try:
            WebDriverWait(self.driver, timeout or self.timeout).until(
                EC.url_contains(partial_url)
            )
            return True
        except TimeoutException:
            return False

class HomePage(BasePage):
    """Page object for the Insider homepage"""
    
    URL = "https://useinsider.com/"
    
    LOCATORS = {
        'logo': (By.CLASS_NAME, "navbar-brand"),
        'company_dropdown': (By.XPATH, "/html/body/nav/div[2]/div/ul[1]/li[6]/a"),
        'careers_link': (By.XPATH, "//a[contains(text(), 'Careers')]"),
        'menu_items': (By.CSS_SELECTOR, ".nav-link"),
        'company_submenu': (By.CSS_SELECTOR, "#navbarDropdownMenuLink + .dropdown-menu"),
        # Adding career page verification locators
        'locations_block': (By.XPATH, "//h3[contains(text(), 'Our Locations')]"),
        'teams_block': (By.XPATH, "//h3[contains(text(), 'Find your calling')]"),
        'life_at_insider_block': (By.XPATH, "//h2[contains(text(), 'Life at Insider')]")
    }
    
    def __init__(self, driver):
        """Initialize HomePage with WebDriver instance"""
        super().__init__(driver)
        self.driver = driver

    def navigate(self) -> bool:
        """
        Navigate to homepage
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            self.driver.get(self.URL)
            return self.is_loaded()
        except Exception as e:
            logger.error(f"Navigation to homepage failed: {str(e)}")
            return False

    def is_loaded(self) -> bool:
        """
        Verify if homepage is loaded by checking essential elements
        Returns:
            bool: True if page is loaded, False otherwise
        """
        try:
            return all([self.is_element_visible(*self.LOCATORS['logo'])])
        except TimeoutException as e:
            logger.error(f"Homepage failed to load: {str(e)}")
            return False

    def click_navigation_item(self, locator_key: str) -> bool:
        """
        Generic method to click navigation items
        Args:
            locator_key: Key for the locator in LOCATORS dictionary
        Returns:
            bool: True if click successful, False otherwise
        """
        try:
            element = self.find_clickable(*self.LOCATORS[locator_key])
            self.safe_click(element)
            return True
        except Exception as e:
            logger.error(f"Failed to click {locator_key}: {str(e)}")
            return False

    def click_company_menu(self) -> bool:
        """
        Click the 'Company' dropdown in the navigation bar
        Returns:
            bool: True if click successful, False otherwise
        """
        return self.click_navigation_item('company_dropdown')

    def click_careers_menu(self) -> bool:
        """
        Click the 'Careers' link in the navigation bar
        Returns:
            bool: True if click successful, False otherwise
        """
        return self.click_navigation_item('careers_link')

    def is_company_dropdown_expanded(self) -> bool:
        """
        Check if company dropdown is expanded
        Returns:
            bool: True if dropdown is expanded, False otherwise
        """
        try:
            element = self.find_element(*self.LOCATORS['company_dropdown'])
            return element.get_attribute('aria-expanded') == 'true'
        except Exception as e:
            logger.error(f"Failed to check dropdown state: {str(e)}")
            return False

    def get_company_submenu_items(self) -> Optional[list]:
        """
        Get list of company submenu items
        Returns:
            Optional[list]: List of submenu items if found, None otherwise
        """
        try:
            submenu = self.find_element(*self.LOCATORS['company_submenu'])
            items = submenu.find_elements(*self.LOCATORS['menu_items'])
            return [item.text for item in items]
        except Exception as e:
            logger.error(f"Failed to get submenu items: {str(e)}")
            return None

    def verify_career_blocks_displayed(self) -> bool:
        """
        Verify if all career page blocks are displayed
        Returns:
            bool: True if all blocks are displayed, False otherwise
        """
        try:
            blocks_visible = all([
                self.is_element_visible(*self.LOCATORS['locations_block']),
                self.is_element_visible(*self.LOCATORS['teams_block']),
                self.is_element_visible(*self.LOCATORS['life_at_insider_block'])
            ])
            return blocks_visible
        except Exception as e:
            logger.error(f"Failed to verify career blocks: {str(e)}")
            return False

class CareersPage(BasePage):
    """Page object for the Careers page"""
    
    URL = "https://useinsider.com/careers/quality-assurance/"
    LOCATORS = {
        'cookie_accept': (By.XPATH, "//*[@id='wt-cli-accept-all-btn']"),
        'see_all_qa_jobs': (By.XPATH, "//a[contains(text(), 'See all QA jobs')]"),
        'location_filter': (By.XPATH, "//span[contains(@id, 'select2-filter-by-location-container')]"),
        'istanbul_option': (By.XPATH, "//li[contains(text(), 'Istanbul, Turkey')]"),
        'department_filter': (By.XPATH, "//span[contains(@id, 'select2-filter-by-department-container')]"),
        'qa_option': (By.XPATH, "//li[contains(text(), 'Quality Assurance')]"),
        'jobs_list': (By.XPATH, "/html/body/section[3]/div/div/div[2]/div/div/span"),
        'view_role': (By.CSS_SELECTOR, ".position-list-item-wrapper .btn.btn-navy")
    }
    
    def navigate(self) -> bool:
        """Navigate to careers page"""
        try:
            self.driver.get(self.URL)
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to careers page: {str(e)}")
            return False

    def accept_cookies(self) -> bool:
        """Accept cookies on the page"""
        try:
            button = self.find_clickable(*self.LOCATORS['cookie_accept'])
            return self.safe_click(button)
        except Exception as e:
            logger.error(f"Failed to accept cookies: {str(e)}")
            return False

    def click_see_all_qa_jobs(self) -> bool:
        """Click the 'See all QA jobs' button"""
        try:
            button = self.find_clickable(*self.LOCATORS['see_all_qa_jobs'])
            return self.safe_click(button)
        except Exception as e:
            logger.error(f"Failed to click 'See all QA jobs': {str(e)}")
            return False

    def select_location(self, location: str = "Istanbul, Turkey") -> bool:
        """Select location from the filter"""
        try:
            time.sleep(10)
            self.safe_click(self.find_clickable(*self.LOCATORS['location_filter']))
            self.safe_click(self.find_clickable(*self.LOCATORS['istanbul_option']))
            return True
        except Exception as e:
            logger.error(f"Failed to select location: {str(e)}")
            return False

    def select_department(self) -> bool:
        """Select QA department from the filter"""
        try:
            self.safe_click(self.find_clickable(*self.LOCATORS['department_filter']))
            self.safe_click(self.find_clickable(*self.LOCATORS['qa_option']))
            return True
        except Exception as e:
            logger.error(f"Failed to select department: {str(e)}")
            return False

    def view_first_role(self) -> bool:
        """Click first available 'View Role' button and verify Lever Application form"""
        try:
            time.sleep(10)
            buttons = self.driver.find_elements(*self.LOCATORS['view_role'])
            if not buttons:
                logger.error("No 'View Role' buttons found")
                return False
            
            time.sleep(10)
            original_window = self.driver.current_window_handle
            if len(self.driver.window_handles) != 1:
                logger.warning("Multiple tabs open before clicking View Role")
                return False
            
            self.safe_click(buttons[0])
            
            # Wait for new tab and switch to it
            if not WebDriverWait(self.driver, self.timeout).until(
                lambda d: len(d.window_handles) > 1
            ):
                return False
            
            new_window = [w for w in self.driver.window_handles if w != original_window][0]
            self.driver.switch_to.window(new_window)
            
            # Verify Lever form loaded
            if not self.wait_for_url_contains("jobs.lever.co"):
                return False
            
            logger.info("Successfully navigated to Lever Application form")
            self.driver.close()
            self.driver.switch_to.window(original_window)
            return True
            
        except Exception as e:
            logger.error(f"Failed to view role: {str(e)}")
            return False

class InsiderWebsiteTest:
    """Main test class for Insider website automation"""
    
    def __init__(self, headless: bool = False):
        self.driver = WebDriverFactory.create_chrome_driver(headless)
        self.home_page = HomePage(self.driver)
        self.careers_page = CareersPage(self.driver)
        self.test_results: Dict[str, TestResult] = {}
    
    def run_test_step(self, step: TestStep) -> bool:
        """Execute a single test step with logging"""
        logger.info(f"Executing step: {step.description}")
        try:
            result = step.function()
            if not result:
                logger.error(f"Step failed: {step.description}")
            return result
        except Exception as e:
            logger.error(f"Step failed with exception: {step.description}\n{str(e)}")
            return False
    
    def test_homepage_loading(self) -> bool:
        """Test homepage loading"""
        steps = [
            TestStep("navigate", self.home_page.navigate, "Navigating to homepage"),
            TestStep("verify", self.home_page.is_loaded, "Verifying homepage loaded"),
            TestStep("company_menu", self.home_page.click_company_menu, "Clicking 'Company' menu"),
            TestStep("careers_menu", self.home_page.click_careers_menu, "Clicking 'Careers' menu")
        ]
        
        for step in steps:
            if not self.run_test_step(step):
                self.test_results["Homepage Test"] = TestResult.FAILED
                return False
        
        self.test_results["Homepage Test"] = TestResult.PASSED
        return True

    def test_qa_jobs_filtering(self) -> bool:
        """Test QA jobs filtering functionality"""
        steps = [
            TestStep("navigate", self.careers_page.navigate, "Navigating to careers page"),
            TestStep("cookies", self.careers_page.accept_cookies, "Accepting cookies"),
            TestStep("qa_jobs", self.careers_page.click_see_all_qa_jobs, "Clicking 'See all QA jobs'"),
            TestStep("location", self.careers_page.select_location, "Selecting location"),
            TestStep("department", self.careers_page.select_department, "Selecting department"),
            TestStep("view_role", self.careers_page.view_first_role, "Viewing first role")
        ]
        
        for step in steps:
            if not self.run_test_step(step):
                self.test_results["QA Jobs Test"] = TestResult.FAILED
                return False
        
        self.test_results["QA Jobs Test"] = TestResult.PASSED
        return True

    def teardown(self):
        """Clean up resources"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def run_tests(headless: bool = False):
    """Execute all tests and print results"""
    test = InsiderWebsiteTest(headless)
    try:
        logger.info("Starting test execution...")
        
        test.test_homepage_loading()
        test.test_qa_jobs_filtering()
        
        # Print test results
        logger.info("\nTest Results:")
        for test_name, result in test.test_results.items():
            symbol = "✅" if result == TestResult.PASSED else "❌"
            logger.info(f"{test_name}: {result.name} {symbol}")
            
    finally:
        test.teardown()
        logger.info("Test execution completed!")

if __name__ == "__main__":
    run_tests()
