import os
import re
import shutil
from copy import deepcopy
from PIL import Image
import json

import logging
logging.basicConfig(level=logging.INFO)

from kivy.utils import platform

if platform == "android":
    from jnius import cast
    from jnius import autoclass
    from android import mActivity, api_version

def rename_files_in_folder(folder_path):
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return

    files = sorted(os.listdir(folder_path))

    for index, filename in enumerate(files):
        file_name, file_extension = os.path.splitext(filename)
        new_filename = f"{index:04d}" + file_extension
        new_filepath = os.path.join(folder_path, new_filename)
        
        os.rename(os.path.join(folder_path, filename), new_filepath)

def resize_pic(path, target_resolution: tuple, fill_color=(230, 255, 255)):
    image = Image.open(path)
    image.thumbnail(target_resolution)
    new_image = Image.new('RGB', target_resolution, fill_color)
    left = (target_resolution[0] - image.width) // 2
    top = (target_resolution[1] - image.height) // 2
    new_image.paste(image, (left, top))
    new_image.save(f'n_{path}')
    image.close()
    new_image.close()
    return f'n_{path}'


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
        except Exception as e:
            logging.error(f"{e}")

 
    else:
        import shutil
        shutil.rmtree(path)
        
    logging.info(f"rm_folder: remove folder {path} successfully.")


class Book_shelf:
    def __init__(self):
        f = open('data_json/book_shelf.json', 'r')
        self.books_data = json.load(f)
        self.book_max_label = len(self.books_data) - 1
        self.check_json()

    def refresh_shelf(self):
        f = open('data_json/book_shelf.json', 'r')
        self.books_data = json.load(f)
        self.check_json()
        self.book_max_label = len(self.books_data) - 1

    def load_a_book(self, book_folder, mode=0):
        book_folder = load_folder_to_local(book_folder)
        num_chapter = len(os.listdir(book_folder))

        self.books_data.update(
            {
                f"book{self.book_max_label + 1}": {
                    "cover_path": f"cover/02.jpg",
                    "name": book_folder.split("/")[-1].split("\\")[-1].split(".")[0],
                    "folder": f"{book_folder}",
                    "num_chapter": num_chapter
                }
            }
        )
        self.sava_json()

        chapter_list = sorted(os.listdir(book_folder))
        new_kv = {}
        for i in chapter_list:
            chapter_type = os.listdir(f"{book_folder}/{i}")[0].split(".")[-1] if not mode else "pdf"
            book_len = len(os.listdir(f"{book_folder}/{i}")) - 1 if not mode else 1
            new_kv.update({
                f"chapter{i}": {
                    "cover_path": "cover/02.jpg",
                    "name": f"chapter{i.split('.')[0]}",
                    "book_path": f"{book_folder}/{i}",
                    "book_len": book_len,
                    "book_type": chapter_type
                }
            })
        self.save_book(new_kv, f"book{self.book_max_label + 1}.json")
        self.refresh_shelf_json()

    def save_book(self, kv, path):
        with open(f"./data_json/{path}", "w") as f:
            f.write(json.dumps(kv, indent=4))

    def sava_json(self):
        with open("data_json/book_shelf.json", "w") as f:
            f.write(json.dumps(self.books_data, indent=4))

    def refresh_shelf_json(self):
        shelf_book_list = list(self.books_data.keys())
        new_keys = {key: key for key in self.books_data}
        self.refresh_shelf()
        
        for i in range(self.book_max_label + 1):
            new_book_name = f"book{i}"
            if shelf_book_list[i] != new_book_name:
                os.rename(f"./data_json/{shelf_book_list[i]}.json", f"./data_json/{new_book_name}.json")
                new_keys[f"{shelf_book_list[i]}"] = new_book_name
                
        
        new_dict = {new_keys.get(old_key, old_key): value for old_key, value in self.books_data.items()}
        self.books_data = new_dict
        self.sava_json()
        
        logging.info("shelf json:refreshed")
        pics_l = os.listdir("pics")
        book_list = [self.books_data[i]["name"] for i in self.books_data]
        logging.info(f"pics:{pics_l}")
        logging.info(f"book_list: {book_list}")
        #pics_l.remove("rename.py")
        #pics_l.remove("__pycache__")
        for book in pics_l:
            if book.split(".")[0] not in book_list:
                delete_director(f"pics/{book}")

    def delete_book(self, book_id):
        rm_folder = self.books_data[f"{book_id}"]["folder"]
        logging.info(f"rm_book_folder:{rm_folder}")
        del self.books_data[f"{book_id}"]
        os.remove(f"./data_json/{book_id}.json")
        delete_director(f"{rm_folder}")
        self.sava_json()
        self.refresh_shelf_json()

    def update_cover(self, book_id, cover_path):
        self.books_data[book_id]["cover_path"] = cover_path
        self.sava_json()

    def check_json(self):
        bsd = deepcopy(self.books_data)
        for book_id in self.books_data:
            if not os.path.exists(f"data_json/{book_id}.json"):
                del bsd[f"{book_id}"]
        self.books_data = bsd


        json_list = os.listdir(path=f"data_json")
        json_list.remove("book_shelf.json")
        for book in json_list:
            if book.split(".")[0] not in self.books_data:
                os.remove(path=f"data_json/{book}")

        self.sava_json()

class Book_detail:
    def __init__(self, book_json_path):
        f = open(book_json_path, 'r')
        self.book_json_path = book_json_path
        self.book_data = json.load(f)
        self.book_max_label = len(self.book_data) - 1

    def update_cover(self, chapter_id, cover_path):
        self.book_data[chapter_id]["cover_path"] = cover_path
        self.sava_json(chapter_id)
    
    def sava_json(self, chapter_id):
        with open(f"{self.book_json_path}", "w") as f:
            f.write(json.dumps(self.book_data))


def copy_directory_java(source, destination):
    Context = autoclass('android.content.Context')
    File = autoclass('java.io.File')
    context = cast('android.content.Context', autoclass('org.kivy.android.PythonActivity').mActivity)
    app_files_dir = context.getFilesDir()
    directory_path = File(app_files_dir, "app/")
    app_path = directory_path.getAbsolutePath()  
    
    CopyUtils = autoclass('org.open.marpy.FolderCopyExample')

    try:
        logging.info("start copy")
        source_file = autoclass('java.io.File')(source)
        destination_file = autoclass('java.io.File')( f"{app_path}/{destination}")
        CopyUtils.copyFolder(source_file,destination_file)
        logging.info(f"Successfully copied {source} to {destination}")
    except Exception as e:
        logging.error(f"copy Error: {e}")
        

def load_folder_to_local(folder):
    folder_name = folder.split("\\")[-1].split("/")[-1]
    local_path = f"pics/{folder_name}"
    
    if os.path.exists(local_path):
        delete_director(local_path)
        
    if platform == "android":
        copy_directory_java(folder, local_path)
    else:
        shutil.copytree(folder, local_path)

    files = sorted(os.listdir(local_path))
    for filename in files:
        index = int(re.findall(r'\d+', filename)[0])  # 默认第一个出现的数字为章节数
        new_filename = f"{index:3d}"
        if filename.split(".")[-1] == "pdf":
            new_filename += ".pdf"
        
        os.rename(f"{local_path}/{filename}", f"{local_path}/{new_filename}")
        rename_files_in_folder(f"{local_path}/{new_filename}")
    return f"{local_path}"


if __name__ == "__main__":
    # sh = Book_shelf()
    # sh.refresh_shelf_json()
    # sh.update_cover("book1", "cover/02.jpg")
    # sh.delete_book("book3")
    
