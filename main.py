# -*- coding: utf-8 -*-

import os
import re

import PyPDF2
import requests

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "download")
BOOK_LIST_FILE = 'springer-ebooks.pdf'


def extract_book_urls(filename):
    text = ""
    with open(filename,'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        num_pages = pdf_reader.numPages
        count = 0
        while count < num_pages:
            page_obj = pdf_reader.getPage(count)
            text += page_obj.extractText()
            count +=1
    urls = re.findall('http://link.springer.com/openurl?.+', text)
    return urls


def start_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def download_book(driver: webdriver.Chrome, url: str):
    driver.get(url)
    title_h1 = _find_element(driver, By.XPATH, "//div[@class='page-title']/h1", timeout=30)
    book_title = title_h1.text  # type: str
    downloading_file_name = re.sub('[^a-zA-Z0-9.]', '_', book_title)
    pdf_link = _find_element(driver, By.LINK_TEXT, 'Download book PDF', timeout=10).get_attribute('href')
    _download_file(pdf_link, os.path.join(DOWNLOAD_FOLDER, '%s.pdf' % downloading_file_name))
    epub_btn = _find_element(driver, By.LINK_TEXT, 'Download book EPUB', timeout=1)
    if epub_btn:
        epub_link = epub_btn.get_attribute('href')
        _download_file(epub_link, os.path.join(DOWNLOAD_FOLDER, '%s.epub' % downloading_file_name))


def _download_file(url, local_path):
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        with open(local_path, 'wb') as file:
            for chunk in res.iter_content(chunk_size=10240):
                if chunk:
                    file.write(chunk)


def _find_element(driver, by, value, timeout=10):
    start_at = datetime.now()
    found_element = None
    while not found_element and (datetime.now() - start_at).total_seconds() < timeout:
        try:
            tmp_elem = WebDriverWait(driver, 0.5).until(EC.element_to_be_clickable((by, value)))
            if tmp_elem:
                found_element = tmp_elem
        except:
            pass
    return found_element


if __name__ == '__main__':
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    chrome_driver = start_browser()

    book_urls = extract_book_urls(BOOK_LIST_FILE)
    for book_url in book_urls:
        download_book(chrome_driver, book_url)

