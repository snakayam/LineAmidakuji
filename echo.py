import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, JoinEvent,
)
import random

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

#LINE DevelopersのWebhookにURLを指定してWebhookからURLにイベントが送られるようにする
@app.route("/callback", methods=['POST'])
def callback():
    # リクエストヘッダーから署名検証のための値を取得
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # リクエストボディを取得
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 署名を検証し、問題なければhandleに定義されている関数を呼ぶ
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# あみだくじ部分
def amidakuji(receive_text):
    array = receive_text.splitlines()
    attend = array.index("<参加者>") + 1
    result = array.index("<結果>") + 1
    attend_array = []
    result_array = []
    attend_total = 0
    # 配列の作成
    for i in range(attend, result-1):
        if array[i].replace(' ', '').replace('　','') != "":
            attend_array.append(array[i])
            attend_total += 1
    for i in range(result, len(array)):
        if array[i].replace(' ', '').replace('　','') != "":
            result_array.append(array[i])
    # 結果の補充
    while len(result_array) < attend_total:
        result_array.append("ハズレ")
    # あみだくじ
    random.shuffle(result_array)
    # 返信内容の入力
    reply_text = "<あみだくじ結果>"
    for i in range(0, attend_total):
        reply_text += "\n" + attend_array[i] + " : " + result_array[i]
    return reply_text

#以下でWebhookから送られてきたイベントをどのように処理するかを記述する
@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    if event.message.text == 'お試し':
        event.message.text = "成功！"
    # あみだくじ
    elif ("あみだくじ" in event.message.text and
        "<参加者>" in event.message.text and
        "<結果>" in event.message.text):
        event.message.text = amidakuji(event.message.text)
    # 退出処理
    elif event.message.text == "帰って":
        line_bot_api.reply_message(event.reply_token, TextSendMessage("任務完了！！"))
        #グループトークからの退出処理
        if hasattr(event.source,"group_id"):
            line_bot_api.leave_group(event.source.group_id)
        #ルームからの退出処理
        if hasattr(event.source,"room_id"):
            line_bot_api.leave_room(event.source.room_id)
        return
    # # ユーザー名取得
    # # グループ
    elif hasattr(event.source,"group_id"):
        event.message.text = ""
    #     profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
    #     members_count = line_bot_api.get_group_members_count(event.source.group_id)
    #     event.message.text = profile.display_name
    # # トークルーム
    elif hasattr(event.source,"room_id"):
        event.message.text = ""
    #     profile = line_bot_api.get_room_member_profile(event.source.room_id, event.source.user_id)
    #     members_count = line_bot_api.get_room_members_count(event.source.room_id)
    #     event.message.text = profile.display_name
    # 返信(個人チャットだとオウム返し)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

# 参加挨拶
@handler.add(JoinEvent)
def greeting_text(event):
    text1="招待ありがとうございます。あみだくじです。\n\n下のテンプレートをコピーして参加者と結果を書き足すとあみだくじが自動生成されます。\結果が空白のくじは「ハズレ」と表示されます。\n\n「帰って」とトークに送るとグループ・トークルームから退会させることができます。"
    text2="あみだくじ\n<参加者>\n\n<結果>\n"
    line_bot_api.reply_message(
        event.reply_token,
        [TextSendMessage(text=text1), TextSendMessage(text=text2)]
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)