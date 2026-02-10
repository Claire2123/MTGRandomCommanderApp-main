import requests
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.checkbox import CheckBox
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import platform
from kivy.uix.popup import Popup
from kivy.loader import Loader
from kivy.core.image import Image as CoreImage
from kivy.clock import mainthread, Clock
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
        # UI scale factor to make the app slightly smaller on normal-screen devices.
        # Tweak this value if you want larger/smaller overall UI.
        self.ui_scale = 0.88
        
        # Mapping of color codes to symbol files
        self.color_to_symbol = {
            "W": "White.jpg",
            "U": "Blue.jpg",
            "B": "Black.jpg",
            "R": "Red.jpg",
            "G": "Green.jpg",
            "C": "Colorless.jpg"
        }

    def sdp(self, value):
        """Scaled dp: returns dp(value) multiplied by ui_scale."""
        try:
            return dp(value) * self.ui_scale
        except Exception:
            return dp(value)

    def ssize(self, value):
        """Scaled size for raw pixel values (int)."""
        try:
            return int(value * self.ui_scale)
        except Exception:
            return int(value)
    
    def get_system_bar_heights(self):
        """Return (left_px, top_px, right_px, bottom_px) for system UI bars in pixels.

        Attempts Android-specific lookup via resources; falls back to sensible dp defaults.
        """
        left_px = right_px = 0
        top_px = bottom_px = 0
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                resources = activity.getResources()
                # status bar
                res_id = resources.getIdentifier('status_bar_height', 'dimen', 'android')
                if res_id:
                    top_px = resources.getDimensionPixelSize(res_id)
                # navigation bar (may be 0 if using gestures)
                nav_id = resources.getIdentifier('navigation_bar_height', 'dimen', 'android')
                if nav_id:
                    bottom_px = resources.getDimensionPixelSize(nav_id)
            except Exception:
                # Non-fatal; fall back to default dp-based values below
                top_px = bottom_px = 0
        if top_px == 0:
            top_px = int(self.sdp(24))
        if bottom_px == 0:
            bottom_px = int(self.sdp(24))
        return left_px, top_px, right_px, bottom_px

    def update_safe_area_padding(self, *args):
        """Apply safe-area padding to the main layout (in pixels)."""
        left_px, top_px, right_px, bottom_px = self.get_system_bar_heights()
        base = self.sdp(10)
        if hasattr(self, 'main_layout'):
            self.main_layout.padding = [base + left_px, base + top_px, base + right_px, base + bottom_px]

    def update_card_size(self, *args):
        """Resize the commander image to a percentage of the current window width while preserving aspect ratio.

        Chooses a width of about 50% of Window.width, with sensible min/max limits, and clamps height
        so the image never overlaps the top UI or bottom disclaimer.
        """
        if not hasattr(self, 'image'):
            return
        try:
            win_w = Window.width
            win_h = Window.height
            # target percentage of width (50%)
            target_pct = 0.5
            desired_w = int(win_w * target_pct)
            # sensible width bounds
            min_w = int(self.sdp(200))
            max_w = int(win_w * 0.85)
            desired_w = max(min_w, min(desired_w, max_w))
            # aspect ratio (height/width)
            aspect = 546.0 / 420.0
            desired_h = int(desired_w * aspect)

            # Compute reserved space for top UI (padding + checkboxes + buttons + spacer + info label)
            top_padding = int(self.main_layout.padding[1]) if hasattr(self, 'main_layout') else int(self.sdp(10))
            spacer_between = self.sdp(16)
            checkbox_h = getattr(self, 'checkbox_grid').height if hasattr(self, 'checkbox_grid') else 0
            action_h = getattr(self, 'action_row').height if hasattr(self, 'action_row') else 0
            info_h = getattr(self, 'info_label').height if hasattr(self, 'info_label') else self.sdp(160)
            top_used = top_padding + checkbox_h + action_h + spacer_between + info_h

            # Compute reserved bottom space (disclaimer + main_layout bottom padding)
            bottom_reserved = (getattr(self, 'disclaimer_layout').height if hasattr(self, 'disclaimer_layout') else self.sdp(80)) + (int(self.main_layout.padding[3]) if hasattr(self, 'main_layout') else int(self.sdp(10)))

            # Available height for the image (leave a small margin)
            available_height = int(max(self.sdp(160), win_h - top_used - bottom_reserved - self.sdp(20)))

            # If desired height doesn't fit, scale down maintaining aspect ratio
            if desired_h > available_height:
                desired_h = available_height
                desired_w = int(desired_h / aspect)

            # Enforce minimum width/height
            if desired_w < min_w:
                desired_w = min_w
                desired_h = int(desired_w * aspect)

            self.image.size = (desired_w, desired_h)
            # Place image above the bottom reserved area with a small margin
            y_pos = float((bottom_reserved + self.sdp(8)) / float(win_h)) if win_h > 0 else 0.02
            self.image.pos_hint = {'center_x': 0.5, 'y': max(y_pos, 0.02)}

            # Update info_label wrapping width
            if hasattr(self, 'info_label'):
                self.info_label.text_size = (win_w - self.sdp(40), None)
        except Exception:
            pass

    def create_mana_button(self, code):
        """Create a button with mana symbol images"""
        # Create a ManaButton (which is a BoxLayout with button behavior)
        btn = ManaButton(
            orientation='vertical',
            size_hint_y=None,
            height=self.ssize(70),
            spacing=self.ssize(5),
            padding=self.ssize(5)
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
            height=self.ssize(40),
            spacing=self.ssize(5)
        )
        
        # Add left spacer to center images horizontally
        image_container.add_widget(Widget(size_hint_x=1))
        
        # For colorless, only use the colorless symbol
        if code == "C":
            symbol_path = os.path.join(self.mana_symbols_path, self.color_to_symbol["C"])
            img = Image(source=symbol_path, size_hint=(None, None), size=(self.ssize(40), self.ssize(40)), allow_stretch=True)
            image_container.add_widget(img)
        else:
            # For each color in the code, add the corresponding symbol
            for color_char in code:
                if color_char in self.color_to_symbol:
                    symbol_path = os.path.join(self.mana_symbols_path, self.color_to_symbol[color_char])
                    img = Image(source=symbol_path, size_hint=(None, None), size=(self.ssize(40), self.ssize(40)), allow_stretch=True)
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

    def create_symbol_widget(self, code, image_size=40):
        """Return a fixed-size widget containing the mana symbol image(s).

        The widget has size_hint=(None, None) so it can be positioned exactly (centered) by a parent FloatLayout.
        """
        # Determine symbol files for this code
        if code == 'C':
            files = [self.color_to_symbol['C']]
        else:
            files = [self.color_to_symbol[ch] for ch in code if ch in self.color_to_symbol]

        spacing = self.sdp(8)
        count = max(1, len(files))
        width = count * image_size + (count - 1) * spacing
        container = BoxLayout(orientation='horizontal', size_hint=(None, None), size=(width, image_size), spacing=spacing)
        for f in files:
            symbol_path = os.path.join(self.mana_symbols_path, f)
            img = Image(source=symbol_path, size_hint=(None, None), size=(image_size, image_size), allow_stretch=True)
            container.add_widget(img)
        return container

    class LoadingWheel(Widget):
        """Simple rotating image used as a loading indicator."""
        def __init__(self, image_source=None, size=40, **kwargs):
            super().__init__(**kwargs)
            self.size_hint = (None, None)
            self.size = (size, size)
            self.opacity = 0
            self.angle = 0
            self.source = image_source
            from kivy.graphics import PushMatrix, PopMatrix, Rotate, Color, Rectangle
            with self.canvas:
                PushMatrix()
                self.rot = Rotate(origin=self.center, angle=self.angle)
                Color(1, 1, 1, 1)
                self.rect = Rectangle(source=self.source or '', pos=self.pos, size=self.size)
                PopMatrix()
            self.bind(pos=self._update, size=self._update)
            self._event = None

        def _update(self, *args):
            self.rect.pos = self.pos
            self.rect.size = self.size
            self.rot.origin = self.center

        def _spin(self, dt):
            self.angle = (self.angle + dt * 360) % 360
            self.rot.angle = self.angle

        def start(self):
            if self._event is None:
                self._event = Clock.schedule_interval(self._spin, 1 / 30)
                self.opacity = 1

        def stop(self):
            if self._event is not None:
                self._event.cancel()
                self._event = None
                self.opacity = 0

    def build(self):
        self.title = "MTG Random Commander Generator"

        # Main layout (no scrolling)
        main_layout = BoxLayout(orientation='vertical', size_hint=(1, 1), spacing=self.ssize(10), padding=self.ssize(10))
        # Keep a reference to modify padding based on device safe-area
        self.main_layout = main_layout
        # Initialize safe-area padding and update when window size changes
        self.update_safe_area_padding()
        Window.bind(size=self.update_safe_area_padding)
        # Also update card size responsively when the window dimensions change
        Window.bind(size=self.update_card_size)
        
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

        # Color selection (styled boxes that behave like buttons)
        self.checkboxes = {}
        colors_order = [('W', 'White'), ('U', 'Blue'), ('B', 'Black'), ('R', 'Red'), ('G', 'Green'), ('C', 'Colorless')]
        checkbox_grid = GridLayout(cols=3, spacing=self.ssize(10), padding=[self.ssize(10), self.ssize(10), self.ssize(10), self.ssize(10)], size_hint_y=None)
        checkbox_grid.size_hint_y = None
        checkbox_grid.height = self.sdp(220)
        for code, name in colors_order:
            # Use ManaButton styling so the boxes look like the previous buttons
            box = ManaButton(orientation='horizontal', size_hint_y=None, height=self.ssize(100), spacing=self.ssize(5), padding=self.ssize(5))
            from kivy.graphics import Color, Rectangle, Line
            box.canvas.before.clear()
            with box.canvas.before:
                Color(0, 0, 0, 1)
                Rectangle(size=box.size, pos=box.pos)
                Color(0.3, 0.3, 0.3, 1)
                Line(rectangle=(box.x, box.y, box.width, box.height), width=2)
            box.bind(size=self._update_rect, pos=self._update_rect)

            cb = CheckBox(active=False, size_hint=(None, None), size=(self.ssize(36), self.ssize(36)))
            cb.bind(active=lambda checkbox, value, c=code: self.on_color_checkbox(c, value))
            self.checkboxes[code] = cb
            # Use larger symbol images and center them using a FloatLayout so checkbox doesn't offset them
            from kivy.uix.floatlayout import FloatLayout
            float_area = FloatLayout(size_hint=(1, 1))
            # position checkbox at the left edge of the box
            cb.pos_hint = {'x': 0.02, 'center_y': 0.5}
            float_area.add_widget(cb)
            # Create fixed-size symbol widget and center it in the float area
            symbol_widget = self.create_symbol_widget(code, image_size=self.ssize(56))
            symbol_widget.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            float_area.add_widget(symbol_widget)
            box.add_widget(float_area)
            box.bind(on_release=lambda b, c=code: self.toggle_checkbox(c))
            checkbox_grid.add_widget(box)
        main_layout.add_widget(checkbox_grid)
        # Keep a reference for sizing calculations
        self.checkbox_grid = checkbox_grid
        # Small spacer so action buttons sit slightly below the checkboxes
        main_layout.add_widget(Widget(size_hint_y=None, height=self.ssize(6)))

        # Buttons: Generate and Clear Selection side-by-side
        action_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=self.ssize(40), spacing=self.ssize(10), padding=[self.ssize(10),0])
        generate_btn = Button(
            text="Fetch Commander",
            background_color=(0.2, 0.3, 0.5, 1),
            color=(0.5, 1, 1, 1),
            font_size=self.sdp(14)
        )
        generate_btn.bind(on_release=self.generate_commander)

        clear_btn = Button(
            text="Clear Selection",
            background_color=(0.4, 0.1, 0.1, 1),
            color=(1,1,1,1),
            font_size=self.sdp(14)
        )
        clear_btn.bind(on_release=self.clear_selection)

        action_row.add_widget(generate_btn)
        action_row.add_widget(clear_btn)
        # Keep a reference for sizing calculations
        self.action_row = action_row
        main_layout.add_widget(action_row)
        # Add extra vertical space so the info text is separated from the action buttons
        main_layout.add_widget(Widget(size_hint_y=None, height=16))
        # Content overlay area (fills remaining space) so we can center a large loading wheel behind the text
        from kivy.uix.floatlayout import FloatLayout
        content_area = FloatLayout(size_hint=(1, 1))

        # Large loading wheel centered behind text (hidden by default)
        self.loading_wheel = self.LoadingWheel(image_source=os.path.join(self.mana_symbols_path, 'Colorless.jpg'), size=self.ssize(180))
        self.loading_wheel.pos_hint = {'center_x': 0.5, 'center_y': 0.65}
        content_area.add_widget(self.loading_wheel)

        # Description label (on top of loading wheel)
        self.info_label = Label(
            text="",
            halign="center",
            valign="top",
            size_hint=(0.9, None),
            height=self.ssize(160),
            color=(1,1,1,1),
            font_size=self.sdp(15),
            text_size=(Window.width - self.sdp(40), None),
            pos_hint={'center_x':0.5, 'top':0.80}
        )
        content_area.add_widget(self.info_label)

        # Card image centered below the info text
        self.image = Image(size_hint=(None, None), size=(self.ssize(420), self.ssize(546)), pos_hint={'center_x':0.5, 'y':0.06})
        content_area.add_widget(self.image)
        # Ensure the card scales to the current window size at startup
        self.update_card_size()

        # No-image label below image area
        self.no_image_label = Label(text="", color=(1,1,1,1), size_hint=(0.9, None), height=self.ssize(40), font_size=self.sdp(14), pos_hint={'center_x':0.5, 'y':0.02})
        content_area.add_widget(self.no_image_label)

        main_layout.add_widget(content_area)

        # Disclaimer section at the bottom
        disclaimer_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=self.ssize(80), padding=self.ssize(10), spacing=self.ssize(5))
        disclaimer_label = Label(
            text="!!!This app is currently under development and may not be perfect!!!",
            color=(1, 1, 0, 1),  # Yellow text
            size_hint_y=None,
            height=self.ssize(30),
            font_size=self.sdp(16)
        )
        disclaimer_layout.add_widget(disclaimer_label)
        
        github_button = Button(
            text="My Github",
            size_hint_y=None,
            height=self.ssize(40),
            background_color=(0.2, 0.3, 0.5, 1),
            color=(0.5, 1, 1, 1),  # Cyan text
            font_size=self.sdp(12)
        )
        github_button.bind(on_press=self.open_github)
        disclaimer_layout.add_widget(github_button)
        # Keep a reference for sizing calculations and overlap checks
        self.disclaimer_layout = disclaimer_layout
        main_layout.add_widget(disclaimer_layout) 

        return main_layout

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message, font_size=self.sdp(16)), size_hint=(None, None), size=(self.ssize(800), self.ssize(400)))
        popup.open()

    def on_color_checkbox(self, code, active):
        """Ensure 'Colorless' (C) is mutually exclusive with other colors."""
        # cb.active __changing__ sets active state; we only act when checkbox becomes active
        if not hasattr(self, 'checkboxes'):
            return
        if active:
            if code == 'C':
                # Unselect all other checkboxes when Colorless selected
                for k, cb in self.checkboxes.items():
                    if k != 'C':
                        cb.active = False
            else:
                # Unselect Colorless if any other color is selected
                c_cb = self.checkboxes.get('C')
                if c_cb:
                    c_cb.active = False

    def toggle_checkbox(self, code):
        """Toggle the checkbox state (used when box is clicked)."""
        cb = self.checkboxes.get(code)
        if cb is not None:
            cb.active = not cb.active

    def clear_selection(self, instance):
        """Clear all color selections."""
        for k, cb in self.checkboxes.items():
            cb.active = False

    def generate_commander(self, instance):
        """Build a color code from selected checkboxes and fetch a commander."""
        selected = [k for k, cb in self.checkboxes.items() if cb.active]
        if not selected:
            self.show_popup("Select Colors", "Please select at least one color.")
            return
        # Start loading indicator only when we are about to fetch
        if 'C' in selected:
            # Colorless selected — fetch colorless commanders
            if hasattr(self, 'loading_wheel'):
                self.loading_wheel.start()
            self.get_commander('C')
            return
        # Keep color ordering stable WUBRG
        order = ['W', 'U', 'B', 'R', 'G']
        code = ''.join([c for c in order if c in selected])
        if hasattr(self, 'loading_wheel'):
            self.loading_wheel.start()
        self.get_commander(code)

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
                # Ensure loading stops on error
                self.stop_loading()
                self.show_popup("Error", f"Failed to fetch data: {e}")
                return

            if "data" not in data or len(data["data"]) == 0:
                self.stop_loading()
                self.show_popup("No Commanders", "No commanders found for this color combination.")
                return

            # Filter out unwanted cards:
            # - Arena-only cards
            # - Cards that are banned in the Commander format
            # - Silver-bordered cards (funny / silver border)
            # - Specific known problematic names (lowercased)
            banned_names = {"acorn"}
            commanders = []
            for c in data["data"]:
                # Skip Arena-only entries
                if 'arena' in c.get('games', []):
                    continue
                # Skip if explicitly banned in Commander format
                if c.get('legalities', {}).get('commander') == 'banned':
                    continue
                # Skip silver-bordered / funny cards
                if c.get('border_color') == 'silver':
                    continue
                # Skip explicit blacklisted names
                if c.get('name', '').strip().lower() in banned_names:
                    continue
                commanders.append(c)
            if not commanders:
                self.stop_loading()
                self.show_popup("No Commanders", "No suitable commanders found for this color combination.")
                return
            # Shuffle the list to ensure randomness
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
                # Download and process the image in this background thread, then set texture on main thread
                self.download_and_show_image(img_url)
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
        # Stop the loading wheel now that we have either an image or a no-image message
        if hasattr(self, 'loading_wheel'):
            self.loading_wheel.stop()

    @mainthread
    def stop_loading(self):
        """Called from background thread to ensure the loading wheel is stopped on the main thread."""
        if hasattr(self, 'loading_wheel'):
            self.loading_wheel.stop()

    def download_and_show_image(self, url):
        """Download image bytes, convert white rounded corners to transparent if detected, and set texture."""
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            content = resp.content
        except requests.exceptions.RequestException as e:
            # Stop the spinner and show a message
            self.stop_loading()
            self.show_popup("Image Error", f"Failed to download image: {e}")
            return

        # Default extension detection
        ext = 'png' if (len(content) >= 8 and content[:8].startswith(b'\x89PNG')) else 'jpg'

        # Try to use PIL to detect rounded white corners and make them transparent
        try:
            from PIL import Image as PILImage
            im = PILImage.open(BytesIO(content)).convert('RGBA')
            w, h = im.size
            threshold = 245
            def corners_are_white():
                for cx, cy in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]:
                    r,g,b,a = im.getpixel((cx,cy))
                    if not (r >= threshold and g >= threshold and b >= threshold):
                        return False
                return True
            if corners_are_white():
                datas = im.getdata()
                newData = []
                for item in datas:
                    r,g,b,a = item
                    if r >= threshold and g >= threshold and b >= threshold:
                        newData.append((255,255,255,0))
                    else:
                        newData.append((r,g,b,a))
                im.putdata(newData)
                buf = BytesIO()
                im.save(buf, format='PNG')
                content = buf.getvalue()
                ext = 'png'
        except Exception:
            # If PIL is not available or fails, proceed with raw bytes
            pass

        # Set the image on the main thread
        self._set_image_bytes(content, ext)

    @mainthread
    def _set_image_bytes(self, content, ext):
        try:
            core = CoreImage(BytesIO(content), ext=ext)
            # Preserve transparency by using CoreImage texture directly
            self.image.texture = core.texture
            self.no_image_label.text = ""
            self.no_image_label.background_color = (0.27, 0.19, 0.98, 0)  # Hide textbox
        except Exception as e:
            self.show_popup("Image Error", f"Failed to load image: {e}")
        finally:
            if hasattr(self, 'loading_wheel'):
                self.loading_wheel.stop()

    def _on_image_loaded(self, img, *args):
        self.image.texture = img.texture

    def open_github(self, instance):
        webbrowser.open("https://github.com/Claire2123")

if __name__ == "__main__":
    CommanderApp().run()
