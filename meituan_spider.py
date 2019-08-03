from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from scrapy import Selector
from models import *

import hashlib
import os
import re
import time
import json

chrome_options = Options()

# 设置headless模式，这种方式下无启动界面，能够加速程序的运行
# chrome_options.add_argument("--headless")
# 禁用gpu防止渲染图片
chrome_options.add_argument('disable-gpu')
# 设置不加载图片
chrome_options.add_argument('blink-settings=imagesEnabled=false')


# 通过页面展示的像素数计算星级
def star_num(num):
    numbers = {
        "16.8": 1,
        "33.6": 2,
        "50.4": 3,
        "67.2": 4,
        "84": 5
    }

    return numbers.get(num, 0)


# 解析商家内容
def parse(merchant_id):
    weblink = "https://www.meituan.com/meishi/{}/".format(merchant_id)
    # 启动selenium
    browser = webdriver.Chrome(executable_path="/Users/guozhaoran/python/tools/chromedriver", options=chrome_options)
    browser.get(weblink)
    # 不重复爬取数据
    hash_weblink = hashlib.md5(weblink.encode(encoding='utf-8')).hexdigest()
    existed = Merchant.select().where(Merchant.website_address_hash == hash_weblink)
    if (existed):
        print("数据已经爬取")
        os._exit(0)
    time.sleep(2)
    # print(browser.page_source)  #获取到网页渲染后的内容
    sel = Selector(text=browser.page_source)

    # 提取商家的基本信息
    # 商家名称
    name = "".join(sel.xpath("//div[@id='app']//div[@class='d-left']//div[@class='name']/text()").extract()).strip()
    detail = sel.xpath("//div[@id='app']//div[@class='d-left']//div[@class='address']//p/text()").extract()
    address = "".join(detail[1].strip())
    mobile = "".join(detail[3].strip())
    business_hours = "".join(detail[5].strip())
    # 保存商家信息
    merchant_id = Merchant.insert(name=name, address=address, website_address=weblink,
                                  website_address_hash=hash_weblink, mobile=mobile, business_hours=business_hours
                                  ).execute()

    # 获取推荐菜信息
    recommended_dish_list = sel.xpath(
        "//div[@id='app']//div[@class='recommend']//div[@class='list clear']//span/text()").extract()

    # 遍历获取到的数据，批量插入数据库
    dish_data = [{
        'merchant_id': merchant_id,
        'name': i
    } for i in recommended_dish_list]

    Recommended_dish.insert_many(dish_data).execute()

    # 也可以遍历list，一条条插入数据库
    # for dish in recommended_dish_list:
    #     Recommended_dish.create(merchant_id=merchant_id, name=dish)

    # 查看链接一共有多少页的评论
    page_num = 0
    try:
        page_num = sel.xpath(
            "//div[@id='app']//div[@class='mt-pagination']//ul[@class='pagination clear']//li[last()-1]//span/text()").extract_first()
        page_num = int("".join(page_num).strip())
        # page_num = int(page_num)
    except NoSuchElementException as e:
        print("改商家没有用户评论信息")
        os._exit(0)

    # 当有用户评论数据，每页每页的读取用户数据
    if (page_num):
        i = 1
        number_pattern = re.compile(r"\d+\.?\d*")
        chinese_pattern = re.compile(u"[\u4e00-\u9fa5]+")
        illegal_str = re.compile(u'[^0-9a-zA-Z\u4e00-\u9fa5.，,。？“”]+', re.UNICODE)
        while (i <= page_num):
            # 获取评论区元素
            all_evalutes = sel.xpath(
                "//div[@id='app']//div[@class='comment']//div[@class='com-cont']//div[2]//div[@class='list clear']")
            for item in all_evalutes:
                # 获取用户昵称
                user_name = item.xpath(".//div[@class='info']//div[@class='name']/text()").extract()[0]
                # 获取用户评价星级
                star = item.xpath(
                    ".//div[@class='info']//div[@class='source']//div[@class='star-cont']//ul[@class='stars-ul stars-light']/@style").extract_first()
                starContent = "".join(star).strip()
                starPx = number_pattern.search(starContent).group()
                starNum = star_num(starPx)
                # 获取评论时间
                comment_time = "".join(
                    item.xpath(".//div[@class='info']//div[@class='date']//span/text()").extract_first()).strip()
                evaluate_time = chinese_pattern.sub('-', comment_time, 3)[:-1] + ' 00:00:00'
                # 获取评论内容
                comment_content = "".join(
                    item.xpath(".//div[@class='info']//div[@class='desc']/text()").extract_first()).strip()
                comment_filter_content = illegal_str.sub("", comment_content)
                # 如果有图片，获取图片
                image_container = item.xpath(
                    ".//div[@class='noShowBigImg']//div[@class='imgs-content']//div[contains(@class, 'thumbnail')]//img/@src").extract()
                image_list = json.dumps(image_container)

                Evaluate.insert(merchant_id=merchant_id, user_name=user_name, evaluate_time=evaluate_time,
                                content=comment_filter_content, star=starNum, image_list=image_list).execute()
            i = i + 1
            if (i < page_num):
                next_page_ele = browser.find_element_by_xpath(
                    "//div[@id='app']//div[@class='mt-pagination']//span[@class='iconfont icon-btn_right']")
                next_page_ele.click()
                time.sleep(10)
                sel = Selector(text=browser.page_source)


if __name__ == "__main__":
    parse("5451106")
