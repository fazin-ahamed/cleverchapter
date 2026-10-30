from customtkinter import *
from PIL import Image
from tkVideoPlayer import TkinterVideo
import fetchbooks

root = CTk()
root.title("Clever Read")
#root.geometry("600x400")

def destroy_all():
    for widget in root.winfo_children():
        widget.destroy()
def view_book(rt : CTk):
    destroy_all()
    videoplayer = TkinterVideo(master=root, scaled=True)
    videoplayer.load(r"samplevideo.mp4")
    videoplayer.pack(expand=True, fill="both")

    videoplayer.play()


BW = 185
BH = 150
books = fetchbooks.fetchbook()
#THUMBNAILS :
def main_menu():
    for i in range(1,3):
        for x in range(3):
            bookval = books[x+(i-1)*3][2]
            BFrame = CTkFrame(root)
            BFrame.grid(row=i,column=x)
            img = Image.open(bookval)
            Thumbnail = CTkImage(dark_image=img,size=(BW,BH))
            TB = CTkButton(BFrame,image=Thumbnail,text="",width=BW,height=BH,command=lambda : view_book(root))
            TB.grid(row=0)
            CTkLabel(BFrame,text=f"{books[x+(i-1)*3][0]}     "+"★"*books[x+(i-1)*3][1]).grid(row=1,column = 0)


main_menu()
root.mainloop()
