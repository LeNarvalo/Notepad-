# -*- coding: utf8 -*-
import os
import time
import win32gui
import winsound
import threading
import pyautogui
import tkinter as tk
import tkinter.font as tkFont  
from tkinter import colorchooser

PATH = os.getenv('APPDATA')+r'\Notepad++\backup'
if not os.path.exists(os.path.expanduser(r'~\Notepad++')):
    os.mkdir(os.path.expanduser(r'~\Notepad++'))

p = os.path.expanduser(r'~\Notepad++') + r'\log.txt'

def enumHandler(hwnd, windows):
    if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if '- Notepad++' in title :
            #print(title.removesuffix(' - Notepad++'))
            #rect = win32gui.GetWindowRect(hwnd)
            #rect_2 = win32gui.GetClientRect(hwnd)
            #x0, y0 = win32gui.ClientToScreen(hwnd, (rect_2[0], rect_2[1]))
            #x1, y1 = win32gui.ClientToScreen(hwnd, (rect_2[2], rect_2[3]))
            #rect = (x0, y0, x1, y1, )
            windows.append(title.removesuffix(' - Notepad++'))#, rect, hwnd))

def get_file(f_path): 
    b_name = os.path.basename(f_path[1:])
   
    FILES = []
    directory = os.listdir(PATH) 
    for file in directory:
        if file[:file.index('@')] == b_name:  
            try:
                FILES.append((os.path.getmtime(fr'{PATH}\{file}'), fr'{PATH}\{file}'))
            except FileExistsError: #Fichier renommé entre temps, pas de chance ?
                print('BUG TEMPORAIRE ?', file)
                pass
 
    if FILES:
        file = max(FILES) #GET THE MOST RECENT FILE
        return file[1]
        
def hastag_is_string(ligne, index):
    #STRING    
    for c in ("'",'"'):
        try:
            id_s = ligne.index(c)
            id_e = ligne[id_s+len(c):].index(c)+id_s+len(c)
        except ValueError:
            pass
        else:
            if id_s < index < id_e:
                #print'# is stringed') 
                return True
    return False 

def find_exception(char, relative_index, ligne):
    '''CHECK IF IT'S NOT A STRING OR A COMMENT'''

    #COMMENT 
    if '#' in ligne and relative_index > ligne.index('#') and not hastag_is_string(ligne, ligne.index('#')):
        return True

    #STRING    
    indexs = [] 
    for c in ('"',"'"):
        couple = []
        for i, char in enumerate(ligne):
            if char == c:
                couple.append(i)
            if len(couple) == 2:
                indexs.append(couple)
                couple = []
    for couple in indexs:
        if couple[0] < relative_index < couple[1]:
            return True

    return False 

def cntrl(o, c, w):
    #o = [(1,1), (9,10)] #Opened (str_id, real_id)
    #c = [(4,4), (8,8), (11,12)] #Closed (str_id, real_id)
    #start_time = time.time()
    association = {}
    not_used_c = []
    for k in c:
        for l in o[::-1]:
            if l[0] < k[0]: 
                association[k[0]] = l[0]
                o.remove(l)
                break
        else:
            not_used_c.append(k)

    results = []
    for l in o:
        var = f'{l[1]}: {w} is not closed'
        results.append(var)

    for k in not_used_c:
        var = f'{k[1]}: {w} is not opened'
        results.append(var)

    #print( time.time() - start_time ) #0.0 sec =)
    return results 

def check():
    before_ttd = [] 
    old_fp = ''
    
    paths = {}
    while run:
        time.sleep(0.97)
        text_to_display = []
        #start_time = time.time()
        windows = [] 
        win32gui.EnumWindows(enumHandler, windows)
        if not windows:
            if not root.iconify:
                if LABEL.cget('bg')==bad_color:
                    shake()
                root.withdraw()
                top.withdraw()
                root.iconify=True            
            continue
        f_path = windows[0]
        if f_path:
            if root.iconify: 
                root.iconify=False
                root.deiconify()
            if f_path.startswith('*'):  
                '''IT IS IN APPDATA'''
                notepad_path = get_file(f_path)
                if notepad_path:
                    #C:\Users\toto\AppData\Roaming\Notepad++\backup\notepad++.py@2022-07-23_212405()
                    mtime = os.path.getmtime(notepad_path) #1-2 msec
                    if mtime in paths and f_path == old_fp:
                        continue
                    paths[mtime] = True
                        
                    old_fp = f_path
                    
                    NOTEPAD = {'(':[],'[':[],'{':[],'}':[],']':[],')':[]} 

                    with open(notepad_path,"r+b") as f :
                        text = f.read() #5-6 msec
                        text_str = text.decode('utf8') #<1 msec 
                        text_set = set(text_str) #<1 msec 
                        moins = 0
                        pcd = -1
                        line_id = 0
                        current_id = 0
                        mega_string = False
                        #etape = time.time()           
                        for real_id, binary in enumerate(text): #TOUT LE BLOC : 10-14 msec
                            char = chr(binary)
                            
                            if char not in text_set and real_id != pcd +1:                                
                                moins += 1
                                pcd = real_id
                            index = real_id-moins

                            if text_str[index:index+3] == "'''": #''' 
                                mega_string = 1-mega_string
                            
                            if mega_string:
                                continue
                            
                            if '\n' == char:
                                line_id += 1
                                current_id = index + 1 

                            if char in '{([])}' :
                                relative_index = index-current_id
                                ligne = text_str[current_id:]
                                try:
                                    n_id = ligne.index('\n')
                                except ValueError:
                                    n_id = len(ligne)
                                ligne = ligne[:n_id]
                                
                                if not find_exception(char, relative_index, ligne): #<1 msec
                                    NOTEPAD[char].append((index, real_id+1))

                        #print('ETAPE :',time.time()-etape)
                        #for key in NOTEPAD:
                        #    print(key, NOTEPAD[key])  
                        if len(NOTEPAD['(']) != len(NOTEPAD[')']):
                            text_to_display.extend(cntrl(NOTEPAD['('], NOTEPAD[')'], 'paranthèse'))
                        
                        if len(NOTEPAD['[']) != len(NOTEPAD[']']):
                            text_to_display.extend(cntrl(NOTEPAD['['], NOTEPAD[']'], 'crochet'))

                        if len(NOTEPAD['{']) != len(NOTEPAD['}']):
                            text_to_display.extend(cntrl(NOTEPAD['{'], NOTEPAD['}'], 'accolade'))
                        
                    if LABEL.cget('bg') == 'yellow':
                        LISTEBOX.configure(bg=good_color) 
                        LABEL.configure(bg=good_color) 
                        LABEL.configure(text='0')
                        
            elif old_fp[1:] != f_path :
                LISTEBOX.configure(bg="yellow")
                LABEL.configure(bg="yellow")
                LABEL.configure(text='-')
            else:
                continue  

            if text_to_display != before_ttd:
                before_ttd = text_to_display.copy() 
                LISTEBOX.delete(0,"end")

                if len(text_to_display):
                    if LISTEBOX.cget('bg') != bad_color:
                        LISTEBOX.configure(bg=bad_color)
                        LABEL.configure(bg=bad_color)
                        x, y = root.winfo_pointerx(), root.winfo_pointery()
                        x0 = root.winfo_x()
                        y0 = root.winfo_y()
                        #x0 = data[data.index('+')
                        if x0 < x < x0+min_w and y0 < y < y0+min_h:
                            on_enter_min(None)
                    if len(text_to_display) > 9:
                        string = '+9'
                    else:
                        string = str(len(text_to_display))
                    LABEL.configure(text=string)
                else:
                    LISTEBOX.configure(bg=good_color)
                    LABEL.configure(bg=good_color)
                    LABEL.configure(text=str(0))
                    on_leave_max(None)
                    
                for i, ligne in enumerate(text_to_display):
                    if len(ligne):
                        if len(ligne)>31:
                            ligne = ligne[:29]+'...'
                        LISTEBOX.insert(i, ligne)
                        
        #print('', round((time.time()-start_time),3))

def choose_color_good():
    global good_color
    color = colorchooser.askcolor(title ="Choisissez la couleur OK")[-1]
    if color and color.startswith('#'):
        ancien_color = good_color
        good_color = color
        if ancien_color == LISTEBOX.cget('bg') or ancien_color == LABEL.cget('bg'):
            LISTEBOX.configure(bg=good_color)
            LABEL.configure(bg=good_color)
        log()

def choose_color_bad():
    global bad_color
    color = colorchooser.askcolor(title ="Choisissez la couleur ERREUR")[-1]
    if color and color.startswith('#'):
        ancien_color = bad_color
        bad_color = color
        if ancien_color == LISTEBOX.cget('bg') or ancien_color == LABEL.cget('bg'):
            LISTEBOX.configure(bg=bad_color)
            LABEL.configure(bg=bad_color)
        log()

def log():
    file = open(p,"w",encoding="utf8")
    file.write(good_color+"\n")
    file.write(bad_color+"\n")
    file.write(str(font_size)+"\n")
    file.write(str(X)+"\n")
    file.write(str(Y)+"\n")
    file.write(str(root.coller))
    file.close()

def change_font_size():
    x0, y0 = root.winfo_pointerx(), root.winfo_pointery()
    top.deiconify()
    top.geometry(f'{120}x{273}+{min(x0,root.winfo_screenwidth()-120)}+{max(0,y0-200)}')
    SCALE.set(font_size)

def valider_selection(event):
    global font_size
    font_size = int(SCALE.get()) 
    font = tkFont.Font(family='Courrier', size=font_size)
    LABEL.configure(font=font) 
    log()

def close():
    top.withdraw()

def on_enter(event):
   button.config(bg='OrangeRed3', foreground= "white")

def on_leave(event):
   button.config(bg= 'SystemButtonFace', foreground= 'RED')

def on_enter_min(event):
    global min_w , min_h
    if root.winfo_width() == 50:
        if LABEL.cget('bg') not in ('yellow', good_color):
            LABEL.pack_forget()
            LISTEBOX.pack()
            min_w = 300
            min_h = 100
            x = min(root.winfo_screenwidth()-min_w, X)
            y = min(root.winfo_screenheight()-(min_h+60), Y)
            root.attributes('-alpha',0.95)
            root.geometry(f'{min_w}x{min_h}+{x}+{y}')

def on_leave_max(event):
    global min_w , min_h
    if root.winfo_width() == 300:
        min_w , min_h = 50, 50
        LISTEBOX.pack_forget()
        LABEL.pack(expand=True, fill=tk.BOTH)
        root.attributes('-alpha',0.55)
        root.geometry(f'{min_w}x{min_h}+{X}+{Y}')

def option(event):
    try:
        y =  root.winfo_pointery()-(MENU.winfo_reqheight()+5)
        if root.winfo_pointerx() >= root.winfo_screenwidth()/2: #Déployer à gauche
            x = root.winfo_pointerx()-(MENU.winfo_reqwidth()+25)
        else:
            x = root.winfo_pointerx()
        MENU.tk_popup(x, y)
    finally:
        MENU.grab_release()

def drag(event):
    global X, Y
    x, y = root.winfo_pointerx(), root.winfo_pointery() #Mouse position

    if not root.coller:
        X = min(root.winfo_screenwidth()-min_w, x)
        Y = min(root.winfo_screenheight()-(min_h+60), y)
        root.geometry(f'{min_w}x{min_h}+{X}+{Y}')
    else:
        if rect[1] < y < rect[3]-min_h:
            Y = y
            root.geometry(f'{min_w}x{min_h}+{X}+{Y}')

    log()

def shake():
    winsound.MessageBeep(winsound.MB_OK)
    data = root.winfo_geometry()
    root.attributes('-topmost',True)
    x0, y0 = int(data.split('+')[1]), int(data.split('+')[2])
    if x0>10:
        for _ in range(5):
            for x1 in (x0, x0-5, x0-10):
                root.geometry(f'{min_w}x{min_h}+{x1}+{y0}')
                time.sleep(0.01)
            if x0+10 < root.winfo_screenwidth():
                for x1 in (x0-5, x0, x0+5, x0+10):
                    root.geometry(f'{min_w}x{min_h}+{x1}+{y0}')
                    time.sleep(0.01)
            
                for x1 in (x0+5, x0):
                    root.geometry(f'{min_w}x{min_h}+{x1}+{y0}')
                    time.sleep(0.01)
            else:
                for x1 in (x0-5,x0):
                    root.geometry(f'{min_w}x{min_h}+{x1}+{y0}')
                    time.sleep(0.01)
            
    else:
        for _ in range(5):
            for x1 in (x0, x0+5, x0+10):
                root.geometry(f'{min_w}x{min_h}+{x1}+{y0}')
                time.sleep(0.01)
            for x1 in (x0+5,x0):
                root.geometry(f'{min_w}x{min_h}+{x1}+{y0}')
                time.sleep(0.01)
    root.attributes('-topmost',False)

def accoller():
    global X, Y
    if root.coller: #Collé
        root.coller = 0 #Pas collé
        MENU.entryconfig(3, label = "Coller à Notepad++")
        X = root.winfo_screenwidth()-min_w
        Y = root.winfo_screenheight()-(min_h+60)
        x = root.winfo_x()
        y = root.winfo_y()
        add_x = 1
        if x > X:
            add_x = -1
        add_y = 1
        if y > Y:
            add_y = -1
        all_x = [cur_x for cur_x in range(x,X,add_x)]
        all_y = [cur_y for cur_y in range(y,Y,add_y)]
        
        nx = len(all_x)
        ny = len(all_y)
        
        if nx > ny:
            div = nx/ny
            couples = []
            index = 0
            nb = nx-1
            for i, n in enumerate(all_x):
                if i != 0 and i % div < 1:
                    index+=1
                couples.append((n,all_y[min(index,nb)]))
        else:
            div = ny/nx
            couples = []
            index = 0
            nb = ny-1
            for i, n in enumerate(all_y):
                if i != 0 and i % div < 1:
                    index+=1
                couples.append((all_x[min(index,nb)], n))

        for i in range(0, len(couples), 6):
            x,y = couples[i]
            root.geometry(f'{min_w}x{min_h}+{x}+{y}')
            root.update()
        x,y = couples[-1]
        root.geometry(f'{min_w}x{min_h}+{x}+{y}')
        
    else: #Pas collé
        keep_coller()
        root.coller = 1 #Collé
        MENU.entryconfig(3, label = "Décoller de Notepad++")
    log()

def boucle():
    global rect, HWND
    old_rect = None
    while run:
        hwnd = win32gui.GetForegroundWindow()
        fg = win32gui.GetWindowText(hwnd)
        #print(fg)
        if '- Notepad++' in fg :
            root.attributes('-topmost',True)
            root.lift()
             #print('lift')
        elif 'Tool for Notepad++' != fg :
            #root.withdraw()
            root.attributes('-topmost',False)
            try:
                x0, y0, x1, y1 = win32gui.GetClientRect(hwnd)
                geo = root.geometry().split('+')
                x, y =  int(geo[1]), int(geo[2])
                if x0<x<x1-min_w and y0<y<y1-min_h :
                    root.lower()
            except:
                #print(fg,'non compatible')
                pass 
 
        if root.coller:
            if '- Notepad++' in fg:
                rect = win32gui.GetWindowRect(hwnd)
                rect = rect[0]+15, rect[1]+130, rect[2], rect[3]-62
                HWND = hwnd
                if old_rect != rect:
                    old_rect = rect
                    keep_coller()

        time.sleep(0.01)

def keep_coller():
    global X, Y
    WIDTH = (rect[3]-rect[1])
    if not root.iconify and WIDTH < min_h:
        root.withdraw()
        root.iconify = True
    elif root.iconify and WIDTH >= min_h: 
        root.deiconify()
        root.iconify = False
    X, Y = rect[0], int(WIDTH/2)+rect[1]-int(min_h/2)
    root.geometry(f'{min_w}x{min_h}+{X}+{Y}')
    log()

def Quitter():
    global run
    run = False
    top.destroy()
    root.destroy()

def select_list(event):
    global wait_select
    if time.time() - wait_select < 2:
        return
        
    selected_indices = LISTEBOX.curselection()
    for i in selected_indices:
        ligne = LISTEBOX.get(i)
        num = ligne[:ligne.index(':')]
        #root.lower()
        win32gui.SetForegroundWindow(HWND)
        '''pyautogui.keyDown('ctrlleft')
        pyautogui.keyDown('g')
        pyautogui.keyUp('ctrlleft')
        pyautogui.keyUp('g')
        pyautogui.keyDown('altleft')
        pyautogui.keyDown('tab')
        pyautogui.keyUp('altleft')
        pyautogui.keyUp('tab')'''
        pyautogui.hotkey('ctrlleft','g')
        pyautogui.hotkey('shiftleft','tab')
        pyautogui.press('right')
        pyautogui.press('tab')
        pyautogui.write(num) 
        pyautogui.press('return') 


run = True

good_color = '#94FF93'
bad_color = '#FF6F6F'
font_size = 12
X, Y, coller = None, None, True

if os.path.exists(p):
    try:
        with open(p,"r", encoding='utf8') as f :
            text = f.read()
            liste = text.split('\n')
            good_color = liste[0]
            bad_color = liste[1]
            font_size = int(liste[2])
            X = int(liste[3])
            Y = int(liste[4])
            coller = int(liste[5])
    except:
        os.remove(p)

#MAIN ROOT
root = tk.Tk()
root.title('Tool for Notepad++')
#root.attributes('-topmost',True)
#root.lower()
root.attributes('-alpha',0.55)
root.overrideredirect(True)

#SOME GLOBAL VARIABLES
helv10 = tkFont.Font(family='Helvetica', size=10, weight='bold')
sysv = tkFont.Font(family='Courrier', size=font_size)
sys12 = tkFont.Font(family='Courrier', size=12)

min_w , min_h = 50, 50
if X == None: 
    X = root.winfo_screenwidth()-min_w
    Y = root.winfo_screenheight()-(min_h+60)
root.geometry(f'{min_w}x{min_h}+{X}+{Y}') 
rect = (X,Y,X,Y)

root.coller = 1
if not coller:
    root.coller = 0

wait_select = time.time()

#LABEL WHEN "MINIMIZED"
LABEL = tk.Label(root,bg='yellow', text='', font=sysv) 
LABEL.pack(expand=True, fill=tk.BOTH)
LABEL.bind("<Enter>", on_enter_min)

#LISTEBOX WHEN "MAXIMIZED"
LISTEBOX = tk.Listbox(root, width=200, height=100, font=sys12) 
LISTEBOX.bind('<Double-Button-1>', select_list)
LISTEBOX.bind("<Leave>", on_leave_max)

#MENU OPTION
MENU = tk.Menu(root, tearoff = 0)
MENU.add_command(label ="Font Size", command=change_font_size)
MENU.add_command(label ="Couleur OK", command=choose_color_good)
MENU.add_command(label ="Couleur ERREUR", command=choose_color_bad)
if root.coller:
    MENU.add_command(label ="Décoller de Notepad++", command=accoller)
else:
    MENU.add_command(label ="Coller à Notepad++", command=accoller)

MENU.add_separator()
MENU.add_command(label ="Quitter", command=Quitter)

#BINDING ROOT
root.bind('<ButtonRelease-3>', option)
root.bind('<B1-Motion>', drag)
 
#TOPLEVEL
top = tk.Toplevel(root, relief='solid', bd=1)
top.attributes('-topmost',True)
top.overrideredirect(True)

tk.Label(top,text='Font Size', font=helv10).grid(row=0,column=0,padx=1)

red8 = tkFont.Font(family='Arial Black', size=8)

button = tk.Button(top, text ="❌", command = close, font=red8, fg='RED', relief=tk.FLAT)
button.grid(row=0,column=1, sticky='ne')
button.bind('<Enter>', on_enter)
button.bind('<Leave>', on_leave)
tk.ttk.Separator(top, orient='horizontal').grid(row=1,column=0, columnspan=2, sticky = 'ew', padx = 5, pady = 2)

SCALE = tk.Scale(top, orient='vertical', from_=4, to=28,
      resolution=1, tickinterval=2, length=220, troughcolor = 'white', relief='solid')
SCALE.grid(row=2,column=0,columnspan=2)
SCALE.bind('<ButtonRelease-1>', valider_selection)

#HIDE TOP
top.withdraw()

#HIDE ROOT
root.withdraw()
root.iconify = True

#THREADS
threading.Thread(target=check, daemon=True).start()
threading.Thread(target=boucle, daemon=True).start()

root.mainloop()



 


