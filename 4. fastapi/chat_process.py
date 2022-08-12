from transformers import PreTrainedTokenizerFast, GPT2LMHeadModel, AutoTokenizer, AutoModel
import torch
import numpy as np
import pandas as pd
import os
import random
import re

class emochatbot():
  def __init__(self):
    bos_token = '<s>'
    eos_token = '</s>'
    pad_token = '<pad>'
    #kogpt2 모델 load"
    self.Tokenizer_kogpt2 = PreTrainedTokenizerFast.from_pretrained('skt/kogpt2-base-v2',
                                                                    bos_token = bos_token, 
                                                                    eos_token = eos_token,
                                                                    pad_token = pad_token)
    self.model_kogpt2 = GPT2LMHeadModel.from_pretrained('skt/kogpt2-base-v2')
    #kcelectra 모델 load
    self.Tokenizer_kce = AutoTokenizer.from_pretrained("beomi/KcELECTRA-base")
    self.model_kce = AutoModel.from_pretrained("beomi/KcELECTRA-base", num_labels=6)
    # finetuning된 모델 load
    checkpoint_kogpt = torch.load('./models/220525_unified_gpt_model.pt',
                                  map_location=torch.device('cpu'))
    self.model_kogpt2.load_state_dict(checkpoint_kogpt['model_state_dict'])
    checkpoint_kce = torch.load('./models/emo_classify_model.pt',
                                  map_location=torch.device('cpu'))
    self.model_kce.load_state_dict(checkpoint_kce)

  def sent_gen(self,sent):
    self.model_kogpt2.eval()
    sent = str(sent)
    tokenized_sent = self.Tokenizer_kogpt2.encode(sent)
    input_ids = torch.tensor([self.Tokenizer_kogpt2.bos_token_id] + tokenized_sent + [self.Tokenizer_kogpt2.eos_token_id]).unsqueeze(0)
    output_token =  self.model_kogpt2.generate(input_ids = input_ids,
				        do_sample = True,
				        max_length = 48,
				        min_length = 13,
				        top_p= 0.75,
				        top_k = 50,
				        temperature = 0.8,
				        early_stopping=False,
				        no_repeat_ngrm_size=3,
				        num_beans=3,
				        use_cache=True)
    output_gen = self.Tokenizer_kogpt2.decode(output_token[0].tolist()[len(tokenized_sent)+1:], skip_special_tokens = True)
    output_gen = re.sub('.*\s?[10-99]','',output_gen)
    output_gen = re.sub('^\s', '', output_gen)
    return output_gen

  def clssify_emo(self, sent):
    self.model_kce.eval()
    inputs =  self.Tokenizer_kce(sent,
                                 return_tensors='pt',
                                 truncation = True,
                                 max_length=64,
                                 pad_to_max_length = True,
                                 add_special_tokens = True)
    
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']
    out = self.model_kce(input_ids = input_ids, attention_mask = attention_mask).last_hidden_state
    out = out[:, -1, :]
    # 0 : happiness, 1 : angry,  2 : sadness, 3 : disgust, 4 : surprise, 5 : fear
    emotion = np.argmax(out.detach().cpu().numpy())
    return emotion

  def recommendation(self, sent):
    answer = self.sent_gen(sent)
    emotion_status = self.clssify_emo(sent)
    
    if emotion_status == 0:
      status = '기쁨'
    elif emotion_status == 1:
      status = '분노'
    elif emotion_status == 2:
      status = '슬픔'
    elif emotion_status == 3:
      status = '혐오'
    elif emotion_status == 4:
      status = '놀람'
    elif emotion_status == 5:
      status = '공포'

    emoclass = f"오늘의 기분은 기쁨, 공포, 혐오, 분노, 놀람, 슬픔 &nbsp;중&nbsp;  <b>{status}</b>(으)로 판단됩니다.<br/>"
    
    if status == '분노':
    		emoclass += f"제가 들려드리는 음악이 {status} 를 가라앉힐 수 있다면 좋겠습니다."
    elif status == '공포':
    	    	emoclass += "공포 음악 몇 번씩 듣다보면 더 이상 공포가 아닐 것입니다. 이것쯤이야 하고 털어버리세요."
    elif status == '혐오':
    	    	emoclass += "많이 당황하셨을 것 같아요. 극혐이 아니라면 우리 함께 음악으로 치유해 보아요."
    elif status == '놀람':
    	    	emoclass += "혹시 아직도 심장이 뛰시나요.  저도 놀랐습니다. 이럴 때 제가 즐겨듣는 음악입니다."
    elif status == '슬픔':
    	    	emoclass += "누군가 또는 어떤 소식이 슬픈 가슴을 짓누를 때, 이런 음악은 어루만져 줄 수 있답니다."
    elif status == '기쁨':
    		emoclass += f"오늘 기분에 맞는 {status} 음악을 추천해 드릴게요."

    if emotion_status == 0:
      mood = 'Happy'
    elif emotion_status == 1:
      mood = 'Angry'
    elif emotion_status == 2:
      mood = 'Sad'
    elif emotion_status == 3:
      mood = 'Calm'
    elif emotion_status == 4:
      mood = 'Dramatic'
    elif emotion_status == 5:
      mood = 'Dark'
    total_list = pd.read_csv('./content/S3_music_list_new.tsv', sep = '\t',header = None)
    music4mood = total_list[total_list[1] == mood][0].values.tolist()
    rand_music_num = random.sample(music4mood, 5)
    rand_music_reco = total_list.loc[rand_music_num,[2]].values.flatten().tolist()

    return answer, emoclass, rand_music_reco, mood, rand_music_num