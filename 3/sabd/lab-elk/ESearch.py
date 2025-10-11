import kivy
kivy.require('2.3.1')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty

import requests

class SearchScreen(BoxLayout):
    result = ObjectProperty()
    url = ObjectProperty()
    field = ObjectProperty()
    request = ObjectProperty()
    index = ObjectProperty()

    def on_search(self):
        url = f'http://{self.url.text}/lab/_search'
        params = {
            'q': f'{self.field.text}:{self.request.text}'
        }

        index = int(self.index.text)

        responce = requests.get(url, params=params)
        body = responce.json()

        count = body['hits']['total']['value']
        output = f'Count: {count}'
        if count > 0 and index < 10:
            value = body['hits']['hits'][index]['_source']['event']['original']
            output += f'\n\n{value}'
        self.result.text = output

class ESearchApp(App):
    def build(self):
        return SearchScreen()

if __name__ == '__main__':
    ESearchApp().run()
