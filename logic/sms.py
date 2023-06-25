import africastalking

username = "sandbox"
api_key = "0a6d000a22c9ca327e13b9c006f0f6d1845ae32c155c0f42d48c84de1523fdfb"

africastalking.initialize(username, api_key)
sms_handler = africastalking.SMS


class send_sms():
    def sending(self, recipients, message):
        sender = "UniquesGeek"
        try:
            response = sms_handler.send(message, recipients, sender)
            print (response)
        except Exception as e:
            print (f'Houston, we have a problem: {e}')
            return(1)
        return(0)
        