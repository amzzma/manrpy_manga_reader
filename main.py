import os
import zipfile
import time
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image, AsyncImage
from kivy.uix.scatter import Scatter
from kivymd.app import MDApp
from kivymd.uix.behaviors import TouchBehavior
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.carousel import MDCarousel
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from book import Book_shelf, Book_detail
from kivy.utils import platform
import sys
import re
from pdf_extract import pdf_pic_write2dir
from pdf_func import PDFDocumentWidget

from kivy.core.text import LabelBase
LabelBase.register('Roboto', './fonts/static/NotoSansSC-Regular.ttf')

import logging
logging.basicConfig(level=logging.INFO)


if platform == "android":
    from jnius import cast
    from jnius import autoclass
    from android import mActivity, api_version


def delete_director(path):
    if platform == "android":
        path = "app/" + path
        
        def delete_recursively(file):
            if file.isDirectory():
                for child in file.listFiles():
                    delete_recursively(child)
            file.delete()

        Context = autoclass('android.content.Context')
        File = autoclass('java.io.File')

        context = cast('android.content.Context', autoclass('org.kivy.android.PythonActivity').mActivity)
        app_files_dir = context.getFilesDir()

        temp_directory_path = File(app_files_dir, path)
        logging.info(f"temp_directory_path:{temp_directory_path.getAbsolutePath()}")
        
        try:
            delete_recursively(temp_directory_path)
            print(f"Directory '{temp_directory_path.getAbsolutePath()}' successfully deleted.")
        except Exception as e:
            logging.error(f"{e}")
    else:
        import shutil
        shutil.rmtree(path)
    
    
os.environ["SDL_AUDIODRIVER"] = "android"

Builder.load_file('KV_UI/detail_screen.kv')
Builder.load_file('KV_UI/add_book_screen.kv')
Builder.load_file("KV_UI/delete_book_screen.kv")
Builder.load_file("KV_UI/book_shelf.kv")
Builder.load_file('KV_UI/mg.kv')
Builder.load_file('KV_UI/edit_book.kv')
Builder.load_file('KV_UI/edit_detail_screen.kv')
Builder.load_file('KV_UI/log.kv')


class book_detail_screen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "screen0"


class add_book_screen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "screen1"


class manga_screen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "screen2"


class book_shelf_screen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "screen3"


class delete_book_screen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "screen4"


class edit_book_screen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "screen5"


class edit_detail_screen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "screen6"


class pdf_screen(MDScreen, TouchBehavior):
    def __init__(self, source, sm, cols=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "screen7"
        self.size = (Window.width, Window.height)
        self.pdoc = PDFDocumentWidget(source=source, cols=cols)
        self.add_widget(self.pdoc)
        self.sm = sm

    def on_double_tap(self, touch, *args):
        print(f"touch:{touch}")
        self.sm.current = "screen0"
        del self


class log_screen(MDScreen, TouchBehavior):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "screen8"
        self.load_dev_log()

    def load_dev_log(self):
        f = open("develop_log.txt", mode="r", encoding="utf-8")
        devlog_content = f.readlines()
        devlog_lines = devlog_content
        # print(devlog_lines)
        devlog_grid = self.ids.devlog_grid

        for line in devlog_lines:
            label = MDLabel(text=line, markup=True, size_hint_y=None, height=dp(15))
            devlog_grid.add_widget(label)


class MangaPage(MDCarousel):
    def __init__(self, image, window_size, **kwargs):
        super().__init__(**kwargs)
        self.size = window_size
        # print(f'Screen Size: {Window.width}x{Window.height}\nself.size: {window_size}')

        self.add_widget(MangaImage(source=image, window_size=window_size))
        # print(self.size)


class MangaImage(MDCarousel):
    def __init__(self, source, window_size, **kwargs):
        super().__init__(**kwargs)
        # print(source)
        # print(window_size)
        # print(f'Screen Size: {Window.width}x{Window.height}')
        card0 = MDCard(
            size_hint_y=None,
            size_hint=(None, None),
            size=window_size  # ("400dp", "711dp")
            # on_double_tap=lambda: self.toggle_scale(sca)
        )
        sca = Scatter(do_rotation=False, do_translation_y=True, scale_min=0.5, scale_max=2.0)
        img = AsyncImage(
            size=window_size, 
            source=f"{source}",
            size_hint=(None, None),
            fit_mode="contain"
        )

        sca.add_widget(img)
        card0.add_widget(sca)
        self.add_widget(card0)

    def toggle_scale(self, scatter):
        # print("tete")
        if scatter.scale == 1.0:
            scatter.scale = 2.0
        else:
            scatter.scale = 1.0


class CustomCard(MDCard):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


def get_pixel():
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    DisplayMetrics = autoclass('android.util.DisplayMetrics')

    display_metrics = DisplayMetrics()
    PythonActivity.mActivity.getWindowManager().getDefaultDisplay().getMetrics(display_metrics)
    screen_width = display_metrics.widthPixels
    screen_height = display_metrics.heightPixels

    return (screen_width, screen_height)


class App(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        left_menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": f"add_book",
                "height": dp(56),
                "on_release": self.menu_callback_add_book,
            },
            {
                "viewclass": "OneLineListItem",
                "text": f"delete_book",
                "height": dp(56),
                "on_release": self.menu_callback_delete_book,
            },
            {
                "viewclass": "OneLineListItem",
                "text": f"edit_book",
                "height": dp(56),
                "on_release": self.menu_callback_edit_book,
            },
            {
                "viewclass": "OneLineListItem",
                "text": f"developing log",
                "height": dp(56),
                "on_release": self.menu_callback_more_l,
            }
        ]
        right_menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": f"setting",
                "height": dp(56),
                "on_release": self.menu_callback_setting,
            }
        ]

        self.menu_l = MDDropdownMenu(
            items=left_menu_items,
            width_mult=4,
        )

        self.menu_r = MDDropdownMenu(
            items=right_menu_items,
            width_mult=4,
        )

    def build(self):
        self.device = 0
        # screen_width = Window.width
        # screen_height = Window.height
        self.window_size = (Window.size[1], Window.size[0])
        self.Toast(f"{self.window_size}")
        if self.device == 0:
            self.window_size = (self.window_size[1], self.window_size[0])
        if self.device == 1:
            self.window_size = (self.window_size[0], self.window_size[1])

        Window.size = self.window_size
        self.book_shelf = Book_shelf()
        self.sm = MDScreenManager()

        self.book_shelf_screen = book_shelf_screen()
        self.sm.add_widget(self.book_shelf_screen)
        self.build_main_screen()

        self.add_book = add_book_screen()
        self.add_book.ids.add_book_butt.on_release = self.a_screen_back_main
        self.sm.add_widget(self.add_book)

        self.delete_book = delete_book_screen()
        self.delete_book.ids.del_book_butt.on_release = self.d_screen_back_main
        self.sm.add_widget(self.delete_book)

        self.mgs = manga_screen()
        self.mgs.ids.manga_butt.on_release = self.manga_screen_back_detail
        self.mgs.ids.carousel.size = self.window_size
        self.sm.add_widget(self.mgs)

        self.edit_book_screen = edit_book_screen()
        self.edit_book_screen.ids.edit_butt.on_release = self.edit_back_main
        self.sm.add_widget(self.edit_book_screen)

        return self.sm

    def on_start(self):
        self.Toast(f"platform:{platform}")
        pass

    def Toast(self, text):
        if platform == "android":
            from kivymd.toast.androidtoast import toast
            return toast(f"{text}", length_long=2)

        else:
            from kivymd.toast import toast
            return toast(f"{text}", duration=2)

    def build_main_screen(self):
        self.book_shelf_screen.ids.grid0.spacing = self.window_size[0] * 0.04
        self.book_shelf_screen.ids.grid0.padding = self.window_size[0] * 0.045
        for i in self.book_shelf.books_data:
            card2 = MDCard(
                id=f"{i}",
                size_hint_y=None,
                size_hint=(None, None),
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275),
                on_release=self.on_cover_touch_card
            )
            grid0 = self.book_shelf_screen.ids.grid0

            box_layout = BoxLayout(
                orientation='vertical',
                padding=0,
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275),
            )
            # book = Book("02.jpg", f"{i['name']}")

            img = Image(
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.8),
                source=f"{self.book_shelf.books_data[i]['cover_path']}", 
                size_hint=(None, None),
                fit_mode="fill",
            )
            if self.device == 1:
                img.size = (self.window_size[0] * 0.275 * 0.8, self.window_size[1] * 0.275)

            md_label = MDLabel(
                text=f"{self.book_shelf.books_data[i]['name']}",
                halign="center",
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.2)
            )
            if self.device == 1:
                md_label.size = (self.window_size[0] * 0.275 * 0.2, self.window_size[1] * 0.275)

            box_layout.add_widget(img)
            box_layout.add_widget(md_label)
            card2.add_widget(box_layout)
            grid0.add_widget(card2)

    def build_book_detail_screen(self):
        # print(f'Screen Size: {Window.width}x{Window.height}\nself.size: {self.window_size}')

        self.book_detail_screen.ids.grid0.spacing = self.window_size[0] * 0.04
        self.book_detail_screen.ids.grid0.padding = self.window_size[0] * 0.045
        for i in self.book_detail.book_data:
            card0 = MDCard(
                id=f"{i}",
                size_hint_y=None,
                size_hint=(None, None),
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275),  # size=("120dp", "213dp"),
                on_release=self.on_chapter_touch_card
            )
            grid0 = self.book_detail_screen.ids.grid0

            box_layout = BoxLayout(
                orientation='vertical',
                padding=0,
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275),  # size=("120dp", "213dp")
            )
            img = Image(
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.8),
                # size=(self.window_size[0] * 0.275 * 0.8, self.window_size[1] * 0.275),
                source=f"{self.book_detail.book_data[i]['cover_path']}",
                size_hint=(None, None),
                fit_mode="fill"
            )
            if self.device == 1:
                img.size = (self.window_size[0] * 0.275 * 0.8, self.window_size[1] * 0.275)

            md_label = MDLabel(
                text=f"{self.book_detail.book_data[i]['name']}",
                halign="center",
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.2)
            )
            if self.device == 1:
                md_label.size = (self.window_size[0] * 0.275 * 0.2, self.window_size[1] * 0.275)

            box_layout.add_widget(img)
            box_layout.add_widget(md_label)
            card0.add_widget(box_layout)
            grid0.add_widget(card0)

    def build_add_screen(self):
        self.add_book.ids.grid1.spacing = self.window_size[0] * 0.04
        self.add_book.ids.grid1.padding = self.window_size[0] * 0.045

        def creat_acard(card_id, icon):
            card1 = MDCard(
                id=f"{card_id}",
                size_hint_y=None,
                size_hint=(None, None),
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275), 
                on_release=self.on_touch_add_card
            )
            grid1 = self.add_book.ids.grid1

            box_layout = BoxLayout(
                orientation='vertical',
                padding=0,
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275),
            )
            aicon = MDIconButton(icon=icon)
            md_label = MDLabel(
                text=f"{icon}",
                halign="center",
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.2)
                # size=(self.window_size[0] * 0.275 * 0.2, self.window_size[1] * 0.275),
            )
            if self.device == 1:
                md_label.size = (self.window_size[0] * 0.275 * 0.2, self.window_size[1] * 0.275)

            box_layout.add_widget(aicon)
            box_layout.add_widget(md_label)
            card1.add_widget(box_layout)
            grid1.add_widget(card1)

        for i, ico in enumerate(["folder", "folder-zip", "file-pdf-box"]):
            creat_acard(f"a_card{i}", ico)

    def build_delete_screen(self):
        self.delete_book.ids.grid0.spacing = self.window_size[0] * 0.04
        self.delete_book.ids.grid0.padding = self.window_size[0] * 0.045
        for i in self.book_shelf.books_data:
            card2 = MDCard(
                id=f"{i}",
                size_hint_y=None,
                size_hint=(None, None),
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275), 
                on_release=self.on_pic_touch_card_delete
            )
            grid0 = self.delete_book.ids.grid0

            box_layout = BoxLayout(
                orientation='vertical',
                padding=0,
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275), 
            )
            # book = Book("02.jpg", f"{i['name']}")

            img = Image(
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.8),
                source=f"{self.book_shelf.books_data[i]['cover_path']}",
                size_hint=(None, None),
                fit_mode="fill"
            )
            if self.device == 1:
                img.size = (self.window_size[0] * 0.275 * 0.8, self.window_size[1] * 0.275)

            md_label = MDLabel(
                text=f"{self.book_shelf.books_data[i]['name']}",
                halign="center",
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.2)
            )
            if self.device == 1:
                md_label.size = (self.window_size[0] * 0.275 * 0.2, self.window_size[1] * 0.275)

            box_layout.add_widget(img)
            box_layout.add_widget(md_label)
            card2.add_widget(box_layout)
            grid0.add_widget(card2)

    def build_edit_screen(self):
        self.edit_book_screen.ids.grid0.spacing = self.window_size[0] * 0.04
        self.edit_book_screen.ids.grid0.padding = self.window_size[0] * 0.045
        for i in self.book_shelf.books_data:
            card2 = MDCard(
                id=f"{i}",
                size_hint_y=None,
                size_hint=(None, None),
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275),
                on_release=self.on_pic_touch_card_edit
            )

            grid0 = self.edit_book_screen.ids.grid0

            box_layout = BoxLayout(
                orientation='vertical',
                padding=0,
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275),
            )
            img = Image(
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.8),
                # size=(self.window_size[0] * 0.275 * 0.8, self.window_size[1] * 0.275), 
                source=f"{self.book_shelf.books_data[i]['cover_path']}",
                size_hint=(None, None),
                fit_mode="fill",
            )
            if self.device == 1:
                img.size = (self.window_size[0] * 0.275 * 0.8, self.window_size[1] * 0.275)

            md_label = MDLabel(
                text=f"{self.book_shelf.books_data[i]['name']}",
                halign="center",
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.2)
            )
            if self.device == 1:
                md_label.size = (self.window_size[0] * 0.275 * 0.2, self.window_size[1] * 0.275)

            box_layout.add_widget(img)
            box_layout.add_widget(md_label)
            card2.add_widget(box_layout)
            grid0.add_widget(card2)
            
    def build_edit_chapter_screen(self, book_id):
        def edit_detail_back_main():
            self.sm.current = "screen5"
            self.sm.remove_widget(book_edit_detail_screen)

        book_edit_detail_screen = book_detail_screen()
        book_edit_detail_screen.ids.grid0.spacing = self.window_size[0] * 0.04
        book_edit_detail_screen.ids.grid0.padding = self.window_size[0] * 0.045
        book_edit_detail_screen.name = "screen10"
        book_edit_detail_screen.ids.detail_butt.on_release = edit_detail_back_main

        book_detail = Book_detail(f"data_json/{book_id}.json")
        for i in book_detail.book_data:
            card0 = MDCard(
                id=f"{i}",
                size_hint_y=None,
                size_hint=(None, None),
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275),  # size=("120dp", "213dp"),
                on_release=lambda x: self.open_file_manager(x.id, mode=2, book_id=book_id)
            )
            grid0 = book_edit_detail_screen.ids.grid0

            box_layout = BoxLayout(
                orientation='vertical',
                padding=0,
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275),  # size=("120dp", "213dp")
            )
            # book = Book("02.jpg", f"{i['name']}")

            img = Image(
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.8),
                source=f"{book_detail.book_data[i]['cover_path']}",
                size_hint=(None, None),
                fit_mode="fill", 
            )
            if self.device == 1:
                img.size = (self.window_size[0] * 0.275 * 0.8, self.window_size[1] * 0.275)

            md_label = MDLabel(
                text=f"{book_detail.book_data[i]['name']}",
                halign="center",
                size=(self.window_size[0] * 0.275, self.window_size[1] * 0.275 * 0.2)
            )
            if self.device == 1:
                md_label.size = (self.window_size[0] * 0.275 * 0.2, self.window_size[1] * 0.275)

            box_layout.add_widget(img)
            box_layout.add_widget(md_label)
            card0.add_widget(box_layout)
            grid0.add_widget(card0)
        self.sm.add_widget(book_edit_detail_screen)

    def build_edit_detail_screen(self, card_id):
        def edit_cover(mode=1):
            try:
                self.open_file_manager(card_id, mode=mode)
            except Exception as e:
                self.Toast(f"ERROR:{e}")
                logging.error(f"ERROR:{e}")
                
        def edit_chapter():
            try:
                # print(card_id)
                self.build_edit_chapter_screen(card_id)
                self.sm.current = "screen10"
            except Exception as e:
                self.Toast(f"ERROR:{e}")
                
        self.edit_detail = edit_detail_screen()
        self.edit_detail.ids.edit_detail_butt.on_release = self.edit_detail_back_main
        self.edit_detail.ids.cover_pic.on_release = edit_cover
        self.edit_detail.ids.chapter_pic.on_release = edit_chapter
        self.sm.add_widget(self.edit_detail)
        self.sm.current = "screen6"

    def on_cover_touch_card(self, card):
        book_id = card.id.split("book")[-1]

        self.book_detail = Book_detail(f"./data_json/book{book_id}.json")
        self.book_detail_screen = book_detail_screen()
        self.book_detail_screen.ids.detail_butt.on_release = self.detail_back_main
        self.sm.add_widget(self.book_detail_screen)

        self.build_book_detail_screen()
        self.sm.current = "screen0"

    def on_pic_touch_card_edit(self, card):
        self.build_edit_detail_screen(card.id)

    def on_pic_touch_card_delete(self, card):
        try:
            self.book_shelf.delete_book(f"{card.id}")
        except Exception as e:
            self.Toast(f"{e}")
            logging.error(f"{e}")

        self.Toast("delete")
        self.update_main_screen()
        self.sm.current = "screen3"
        self.update_delete()

    def on_touch_add_card(self, card):
        if card.id == "a_card0":
            self.add_book_type = "folder"
        elif card.id == "a_card1":
            self.add_book_type = "zip"
        elif card.id == "a_card2":
            self.add_book_type = "pdf"

        try:
            self.open_file_manager()
        except Exception as e:
            self.Toast(f"ERROR:{e}")
            logging.error(f"{e}")
            
        self.Toast(self.add_book_type)

    def on_chapter_touch_card(self, card):
        self.create_mange(card.id)

    def callback_l(self, button):
        self.menu_l.caller = button
        self.menu_l.open()

    def callback_r(self, button):
        self.menu_r.caller = button
        self.menu_r.open()

    def menu_callback_add_book(self, *args):
        self.menu_l.dismiss()
        self.sm.current = "screen1"
        self.build_add_screen()

    def menu_callback_delete_book(self, *args):
        self.menu_l.dismiss()
        self.sm.current = "screen4"
        self.build_delete_screen()

    def menu_callback_more_l(self, *args):
        self.menu_l.dismiss()
        self.log = log_screen()
        self.log.ids.log_butt.on_release = self.more_back_main
        self.sm.add_widget(self.log)
        self.sm.current = "screen8"

    def more_back_main(self):
        self.sm.remove_widget(self.log)
        self.sm.current = "screen3"

    def menu_callback_edit_book(self, *args):
        self.menu_l.dismiss()
        self.build_edit_screen()
        self.sm.current = "screen5"

    def menu_callback_setting(self, *args):
        self.menu_r.dismiss()
        self.Toast("setting")

    def create_mange(self, book_id):
    
        def touch_load_slides(touch):
            print(touch.spos[0])
            if touch.spos[0] > 0.6:
                self.carousel.load_previous()
                return True
            elif touch.spos[0] < 0.4:
                self.carousel.load_next()
                return True
            return False

        ## in dev
        def on_keyboard(instance, keyboard, keycode, text, modifiers):
            logging.info(f"on_keyboard: {keyboard}, {keycode}, {text}")
            if keycode == 128 and self.sm.current == "screen2":
                self.carousel.load_previous()
                return True
            elif keycode == 129 and self.sm.current == "screen2":
                self.carousel.load_next()
                return True
            return False

        self.book = self.book_detail.book_data[book_id]
        self.carousel = self.mgs.ids.carousel
        
        if self.book["book_type"] == "pdf":
            if hasattr(self, "ps"):
                self.sm.remove_widget(self.ps)
                print("yes")
            pdf_path = f"{book['book_path']}"
            self.ps = pdf_screen(pdf_path, self.sm)
            self.ps.name = "screen7"
            self.sm.add_widget(self.ps)
            self.sm.current = "screen7"
            return

        self.sm.current = "screen2"
        self.load_page = [0, 0, 0, 0]
        
        for page_number in range((self.book['book_len'] + 1) // 8):
            if page_number % 10 == 0:
                time.sleep(0.1)
            image_path = f"{self.book['book_path']}/{page_number:04d}.{self.book['book_type']}"
            win_size = (Window.width, Window.height)
            self.carousel.add_widget(MangaPage(image=image_path, window_size=win_size))

        Window.bind(on_keyboard=on_keyboard)


    def detail_back_main(self):
        self.sm.remove_widget(self.book_detail_screen)
        self.sm.current = "screen3"

    def a_screen_back_main(self):
        self.sm.remove_widget(self.add_book)
        self.add_book = add_book_screen()
        self.add_book.ids.add_book_butt.on_release = self.a_screen_back_main
        self.sm.add_widget(self.add_book)
        self.sm.current = "screen3"

    def d_screen_back_main(self):
        self.update_main_screen()
        self.sm.current = "screen3"
        self.update_delete()

    def edit_back_main(self):
        self.update_main_screen()
        self.sm.current = "screen3"
        self.update_edit_screen()

    def edit_detail_back_main(self):
        self.update_main_screen()
        self.sm.current = "screen3"
        self.update_edit_screen()
        self.sm.remove_widget(self.edit_detail)

    def manga_screen_back_detail(self):
        self.sm.remove_widget(self.mgs)
        self.mgs = manga_screen()
        self.mgs.ids.manga_butt.on_release = self.manga_screen_back_detail
        self.sm.add_widget(self.mgs)
        for i, j in enumerate(self.load_page):
            self.load_page[i] = 0
        self.sm.current = "screen0"

    def add_book_by_folder(self, folder):
        self.book_shelf.load_a_book(folder)
        self.Toast("add a book")
        self.update_main_screen()

    def add_book_by_zip(self, path):
        def support_gbk(zip_file: zipfile.ZipFile):
            name_to_info = zip_file.NameToInfo
            # copy map first
            for name, info in name_to_info.copy().items():
                real_name = name.encode('cp437').decode('gbk')
                if real_name != name:
                    info.filename = real_name
                    del name_to_info[name]
                    name_to_info[real_name] = info
            return zip_file
            
        zip_name = path.split("\\")[-1].split("/")[-1].split(".")[0]
        if not os.path.exists("temp"):
            os.mkdir("temp")
            
        with support_gbk(zipfile.ZipFile(rf'{path}', "r")) as zfp:
            path = f"temp/{zip_name}"
            zfp.extractall(path)
                
        self.add_book_by_folder(f"temp/{zip_name}")

    def add_book_by_pdf(self, path):
        def extract_numbers(s):
            numbers = re.findall(r'\d+', s)
            return tuple(map(int, numbers)) if numbers else ()
    
        logging.info(f'add pdf folder:{path}')
        name = path.split('/')[-1].split('\\')[-1]

        if path.split("/")[-1].split("\\")[-1].split(".")[-1] in ["zip"]:
            if not os.path.exists("temp"):
                os.mkdir("temp")

            def support_gbk(zip_file: zipfile.ZipFile):
                name_to_info = zip_file.NameToInfo
                # copy map first
                for name, info in name_to_info.copy().items():
                    real_name = name.encode('cp437').decode('gbk')
                    if real_name != name:
                        info.filename = real_name
                        del name_to_info[name]
                        name_to_info[real_name] = info
                return zip_file

            with support_gbk(zipfile.ZipFile(rf'{path}', "r")) as zfp:
                extracted_files = name
                path = "temp/" + extracted_files.split("/")[0].split("\\")[0] + "(zip)"
                zfp.extractall(path)

        p = f"temp/{name}"
        if not os.path.exists(p):
            os.mkdir(p)
        else:
            while 1:
                p += "(1)"
                try:
                    os.mkdir(p)
                    break
                except:
                    pass

        for i, pdf in enumerate(sorted(os.listdir(path), key=extract_numbers)):
            folder = f"{path}/{pdf}"
            pdf_pic_write2dir(f"{folder}", f"{p}/{i}")
        logging.info(f"pdf_pic_write2dir: pdf2pic in temp success")

        self.book_shelf.load_a_book(f"{p}", mode=0)
        self.update_main_screen()
        self.Toast("add a book")

    def update_main_screen(self):  # just reload
        self.sm.remove_widget(self.book_shelf_screen)
        self.book_shelf_screen = book_shelf_screen()
        self.sm.add_widget(self.book_shelf_screen)
        self.build_main_screen()

    def add_page(self, start, end, i):
        if not self.load_page[i]:
            self.load_page[i] = 1
            for page_number in range(start, end):
                if page_number % 10 == 0:
                    time.sleep(0.1)
                image_path = f"{self.book['book_path']}/{page_number:04d}.{self.book['book_type']}"
                win_size = (Window.width, Window.height)
                self.carousel.add_widget(MangaPage(image=image_path, window_size=win_size))
            
    def update_page_indicator(self, current_page):
        page_indicator = self.mgs.ids.page_indicator
        page_indicator.text = f'Page {int(current_page) + 1}'

        if self.carousel.index == (self.book['book_len'] + 1) // 8 - 1:
            self.add_page((self.book['book_len'] + 1) // 8, (self.book['book_len'] + 1) // 4, 0)
        if self.carousel.index == (self.book['book_len'] + 1) // 4 - 1:
            self.add_page((self.book['book_len'] + 1) // 4, 2 * (self.book['book_len'] + 1) // 4, 1)
        if self.carousel.index == 2 * (self.book['book_len'] + 1) // 4 - 1:
            self.add_page(2 * (self.book['book_len'] + 1) // 4, 3 * (self.book['book_len'] + 1) // 4, 2)
        if self.carousel.index == 3 * (self.book['book_len'] + 1) // 4 - 1:
            self.add_page(3 * (self.book['book_len'] + 1) // 4, self.book['book_len'] + 1, 3)

    def update_add_screen(self):
        self.sm.remove_widget(self.add_book)
        self.add_book = add_book_screen()
        self.add_book.ids.add_book_butt.on_release = self.a_screen_back_main
        self.sm.add_widget(self.add_book)

    def update_delete(self):
        self.sm.remove_widget(self.delete_book)
        self.delete_book = delete_book_screen()
        self.delete_book.ids.del_book_butt.on_release = self.d_screen_back_main
        self.sm.add_widget(self.delete_book)

    def update_edit_screen(self):
        self.sm.remove_widget(self.edit_book_screen)
        self.edit_book_screen = edit_book_screen()
        self.edit_book_screen.ids.edit_butt.on_release = self.edit_back_main
        self.sm.add_widget(self.edit_book_screen)

    def open_file_manager(self, card_id=0, mode=0, book_id=None):
        if mode == 1:
            self.edit_cover_card_id = card_id
            self.file_manager = MDFileManager(
                exit_manager=self.exit_manager,
                select_path=self.cover_select_path,
                # ext=[".jpg", ".jpeg", "png"]
            )
        elif mode == 0:
            self.file_manager = MDFileManager(
                exit_manager=self.exit_manager,
                select_path=self.add_select_path,
                # ext=[".zip"]
            )
        elif mode == 2:
            print(card_id)
            self.file_manager = MDFileManager(
                exit_manager=self.exit_manager,
                select_path=lambda x: self.select_chapter_path(x, card_id, book_id),
                # ext=[".zip"]
            )
            
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            android_version = self.get_android_version()
            self.Toast(f"{android_version}")

            if android_version <= 10:
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            elif android_version > 10:
                self.permissions_external_storage()

            from android.storage import primary_external_storage_path
            primary_ext_storage = primary_external_storage_path()
            self.Toast(primary_ext_storage)
            self.file_manager.show(primary_ext_storage)

        else:
            self.file_manager.show(os.path.expanduser("~"))

        return

    def exit_manager(self, *args):
        self.file_manager.close()
        self.file_manager = None

    def add_select_path(self, path):
        self.file_manager.close()
        logging.info(f"os_absolute path:{os.getcwd()}")
        
        name = path.split("/")[-1].split("\\")[-1].split(".")[0]
        logging.info(f"add book name: {name}")
        book_name_list = [self.book_shelf.books_data[f"book{i}"]["name"] for i in range(self.book_shelf.book_max_label + 1)] if  self.book_shelf else []
        
        logging.info(f"book name list: {book_name_list}")
        if name in book_name_list:
            self.Toast(f"{name} already exists")
            logging.warning(f"add book: {name} already exists")
            logging.info(f"app router list: {os.listdir('.')}")
            self.book_shelf.refresh_shelf_json()
            return 
            
        if not os.path.exists("temp"):
            os.mkdir("temp")
            
        try:
            if self.add_book_type == "folder":
                self.add_book_by_folder(path)
            elif self.add_book_type == "zip":
                self.add_book_by_zip(path)
            elif self.add_book_type == "pdf":
                self.add_book_by_pdf(path)
        except Exception as e:
            self.Toast(f"ERROR:{e}")
            logging.error(f"ERROR:{e}")
        
        if os.path.exists("temp"):
            delete_director("temp")
        logging.info(f"app router list: {os.listdir('.')}")
        
        os.mkdir("temp")
        self.book_shelf.refresh_shelf()
        return 
        
    def cover_select_path(self, path):
        self.file_manager.close()
        self.book_shelf.update_cover(self.edit_cover_card_id, path)
        self.update_main_screen()
        self.book_shelf.refresh_shelf()

    def select_chapter_path(self, path, chapter_id, book_id):
        self.file_manager.close()
        book = Book_detail(f"data_json/{book_id}.json")
        book.update_cover(chapter_id, path)
    
    def get_android_version(self):
        if platform == "android":
            VERSION = autoclass("android.os.Build$VERSION")
            android_version = int(VERSION.RELEASE.split(".")[0])
            return android_version

    # try to do this, it will allow you to have access to all directories and files in the storage.
    def permissions_external_storage(self, *args):
        if platform == "android":
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Environment = autoclass("android.os.Environment")
            Intent = autoclass("android.content.Intent")
            Settings = autoclass("android.provider.Settings")
            Uri = autoclass("android.net.Uri")

            if api_version > 29:
                # If you have access to the external storage, do whatever you need
                if Environment.isExternalStorageManager():
                    # If you don't have access, launch a new activity to show the user the system's dialog
                    # to allow access to the external storage
                    pass
                else:
                    try:
                        activity = mActivity.getApplicationContext()
                        uri = Uri.parse("package:" + activity.getPackageName())
                        intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION, uri)
                        currentActivity = cast(
                            "android.app.Activity", PythonActivity.mActivity
                        )
                        currentActivity.startActivityForResult(intent, 101)
                    except:
                        intent = Intent()
                        intent.setAction(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)
                        currentActivity = cast(
                            "android.app.Activity", PythonActivity.mActivity
                        )
                        currentActivity.startActivityForResult(intent, 101)


App().run()
