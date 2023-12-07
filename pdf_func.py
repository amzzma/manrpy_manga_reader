# adjusted from https://gist.github.com/tshirtman/2552c4bcbc3d9766e80809b494f35a78

from os.path import exists
from tempfile import mkdtemp, mkstemp
from shutil import rmtree
from binascii import b2a_hex
from os import write, close
from threading import Thread
from kivy.core.window import Window
from kivymd.uix.behaviors import TouchBehavior
from kivymd.uix.label import MDLabel
from kivymd.uix.recycleview import MDRecycleView
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.screen import MDScreen
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import (
    LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTChar, LTCurve,
    LTLine, LTRect,
)
from kivy.lang import Builder
from kivy.uix.image import Image, AsyncImage

from kivy.properties import (
    StringProperty, ListProperty, NumericProperty, AliasProperty,
    DictProperty, ObjectProperty, BooleanProperty, ColorProperty,
)

Builder.load_string('''
#:import RGBA kivy.utils.rgba
<PDFDocumentWidget>:
    viewclass: 'PDFPageWidget'
    key_size: 'size'

    MDRecycleGridLayout:
        spacing: 5
        cols: root.cols
        rows: root.rows
        size_hint: None, None
        size: self.minimum_size
        default_size_hint: None, None

<PDFPageWidget>:
    size_hint: None, None
    md_bg_color: RGBA('FFFFFF')


<PDFLabelWidget,PDFImageWidget>:
    size_hint: None, None
    
<PDFImageWidget>:
    # pos: self.bbox[:2]
    # size: self.bbox[2] - self.x, self.bbox[3] - self.y
<PDFLabelWidget>:
    text_size: self.width, None
    height: self.texture_size[1]
    color: RGBA('000000')
    font_size: 8
''')


class PDFDocumentWidget(MDRecycleView):
    source = StringProperty()
    password = StringProperty()
    cols = NumericProperty(None)
    rows = NumericProperty(None)
    _toc = ListProperty()
    async_load = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(PDFDocumentWidget, self).__init__(**kwargs)
        self._fp = None
        self._document = None
        self._tmpdir = None
        self.do_scroll_x = False
        self.bind(source=self.load)
        self.size = (Window.width, Window.height)
        self.size_hint = (None, None)

        if self.source:
            self.load()

    def load(self, *args):
        if self._fp:
            # close the previous pdf file
            self._fp.close()

        pdf_doc = self.source
        if not pdf_doc or not exists(pdf_doc):
            self.pages = []
            self._doc = []
            self._document = None
            if self._tmpdir:
                rmtree(self._tmpdir)
                self._tmpdir = None

        try:
            self._fp = fp = open(pdf_doc, 'rb')
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            parser.set_document(doc)
            self._document = doc
            self._create_tmpdir()
            self._parse_pages()

        except IOError as e:
            # the file doesn't exist or similar problem
            raise IOError(e)

    def _create_tmpdir(self):
        if not self._tmpdir:
            self._tmpdir = mkdtemp()
        return self._tmpdir

    def _parse_pages(self):
        doc = self._document
        if not doc:
            self.data = []
            return

        data = []

        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        self.device = device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        self.interpreter = PDFPageInterpreter(rsrcmgr, device)

        for i, page in enumerate(PDFPage.create_pages(doc)):
            p = {
                'manager': self,
                'page': page,
                # 'size': ("400dp", "711dp")
                'size': page.attrs.get('MediaBox', [0, 0, 0, 0])[2:],
            }
            data.append(p)

        self.data = data


class PDFPageWidget(MDRelativeLayout):
    labels = DictProperty()
    attributes = DictProperty()
    manager = ObjectProperty()
    page = ObjectProperty()
    items = ListProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # print((Window.width, Window.height))
        self.size = (Window.width, Window.height)

    def on_page(self, *args):
        if self.manager.async_load:
            Thread(target=self._load_page).start()
        else:
            self._load_page()

    def _load_page(self):
        self.manager.interpreter.process_page(self.page)
        self.items = self.manager.device.get_result()

    def on_items(self, *args):
        self.clear_widgets()
        self._render_content(self.items)

    def _render_content(self, lt_objs):
        """Iterate through the list of LT* objects and capture the text
        or image data contained in each
        """
        for lt_obj in lt_objs:
            # print(lt_obj)
            if isinstance(lt_obj, LTChar):
                self.add_text(
                    text=lt_obj.get_text(),
                    box_pos=(lt_obj.x0, lt_obj.y0),
                    box_size=(lt_obj.width, lt_obj.height),
                    # font_size=lt_obj.fontsize,
                    # font_name=lt_obj.fontname,
                )

            elif isinstance(lt_obj, (LTTextBox, LTTextLine)):
                self.add_text(
                    text=lt_obj.get_text(),
                    box_pos=(lt_obj.x0, lt_obj.y0),
                    box_size=(lt_obj.width, lt_obj.height),
                )

            elif isinstance(lt_obj, LTImage):
                saved_file = self.save_image(lt_obj)
                if saved_file:
                    image = PDFImageWidget(
                        source=saved_file,
                        bbox=lt_obj.bbox,
                        size=(Window.width, Window.height),

                        size_hint=(None, None),
                        fit_mode="fill"
                    )
                    image.allow_stretch = True
                    image.keep_ratio = True

                    self.add_widget(image)

            elif isinstance(lt_obj, LTFigure):
                self._render_content(lt_obj)

    def save_image(self, lt_image):
        """Try to save the image data from this LTImage object, and
        return the file name, if successful
        """
        if lt_image.stream:
            file_stream = lt_image.stream.get_rawdata()
            if file_stream:
                file_ext = self.determine_image_type(file_stream[0:4])
                if file_ext:
                    fd, fn = mkstemp(dir=self.manager._tmpdir, suffix=f'.{file_ext}')
                    write(fd, file_stream)
                    close(fd)
                    return fn

    @staticmethod
    def determine_image_type(stream_first_4_bytes):
        """Find out the image file type based on the magic number comparison of the first 4 (or 2) bytes"""
        file_type = None
        bytes_as_hex = b2a_hex(stream_first_4_bytes)
        if bytes_as_hex.startswith(b'ffd8'):
            file_type = '.jpeg'
        elif bytes_as_hex == b'89504e47':
            file_type = '.png'
        elif bytes_as_hex == b'47494638':
            file_type = '.gif'
        elif bytes_as_hex.startswith(b'424d'):
            file_type = '.bmp'
        return file_type

    def add_text(self, text, box_pos, box_size, **kwargs):
        label = self.labels.get((box_pos, box_pos))
        if not label:
            label = PDFLabelWidget(text=text, pos=box_pos, size=box_size, **kwargs)
            self.labels[(box_pos, box_size)] = label
            self.add_widget(label)
        else:
            label.text += text

    # def add_image(self, lt_image):
    #     source = self.save_image(lt_image)
    #     if source:
    #         image = PDFImageWidget(
    #             source=source,
    #             pos=(lt_image.x0, lt_image.y0),
    #             size=(Window.width, Window.height), #(lt_image.widt, lt_image.height)
    #         )
    #         image.allow_stretch = True
    #         image.keep_ratio = True
    #
    #         self.add_widget(image)
    #         self.images.append(image)


class PDFImageWidget(AsyncImage):
    bbox = ListProperty([0, 0, Window.width, Window.height])


class PDFLabelWidget(MDLabel):
    bbox = ListProperty([0, 0, Window.width, Window.height])

