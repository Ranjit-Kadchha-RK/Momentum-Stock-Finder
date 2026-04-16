import kivy
from kivy.utils import platform
from kivy.graphics import Color, Rectangle
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import ScrollView
from kivymd.uix.toolbar import MDTopAppBar
import threading
import requests
from datetime import datetime
import webbrowser
import time
import os

kivy.require('2.1.0')

Symbols = []

def data_Creator(symbol):
    today = datetime.today().strftime('%Y-%m-%d')
    year_start = datetime(datetime.today().year, 1, 1).strftime('%Y-%m-%d')
    try:
        period1 = int(datetime.strptime(year_start, '%Y-%m-%d').timestamp())
        period2 = int(datetime.strptime(today, '%Y-%m-%d').timestamp())
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={period1}&period2={period2}&interval=1d"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 429:
            time.sleep(2)
            return data_Creator(symbol)
        data = response.json()
        result = data.get('chart', {}).get('result', [])
        if not result:
            return None
        closes = result[0].get('indicators', {}).get('quote', [{}])[0].get('close', [])
        if not closes or closes[0] is None or closes[-1] is None:
            return None
        ytd_change = ((closes[-1] - closes[0]) / closes[0]) * 100
        return float(ytd_change)
    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {e}")
        return None

def open_stock_link(instance, value):
    webbrowser.open(f"https://finance.yahoo.com/quote/{value}")

class MomentumStocksFinderApp(MDApp):
    def build(self):
        self.stop_fetching = False
        root = MDBoxLayout(orientation='vertical', spacing=10)

        with root.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(source="MSF2.png", pos=root.pos, size=root.size)
        root.bind(size=self.update_background, pos=self.update_background)

        top_app_bar = MDTopAppBar(title="Momentum Stock Finder", size_hint_y=None, height="56dp")
        root.add_widget(top_app_bar)

        scroll_view = ScrollView(size_hint=(1, 1))
        self.results_label = MDLabel(
            size_hint_y=None, height=1000,
            text_size=(None, None), halign="left", valign="top",
            font_size="20sp", theme_text_color="Custom",
            text_color="white", font_style="H6", markup=True
        )
        self.results_label.bind(
            width=lambda instance, value: instance.setter('text_size')(instance, (value, None))
        )
        self.results_label.bind(on_ref_press=open_stock_link)
        scroll_view.add_widget(self.results_label)
        root.add_widget(scroll_view)

        button_layout = MDBoxLayout(orientation="horizontal", size_hint_y=None, height="48dp", spacing=10, padding=10)

        self.show_button = MDRaisedButton(text="Show Top Changes")
        self.show_button.bind(on_release=lambda instance: self.start_fetch())

        self.cancel_button = MDRaisedButton(text="Cancel", disabled=True)
        self.cancel_button.bind(on_release=lambda instance: self.cancel_fetch())

        button_layout.add_widget(self.show_button)
        button_layout.add_widget(self.cancel_button)
        root.add_widget(button_layout)

        file_path = "Stock Symbols.txt"

        try:
            with open(file_path, 'r') as f:
                Symbols.extend([line.strip() + ".NS" for line in f])
        except Exception as e:
            self.results_label.text = f"Error loading symbols: {e}"

        return root

    def start_fetch(self):
        self.stop_fetching = False
        self.cancel_button.disabled = False
        self.show_button.disabled = True
        threading.Thread(target=self.data_Show).start()

    def cancel_fetch(self):
        self.stop_fetching = True
        self.cancel_button.disabled = True

    def data_Show(self):
        self.results_label.text = ""
        largest_changes = []
        for i, symbol in enumerate(Symbols):
            if self.stop_fetching:
                break
            self.show_button.text = f"Loading...({i+1}/{len(Symbols)})"
            ytd_change = data_Creator(symbol)
            if ytd_change is not None:
                largest_changes.append((symbol, ytd_change))
        largest_changes.sort(key=lambda x: x[1], reverse=True)
        result_text = ""
        for i in range(min(10, len(largest_changes))):
            symbol, change = largest_changes[i]
            result_text += f"[ref={symbol}]{symbol}: {change:.2f}%[/ref]\n"
        self.results_label.text = result_text
        self.show_button.text = "Show Top Changes"
        self.show_button.disabled = False
        self.cancel_button.disabled = True

    def update_background(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

if __name__ == '__main__':
    MomentumStocksFinderApp().run()
