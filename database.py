import sqlite3
import json, urllib
from flask import Flask, render_template, redirect, url_for, request
from werkzeug import secure_filename
import pandas as pd
import os
from datetime import datetime

os.environ["HTTPS_PROXY"]="http://googleapis-dev.gcp.cloud.uk.hsbc:3128"


app = Flask(__name__)


@app.route('/index')

def index():
   result = get_results()
   return render_template('index.html', data=result)



@app.route('/upload', methods=['POST', 'GET'])

def upload():

    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename('input_file.csv'))

        data = pd.read_csv(r"input_file.csv", header=None)
        df = pd.DataFrame()
        for index, row in data.iterrows():
            row[0]=row[0].replace(" ", "%20")
            print(row[0])
            url1 = "https://www.googleapis.com/customsearch/v1?key=AIzaSyBVyGDJi0wtQnZCQVmeYHhp2oziYvqo-2I&cx=017871694751435837305:_em_2x9kobm&q=" + \
                   row[0] + "&fields=queries,searchInformation"

            url2 = "https://www.googleapis.com/customsearch/v1?key=AIzaSyBVyGDJi0wtQnZCQVmeYHhp2oziYvqo-2I&cx=017871694751435837305:_em_2x9kobm&q=" + \
                   row[0] + "&start=11"
            url3 = "https://www.googleapis.com/customsearch/v1?key=AIzaSyBVyGDJi0wtQnZCQVmeYHhp2oziYvqo-2I&cx=017871694751435837305:_em_2x9kobm&q=" + \
                   row[0] + "&start=21"


            print(url1)
            print(url2)
            print(url3)
            response1 = urllib.urlopen(url1)
            response2 = urllib.urlopen(url2)
            response3 = urllib.urlopen(url3)
            output1 = json.loads(response1.read())
            output2 = json.loads(response2.read())
            output3 = json.loads(response3.read())
            company_name = output1['queries']['request'][0]['title']
            company_name = company_name[23:].strip('\"')
            #searchTime = output1['searchInformation']['searchTime']
            try:
                page1_hits = float(output1['queries']['request'][0]['totalResults'])
            except Exception as E:
                print('Error : ', E)
                page1_hits=float(output2['searchInformation']['totalResults'])
            try:
                page2_hits = float(output3['queries']['request'][0]['totalResults'])

            except:
                page2_hits = 0
            try:
                page3_hits = float(output3['queries']['request'][0]['totalResults'])
            except:
                page3_hits = 0
            df.loc[index, 'company_name'] = company_name
            df.loc[index, 'page1_hits'] = page1_hits
            df.loc[index, 'page2_hits'] = page2_hits
            df.loc[index, 'page3_hits'] = page3_hits
        #df.sort_values(by=['page1_hits'])
        print(df)
        df.to_csv("results.csv", index=False)
        return redirect(url_for('index'))

    else:
        return "upload failed"


def get_results():
    risk_rating = 0

    conn = sqlite3.connect('test.sqlite')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE shell_companies_hits')
    cursor.execute('CREATE TABLE IF NOT EXISTS shell_companies_hits(id varchar(50) primary key, company_name varchar(50), page1_hits integer, page2_hits integer, page3_hits integer, risk_rating varchar(20))')
    print('created table')



    result = pd.read_csv(r'results.csv')

    for index, row in result.iterrows():
        time=datetime.now().strftime('%Y%m%d%H%M%S')
        id = row['company_name'] + '_' + time


        # rag_score = row['hits'] * row['searchTime']
        if row['page1_hits'] < 1000:
            risk_rating = 'Red'
        elif row['page1_hits'] < 1000000:
            risk_rating = 'Amber'
        else:
            risk_rating = 'Green'

        try:
            cursor.execute('insert into shell_companies_hits values(?,?,?,?,?,?)', (id, row['company_name'], row['page1_hits'], row['page2_hits'], row['page3_hits'], risk_rating))
        except Exception as E:
            print('Error : ', E)

        else:
            conn.commit()
            print('data inserted')


    try:
        print('SELECT FROM TABLE')

        df = pd.read_sql_query('select * from shell_companies_hits', conn)

        print(df)

        return(df)

    except Exception as E:
        print('Error : ', E)
    else:
        for row in cursor.fetchall():
            print (row)
        conn.close()



if __name__ == '__main__':
    app.run(debug=True)

