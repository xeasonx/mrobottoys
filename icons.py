from tkinter import PhotoImage
from PIL import Image, ImageTk

pil_img_download = Image.open("assets/icons/download.png")
pil_img_gear = Image.open("assets/icons/gear.png")
pil_img_reload = Image.open("assets/icons/reload.png")
pil_img_view_list = Image.open("assets/icons/view_list.png")
pil_img_zoom = Image.open("assets/icons/zoom.png")

pil_img_gear = pil_img_gear.resize((32, 32))


ICON_DOWNLOAD = ImageTk.PhotoImage(pil_img_download)
ICON_GEAR = ImageTk.PhotoImage(pil_img_gear)
ICON_RELOAD = ImageTk.PhotoImage(pil_img_reload)
ICON_VIEW_LIST = ImageTk.PhotoImage(pil_img_view_list)
ICON_ZOOM = ImageTk.PhotoImage(pil_img_zoom)
