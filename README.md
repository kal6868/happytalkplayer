# happytalkplayer
* 사용자 감정을 기반으로 한 음악 추천 챗봇
* happytalkplayer 도메인 등록하여 쉬운 접속이 가능 (현재는 비용 문제로 폐쇄)
<br/></br>
# Introduction
![그림1](https://user-images.githubusercontent.com/89456014/180804568-4043f193-bca8-4cce-aa6f-53b8a194fca0.png)
![chatbot1](https://user-images.githubusercontent.com/89456014/180813127-6bca0ebc-9edd-452b-8a1b-f62e43974f17.png)
![chatbot2](https://user-images.githubusercontent.com/89456014/180813134-da585c1b-dd3a-43d8-9674-e52806dd71fe.png)
* 개발 의도 : 문장에서 감정을 파악하고 그에 맞는 음악을 추천하고자 하는 챗봇 개발 
  * 사용자가 들어본 적이 없더라도 취향에 맞는 음악 추천 시스템의 중요성이 증대
  * 인간의 감정을 텍스트 등에서 파악하려는 시도의 증가
  * Rule-Base 챗봇에서 문장을 생성하는 인공지능 챗봇 모델들의 출현
<br/></br>
# Service Diagram
![chatbot3](https://user-images.githubusercontent.com/89456014/180813138-0f77a46f-1416-4a13-bc87-f1ec6ddbbd69.png)
* 1. 웹 페이지인 Happytalkplayer.com에서 EC2(ubuntu server)의 API로 문장을 전달
* 2. API가 학습이 완료된 문장 생성모델로 사용자가 입력한 문장을 전달
* 3. 문장 분석 후 문장 생성 모델이 답변을 만들고, 감정 분류 모델이 사용자의 감정을 파악
* 4. 간단한 대답과 함께 감정 분류에 따른 음악 5곡을 추천
* 5. 음악 5곡 중 가장 사용자의 취향에 맞는 음악을 선택
* 6. 선택된 음악과 가장 유사한 음악 5곡을 사용자에게 추가로 제공
<br/></br>
# AI Model 1 : 문장 생성 모델(Kogpt2)
![chatbot4](https://user-images.githubusercontent.com/89456014/180813143-f659d33a-8ca4-4660-9508-dafb36706c3a.png)
![chatbot5](https://user-images.githubusercontent.com/89456014/180813148-b939f719-65dc-4da8-9502-e60505fa0c84.png)
* 감성 대화 말뭉치 + Wellness Script를 합쳐서 미세 조정(Fine Tuning)
  * 감성 대화 말뭉치만 사용시 무미 건조한 문장만이 생성되고 되묻는 질문이 생성
    * ex) I) 나 너무 힘들어 / A) 너무 힘드시군요
    * ex) I) 나 너무 힘들어 / A) 왜 힘드신가요?
  * Wellness Script만 사용시 문장의 구조가 무너지는 현상 발생
    * ex) A) 점심은 저녁은 무엇을 무엇을 맛있게 드셨나요?
* 두 데이터 셋의 장점만 사용하기 위해 필요 없는 문장은 제거 후 데이터셋을 합산하여 미세 조정

![chatbot6](https://user-images.githubusercontent.com/89456014/180813151-c4ececf7-10b2-4de8-ba4e-376cb2b84567.png)
* Ko-gpt-trinity, kakao-kogpt등 다양한 모델을 고려하였지만 응답 속도와 가용 자원을 고려하여 Kogpt2 모델 선정

![chatbot7](https://user-images.githubusercontent.com/89456014/180813155-f34601a3-6956-4b00-9bbb-28aeea350050.png)
* 학습시 데이터 셋에 감정 분류 토큰(가용시), 문장 구분 토큰, Pad 토큰 등을 활용하여 데이터를 재가공 
* 10 epochs 학습을 진행하였으며, 학습 데이터 셋 Loss 값은 0.7456으로 종료

![chatbot8](https://user-images.githubusercontent.com/89456014/180813159-4f9b22f7-f7a5-4a08-b717-bffced9b2a21.png)
* HuggingFace의 Generation 페이지를 활용하여 여러가지 Parameter를 수정해가며 최대한 자연스러운 응답을 생성
<br/></br>
# AI Model 2 : 감정 분류 모델(KcElectra)
![chatbot9](https://user-images.githubusercontent.com/89456014/180813163-43628f40-99d8-4487-a16a-ced37fcd4768.png)
* 한국어 감정 정보가 포함된 단발성 대화 데이터셋에서 중립 문장을 제외한 6가지 감정 문장을 사용하여 미세 조정(Fine Tuning)

![chatbot11](https://user-images.githubusercontent.com/89456014/180813169-9c3561c1-b2b5-4396-9d83-3684429d799c.png)
* 학습시 문장 시작 토큰과 종료 토큰, Pad 토큰을 활용하여 데이터를 재가공
* 5 epochs 학습을 진행하였으며, 학습 데이터 셋 Accuracy 값은 0.9406, 검증 데이터 셋 Accuracy 값은 0.9165로 학습 종료

![chatbot12](https://user-images.githubusercontent.com/89456014/180813175-07b485a8-554c-4aec-909e-c5241fe16cf5.png)
* Kobert, Kcbert 등 다양한 모델 중 구어체로 사전 학습된 모델이 챗봇 활용에 가장 유리할 것으로 생각되어 모델 선정

# Aknn Algorithm : Annoy
![chatbot13](https://user-images.githubusercontent.com/89456014/180813178-1ee83555-cb1f-43d9-b6fb-406c6f77d595.png)
* Youtube 음악 보관함에 감정 태그가 완료된 음악 720곡을 수집(각 감정 당 120곡 씩 수집)

![chatbot14](https://user-images.githubusercontent.com/89456014/180813183-b3e7efb0-f168-4950-808b-0874e694175a.png)
![chatbot15](https://user-images.githubusercontent.com/89456014/180813190-ce8dffdb-3a6f-4e19-8a7a-1ef5688e64c2.png)
* 각 음악의 0 ~ 30초를 추출
* librosa를 활용하여 추출할 수 있는 다양한 음악의 특징 중 MFCC를 선정
  * 너무 많은 특성을 고려 시 오히려 분류의 정확도가 떨어져 단일 특성을 선정

![chatbot16](https://user-images.githubusercontent.com/89456014/180813197-b2e9ce51-1ee1-4860-836a-030470321b26.png)
* 다양한 K-nearest Algorithm 중 속도와 정확성, 기법의 최신 정도를 고려하여 Kakao의 Toros N2로 선정
* 추후 EC2에서 ARM 기반의 서버로 이전하면서 Toros N2를 사용불가로 Spotify의 Annoy로 변경
<br/></br>
# Web page & API
![chatbot17](https://user-images.githubusercontent.com/89456014/180813206-02d24dc4-13e8-4f34-ad28-3ed6677be40f.png)
![chatbot18](https://user-images.githubusercontent.com/89456014/180813212-dbfaceff-7bce-4047-b353-ebc5d9ee4988.png)
* AWS의 EC2를 계정이 제공되어 EC2에 ubuntu 설치 후 클라우드 환경을 구축
* 음악 파일의 경우 AWS의 S3에 저장
* 여러 사용자가 이용할 경우와 응답 속도를 고려하여 FastApi 패키지를 사용하여 API를 개발
<br/></br>
# happytalkplayer.com
![chatbot19](https://user-images.githubusercontent.com/89456014/180813218-761cf26d-9853-4e85-b7ce-e61392e87d28.png)
![chatbot20](https://user-images.githubusercontent.com/89456014/180813222-f157f877-9faf-40ad-afd5-ebc2290ea033.png)
![chatbot21](https://user-images.githubusercontent.com/89456014/180813230-4b46d69a-bc46-4c5b-a2e0-3df1d9598a20.png)
* 쉬운 접속을 위해 도메인을 등록하고, 카카오톡, 라인과 같은 사용자에게 친숙한 모바일 메신저 UI를 구성
* Audio Player와 음악을 선택할 수 있는 playlist와 다양한 제어 기능을 제공

