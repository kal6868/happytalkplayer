from typing import Optional, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.logger import logger
import pandas as pd

import recommendate_rest_music
music_for_me = recommendate_rest_music.music_recommendation()


import chat_process
callme = chat_process.emochatbot()



app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")  # 추가1

templates = Jinja2Templates(directory="templates")
#app.mount("/", StaticFiles(directory="templates",html = True), name="templates")

total_list2 = pd.read_csv('./content/S3_music_list_new6.tsv', sep = '\t',header = None)


@app.get("/")
async def client(request: Request):
    # /templates/client.html파일을 response함
    return templates.TemplateResponse("index.html", {"request":request})

# 웹소켓 설정 ws://127.0.0.1:8000/ws 로 접속할 수 있음
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print(f"client connected : {websocket.client}")
    await websocket.accept() # client의 websocket접속 허용
    await websocket.send_text("하루 있었던 일을 말씀해 주시면 오늘 기분에 맞는 음악을 추천해 드립니다.")
	

    while True:
        data = await websocket.receive_text()  # client 메시지 수신대기
        print(f"message received : {data} from : {websocket.client}") 
        
        if data[:3] == "==>":
	        	data = data[-(len(data)-3):]
	        	print(f"Music selected : {data} ") 
	        	data_num = int(data)
	        	data_id =total_list2.loc[data_num][3]
	        	print(f"Music converted : {data_id} is going to AI DJ.")
        		mood, music_list = music_for_me.recommendation_by_id(data_id)
		        a=['BestForYou']
		        b=['Reply']
		        c =[mood]
		        json_set = {"key1": a, "key2": b, "key3": music_list, "key4": c}
		        await websocket.send_json(json_set)
        else:
		        answer, emoclass, music_list, mood, rand_music_num = callme.recommendation(data)
		        a=[answer]
		        b=[emoclass]
		        c =[mood]
		        #d =[rand_music_num]
		        json_set = {"key1": a, "key2": b, "key3": music_list, "key4": c, "key5": rand_music_num}
		        await websocket.send_json(json_set)
        #await websocket.send_text(f"'{answer}' <br/>그리고 '{emoclass}' <br/>드리는 음악은 '{music_list}' ") # client에 메시지 전달

# 개발/디버깅용으로 사용할 앱 구동 함수
def run():
    import uvicorn
    uvicorn.run(app)

# python main.py로 실행할경우 수행되는 구문
# uvicorn main:app 으로 실행할 경우 아래 구문은 수행되지 않는다.
if __name__ == "__main__":
    run()
