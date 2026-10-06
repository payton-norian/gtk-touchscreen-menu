#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, Gdk

# Получаем настройки по умолчанию для приложения
settings = Gtk.Settings.get_default()
# Говорим, что предпочитаем темную тему
settings.set_property("gtk-application-prefer-dark-theme", True)


class MainMenu(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        # 1. Включаем поддержку прозрачности (RGBA альфа-канал)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None and screen.is_composited():
            self.set_visual(visual)

        # Базовые настройки окна (оставляем строго по центру)
        self.set_decorated(False)
        self.set_resizable(True)
        self.set_keep_above(True)
        self.set_modal(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Чтобы меню не отображалось в списке запущенных окон на панели
        self.set_skip_taskbar_hint(True)

        # Подключаем события фокуса и закрытия
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)
        self.connect("map", self.on_map)

        # 2. Стилизация фона через CSS
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
            window {
                background-color: rgba(0, 0, 0, 0.5);
            }
            scrolledwindow, viewport {
                background-color: transparent;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Основной контейнер
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.set_border_width(12)
        outer.set_spacing(8)
        self.add(outer)

        title = Gtk.Label()
        title.set_markup("<span foreground='white'><b>Приложения</b></span>")
        title.set_halign(Gtk.Align.START)
        outer.pack_start(title, False, False, 0)

        # Прокрутка
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(1200, 680)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        outer.pack_start(scrolled, True, True, 0)

        # Сетка кнопок
        flowbox = Gtk.FlowBox()
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_column_spacing(12)
        flowbox.set_row_spacing(12)
        flowbox.set_max_children_per_line(8)
        flowbox.set_min_children_per_line(3)
        scrolled.add(flowbox)

        raw_applications = Gio.AppInfo.get_all()
        applications = []

        for app in raw_applications:
            if not app.should_show():
                continue

            app_categories = app.get_categories() or ""
            cats = [c.strip() for c in app_categories.split(";") if c.strip()]

            if "Screensaver" in cats or "X-GNOME-Screensaver" in cats:
                continue

            if hasattr(app, "get_id") and app.get_id() and "app-install" in app.get_id():
                continue
            if hasattr(app, "get_filename") and app.get_filename() and "app-install" in app.get_filename():
                continue

            applications.append(app)

        applications.sort(key=lambda app: app.get_display_name().lower())

        for app in applications:
            button = self.create_button(app)
            flowbox.add(button)

        self.show_all()
        self.present()

    def on_map(self, window):
        window_gdk = self.get_window()
        display = Gdk.Display.get_default()
        if display:
            seat = display.get_default_seat()
            if seat:
                # Современный и безопасный захват клавиатуры и мыши
                seat.grab(
                    window_gdk, 
                    Gdk.SeatCapabilities.ALL, 
                    True, 
                    None, 
                    None, 
                    None
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
        if event.keyval == Gdk.KEY_Escape:  
            self.destroy()
            return True
        return False


if __name__ == "__main__":
    MainMenu()
    Gtk.main()
