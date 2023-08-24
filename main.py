from app.interfaces.browser.browser import BrowserInterface


def test_browser():
    url = 'https://bot.sannysoft.com/'
    browser_interface = BrowserInterface()
    print(browser_interface.driver)
    browser = browser_interface.driver
    browser.get(url)
    browser.save_screenshot('screen.png')


if __name__ == '__main__':
    test_browser()
