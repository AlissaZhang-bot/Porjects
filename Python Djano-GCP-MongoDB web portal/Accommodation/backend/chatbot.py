##====================================================================
# This file used to connect IBM watson assistant by API, for chatbot
##====================================================================

import ibm_watson

service = ibm_watson.AssistantV1(
    iam_apikey = '_K2FiFz17kUwgtW2lJQSK2DnZQvpktJE7CIuA2iSz_9F', # replace with Password/ API KEY
    url = 'https://gateway-syd.watsonplatform.net/assistant/api', # replace with Watson Assistant's Credentials - URL
    version = '2018-09-20'
)

workspace_id = '7de4544a-1944-4559-895a-fc1605340ab9' # replace with Worksapce ID