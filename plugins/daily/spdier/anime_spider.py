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
    single_img_xpath = '//*[@id="acgs-anime-icons"]/div[1]/a/div[1]/img'
    single_name_xpath = '//*[@id="acgs-anime-icons"]/div[1]/a/div[3]'
    single_day_xpath = '//*[@id="acgs-anime-icons"]/div[1]'
    single_time_xpath = '//*[@id="acgs-anime-icons"]/div[1]/a/div[6]'
    single_tag_xpath = '//*[@id="acgs-anime-list"]/div[1]/div[1]/div/div[3]/div[2]/div[2]/div[1]/tags[1]'  #����tag��ַ����tag��ַΪ: //*[@id="acgs-anime-list"]/div[1]/div[1]/div/div[3]/div[2]/div[2]/div[1]
    try:
        # ���� HTTP ���󲢻�ȡ��ҳ����
        response = requests.get(url)

        # ȷ������ɹ�
        response.raise_for_status()

        # ʹ�� lxml ������ҳ����
        tree = html.fromstring(response.content)

        # ��ȡ��ǰ����������
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

# �滻�� URL Ϊ��Ҫ������Ŀ����ҳ
url_to_search = "https://acgsecrets.hk/bangumi"  # �� URL �滻Ϊ��Ҫ������Ŀ����ҳ

# Ҫ������ XPath ���ʽ

# ���÷�װ�ĺ���������Ŀ��Ԫ�ص� src ����ֵ
result_ssrc = get_imgurl_from_xpath(url_to_search)

print(anime_list)