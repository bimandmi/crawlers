#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
from selenium import webdriver
from bs4 import BeautifulSoup

import re
import sys

import lxml
import utils
from settings import DIR, BASEURL, META_HEADERS, X

URL='http://likms.assembly.go.kr/bill/FinishBill.do'

def html2csv(assembly_id):

    def list_to_file(l, f):
        f.write('"')
        f.write('","'.join(l).encode('utf-8'))
        f.write('"\n')

    def getContents(one_td):
        result = ""
        if one_td.string != None:
            result = one_td.string.strip()
        return result

    def getBillId(one_href):
        result = ""
        splited = one_href.split("'")
        if splited.count >= 2:
            result = splited[1]
        return result

    def getTitileBillId(one_td):
        return one_td.a['title'], getBillId(one_td.a.attrs['href'])

    def parse_columns(columns):
        data = []

        aList = columns.find_all('td')
        bill_id         = getContents(aList[0])     # 의안번호
        title, link_id  = getTitileBillId(aList[1]) # 의안명, Link ID
        proposer_type   = getContents(aList[2])     # 제안자구분
        proposed_date   = getContents(aList[3])     # 제안일
        #submitDt        = getContents(aList[4])     # 회부일
        #committeeName   = getContents(aList[5])     # 소관위원회
        decision_date   = getContents(aList[6])     # 의결일자
        decision_result = getContents(aList[7])     # 의결결과

        status = ''
        status_detail = ''
        has_summaries = ''
        if link_id != None:
            has_summaries = '1'

        data.extend([bill_id, status, title, link_id, proposer_type, proposed_date, decision_date, decision_result, has_summaries, status_detail])

        return data

    def parse_body_of_table(one_tbody, f):
        for bdId in one_tbody.find_all('tr'):
            p = parse_columns(bdId)
            list_to_file(p, f)

    def parse_page(page, f):
        soup = BeautifulSoup(page, 'lxml')
        table = soup.find(summary="검색결과의 의안번호, 의안명, 제안자구분, 제안일, 회부일, 소관위원회, 의결일자, 의결결과 정보")
        parse_body_of_table(table.tbody, f)

    def find_next_page(driver):
        page_elem = driver.find_element_by_xpath("//div[@id='pageListViewArea']")
        all_hrefs = page_elem.find_elements_by_tag_name("a")
        for idx, href in enumerate(all_hrefs):
            if href.get_attribute("class") == 'on':
                if (idx + 1) < len(all_hrefs):
                    all_hrefs[idx + 1].click()
                    return True
        return False

    driver = webdriver.PhantomJS() # you must have phantomjs in your $PATH
    driver.get(URL)

    wanted_age = str(assembly_id)

    search_elem = driver.find_element_by_xpath("//select[@name='age']")
    all_options = search_elem.find_elements_by_tag_name("option")
    for option in all_options:
        if option.get_attribute("value") == wanted_age:
            if(option.get_attribute("selected") == None):
                option.click();
                break

    search_elem = driver.find_element_by_xpath("//select[@title='의안종류선택']")
    all_options = search_elem.find_elements_by_tag_name("option")
    for option in all_options:
        if option.get_attribute("value") == u'전체':
            if(option.get_attribute("selected") == None):
                option.click();
                break

    directory = DIR['meta']
    utils.check_dir(directory)
    meta_data = '%s/%d.csv' % (directory, assembly_id)

    print('\nParsing:')
    with open(meta_data, 'wa') as f:
        list_to_file(META_HEADERS, f)
        parse_page(driver.page_source, f)
        while find_next_page(driver) == True:
            parse_page(driver.page_source, f)

    driver.quit()

    print('\nMeta data written to ' + meta_data)
