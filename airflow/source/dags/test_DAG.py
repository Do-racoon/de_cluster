import sys
import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
import math
#from hbase import Hbase
import happybase
import csv
from datetime import datetime


def get_data():
    print("get data")

def send_thrift_command():
    host = 'thrift'
    port = 9090

    try:
        # transport = TSocket.TSocket(host,port)
        # transport = TTransport.TBufferedTransprot(transport)
        # protocol = TBinaryProtocol.TBinaryProtocol(transport)

        # client = Hbase.Client(protocol) # 있어야함

        connection = happybase.Connection(host=host,port=port)
        table_name = 'test_table'

        data_folder = '/opt/airflow/news_data'

        if bytes(table_name, encoding='utf-8') not in connection.tables():
            connection.create_table(
                'test_table',
                {'cf': dict(),  # use defaults
                }
            ) 
        for file_name in os.listdir(data_folder):
            if file_name.endswith('.csv'):
                check = 1
                file_path = os.path.join(data_folder,file_name)
                with open(file_path,'r', encoding='UTF-8') as file:
                    data = csv.reader(file)
                    table = connection.table(table_name)
                    # put the data in table
                    row_key = file_name[::-1][4:]
                    column_family = 'cf'
                    # for row in data:
                    #     column =row[4]
                    #     content = row[5]
                    #     table.put(row_key,{f'{column_family}:{column}':content})
                    for row in data:
                        
                        #print(file_name, row[4], row[5])
                        if check == 1:
                            column = row[4]
                            content = row[5]
                            table.put(row_key,{f'{column_family}:{column}':content})
                            check = 0
                    #table.put(row_key,{f'{column_family}:{file_name}':data[0][4]})
    
    


    except Exception as e:
        print(f"명령 전송 중 오류가 발생했습니다: {str(e)}")
        sys.exit(1)
    finally:
                # 소켓 및 연결을 정리합니다.
        if connection:
            connection.close()
        print(f"file '{data_folder}의 데이터를 Hbase 저장 완료")


with DAG(
    'test_airflow',
    start_date = datetime(2023,6,13),
    schedule_interval='@daily'
) as dag:
    thrift_operator = PythonOperator(
        task_id = 'send_thrift_command',
        python_callable = send_thrift_command
    )

    thrift_operator

