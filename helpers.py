import requests

def getFieldValues(fields):
  form = []
  b = False
  val = ''
  for char in fields:

    if char == '(':
      b = True
    elif char == ')':
      b = False
      form.append(val);
      val = ''
    else:
      if b:
        val = val + char

  return form

def send_telegram(text, bot_chatID):

    bot_token = '1067906064:AAFxT8ahLn3jEMdKsge26GEPndKpS6xfrUo'
    #bot_chatID = '269928547'
    bot_message = text
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)
    #logger.info('Message sent to chatID ' + bot_chatID)

    return response.json()

class Dict2Obj:
  def __init__(self, dict):
    for k, v in dict.items():
      setattr(self, k, v)