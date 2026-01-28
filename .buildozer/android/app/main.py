import requests
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.loader import Loader
from kivy.clock import mainthread
from io import BytesIO
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
import os
import webbrowser

print("This app is under development and is not perfect!")

# Custom button widget that uses images
class ManaButton(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Clear canvas to remove any default background
        self.canvas.clear()

color_options = {
    "W": "White", "U": "Blue", "B": "Black", "R": "Red", "G": "Green",
    "WU": "White-Blue", "UB": "Blue-Black", "BR": "Black-Red", "RG": "Red-Green", "GW": "Green-White",
    "WB": "White-Black", "UR": "Blue-Red", "BG": "Black-Green", "RW": "Red-White", "GU": "Green-Blue",
    "WUB": "White-Blue-Black", "UBR": "Blue-Black-Red", "BRG": "Black-Red-Green", "RGW": "Red-Green-White", "GWU": "Green-White-Blue",
    "WBR": "White-Black-Red", "URG": "Blue-Red-Green", "BGW": "Black-Green-White", "RWU": "Red-White-Blue", "UBG": "Blue-Black-Green",
    "WUBR": "Non-Green", "UBRG": "Non-White", "BRGW": "Non-Blue", "RGWU": "Non-Black", "GWUB": "Non-Red",
    "WUBRG": "Five-Color",
    "C": "Colorless"
}

class CommanderApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mana_symbols_path = os.path.join(os.path.dirname(__file__), 'mana_symbols')
        
        # Mapping of color codes to symbol files
        self.color_to_symbol = {
            "W": "White.jpg",
            "U": "Blue.jpg",
            "B": "Black.jpg",
            "R": "Red.jpg",
            "G": "Green.jpg",
            "C": "Colorless.jpg"
        }
    
    def create_mana_button(self, code):
        """Create a button with mana symbol images"""
        # Create a ManaButton (which is a BoxLayout with button behavior)
        btn = ManaButton(
            orientation='vertical',
            size_hint_y=None,
            height=70,
            spacing=5,
            padding=5
        )
        
        # Set background color and outline using canvas
        from kivy.graphics import Color, Rectangle, Line
        with btn.canvas.before:
            # Black background to match image boxes
            Color(0, 0, 0, 1)
            Rectangle(size=btn.size, pos=btn.pos)
            # Dark grey outline to distinguish button
            Color(0.3, 0.3, 0.3, 1)
            Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=2)
        
        # Bind to update rectangle and outline when button size/pos changes
        btn.bind(size=self._update_rect, pos=self._update_rect)
        
        # Add top spacer for vertical centering
        btn.add_widget(Widget(size_hint_y=1))
        
        # Create horizontal container for images
        image_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=40,
            spacing=5
        )
        
        # Add left spacer to center images horizontally
        image_container.add_widget(Widget(size_hint_x=1))
        
        # For colorless, only use the colorless symbol
        if code == "C":
            symbol_path = os.path.join(self.mana_symbols_path, self.color_to_symbol["C"])
            img = Image(source=symbol_path, size_hint=(None, None), size=(40, 40), allow_stretch=True)
            image_container.add_widget(img)
        else:
            # For each color in the code, add the corresponding symbol
            for color_char in code:
                if color_char in self.color_to_symbol:
                    symbol_path = os.path.join(self.mana_symbols_path, self.color_to_symbol[color_char])
                    img = Image(source=symbol_path, size_hint=(None, None), size=(40, 40), allow_stretch=True)
                    image_container.add_widget(img)
        
        # Add right spacer to center images horizontally
        image_container.add_widget(Widget(size_hint_x=1))
        
        btn.add_widget(image_container)
        
        # Add bottom spacer for vertical centering
        btn.add_widget(Widget(size_hint_y=1))
        
        return btn
    
    def _update_rect(self, instance, value):
        """Update background rectangle and outline when button size/pos changes"""
        instance.canvas.before.clear()
        from kivy.graphics import Color, Rectangle, Line
        with instance.canvas.before:
            # Black background to match image boxes
            Color(0, 0, 0, 1)
            Rectangle(size=instance.size, pos=instance.pos)
            # Dark grey outline to distinguish button
            Color(0.3, 0.3, 0.3, 1)
            Line(rectangle=(instance.x, instance.y, instance.width, instance.height), width=2)

    def build(self):
        self.title = "MTG Random Commander Generator"

        # Main layout inside a ScrollView for full vertical scrolling
        scrollview = ScrollView(size_hint=(1, 1))
        main_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=10)
        main_layout.bind(minimum_height=main_layout.setter('height'))
        
        # Add gradient background image
        from kivy.graphics import Rectangle
        gradient_path = os.path.join(os.path.dirname(__file__), 'gradient_background.png')
        with main_layout.canvas.before:
            Rectangle(source=gradient_path, pos=(0, 0), size=(Window.width, main_layout.height))
        
        # Bind to update background when size changes
        def update_background(instance, value):
            main_layout.canvas.before.clear()
            with main_layout.canvas.before:
                Rectangle(source=gradient_path, pos=(0, 0), size=(Window.width, main_layout.height))
        
        main_layout.bind(size=update_background)

        # Button grid
        button_grid = GridLayout(
            cols=3,
            spacing=10,
            padding=[10, 10, 10, 10],
            size_hint_y=None
        )
        button_grid.bind(minimum_height=button_grid.setter('height'))
        for code, name in color_options.items():
            btn = self.create_mana_button(code)
            btn.bind(on_release=lambda btn, c=code: self.get_commander(c))
            button_grid.add_widget(btn)
        main_layout.add_widget(button_grid)
        # Spacer to prevent overlap between buttons and card description
        main_layout.add_widget(Widget(size_hint_y=None, height=150))

        # Description label
        self.info_label = Label(
            text="",
            halign="center",
            valign="top",
            size_hint=(1, None),
            height=120,
            color=(1,1,1,1),
            font_size='15sp',
            text_size=(Window.width - 40, None)
        )
        main_layout.add_widget(self.info_label)

        # Move image directly below card description, keep large size
        main_layout.add_widget(Widget(size_hint_y=None, height=120))
        image_box = BoxLayout(orientation='horizontal', size_hint=(1, None), height=780)
        image_box.add_widget(Widget())  # left spacer
        self.image = Image(size_hint=(None, None), size=(600, 780))
        image_box.add_widget(self.image)
        image_box.add_widget(Widget())  # right spacer
        main_layout.add_widget(image_box)

        self.no_image_label = Label(text="", color=(1,1,1,1), size_hint_y=None, height=40)
        main_layout.add_widget(self.no_image_label)

        # Disclaimer section at the bottom
        disclaimer_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80, padding=10, spacing=5)
        disclaimer_label = Label(
            text="!!!This app is currently under development and may not be perfect!!!",
            color=(1, 1, 0, 1),  # Yellow text
            size_hint_y=None,
            height=30,
            font_size='16sp'
        )
        disclaimer_layout.add_widget(disclaimer_label)
        
        github_button = Button(
            text="My Github",
            size_hint_y=None,
            height=40,
            background_color=(0.2, 0.3, 0.5, 1),
            color=(0.5, 1, 1, 1),  # Cyan text
            font_size='12sp'
        )
        github_button.bind(on_press=self.open_github)
        disclaimer_layout.add_widget(github_button)
        
        main_layout.add_widget(disclaimer_layout)

        scrollview.add_widget(main_layout)
        return scrollview

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(800, 400))
        popup.open()

    def get_commander(self, color_code):
        if color_code == "C":
            query = "https://api.scryfall.com/cards/search?q=t:legendary+type:creature+id=c+is:commander&unique=cards"
        else:
            query = f"https://api.scryfall.com/cards/search?q=(t:legendary+type:creature+is:commander+color={color_code}&unique=cards"
    def get_commander(self, color_code):
        # Hide the white box overlay before searching for a new card
        self.no_image_label.text = ""
        self.no_image_label.background_color = (0.27, 0.19, 0.98, 0)
        if color_code == "C":
            query = "https://api.scryfall.com/cards/search?q=t:legendary+type:creature+id=c+is:commander&unique=cards"
        else:
            query = f"https://api.scryfall.com/cards/search?q=(t:legendary+type:creature+OR+oracle:%22can+be+your+commander%22+OR+oracle:partner)+color={color_code}&unique=cards"
        def fetch():
            try:
                response = requests.get(query)
                response.raise_for_status()
                data = response.json()
            except requests.exceptions.RequestException as e:
                self.show_popup("Error", f"Failed to fetch data: {e}")
                return

            if "data" not in data or len(data["data"]) == 0:
                self.show_popup("No Commanders", "No commanders found for this color combination.")
                return

            # Shuffle the list to ensure randomness
            commanders = data["data"][:]
            random.shuffle(commanders)
            last_name = getattr(self, "last_commander_name", None)
            # Filter out last commander if possible
            filtered = [c for c in commanders if c["name"] != last_name]
            if filtered:
                commander = random.choice(filtered)
            else:
                commander = commanders[0]  # fallback if all are the same
            self.last_commander_name = commander["name"]

            info_text = f"Name: {commander['name']}\nMana Cost: {commander.get('mana_cost', 'N/A')}\nType: {commander.get('type_line', 'N/A')}\nText: {commander.get('oracle_text', 'No description available')}"
            self.update_info(info_text)

            img_url = None
            # Try image_uris (normal), then card_faces[0][image_uris][normal], then card_faces[0][image_uris][large], else None
            if "image_uris" in commander and "normal" in commander["image_uris"]:
                img_url = commander["image_uris"]["normal"]
            elif "card_faces" in commander and commander["card_faces"]:
                face = commander["card_faces"][0]
                if "image_uris" in face and "normal" in face["image_uris"]:
                    img_url = face["image_uris"]["normal"]
                elif "image_uris" in face and "large" in face["image_uris"]:
                    img_url = face["image_uris"]["large"]
            # If still no image, show 'no image available' and clear image
            if img_url:
                self.update_image(img_url, no_image=False)
            else:
                self.update_image(None, no_image=True)

        import threading
        threading.Thread(target=fetch).start()

    @mainthread
    def update_info(self, text):
        # Only split by explicit newlines, do not break lines mid-sentence
        self.info_label.text = text
        self.info_label.text_size = (Window.width - 40, None)

    @mainthread
    def update_image(self, url, no_image=False):
        # Always clear image first
        self.image.source = ""
        self.image.texture = None
        if url and not no_image:
            Loader.loading_image = None
            img = Loader.image(url)
            img.bind(on_load=self._on_image_loaded)
            self.no_image_label.text = ""
            self.no_image_label.background_color = (0.27, 0.19, 0.98, 0)  # Hide textbox
        else:
            self.no_image_label.text = "No Image Found"
            self.no_image_label.background_color = (0.27, 0.19, 0.98, 1)

    def _on_image_loaded(self, img, *args):
        self.image.texture = img.texture

    def open_github(self, instance):
        webbrowser.open("https://github.com/Claire2123")

if __name__ == "__main__":
    CommanderApp().run()
