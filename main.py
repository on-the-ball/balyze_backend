from fastapi import FastAPI
import pymysql
import datetime
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
import pickle
import numpy as np
import pandas as pd

# CORSミドルウェアを設定
app = FastAPI()
load_dotenv()

origins = [
    "https://balyze.netlify.app",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def predict(data):
    homewin = 0
    awaywin = 0
    draw = 0
    categorical_features = ['year', 'category','section','matchdate','home', 'away', 'stadium']
    outcome_list = ['1-0','2-0','2-1','3-0','3-1','3-2','Other home wins','0-1','0-2','1-2','0-3','1-3','2-3','Other away wins','0-0','1-1','2-2','Other draws']
    
    data_pred = pd.DataFrame({
            'year': [data["year"]],
            'category': [data["category"]],
            'section': [data["section"]],
            'matchdate': [data["matchdate"]],
            'home': [data["home"]],
            'away': [data["away"]],
            'stadium': [data["stadium"]],
    })

    # カテゴリ変数の変換
    for feature in categorical_features:
        data_pred[feature] = data_pred[feature].astype('category')

            # 試合のscoreを予測
    with open('model.pkl', 'rb') as model_file:
        model = pickle.load(model_file) 
    
    pred_score = model.predict(data_pred)
    pred_score = pred_score[0]

    # ホームチームの勝率の集計
    for i in range(7):
        homewin += pred_score[i]
    homewin = round(homewin, 1) * 100
  
    # アウェイチームの勝率の集計
    for i in range(7,13):
        awaywin += pred_score[i]
    awaywin = round(awaywin, 1) * 100

    # 引き分けの集計
    for i in range(14,18):
        draw += pred_score[i]
    draw = round(draw, 1) * 100
    # 小数点第三位まで四捨五入
    # array = np.array(pred_score)
    # rounded_array = np.round(array, decimals=3)[0]

    # # 確率が高い順に表示
    # rounded_array_rank = list(np.sort(rounded_array))[::-1]
    # score_rank = list(np.argsort(rounded_array))[::-1]

    # pred_list = [[outcome_list[score_rank[0]], rounded_array_rank[0]],[outcome_list[score_rank[1]], rounded_array_rank[1]], 
    #             [outcome_list[score_rank[2]], rounded_array_rank[2]],[outcome_list[score_rank[3]], rounded_array_rank[3]] , [outcome_list[score_rank[4]], rounded_array_rank[4]]]
    
    pred_list = {
        "homewin" : homewin,
        "awaywin" :awaywin,
        "draw" : draw
    }
    
    return pred_list

@app.get("/api/match")
def matchdate():
  connection = pymysql.connect(
      host=os.getenv("HOST"),
      user=os.getenv("USERNAME"),
      password=os.getenv("PASSWORD"),
      db=os.getenv("DATABASE"),
      autocommit = True,
      ssl={"ssl":
           {"ca": "/cert.pem"}
      }
  )

  cursor = connection.cursor()
  
  # 現在の日付を取得します
  current_date = datetime.date.today()

  # 7日後の日付を計算します
  end_date = datetime.date.today() + datetime.timedelta(days=7)

  # クエリを作成します
  query = "SELECT id, year, category, section, matchdate, home, away, stadium FROM jleague WHERE date BETWEEN %s AND %s"

  # クエリを実行し、結果を取得します
  cursor.execute(query, (current_date, end_date))
  results = cursor.fetchall()
  data = []

  for row in results:
      item = {
          "index": row[0],
          "year": row[1],
          "category": row[2],
          "section": row[3],
          "matchdate": row[4],
          "home": row[5],
          "away": row[6],
          "stadium": row[7]
      }
      pred_list = predict(item)
      item['homewin'] = pred_list['homewin']
      item['awaywin'] = pred_list['awaywin']
      item['draw'] = pred_list['draw']
      data.append(item)

  return data

