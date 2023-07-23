# -*- coding: gbk -*-
import requests
from lxml import html

anime_list = []
def add_anime_info(anime_list, name, day_of_week, time, acover, tags):
    anime_info = {
        "name": name,
        "time": [day_of_week, time],
        "acover": acover,
        "tags": tags
    }

    anime_list.append(anime_info)

def get_imgurl_from_xpath(url):
    total_xpath = '//*[@id="acgs-anime-icons"]'
    try:
        # 发送 HTTP 请求并获取网页内容
        response = requests.get(url)

        # 确认请求成功
        response.raise_for_status()

        # 使用 lxml 解析网页内容
        tree = html.fromstring(response.content)

        # 获取当前番剧总数：
        total_number_element = tree.xpath(total_xpath)
        total_number = len(total_number_element[0])

        for i in range(1, total_number + 1):
            day_element = tree.xpath(f'//*[@id="acgs-anime-icons"]/div[{i}]/a/div[6]')
            name_element = tree.xpath(f'//*[@id="acgs-anime-icons"]/div[{i}]/a/div[3]')
            img_element = tree.xpath(f'//*[@id="acgs-anime-list"]/div[{i}]/div[1]/div/div[2]/div/img')
            tag_element = tree.xpath(f'//*[@id="acgs-anime-list"]/div[{i}]/div[1]/div/div[3]/div[2]/div[2]/div[1]')
            get_day = day_element[0].text_content()[0:1]
            time = day_element[0].text_content()[1:]
            name = name_element[0].text_content()
            url = img_element[0].get('src')
            tag = tag_element[0].text_content()
            tags = []
            for j in range(1,len(tag_element[0])+1) :
                single_tag_element = tree.xpath(f'//*[@id="acgs-anime-list"]/div[{i}]/div[1]/div/div[3]/div[2]/div[2]/div[1]/tags[{j}]')
                tags.append(single_tag_element[0].text_content())
            add_anime_info(anime_list,name,get_day,time,url,tags)

    except requests.exceptions.RequestException as e:
        print("Error fetching the URL:", e)
        return None
    except Exception as ex:
        print("An error occurred:", ex)
        return None

# 替换此 URL 为你要搜索的目标网页
url_to_search = "https://acgsecrets.hk/bangumi"  # 将 URL 替换为你要搜索的目标网页


# 调用封装的函数来搜索目标元素的 src 属性值
result_ssrc = get_imgurl_from_xpath(url_to_search)

print(anime_list)