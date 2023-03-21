import openai

# # #1
# messages = [
#     {"role": "system", "content": "You are a kind helpful assistant."},
# ]
#
# question="For the second-hand car transaction data set. The current price, mileage traveled, resale quantity, and car production year are independent variables, and the final transaction price is the dependent variable, which is fitted with a linear model. The resulting r-squared is 0.854. So, is the relationship between the dependent variable and the independent variable strong?"
#
# messages.append(
#     {"role": "user", "content": question},
# )
# chat = openai.ChatCompletion.create(
#     model="gpt-3.5-turbo", messages=messages
# )
#
# reply = chat.choices[0].message.content
# print(f"ChatGPT: {reply}")
# messages.append({"role": "assistant", "content": reply})
# print(messages)

# openai.api_key='sk-something'
#1
messages = [
    {"role": "system", "content": "You are a kind helpful assistant."},
]

question="For the second-hand car transaction data set. The current price, mileage traveled, resale quantity, and car production year are independent variables, and the final transaction price is the dependent variable, which is fitted with a linear model. The resulting r-squared is 0.854. So, is the relationship between the dependent variable and the independent variable strong?"
# message = input("User : ")
messages.append(
    {"role": "user", "content": question},
)
chat = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", messages=messages
)

reply = chat.choices[0].message.content
print(f"ChatGPT: {reply}")
messages.append({"role": "assistant", "content": reply})
print(messages)


#
# # # 2
import requests
import json

# year_of_vehicle_production=[2014,2013,2017,2011]
# car_Present_Price=[5.59,9.54,9.85,4.15]
# Selling_Price=[3.35,4.75,7.25,2.85]
# message=f"here is some data: year_of_vehicle_production="+str(year_of_vehicle_production)+" car_Present_Price="+str(car_Present_Price)+" Selling_Price="+str(Selling_Price)+" By comparing the above data, If year and current price are independent variables, selling price is dependent variable, under what circumstances the selling price could be as high as possible?"
# print(message)
# URL = "https://api.openai.com/v1/chat/completions"
# payload = {
# "model": "gpt-3.5-turbo",
# "messages": [{"role": "user", "content":message}],
# "temperature" : 1.0,
# "top_p":1.0,
# "n" : 1,
# "stream": False,
# "presence_penalty":0,
# "frequency_penalty":0,
# }
#
# headers = {
# "Content-Type": "application/json",
# "Authorization": f"Bearer {openai.api_key}"
# }
#
# response = requests.post(URL, headers=headers, json=payload, stream=False)
# response.content
# print(response.content)
# output = json.loads(response.content)["choices"][0]['message']['content']
# print(output)

#.strip()
#url = "https://api.openai.com/v1/engines/davinci-codex/completions"
# payload = {
#     "prompt": "When the year and current price meet the specified conditions, the selling price is the highest",
#     "model": "davinci-codex-002",
#     "temperature": 0.7,
#     "max_tokens": 100,
#     "stop": "\n",
#     "inputs": {
#         "year_of_vehicle_production": year_of_vehicle_production,
#         "car_Present_Price": car_Present_Price,
#         "Selling_Price": Selling_Price
#     }
# }
from pandas import read_csv
import ADSTP.IntegratedPipeline as IP

# Set pipelines
pipeline = IP.general_datastory_pipeline
# Set replace variables names
readable_names = dict((kv.split(': ') for kv in (l.strip(' \n') for l in open('./data/readableNamesForTenData.txt'))))

fish_dataset = read_csv('./data/fish.csv')
Xcol = ['Length', 'Diagonal', 'Height', 'Width']
ycol = 'Weight'

key='sk-'
pipeline.LinearFit(fish_dataset, Xcol, ycol, [readable_names.get(key) for key in Xcol], readable_names.get(ycol),chatGPT=1,key=key)



