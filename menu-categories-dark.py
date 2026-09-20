#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, Gdk


class MainMenu(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        # Настройки окна-popup
        self.set_decorated(False)
        self.set_resizable(True)
        self.set_keep_above(True)
        self.set_modal(True)
        self.set_position(Gtk.WindowPosition.CENTER)

        # События
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)
        self.connect("map", self.on_map)

        # Главный вертикальный контейнер
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.set_border_width(12)
        outer.set_spacing(8)
        self.add(outer)

        # Заголовок
        title = Gtk.Label()
        title.set_markup("<b>Приложения</b>")
        title.set_halign(Gtk.Align.START)
        outer.pack_start(title, False, False, 0)

        # Рабочая область: Горизонтальный Box (Категории слева, Приложения справа)
        workspace = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        outer.pack_start(workspace, True, True, 0)

        # --- ЛЕВАЯ ПАНЕЛЬ: Категории ---
        # Оборачиваем в ScrolledWindow, чтобы на тачскрине можно было скроллить и категории
        category_scroll = Gtk.ScrolledWindow()
        category_scroll.set_size_request(180, 620)
        category_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        workspace.pack_start(category_scroll, False, False, 0)

        self.category_list = Gtk.ListBox()
        self.category_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.category_list.connect("row-selected", self.on_category_selected)
        category_scroll.add(self.category_list)

        # --- ПРАВАЯ ПАНЕЛЬ: Сетка приложений ---
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(640, 620) # Уменьшили ширину, освободив место под категории
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        workspace.pack_start(scrolled, True, True, 0)

        # Сетка кнопок
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_column_spacing(8)
        self.flowbox.set_row_spacing(8)
        self.flowbox.set_max_children_per_line(4) # Уменьшили до 4, так как ширина стала меньше
        self.flowbox.set_min_children_per_line(2)
        
        # Подключаем функцию фильтрации к FlowBox
        self.flowbox.set_filter_func(self.filter_applications)
        scrolled.add(self.flowbox)

        # Текущая выбранная категория (None или "All" — показать всё)
        self.current_category = "All"

        # Загрузка данных
        self.load_applications_and_categories()

        self.show_all()
        self.present()

    def load_applications_and_categories(self):
        """Загружает приложения и динамически формирует список доступных категорий."""
        applications = [app for app in Gio.AppInfo.get_all() if app.should_show()]
        applications.sort(key=lambda app: app.get_display_name().lower())

        # Множество для сбора всех уникальных категорий
        unique_categories = set()

        for app in applications:
            button = self.create_button(app)
            self.flowbox.add(button)

            # Получаем категории приложения из desktop-файла
            app_categories = app.get_categories()
            if app_categories:
                # Категории в Gio разделены точкой с запятой (например, "Network;WebBrowser;")
                cats = [c.strip() for c in app_categories.split(";") if c.strip()]
                unique_categories.update(cats)

        # Добавляем дефолтную строку "Все"
        self.add_category_row("Все", "All")

        # Переводим системные категории на человеческий язык (основные)
        category_mapping = {
            "AudioVideo": "Мультимедиа",
            "Development": "Разработка",
            "Education": "Образование",
            "Game": "Игры",
            "Graphics": "Графика",
            "Network": "Интернет",
            "Office": "Офис",
            "Settings": "Настройки",
            "System": "Система",
            "Utility": "Утилиты"
        }

        # Сортируем категории и добавляем в боковую панель
        sorted_categories = sorted(list(unique_categories))
        for cat in sorted_categories:
            # Показываем красивое имя, если оно есть в словаре, иначе — техническое
            display_name = category_mapping.get(cat, cat)
            self.add_category_row(display_name, cat)

        # Выбираем первую строчку ("Все") по умолчанию
        first_row = self.category_list.get_row_at_index(0)
        if first_row:
            self.category_list.select_row(first_row)

    def add_category_row(self, display_name, internal_name):
        """Вспомогательный метод для создания строки в списке категорий."""
        row = Gtk.ListBoxRow()
        row.internal_name = internal_name  # Сохраняем имя категории внутри объекта строки
        
        label = Gtk.Label(label=display_name)
        label.set_halign(Gtk.Align.START)
        label.set_margin_start(16)
        label.set_margin_end(16)
        label.set_margin_top(16)
        label.set_margin_bottom(16)
        
        row.add(label)
        self.category_list.add(row)

    def filter_applications(self, child):
        """Функция-фильтр, которая решает, отображать ли кнопку приложения."""
        if self.current_category == "All":
            return True

        # Извлекаем кнопку и привязанное к ней приложение
        button = child.get_child()
        # Извлекаем объект Gio.AppInfo, который мы привязали к кнопке в create_button
        app = button.app_info 
        
        app_categories = app.get_categories()
        if app_categories:
            cats = [c.strip() for c in app_categories.split(";") if c.strip()]
            return self.current_category in cats
            
        return False

    def on_category_selected(self, listbox, row):
        """Вызывается при смене категории пользователем."""
        if row is not None:
            self.current_category = row.internal_name
            # Заставляем FlowBox применить фильтр заново
            self.flowbox.invalidate_filter()

    def create_button(self, app):
        button = Gtk.Button()
        button.app_info = app  # Сохраняем ссылку на app_info прямо в кнопке для фильтрации
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

    def on_map(self, window):
        window_gdk = self.get_window()
        device_manager = Gdk.Display.get_default().get_device_manager()
        pointer = device_manager.get_client_pointer()
        
        Gdk.device_grab(
            pointer, window_gdk, 
            Gdk.GrabOwnership.APPLICATION, True, 
            Gdk.EventMask.BUTTON_PRESS_MASK, None, 
            Gdk.CURRENT_TIME
        )
        keyboard = pointer.get_associated_device()
        if keyboard:
            Gdk.device_grab(
                keyboard, window_gdk, 
                Gdk.GrabOwnership.APPLICATION, True, 
                Gdk.EventMask.KEY_PRESS_MASK, None, 
                Gdk.CURRENT_TIME
            )

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
    # Принудительно включаем тёмную тему для всего приложения
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-application-prefer-dark-theme", True)

    # Запускаем наше меню
    MainMenu()
    Gtk.main()


