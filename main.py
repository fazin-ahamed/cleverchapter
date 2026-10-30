from customtkinter import *
from PIL import Image

root = CTk()
root.title("Clever Read")
root.geometry("600x400")

BW = 185
BH = 150
#THUMBNAILS :
for i in range(1,3):
    for x in range(3):
        BFrame = CTkFrame(root)
        BFrame.grid(row=i,column=x)
        img = Image.open("image.png")
        Thumbnail = CTkImage(dark_image=img,size=(BW,BH))
        TB = CTkButton(BFrame,image=Thumbnail,text="",width=BW,height=BH)
        TB.grid(row=0)
        CTkLabel(BFrame,text="BOOK NAME     ★★★★★").grid(row=1,column = 0)



root.mainloop()