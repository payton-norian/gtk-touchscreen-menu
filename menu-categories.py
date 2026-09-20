#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, Gdk


class MainMenu(Gtk.Window):
    def __init__(self):
        # 1. Меняем POPUP на TOPLEVEL для корректной работы фокуса
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        # Убираем рамки и заголовки, делая окно похожим на popup
        self.set_decorated(False)
        self.set_resizable(True)
        self.set_keep_above(True)
        self.set_modal(True)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Подключаем события
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)
        
        # 2. Перехватываем ввод после отображения окна (mapping)
        self.connect("map", self.on_map)

        # Основной контейнер
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.set_border_width(12)
        outer.set_spacing(8)
        self.add(outer)

        title = Gtk.Label()
        title.set_markup("<b>Приложения</b>")
        title.set_halign(Gtk.Align.START)
        outer.pack_start(title, False, False, 0)

        # Прокрутка
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(820, 620)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        outer.pack_start(scrolled, True, True, 0)

        # Сетка кнопок
        flowbox = Gtk.FlowBox()
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_column_spacing(8)
        flowbox.set_row_spacing(8)
        flowbox.set_max_children_per_line(5)
        flowbox.set_min_children_per_line(3)
        scrolled.add(flowbox)

        applications = [app for app in Gio.AppInfo.get_all() if app.should_show()]
        applications.sort(key=lambda app: app.get_display_name().lower())

        for app in applications:
            button = self.create_button(app)
            flowbox.add(button)

        self.show_all()
        self.present()

    def on_map(self, window):
        """Метод жестко перехватывает фокус мыши и клавиатуры при показе окна."""
        window_gdk = self.get_window()
        device_manager = Gdk.Display.get_default().get_device_manager()
        pointer = device_manager.get_client_pointer()
        
        # Перехватываем клики мыши вне окна
        Gdk.device_grab(
            pointer, window_gdk, 
            Gdk.GrabOwnership.APPLICATION, True, 
            Gdk.EventMask.BUTTON_PRESS_MASK, None, 
            Gdk.CURRENT_TIME
        )
        # Перехватываем клавиатуру для работы Escape
        keyboard = pointer.get_associated_device()
        if keyboard:
            Gdk.device_grab(
                keyboard, window_gdk, 
                Gdk.GrabOwnership.APPLICATION, True, 
                Gdk.EventMask.KEY_PRESS_MASK, None, 
                Gdk.CURRENT_TIME
            )

    def create_button(self, app):
        button = Gtk.Button()
        button.set_size_request(110, 90)
        button.set_tooltip_text(app.get_description() or "")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        icon = app.get_icon()

        if icon is not None:
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.DIALOG)
            box.pack_start(image, False, False, 0)

        label = Gtk.Label(label=app.get_display_name())
        label.set_max_width_chars(14)
        label.set_ellipsize(3)
        label.set_line_wrap(True)

        box.pack_start(label, False, False, 0)
        button.add(box)

        button.connect("clicked", self.launch_application, app)
        return button

    def launch_application(self, button, app):
        try:
            app.launch([], None)
        except GLib.Error as error:
            print(f"Не удалось запустить приложение: {error}")

        self.destroy()

    def on_focus_out(self, window, event):
        self.destroy()
        return False

    def on_key_press(self, window, event):
        # Проверяем Gdk.KEY_Escape (константа 65307)
        if event.keyval == Gdk.KEY_Escape:  
            self.destroy()
            return True
        return False


if __name__ == "__main__":
    MainMenu()
    Gtk.main()
