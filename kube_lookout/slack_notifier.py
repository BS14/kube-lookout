import slack


class SlackNotifier:
    def __init__(self, token):
        self._client = slack.WebClient(token)

    def post_message(self, channel, blocks):
        response = self._client.chat_postMessage(channel=channel, blocks=blocks)
        return response.data["ts"], response.data["channel"]

    def update_message(self, channel, message_id, blocks):
        response = self._client.chat_update(channel=channel, ts=message_id, blocks=blocks)
        return response.data["ts"], response.data["channel"]
