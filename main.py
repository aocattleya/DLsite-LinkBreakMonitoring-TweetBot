# -*- coding: utf-8 -*-
from urllib.request import build_opener, HTTPCookieProcessor
from urllib.parse import urlencode, parse_qs
from http.cookiejar import CookieJar
from bs4 import BeautifulSoup
from twitter import *
import requests
import datetime
import config
import json
import time


def main():
    try:
        # 監視フロア
        dlsite_floor_list = ['home', 'home-touch', 'maniax', 'maniax-touch', 'girls', 'girls-touch', 'eng', 'eng-touch']
        locale_list = [{'locale': 'ja-jp'}, {'locale': 'zh-cn'}, {'locale': 'zh-tw'}, {'locale': 'ko-kr'}, {'locale': 'en-us'}]

        is_flug = 'false'
        error_text = ''
        locale = ''
        count = 0
        opener = build_opener(HTTPCookieProcessor(CookieJar()))

        '''---------------------
        DLsiteの採用リンク切れを取得
        ---------------------'''
        # フロア毎に監視
        for dlsite_floor in dlsite_floor_list:
            # さらにフロアの多言語毎に監視
            for cookie_locale in locale_list:
                if cookie_locale['locale'] == 'ja-jp':
                    locale = '（日本）'
                elif cookie_locale['locale'] == 'zh-cn':
                    locale = '（中国）'
                elif cookie_locale['locale'] == 'zh-tw':
                    locale = '（台湾）'
                elif cookie_locale['locale'] == 'en-us':
                    locale = '（英語）'
                # URL
                url = "https://www.dlsite.com/" + dlsite_floor
                # cookie付きでアクセス
                response = requests.get(url=url, cookies=cookie_locale)
                html = response.content
                # HTMLをBeautifulSoupで扱う
                soup_html = BeautifulSoup(html, "html.parser")
                # job_list_item newクラスを前取得
                job_list_item = soup_html.find_all('li', class_='job_list_item new')

                # 採用リンクがある要素（3個前後）
                for job_html in job_list_item:
                    # 採用のタイトル取得
                    job_name = job_html.find('p', class_='job_name').get_text()
                    # 採用リンクを取得
                    url = job_html.a.get("href")
                    # 採用リンクにアクセス
                    resp = requests.get(url)
                    print(dlsite_floor + locale + job_name)
                    # 採用リンク先のステータスコードチェック
                    if resp.status_code == 404:
                        # 通知フラグ
                        is_flug = 'true'
                        count = count + 1
                        error_text = error_text + dlsite_floor + locale + 'の' + job_name + '\n'
                # 10秒毎に実行
                time.sleep(10)

        '''------
        天気予報
        ------'''
        # リンク
        url = 'https://weather.yahoo.co.jp/weather/jp/13/4410.html'

        # HTMLを取得
        response = requests.get(url=url)
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')

        # 今日の天気
        tenki_today = soup.select_one('#main > div.forecastCity > table > tr > td > div > p.pict')
        # 明日の天気
        tenki_tomorrow = soup.select_one('#main > div.forecastCity > table > tr > td + td > div > p.pict')


        '''-----------
        ツイート用の日付
        -----------'''
        date = datetime.datetime.now()
        # もっといい方法多分ある
        if datetime.date.today().weekday() == 0:
            youbi = '（月）'
        elif datetime.date.today().weekday() == 1:
            youbi = '（火）'
        elif datetime.date.today().weekday() == 2:
            youbi = '（水）'
        elif datetime.date.today().weekday() == 3:
            youbi = '（木）'
        elif datetime.date.today().weekday() == 4:
            youbi = '（金）'
        elif datetime.date.today().weekday() == 5:
            youbi = '（土）'
        elif datetime.date.today().weekday() == 6:
            youbi = '（日）'
        now = str(date.month) + '月' + str(date.day) + '日' + youbi + str(date.hour) + '時' + str(date.minute) + '分'

        '''------
        ツイート
        ------'''
        if is_flug == 'true':
            # ツイート（リンク切れ）
            t = Twitter(auth=OAuth(config.TW_TOKEN, config.TW_TOKEN_SECRET, config.TW_CONSUMER_KEY, config.TW_CONSUMER_SECRET))
            msg = '@aocattleya \n※注意！\n' + error_text + 'の採用リンクが切れています。'
            if len(msg) > 140:
                msg = '※注意！ @aocattleya \n' + str(count) + '件の採用リンクが切れています。（文字制限のため省略しています。）\n' + now
            t.statuses.update(status=msg)
        else:
            # ツイート（問題なし）
            t = Twitter(auth=OAuth(config.TW_TOKEN, config.TW_TOKEN_SECRET, config.TW_CONSUMER_KEY, config.TW_CONSUMER_SECRET))
            msg = '@aocattleya \n本日の全てのチェックの結果、問題は無いです。\n' + now + '\n\n今日の天気は' + tenki_today.text + '\n' + '明日の天気は' + tenki_tomorrow.text + 'です。'
            t.statuses.update(status=msg)
    except Exception as e:
        '''------
        処理失敗
        ------'''
        print("例外args:", e.args)
        t = Twitter(auth=OAuth(config.TW_TOKEN, config.TW_TOKEN_SECRET, config.TW_CONSUMER_KEY, config.TW_CONSUMER_SECRET))
        msg = '@aocattleya \nどこかで処理が失敗しています。帰宅次第確認お願いします｡°(´•ω•̥`)°｡'
        t.statuses.update(status=msg)

if __name__ == '__main__':
    main()
