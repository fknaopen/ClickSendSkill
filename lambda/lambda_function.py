# -*- coding: utf-8 -*-
import clicksend_client
from clicksend_client import SmsMessage
from clicksend_client.rest import ApiException
import logging
import config
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_intent_name, get_slot_value
from ask_sdk_core.skill_builder import SkillBuilder

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SendSmsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("SendSmsIntent")(handler_input)

    def handle(self, handler_input):
        full_text = get_slot_value(handler_input=handler_input, slot_name="message_content")
        
        if not full_text:
            return handler_input.response_builder.speak("内容が空です。").response

        words = full_text.split()
        try:
            # 最初に見つかった数字のみの単語を特定
            idx = next((i for i, word in enumerate(words) if word.isdigit()), -1)
            if idx == -1:
                return handler_input.response_builder.speak("番号が見つかりません。").response

            # 番号の先頭に + を付与
            to_number = "+" + words[idx]
            
            # メッセージ本文の抽出
            raw_msg = " ".join(words[idx+1:])
            clean_msg = raw_msg.replace("と送って", "").strip()

            if not clean_msg:
                return handler_input.response_builder.speak("本文が空です。").response

            # --- ClickSend SDK 設定 (config.py から取得) ---
            configuration = clicksend_client.Configuration()
            configuration.username = config.CLICKSEND_USER
            configuration.password = config.CLICKSEND_KEY
            
            api_instance = clicksend_client.SMSApi(clicksend_client.ApiClient(configuration))
            
            # メッセージオブジェクトの作成
            sms_message = SmsMessage(
                source="Alexa",
                body=clean_msg,
                to=to_number
            )
            
            # 送信リストの作成
            sms_messages = clicksend_client.SmsMessageCollection(messages=[sms_message])

            # API呼び出し
            api_instance.sms_send_post(sms_messages)
            
            speech = f"送信しました。"
            
        except ApiException as e:
            logger.error(f"ClickSend API Exception: {e}")
            speech = "送信に失敗しました。"
        except Exception as e:
            logger.error(f"Unexpected Error: {e}")
            speech = "エラーが発生しました。"

        return handler_input.response_builder.speak(speech).set_should_end_session(True).response

class AllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True
    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        return handler_input.response_builder.speak("プログラムエラーが発生しました。").response

sb = SkillBuilder()
sb.add_request_handler(SendSmsIntentHandler())
sb.add_exception_handler(AllExceptionHandler())

lambda_handler = sb.lambda_handler()
