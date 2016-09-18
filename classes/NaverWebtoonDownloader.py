from html.parser import HTMLParser

import os
import requests


# Globals
webtoon_title = ""
imgs_to_dl = []
newest_ep_id = 0


class NaverWebtoonDownloader():
    def __init__(self, webtoon_id, start_id, directory_path):
        webtoon_list_page_url = 'http://comic.naver.com/webtoon/list.nhn?titleId={}'.format(webtoon_id)

        webtoon_list_r = requests.get(webtoon_list_page_url)
        if webtoon_list_r.status_code != 200:
            print("Get request for webtoon list page failed")
            exit()

        parser = NaverWebtoonListPageParser()
        parser.feed(webtoon_list_r.text)

        print("Downloading webtoon from ep_id:" + str(start_id) + " to ep_id:" + str(newest_ep_id) + " started.")
        while start_id <= newest_ep_id:
            if self.download_ep(directory_path, webtoon_id, start_id):
                print("Downloading " + webtoon_title + "complete.")
                imgs_to_dl = []
            else:
                print("Episode #" + str(start_id) + " doesn't exist. Skipping.")
            start_id += 1

        print("Downloading the webtoon complete.")

    def download_ep(self, directory_path, webtoon_id, ep_id):
        webtoon_ep_url = 'http://comic.naver.com/webtoon/detail.nhn?titleId={}&no={}'.format(webtoon_id, ep_id)

        ep_main_page_r = requests.get(webtoon_ep_url)
        if ep_main_page_r.status_code != 200:
            print("Get request for episode main page failed")
            exit()

        parser = NaverWebtoonEpParser()
        parser.feed(ep_main_page_r.text)

        if len(imgs_to_dl) == 0:
            print("There are no images to download. Probably this ep is not released yet.")
            return False

        #print("Images to download are:")
        #for img_url in imgs_to_dl:
        #    print(img_url)

        headers = {'referer': 'http://comic.naver.com/webtoon/detail.nhn?titleId={}&no={}'.format(webtoon_id, ep_id)}

        # ep_id for sorting purposes
        folder_path = directory_path + ('%04d_' % (ep_id,)) + webtoon_title
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        for i in range(len(imgs_to_dl)):
            r = requests.get(imgs_to_dl[i], headers=headers)
            if r.status_code != 200:
                print("Get request failed")
            
            img_file_name = '%03d.jpg' % (i,)
            with open(folder_path + '/' + img_file_name, 'wb') as outfile:
                outfile.write(r.content)

        return True


class NaverWebtoonEpParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global imgs_to_dl

        if (tag == 'img'):
            if len(attrs) > 2 and len(attrs[0]) > 0 and attrs[0][0] == 'src' and len(attrs[2]) > 1 and attrs[2][0] == 'alt' and attrs[2][1] == 'comic content':
                imgs_to_dl.append(attrs[0][1])
    
    def handle_data(self, data):
        global webtoon_title
        
        # Yay there is only one tag that starts with h3!
        if self.get_starttag_text() == "<h3>" and data.strip():
            webtoon_title = data


class NaverWebtoonListPageParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global newest_ep_id
        
        if (newest_ep_id == 0 and tag == 'a'):  # Lol.. too nested yo
            if len(attrs) == 2 and len(attrs[0]) > 0 and attrs[0][0] == 'href': # len(attrs) == 2 is hacky but easy way to bypass '첫회보기' link
                ep_no_identifier = 'no='
                pos_ep_no = attrs[0][1].find(ep_no_identifier)
                if pos_ep_no >= 0:
                    pos_ep_no_end = attrs[0][1].find('&', pos_ep_no)
                    if pos_ep_no_end == -1:
                        pos_ep_no_end = len(attrs[0][1])
                    newest_ep_id = int(attrs[0][1][pos_ep_no + len(ep_no_identifier) : pos_ep_no_end]) # You know.. Not gonna error check

