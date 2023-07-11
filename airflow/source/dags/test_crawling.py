import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import csv
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import sys
tickers =['095570',
 '006840',
 '027410',
 '282330',
 '138930',
 '001460',
 '001465',
 '001040',
 '079160',
 '00104K']
def crawling_news(ticker, sleep_interval=1):
    data_exists = True
    data = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    }
    try:
        # enter ticker news page
        url = f"https://finance.naver.com/item/news_news.naver?code={ticker}&page={1}&sm=title_entity_id.basic&clusterId="
        time.sleep(sleep_interval)
        response = requests.get(url, headers)
        # parsing => delete related news on page 1
        soup = BeautifulSoup(response.text, "html.parser")
        all_tr = soup.select("table.type5 > tbody > tr:not(.relation_lst)")
        related_tr = soup.select(
            "table.type5 > tbody > tr.relation_lst > td > table > tbody > tr"
        )
        articles = list(set(all_tr) - set(related_tr))

        # collect links and datetimes of articles on page 1
        for article in articles:
            try:
                # link
                link = article.select("a")[0].attrs["href"]
                # date
                date = article.select("td.date")[0].text.strip()
                date = datetime.strptime(date, "%Y.%m.%d %H:%M")
                data.append([date, f"https://finance.naver.com{link}"])
            except Exception as ex:
                print(f"article : 명령 전송 중 오류가 발생했습니다: {str(ex)}")
                data_exists = False
                return (data, data_exists)
        # sort by datetime
        data.sort(reverse=True)

        # collect title and contents of articles
        for i in range(len(data)):
            # link
            url = data[i][1]

            # move to article page
            time.sleep(sleep_interval)
            response = requests.get(url, headers)
            soup = BeautifulSoup(response.text, "html.parser")

            # title
            title = soup.select_one("strong.c")
            if title:
                data[i].append(title.text.strip())

            # content
            content = soup.select_one("div.scr01")
            if content:
                data[i].append(content.text.strip())
        return (data, data_exists)
    except Exception as e:
        print(f"명령 전송 중 오류가 발생했습니다: {str(e)}")

def save_data(ticker,data, data_exists):
    columns = ['date', 'rink', 'title', 'content']
    folder_path = '/opt/airflow/news_data/'
    if data_exists:
        with open(folder_path+ticker+'.csv', 'w', newline='') as file:
            
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(data)

def crawl_task(ticker):
    data, data_exists = crawling_news(ticker)
    save_data(ticker,data, data_exists)

def test_task():
    tickers = ['095570', '006840', '027410', '282330', '138930', '001460', '001465', '001040', '079160', '00104K']
    for ticker in tickers:
        crawl_task(ticker)

default_args = {
    'owner' : 'airflow',
    'start_date' : datetime(2023,6,20),
}

dag = DAG(
    'crawl_and_save_data_dag',
    default_args=default_args,
    schedule_interval=None,
)

crawl_and_save_operator = PythonOperator(
    task_id = 'crawl_and_save_task',
    python_callable=test_task,
    dag=dag,
)
crawl_and_save_operator
# for idx, ticker in enumerate(tickers):
#     task_id = f'crawl_and_save_task_{idx+1}'
#     crawl_and_save_operator = PythonOperator(
#         task_id=task_id,
#         python_callable=crawl_task(ticker),
#         op_kwargs={'task_id' : task_id},
#         dag=dag,

#     )
#     if idx > 0:
#         crawl_and_save_operator.set_upstream(prev_task)

#     prev_task = crawl_and_save_operator
