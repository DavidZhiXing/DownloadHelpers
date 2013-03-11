#-*-coding:GBK-*-
import urllib
import urllib2
import re
import threading
import os
import sys
import time
import Queue
import signal

from common import addToIDM

BASE_URL = 'http://www.5tps.com'  # base url
DOWN_PATH = 'e:\\Downloads\\����С˵'  # saving path
save2path = ''  # saving file name (full path)

jobs_queue = Queue.Queue()  # Ҫ������url����
out_queue = Queue.Queue()  # �����صĶ���


def parseStartUrl(starturl):
    '''
    parse out download page from start url.
    eg. we can get 'http://www.5tps.com/down/8297_52_1_1.html' from 'http://www.5tps.com/html/8297.html'
    '''
    global save2path
    rDownloadUrl = re.compile(".*?<A href=\'(/down/\w+\.html)\'.*")  # find the link of download page
    # rTitle = re.compile("<TITILE>.{4}\s{1}(.*)\s{1}.*</TITLE>")
    #<TITLE>����С˵ ��ɧ1 ����:���� ȫ��</TITLE>
    f = urllib2.urlopen(starturl)
    totalLine = f.readlines()

    title = totalLine[3].split(" ")[1]
    save2path = os.path.join(DOWN_PATH, title)

    # xpath_downUrl ='.//*[@id='bfdz']/div[@class='toolbox']/ul/li/a[2]'
    # xpath_contetn = './/*[@id='full']/div/div/ul/p/span' #���ݼ��
    downUrlLine = [line for line in totalLine if rDownloadUrl.match(line)]
    downLoadUrls = []
    for dl in downUrlLine:
        while True:
            m = rDownloadUrl.match(dl)
            if not m:
                break
            downUrl = m.group(1)
            downLoadUrls.append(downUrl.strip())
            dl = dl.replace(downUrl, '')
    return downLoadUrls

# def addToIDM(downUrl):
#     command='"%s" /a /d "%s" /p "%s"' % (IDM_PATH, downUrl, save2path)
#     subprocess.call(command)


def myExit(signum, frame):
    sys.exit()


class ThreadUrl(threading.Thread):
    ''' ��ȡ��ʵ�����ص�ַ, �������IDM, �����ֶ������й涨���������� '''
    # find the real download link
    rDownUrl = re.compile('<a href=\"(.*)\"><font color=\"blue\">�������.*</a>')

    def __init__(self, queue, out_queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.out_queue = out_queue
        signal.signal(signal.SIGNAL, myExit)

    def run(self):
        while True:
            if self.out_queue.qsize() >= 2:
                time.sleep(2)
            else:
                url = self.queue.get()
                # ������ҳ�õ� ���ص�ַ
                downUrl, filePath = self.getDownUrl(url)
                # �������������ӵ�IDM����
                if not os.path.exists(filePath):
                    addToIDM(downUrl, save2path)
                    print(BASE_URL + url)
                    # �ŵ���������
                    self.out_queue.put(filePath)

                self.queue.task_done()

    def getDownUrl(self, url):
        ''' find out the real download link from download page.
        url like down/8297_52_1_1.html
        eg. we can get the download link 'http://180j-d.ysts8.com:8000/�����ʵ/ͯ��/001.mp3?\
        1251746750178x1356330062x1251747362932-3492f04cf54428055a110a176297d95a' from \
        'http://www.5tps.com/down/8297_52_1_1.html'
        '''
        realurl = BASE_URL + url
        for line in urllib2.urlopen(realurl).readlines():
            m = self.rDownUrl.match(line)
            if m:
                downUrl = m.group(1)

                m = re.search('[^/]+\.mp3', downUrl)
                fileName = m.group().replace('%20', ' ')
                filePath = os.path.join(save2path, fileName)
                return (downUrl, filePath)


class CheckThread(threading.Thread):
    ''' ��������Ƿ���� '''
    def __init__(self, out_queue):
        threading.Thread.__init__(self)
        self.out_queue = out_queue

    def run(self):
        while True:
            filePath = self.out_queue.get()
            while True:
                if os.path.exists(filePath):
                    self.out_queue.task_done()
                    print('�������: %s' % filePath)
                    break
                time.sleep(1)

if __name__ == '__main__':
    starturl = 'http://www.5tps.com/html/6152.html'
    # starturl = sys.argv[1]
    # if not starturl:
        # sys.exit()
    urls = parseStartUrl(starturl)
    for downUrl in urls[61:]:
        jobs_queue.put(downUrl)
    print("The Size of Jobs is %s" % jobs_queue.qsize())

    t = ThreadUrl(jobs_queue, out_queue)
    t.setDaemon(True)
    t.start()

    dt = CheckThread(out_queue)
    dt.setDaemon(True)
    dt.start()

    # wait on the queue until everything has been processed
    jobs_queue.join()
    # out_queue.join()

    print('ȫ�������ɣ�')
