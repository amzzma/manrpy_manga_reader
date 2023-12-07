import os
import shutil
from binascii import b2a_hex
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTImage, LTFigure

import logging
# 设置pdfminer的日志级别为WARNING或更高级别，以取消INFO级别的日志
logging.getLogger('pdfminer').setLevel(logging.WARNING)


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


def save_image(lt_image):
    if lt_image.stream:
        file_stream = lt_image.stream.get_rawdata()
        if file_stream:
            file_ext = determine_image_type(file_stream[0:4])
            if file_ext:
                with open(f"./pdf_folder/test.{file_ext}", mode="wb") as f:
                    f.write(file_stream)


def extract_pic(path):
    pic_l = []
    for page_layout in extract_pages(path):
        for element in page_layout:
            if isinstance(element, LTImage):
                x = element.stream.get_rawdata()
                pic_l.append(x)
            elif isinstance(element, LTFigure):
                for j in element:
                    if isinstance(j, LTImage):
                        x = j.stream.get_rawdata()
                        pic_l.append(x)
    return pic_l


def pdf_pic_write2dir(pdf_path, to_folder):
    # logging.info(f"pdf_pic_write2dir: {pdf_path} to {to_folder}")

    pic_l = extract_pic(pdf_path)
    pic_type = determine_image_type(pic_l[0])
    if not os.path.exists(f"{to_folder}"):
        os.mkdir(f"{to_folder}")
    # print(pic_type)
    for i, pic_stream in enumerate(pic_l):
        with open(f"{to_folder}/{i:4d}{pic_type}", mode="wb") as f:
            f.write(pic_stream)


if __name__ == "__main__":
    pdf_pic_write2dir(r"E:\learning_package\kvmd\test\t_pdf\Doc1.pdf", "folder_pdf/yuri1")


