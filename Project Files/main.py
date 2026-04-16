import kivy
from kivy.app import App
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import BoxLayout
from kivymd.uix.scrollview import ScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivy.graphics import Color, Rectangle
import threading
import yfinance as yf
from datetime import datetime
import webbrowser
import ssl
import certifi

# Ensure secure HTTPS context
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

kivy.require('2.1.0')

Symbols = []

def data_Creator(symbol):
    today = datetime.today().strftime('%Y-%m-%d')
    year_start = datetime(datetime.today().year, 1, 1).strftime('%Y-%m-%d')

    try:
        data = yf.download(symbol, start=year_start, end=today)
        if data.empty:
            return None
        ytd_change = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
        return float(ytd_change)

    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {e}")
        return None

def data_Show(label, button):
    button.text = "Loading..."
    button.disabled = True
    label.text = ""

    largest_changes = []
    for i, symbol in enumerate(Symbols):
        button.text = f"Loading...({i+1}/{len(Symbols)})"
        ytd_change = data_Creator(symbol)
        if ytd_change is not None:
            largest_changes.append((symbol, ytd_change))

    largest_changes.sort(key=lambda x: x[1], reverse=True)

    result_text = ""
    for i in range(min(10, len(largest_changes))):
        symbol, change = largest_changes[i]
        result_text += f"[ref={symbol}]{symbol}: {change:.2f}%[/ref]\n"

    label.text = result_text
    button.text = "Show Top Changes"
    button.disabled = False

def on_button_click(label, button):
    task_thread = threading.Thread(target=data_Show, args=(label, button))
    task_thread.start()

def open_stock_link(instance, value):
    stock_symbol = value
    webbrowser.open(f"https://finance.yahoo.com/quote/{stock_symbol}")

class MomentumStocksFinderApp(MDApp):
    def build(self):
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        with root.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(source="MSF2.png", pos=root.pos, size=root.size)
        root.bind(size=self.update_background, pos=self.update_background)

        top_app_bar = MDTopAppBar(title="Momentum Stock Finder", size_hint_y=None, height="56dp")
        root.add_widget(top_app_bar)

        scroll_view = ScrollView()
        self.results_label = MDLabel(
            size_hint_y=None, height=650, text_size=(None, None),
            halign="left", valign="top", font_size="48sp",
            theme_text_color="Custom", text_color="white",
            font_style="H5", markup=True
        )
        self.results_label.bind(
            width=lambda instance, value: instance.setter('text_size')(instance, (value, None))
        )
        self.results_label.bind(on_ref_press=open_stock_link)
        scroll_view.add_widget(self.results_label)

        self.show_button = MDRaisedButton(text="Show Top Changes", size_hint_y=None, height="50dp", font_size="16sp")
        self.show_button.bind(on_release=lambda instance: on_button_click(self.results_label, self.show_button))

        root.add_widget(scroll_view)
        root.add_widget(self.show_button)

        with open('Stock Symbols.txt', 'r') as f:
            Symbols.extend([line.strip() + ".NS" for line in f])

        return root

    def update_background(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

if __name__ == '__main__':
    MomentumStocksFinderApp().run()
