# -*- coding: utf-8 -*-
import config
from twitter import *
from bs4 import BeautifulSoup
import requests
from urllib.request import build_opener, HTTPCookieProcessor
from urllib.parse import urlencode, parse_qs
from http.cookiejar import CookieJar
import re
import json
import time
import datetime


def main():
    try:
        dlsite_floor_list = ['home', 'home-touch', 'eng', 'eng-touch']
        locale_list = [{'locale': 'ja-jp'}, {'locale': 'zh-cn'}, {'locale': 'zh-tw'}, {'locale': 'ko-kr'}, {'locale': 'en-us'}]
        is_flug = 'false'
        error_title = []
        error_lang = []
        error_floor = []
        count = 0
        opener = build_opener(HTTPCookieProcessor(CookieJar()))

        ##################################
        #  DLsite
        ##################################
        # フロア毎に監視
        for dlsite_floor in dlsite_floor_list:
            # 多言語毎に監視
            for cookie_locale in locale_list:
                # 英語フロアはcookie出しわけ不要
                if (dlsite_floor == 'eng' and cookie_locale['locale'] != 'ja-jp') or (dlsite_floor == 'eng-touch' and cookie_locale['locale'] != 'ja-jp'):
                    continue
                # URL
                url = "https://www.dlsite.com/" + dlsite_floor
                # URLにアクセス
                response = requests.get(url=url, cookies=cookie_locale)
                html = response.content
                # HTMLをBeautifulSoupで扱う
                soup_html = BeautifulSoup(html, "html.parser")

                # job_list_item newクラスを前取得
                job_list_item = soup_html.find_all(
                    'li', class_='job_list_item new')

                for job_html in job_list_item:
                    job_name = job_html.find('p', class_='job_name').get_text()
                    # hrmosのURLを取得
                    url = job_html.a.get("href")
                    # hrmosにアクセス
                    resp = requests.get(url)
                    print(dlsite_floor + '（' + cookie_locale['locale'] + '）' + job_name)
                    # hrmosのステータスコードチェック
                    if resp.status_code == 404:
                        is_flug = 'true'
                        error_title.append(job_name)
                        error_lang.append(cookie_locale['locale'])
                        count = count + 1
                time.sleep(10)

        ##################################
        #  天気
        ##################################
        url = 'https://weather.yahoo.co.jp/weather/jp/13/4410.html'

        response = requests.get(url=url)
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')

        # 今日の天気
        tenki_today = soup.select_one('#main > div.forecastCity > table > tr > td > div > p.pict')
        # 明日の天気
        tenki_tomorrow = soup.select_one('#main > div.forecastCity > table > tr > td + td > div > p.pict')

        ##################################
        #  ツイート
        ##################################
        date = datetime.datetime.now()
        week_list = ['月', '火', '水', '木', '金', '土', '日']
        now_week = datetime.datetime.now().weekday()
        youbi = '(' + week_list[now_week] + ')'
        now = str(date.month) + '月' + str(date.day) + '日' + youbi + str(date.hour) + '時' + str(date.minute) + '分'

        if is_flug == 'true':
            title = '\n'.join(set(error_title))
            lang = ', '.join(set(error_lang))
            t = Twitter(auth=OAuth(config.TW_TOKEN, config.TW_TOKEN_SECRET, config.TW_CONSUMER_KEY, config.TW_CONSUMER_SECRET))
            msg = '採用リンクが切れています。 @aocattleya \n\n■ タイトル\n' + title + '\n■ 言語\n' + lang
            if len(msg) > 140:
                msg = '※注意！ @aocattleya \n' + str(count) + '件の採用リンクが切れています。（文字制限のため省略しています。）\n' + now
            t.statuses.update(status=msg)
            # 天気ツイートも追従して呟く
            time.sleep(10)
            msg = '@aocattleya \n今日の天気は' + tenki_today.text + '\n' + '明日の天気は' + tenki_tomorrow.text + 'です。'
            t.statuses.update(status=msg)

        else:
            t = Twitter(auth=OAuth(config.TW_TOKEN, config.TW_TOKEN_SECRET, config.TW_CONSUMER_KEY, config.TW_CONSUMER_SECRET))
            msg = '@aocattleya \n本日の全てのチェックの結果、問題は無いです。\n' + now + '\n\n今日の天気は' + tenki_today.text + '\n' + '明日の天気は' + tenki_tomorrow.text + 'です。'
            t.statuses.update(status=msg)
    except Exception as e:
        ##################################
        #  処理失敗
        ##################################
        print("例外args:", e.args)
        t = Twitter(auth=OAuth(config.TW_TOKEN, config.TW_TOKEN_SECRET, config.TW_CONSUMER_KEY, config.TW_CONSUMER_SECRET))
        msg = '@aocattleya \nどこかで処理が失敗しています。帰宅次第確認お願いします｡°(´•ω•̥`)°｡'
        t.statuses.update(status=msg)


if __name__ == '__main__':
    main()
