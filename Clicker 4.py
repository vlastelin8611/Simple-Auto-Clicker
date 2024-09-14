import tkinter as tk
from tkinter import ttk
import random
import ctypes
import platform
import keyboard
from PIL import Image, ImageTk, ImageDraw

# Low-level functions for mouse clicks
SendInput = ctypes.windll.user32.SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

def click(x, y):
    ctypes.windll.user32.SetCursorPos(x, y)
    mouse_input_down = MouseInput(dx=0, dy=0, mouseData=0, dwFlags=0x0002, time=0, dwExtraInfo=None)
    input_struct_down = Input(type=0, ii=Input_I(mi=mouse_input_down))
    SendInput(1, ctypes.byref(input_struct_down), ctypes.sizeof(input_struct_down))

    mouse_input_up = MouseInput(dx=0, dy=0, mouseData=0, dwFlags=0x0004, time=0, dwExtraInfo=None)
    input_struct_up = Input(type=0, ii=Input_I(mi=mouse_input_up))
    SendInput(1, ctypes.byref(input_struct_up), ctypes.sizeof(input_struct_up))

class ClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Автокликер")
        self.root.geometry("300x500")
        self.is_running = False

        self.create_widgets()
        self.click_labels = []
        self.add_click_label()
        self.update_status()

        self.listener = None

        if platform.system() == 'Windows':
            self.start_keyboard_listener()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TLabel", foreground="#FF1493", background="#2b2b2b", font=("Helvetica", 12))
        style.configure("TEntry", foreground="#FF1493", background="#2b2b2b", font=("Helvetica", 12))
        style.configure("TButton", foreground="#FF1493", background="#2b2b2b", font=("Helvetica", 12), padding=6)

        self.root.configure(bg="#2b2b2b")

        ttk.Label(self.root, text="Количество кликов:", style="TLabel").pack(pady=5)
        self.clicks_entry = ttk.Entry(self.root, style="TEntry")
        self.clicks_entry.insert(0, "100")
        self.clicks_entry.pack(pady=5)

        ttk.Label(self.root, text="Интервал между кликами (мс):", style="TLabel").pack(pady=5)
        self.interval_entry = ttk.Entry(self.root, style="TEntry")
        self.interval_entry.insert(0, "100")
        self.interval_entry.pack(pady=5)

        ttk.Label(self.root, text="Множитель кликов:", style="TLabel").pack(pady=5)
        self.multiplier_entry = ttk.Entry(self.root, style="TEntry")
        self.multiplier_entry.insert(0, "1")
        self.multiplier_entry.pack(pady=5)

        self.toggle_button = ttk.Button(self.root, text="Запустить", command=self.toggle_clicking, style="TButton")
        self.toggle_button.pack(pady=10)

        self.add_button = ttk.Button(self.root, text="Добавить метку", command=self.add_click_label, style="TButton")
        self.add_button.pack(pady=5)

        self.remove_button = ttk.Button(self.root, text="Удалить метку", command=self.remove_click_label, style="TButton")
        self.remove_button.pack(pady=5)

        self.instruction_label = ttk.Label(self.root, text="Используйте 'L' для запуска/остановки", style="TLabel")
        self.instruction_label.pack(side="bottom")

    def add_click_label(self):
        diameter = 42
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        overlay.attributes("-transparentcolor", "black")
        overlay.geometry(f"{diameter}x{diameter}+100+100")

        image = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([(5, 5), (diameter - 5, diameter - 5)], outline="#FF1493", width=4)
        click_image = ImageTk.PhotoImage(image)

        label_on_overlay = tk.Label(overlay, image=click_image, bg="black")
        label_on_overlay.image = click_image  # Keep a reference to the image
        label_on_overlay.pack()

        # Bind mouse events for moving the overlay
        label_on_overlay.bind("<Button-1>", lambda event, overlay=overlay: self.start_moving(event, overlay))
        label_on_overlay.bind("<B1-Motion>", lambda event, overlay=overlay: self.moving(event, overlay))
        label_on_overlay.bind("<ButtonRelease-1>", lambda event, overlay=overlay: self.stop_moving(event, overlay))

        self.click_labels.append((overlay, label_on_overlay, click_image))

    def remove_click_label(self):
        if len(self.click_labels) > 1:
            overlay, label_on_overlay, click_image = self.click_labels.pop()
            overlay.destroy()

    def start_moving(self, event, overlay):
        overlay.lift()
        self.mouse_x = event.x
        self.mouse_y = event.y

    def moving(self, event, overlay):
        x = overlay.winfo_x() + event.x - self.mouse_x
        y = overlay.winfo_y() + event.y - self.mouse_y
        overlay.geometry(f"+{x}+{y}")

    def stop_moving(self, event, overlay):
        x = overlay.winfo_x() + event.x - self.mouse_x
        y = overlay.winfo_y() + event.y - self.mouse_y
        overlay.geometry(f"+{x}+{y}")

    def start_keyboard_listener(self):
        try:
            keyboard.on_press_key('l', self.on_toggle_key_press)
        except ValueError as e:
            print(f"Error setting hotkey: {e}")

    def on_toggle_key_press(self, event):
        self.toggle_clicking()

    def toggle_clicking(self):
        self.is_running = not self.is_running
        self.update_status()

        if self.is_running:
            self.start_clicking()
        else:
            self.stop_clicking()

    def update_status(self):
        if self.is_running:
            self.toggle_button.config(text="Остановить")
        else:
            self.toggle_button.config(text="Запустить")

    def start_clicking(self):
        self.total_clicks = int(self.clicks_entry.get())
        self.interval = float(self.interval_entry.get())
        self.multiplier = int(self.multiplier_entry.get())
        self.click_count = self.total_clicks

        self.current_label_index = 0  # Initialize the index for cycling through labels
        self.perform_clicks()

    def stop_clicking(self):
        self.is_running = False
        self.update_status()

    def perform_clicks(self):
        if self.is_running and self.click_count > 0:
            overlay, label_on_overlay, click_image = self.click_labels[self.current_label_index]
            overlay_x = overlay.winfo_x()
            overlay_y = overlay.winfo_y()

            click_x = overlay_x + click_image.width() // 2
            click_y = overlay_y + click_image.height() // 2

            for _ in range(self.multiplier):
                if self.click_count > 0:
                    click(click_x, click_y)
                    self.change_label_color(label_on_overlay)
                    self.click_count -= 1

            # Move to the next label
            self.current_label_index = (self.current_label_index + 1) % len(self.click_labels)

            self.root.update_idletasks()
            self.root.after(int(self.interval), self.perform_clicks)
        else:
            self.stop_clicking()

    def change_label_color(self, label_on_overlay):
        random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        diameter = 42

        image = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([(5, 5), (diameter - 5, diameter - 5)], outline=random_color, width=4)

        click_image = ImageTk.PhotoImage(image)
        label_on_overlay.config(image=click_image)
        label_on_overlay.image = click_image  # Keep a reference to the image

if __name__ == "__main__":
    root = tk.Tk()
    app = ClickerApp(root)
    root.mainloop()
