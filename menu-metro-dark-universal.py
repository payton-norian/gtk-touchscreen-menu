#!/usr/bin/env python3
import os
import glob
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, Gdk

settings = Gtk.Settings.get_default()
settings.set_property("gtk-theme-name", "Adwaita-dark")
settings.set_property("gtk-application-prefer-dark-theme", True)


class MainMenu(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        # 1. Включаем поддержку прозрачности (RGBA альфа-канал)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None and screen.is_composited():
            self.set_visual(visual)

        # Базовые настройки окна
        self.set_decorated(False)
        self.set_resizable(True)
        self.set_keep_above(True)
        self.set_modal(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_skip_taskbar_hint(True)

        # Подключаем события фокуса и закрытия
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)
        self.connect("map", self.on_map)

        # 2. Стилизация фона и скрытие скроллбаров через CSS
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
            window {
                background-color: rgba(0, 0, 0, 0.5);
            }
            scrolledwindow, viewport {
                background-color: transparent;
            }
            scrollbar {
                opacity: 0;
                min-width: 0;
                min-height: 0;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Основной контейнер
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.set_border_width(12)
        outer.set_spacing(10)
        self.add(outer)

        # Контейнер стека для переключения вкладок
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        stack.set_transition_duration(150)

        # Переключатель вкладок в верхней части окна
        switcher = Gtk.StackSwitcher()
        switcher.set_stack(stack)
        switcher.set_halign(Gtk.Align.START)
        outer.pack_start(switcher, False, False, 0)

        # Добавляем две страницы в стек: "Избранное" (откроется первой) и "Все приложения"
        fav_page = self.build_grid_page(self.get_xfce_favorites())
        stack.add_titled(fav_page, "favorites", "Избранное")

        all_page = self.build_grid_page(self.get_all_applications())
        stack.add_titled(all_page, "all", "Все приложения")

        outer.pack_start(stack, True, True, 0)

        self.show_all()
        self.present()

    def build_grid_page(self, applications):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(1600, 920)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        flowbox = Gtk.FlowBox()
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_column_spacing(12)
        flowbox.set_row_spacing(12)
        flowbox.set_max_children_per_line(8)
        flowbox.set_min_children_per_line(3)
        flowbox.set_valign(Gtk.Align.START)
        scrolled.add(flowbox)

        for app in applications:
            button = self.create_button(app)
            flowbox.add(button)

        return scrolled

    def _load_desktop_app(self, desktop_id):
        try:
            return Gio.DesktopAppInfo.new(desktop_id)
        except TypeError:
            return None

    def get_xfce_favorites(self):
        panel_dir = os.path.expanduser("~/.config/xfce4/panel")
        rc_files = sorted(glob.glob(os.path.join(panel_dir, "whiskermenu-*.rc")))

        favorites_line = ""
        for rc_path in rc_files:
            try:
                with open(rc_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("favorites="):
                            favorites_line = line.removeprefix("favorites=").strip()
                            break
            except OSError:
                continue

            if favorites_line:
                break

        if not favorites_line:
            desktop_ids = [
                "exo-web-browser.desktop",
                "exo-mail-reader.desktop",
                "exo-file-manager.desktop",
                "exo-terminal-emulator.desktop",
            ]
        else:
            desktop_ids = [item.strip() for item in favorites_line.split(",") if item.strip()]

        applications = []
        for d_id in desktop_ids:
            app_info = self._load_desktop_app(d_id)
            if app_info and app_info.should_show():
                applications.append(app_info)

        return applications

    def get_all_applications(self):
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
        return applications

    def on_map(self, window):
        window_gdk = self.get_window()
        display = Gdk.Display.get_default()
        if display:
            seat = display.get_default_seat()
            if seat:
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
        button.set_size_request(200, 100)
        button.set_tooltip_text(app.get_description() or "")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
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

