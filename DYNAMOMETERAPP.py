import tkinter
from tkinter import messagebox
from tkinter import *
import customtkinter
import serial
import time
import math
from datetime import datetime
import pandas as pd
import os
from customtkinter import VERTICAL
from datetime import datetime, timedelta

#USTAWIENIA OKNA
app_tk = tkinter.Tk()
app_tk.geometry("1024x600")
app_tk.title("PUT POWERTRAIN DYNAMOMETER")
app_tk.resizable(False, False)
photobackground = PhotoImage(file="C:\\Users\\Vest3\\Desktop\\INŻ\\predkosciomierzm4.png")
my_canvas = Canvas(app_tk, width=1024, height=600)
my_canvas.pack(fill='both', expand=True)
my_canvas.create_image(0,0, image=photobackground, anchor="nw")
windowStatus = False
try:
    ser = serial.Serial('COM3', 38400)
except:
    print("Nie podłączono Arduino")

#ZMIENNE
engine_max_speed = 1300 #MAX PRĘDKOŚĆ SILNIKÓW, OSTROŻNIE (MAX OGÓLNY TO 2000)
arduinoValues = []
rpm1Counts = []
rpm2Counts = []
rpm3Counts = []
rpm4Counts = []
temp1Values = []
tempBatteryValues = []
currentBattery = []
voltageBattery = []
times = []
frequency = 1
measuring = False


#FUNKCJE POMIARU
def arduinoReading():
    line = ser.readline().decode('utf-8').rstrip()
    if line.startswith('*') and line.endswith('#'):
        #print(line)
        line = line.strip('*').strip('#')
        values = line.split(';')
        for i in values:
            arduinoValues.append(i)  
        values.clear()
        ser.flushInput()
    #print(arduinoValues)

def arduinoValuesAllocation():
    if len(arduinoValues) == 8:
        rpm1Counts.append(arduinoValues[0])
        rpm2Counts.append(arduinoValues[1])
        rpm3Counts.append(arduinoValues[2])
        rpm4Counts.append(arduinoValues[3])
        temp1Values.append(arduinoValues[4])
        tempBatteryValues.append(arduinoValues[5])
        currentBattery.append(arduinoValues[6])
        voltageBattery.append(arduinoValues[7])
        print(voltageBattery[-1])
        teraz = datetime.now()
        times.append(teraz.strftime("%H:%M:%S"))
        text_area.see(END)
        arduinoValues.clear()
        windowStatus = False
        text_area.insert(customtkinter.END, rpm1Counts[-1] + ";" + rpm2Counts[-1] + ";" + rpm3Counts[-1] + ";" + rpm4Counts[-1] + ";" + temp1Values[-1] + ";" + tempBatteryValues[-1] + ';' + currentBattery[-1] + ';' + voltageBattery[-1] + ';' + teraz.strftime("%H:%M:%S")+ "\n")
        updateDisplayText()
        update_arrows()
        updateBatteryStatus(0)

def measurment():
    global measuring
    global ser
    if ser.in_waiting > 0 and measuring:
        arduinoReading()  # Czyta wartości z arduino i dzieli do arduinoValues
        arduinoValuesAllocation()  # Przydziela wartości z arduino do wartości parametrów
    app_tk.after(frequency, measurment)  # Opóźnij funkcję o częstotliwość

def stopMeasurement():
    global measuring
    global ser
    ser.flushInput()  # Opróżnij bufor portu szeregowego
    #ser.close()
    measuring = False
    clearWidgets()
    clearBattery()
    
def startMeasurement():
    global ser
    global measuring
    timeNow = datetime.now()


    try:
        ser.flushInput()  # Opróżnij bufor portu szeregowego
    except:
        messagebox.showerror("Błąd", "Nie można połączyć się z portem szeregowym. Sprawdź czy arduino jest podłączone.")
    else:
        measuring = True
        measurment()
        startStopButton.configure(text = 'Stop', fg_color = '#9c1208')
        timeNow = datetime.now()
        updateTimeCounter(timeNow)
        

def clearWidgets():
    clearBattery()
    clearDisplay()

def sendToArduino(message):
    global ser
    ser.write('*'.encode() + message.encode() + '#'.encode())
    text_area.insert(customtkinter.END, message + "\n")
    #ser.close()
    #print(message)
    
def get_charge_percentage(voltage, cell_count=5):
    max_voltage = 4.2 * cell_count
    min_voltage = 3.0 * cell_count
    voltage_range = max_voltage - min_voltage
    voltage_pos = voltage - min_voltage
    percentage = voltage_pos / voltage_range * 100
    return max(min(percentage, 100), 0)


#FUNKCJE ZAPYTANIA
class CustomAskQuestion(tkinter.Toplevel):
    def __init__(self, parent, title, question):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x100")
        self.result = None

        label = tkinter.Label(self, text=question)
        label.pack(pady=10)

        yes_button = tkinter.Button(self, text="Microsoft Excel (.xlsx)", command=self.answer_yes)
        yes_button.pack(side=tkinter.LEFT, padx=10)

        no_button = tkinter.Button(self, text="Plik tekstowy (.txt)", command=self.answer_no)
        no_button.pack(side=tkinter.RIGHT, padx=10)

    def answer_yes(self):
        self.result = "excel"
        self.destroy()

    def answer_no(self):
        self.result = "txt"
        self.destroy()
        
def custom_askquestion(title, question):
    dialog = CustomAskQuestion(app_tk, title, question)
    app_tk.wait_window(dialog)
    return dialog.result

#FUNKCJE ZAMIANY
def strings_to_floats(string_list):

  for i in range(len(string_list)):
    try:
      string_list[i] = float(string_list[i])
    except ValueError:
      string_list[i] = 0
      
  return string_list

#FUNKCJE PRZYCISKÓW
def startStopButton_function():
    if startStopButton.cget('text') == 'Start':
        startMeasurement()
        #sendToArduino("StartMeasuring")
    else: 
        startStopButton.configure(text = 'Start', fg_color='#7fb310')
        stopMeasurement()

def startStopButtonReset_function():
    startStopButton.configure(text = 'Start', fg_color='#7fb310', command=startStopButton_function)

def saveButton_function():
    if not rpm1Counts:
        messagebox.showwarning("Zapis", "Nie ma danych do zapisu.")
        return
    result = custom_askquestion("Zapis", "Wybierz format pliku.")
    if result == "excel":
        df = pd.DataFrame({
        'czas': times,
        'rpm1_silnik1': strings_to_floats(rpm1Counts),
        'rpm_silnik2': strings_to_floats(rpm2Counts),
        'rpm_silnik3': strings_to_floats(rpm3Counts),
        'rpm_silnik4': strings_to_floats(rpm4Counts),
        'temp. otoczenia': strings_to_floats(temp1Values)
        })
        aktualna_data = datetime.now().strftime("%Y%m%d")
        # Tworzenie nazwy pliku w formacie 'YYYYMMDD.xlsx'
        nazwa_pliku = f"{aktualna_data}.xlsx"
        # Sprawdzanie, czy plik o danej nazwie już istnieje
        numer_cyfry = 1
        while os.path.exists(nazwa_pliku):
            numer_cyfry += 1
            nazwa_pliku = f"{aktualna_data}_{numer_cyfry}.xlsx"
        # Zapisywanie do pliku
        df.to_excel(nazwa_pliku, index=False)
    elif result == "txt":
        df = pd.DataFrame({
        'czas': times,
        'rpm1_silnik1': strings_to_floats(rpm1Counts),
        'rpm_silnik2': strings_to_floats(rpm2Counts),
        'rpm_silnik3': strings_to_floats(rpm3Counts),
        'rpm_silnik4': strings_to_floats(rpm4Counts),
        'temp. otoczenia': strings_to_floats(temp1Values)
        })

        aktualna_data = datetime.now().strftime("%Y%m%d")
        nazwa_pliku = f"{aktualna_data}.txt"
        numer_cyfry = 1
        while os.path.exists(nazwa_pliku):
            numer_cyfry += 1
            nazwa_pliku = f"{aktualna_data}_{numer_cyfry}.txt"

        df.to_csv(nazwa_pliku, index=False, sep='\t')
    else: print("Anulowano zapis.")

def resetButton_function():
    if not rpm1Counts:
        messagebox.showwarning("Reset", "Nie ma danych do resetowania.")
        return
    result = messagebox.askquestion("Reset", "Czy na pewno chcesz zresetować? \nStracisz niezapisane pomiary.")
    if result == "yes":
        rpm1Counts.clear()
        rpm2Counts.clear()
        rpm3Counts.clear()
        rpm4Counts.clear()
        temp1Values.clear()
        times.clear()
        text_area.delete('1.0', tkinter.END)

def remoteControlButton_function():
    global remoteControl_window
    if windowStatus==False: 
        reveal_remote_control_window()
        remoteControl_window.deiconify()
    else: remoteControl_window.focus_force()


#OKNO ZDALNEGO STEROWANIA
def reveal_remote_control_window():
    global engine_max_speed
    global remoteControl_window
    windowStatus = True
    remoteControl_window = tkinter.Tk()
    remoteControl_window.geometry("400x300")
    remoteControl_window.title("Zdalne Sterowanie")
    remoteControl_window.configure(bg=dark_theme_bg)
    remoteControl_window.resizable(False, False)

    slider1= customtkinter.CTkSlider(master=remoteControl_window, from_=980, to=engine_max_speed, number_of_steps=10, orientation=VERTICAL)
    slider1.place(x=20, y=20)
    slider2= customtkinter.CTkSlider(master=remoteControl_window, from_=980, to=engine_max_speed, number_of_steps=10, orientation=VERTICAL)
    slider2.place(x=60, y=20)
    slider3= customtkinter.CTkSlider(master=remoteControl_window, from_=980, to=engine_max_speed, number_of_steps=10, orientation=VERTICAL)
    slider3.place(x=100, y=20)
    slider4= customtkinter.CTkSlider(master=remoteControl_window,from_=980, to=engine_max_speed, number_of_steps=10, orientation=VERTICAL)
    slider4.place(x=140, y=20)
    slider1.set(980)
    slider2.set(980) 
    slider3.set(980)
    slider4.set(980)

    def startRemoteControl():
        startStopRemoteControlButton.configure(fg_color="red", text = 'Wyłącz zdalne sterowanie', command=stopRemoteControl)
        slider1.configure(command=lambda value: engine1Control(value))
        slider2.configure(command=lambda value: engine2Control(value))
        slider3.configure(command=lambda value: engine3Control(value))
        slider4.configure(command=lambda value: engine4Control(value))

    def stopRemoteControl():
        startStopRemoteControlButton.configure(fg_color="#7fb310", text = 'Włącz zdalne sterowanie', command=startRemoteControl)
        slider1.configure(command=None)
        slider2.configure(command=None)
        slider3.configure(command=None)
        slider4.configure(command=None)
        sendToArduino("controlEngine;1;980")
        sendToArduino("controlEngine;2;980")
        sendToArduino("controlEngine;3;980")
        sendToArduino("controlEngine;4;980")

    def engine1Control(value):
        sendToArduino(f"controlEngine;1;{value}")
    def engine2Control(value):
        sendToArduino(f"controlEngine;2;{value}")
    def engine3Control(value):
        sendToArduino(f"controlEngine;3;{value}")
    def engine4Control(value):
        sendToArduino(f"controlEngine;4;{value}")
    
    def RemoteProgram():
        
        if entry1.get() == "" or entry2.get() == "" or entry3.get() == "":
            messagebox.showwarning("Programowanie", "Wprowadź wartości dla badania")
            remoteControl_window.focus_force()
        answer = messagebox.askyesno("Programowanie", ("Wybrano następujące parametry badania:\n"+"Krok czasowy: "+entry1.get()+"s\nKrok ciągu: "+entry2.get()+"% \nCzas badania: "+entry3.get()+"s \nPoprzednie wyniki zostaną usunięte. Czy chcesz kontynuować?"))
        if answer:
            remoteControl_window.withdraw()
            #startStopButton_function()
            resetButton_function()
            global rpm1Counts, rpm2Counts, rpm3Counts, rpm4Counts, temp1Values, times
            global arduinoValues
            step = entry2.get()
            delay = entry1.get()
            duration = entry3.get()
            start_time = time.time()
            currentValue = 980
            time.sleep(0.5)
            startStopButton.configure(fg_color="red", text = 'Badanie w toku', command=None)
            while (time.time()-start_time < float(duration)):
                sendToArduino(f"controlEngine;1;{currentValue}")
                sendToArduino(f"controlEngine;2;{currentValue}")
                sendToArduino(f"controlEngine;3;{currentValue}")
                sendToArduino(f"controlEngine;4;{currentValue}")
                arduinoReading()
                arduinoValuesAllocation()
                app_tk.update()
                time.sleep(float(delay))
                app_tk.after(50, measurment)
                    #arduinoValuesAllocation()  # Przydziela wartości z arduino do wartości parametrów
                    #ser.close()
                currentValue = int(currentValue) + int(step)
                if currentValue > engine_max_speed:
                    currentValue = engine_max_speed
            startStopButtonReset_function()
            messagebox.showinfo(title="Badanie", message="Badanie zakończone", parent=None)
        else: 
            return


    def validate_input(new_value):
        if not new_value:
            return True

        if new_value[-1] not in "0123456789":
            return False

        return True

    def on_close_remote():
        global windowStatus
        windowStatus = False
        remoteControl_window.withdraw() 

    startStopRemoteControlButton = customtkinter.CTkButton(master=remoteControl_window, corner_radius=10, command=startRemoteControl, text = 'Włącz zdalne sterowanie', fg_color='#7fb310', width=20, height=50, font = ("Helvetica", 15))
    startStopRemoteControlButton.place(relx=0.25, rely=0.9, anchor=tkinter.CENTER)

    entry1 = customtkinter.CTkEntry(master=remoteControl_window, validate = "key", validatecommand=(remoteControl_window.register(validate_input), '%P'), corner_radius=10, width=50, height=50, font = ("Helvetica", 15))
    entry1.place(relx=0.9, rely=0.2, anchor=tkinter.CENTER)
    entry1text = customtkinter.CTkLabel(master=remoteControl_window, text = 'Krok czasowy (>1s)')
    entry1text.place(relx=0.65, rely=0.2, anchor=tkinter.CENTER)

    entry2 = customtkinter.CTkEntry(master=remoteControl_window, validate = "key", validatecommand=(remoteControl_window.register(validate_input), '%P'), corner_radius=10, width=50, height=50, font = ("Helvetica", 15))
    entry2.place(relx=0.9, rely=0.4, anchor=tkinter.CENTER)
    entry2text = customtkinter.CTkLabel(master=remoteControl_window, text = 'Krok ciągu (%)')
    entry2text.place(relx=0.65, rely=0.4, anchor=tkinter.CENTER)

    entry3 = customtkinter.CTkEntry(master=remoteControl_window, validate = "key", validatecommand=(remoteControl_window.register(validate_input), '%P'), corner_radius=10, width=50, height=50, font = ("Helvetica", 15))
    entry3.place(relx=0.9, rely=0.6, anchor=tkinter.CENTER)
    entry3text = customtkinter.CTkLabel(master=remoteControl_window, text = 'Czas badania (s)')
    entry3text.place(relx=0.65, rely=0.6, anchor=tkinter.CENTER)

    ProgramRemoteControlButton = customtkinter.CTkButton(master=remoteControl_window, corner_radius=10, command=RemoteProgram, text = 'Programuj badanie', fg_color='#7fb310', width=20, height=50, font = ("Helvetica", 15))
    ProgramRemoteControlButton.place(relx=0.75, rely=0.9, anchor=tkinter.CENTER)

    remoteControl_window.protocol("WM_DELETE_WINDOW", on_close_remote)

# PRZYCISKI
startStopButton = customtkinter.CTkButton(master=app_tk, corner_radius=0, command=startStopButton_function, text = 'Start', fg_color='#7fb310', width=200, height=50, font = ("Helvetica", 15), background_corner_colors=('#1c2c5f','#1c2c5f','#1c2c5f','#1c2c5f'))
startStopButton.place(relx=0.5, rely=0.94, anchor=tkinter.CENTER)

saveButton = customtkinter.CTkButton(master=app_tk, corner_radius=0, command=saveButton_function, text = 'Zapisz', fg_color='#1a1a1a', width=180, height=40, font = ("Helvetica", 15))
saveButton.place(relx=0.7, rely=0.94, anchor=tkinter.CENTER)

resetButton = customtkinter.CTkButton(master=app_tk, corner_radius=0, command=resetButton_function, text = 'Reset', fg_color='#1a1a1a', width=180, height=40, font = ("Helvetica", 15))
resetButton.place(relx=0.3, rely=0.94, anchor=tkinter.CENTER)

remoteControlButton = customtkinter.CTkButton(master=app_tk, corner_radius=0, command=remoteControlButton_function, text = 'Zdalne Sterowanie', fg_color='#1a1a1a', width=200, height=50, font = ("Helvetica", 15))
remoteControlButton.place(relx=0.5, rely=0.05, anchor=tkinter.CENTER)

batteryCell1 = my_canvas.create_rectangle(0, 0, 0, 0, fill='green', outline='green')
batteryCell2 = my_canvas.create_rectangle(0, 0, 0, 0, fill='green', outline='green')
batteryCell3 = my_canvas.create_rectangle(0, 0, 0, 0, fill='green', outline='green')
batteryCell4 = my_canvas.create_rectangle(0, 0, 0, 0, fill='green', outline='green')

# WYSWIETLANIE STATUSU AKUMULATORA
def updateBatteryStatus(value):
    global batteryCell1, batteryCell2, batteryCell3, batteryCell4
    clearBattery()
    if value < 25:
        batteryCell1 = my_canvas.create_rectangle(390, 219, 472, 246, fill='green', outline='green')
    elif value >= 25 and value < 50:   
        batteryCell1 = my_canvas.create_rectangle(390, 219, 472, 246, fill='green', outline='green')
        batteryCell2 = my_canvas.create_rectangle(390, 185, 472, 212, fill='green', outline='green')
    elif value >= 50 and value < 75:
        batteryCell1 = my_canvas.create_rectangle(390, 219, 472, 246, fill='green', outline='green')
        batteryCell2 = my_canvas.create_rectangle(390, 185, 472, 212, fill='green', outline='green')
        batteryCell3 = my_canvas.create_rectangle(390, 152, 472, 178, fill='green', outline='green')
    elif value >= 75:
        batteryCell1 = my_canvas.create_rectangle(390, 219, 472, 246, fill='green', outline='green')
        batteryCell2 = my_canvas.create_rectangle(390, 185, 472, 212, fill='green', outline='green')
        batteryCell3 = my_canvas.create_rectangle(390, 152, 472, 178, fill='green', outline='green')
        batteryCell4 = my_canvas.create_rectangle(390, 118, 472, 144, fill='green', outline='green')

def clearBattery():
    global batteryCell1, batteryCell2, batteryCell3, batteryCell4
    my_canvas.delete(batteryCell1)
    my_canvas.delete(batteryCell2)
    my_canvas.delete(batteryCell3)
    my_canvas.delete(batteryCell4)

# WYŚWIETLANIE WYNIKÓW
    
def clearDisplay():
    global arrow1, arrow2, arrow3, arrow4
    my_canvas.itemconfig(rpmDisplay1, text = '0')
    my_canvas.itemconfig(rpmDisplay2, text = '0')
    my_canvas.itemconfig(rpmDisplay3, text = '0')
    my_canvas.itemconfig(rpmDisplay4, text = '0')
    my_canvas.itemconfig(tempDisplay1, text = '0°C')
    tempDisplay1.config(text = '0°C')
    my_canvas.itemconfig(batteryDisplay, text=('0 °C\n'+'0  A\n' + '0  V'))
    arrow1 = change_angle(my_canvas, arrow1, 244, 172, 80, 210)
    arrow2 = change_angle(my_canvas, arrow2, 782, 172, 80, -30)
    arrow3 = change_angle(my_canvas, arrow3, 244, 395, 80, -30)
    arrow4 = change_angle(my_canvas, arrow4, 782, 395, 80, 210)

def updateDisplayText():
    my_canvas.itemconfig(rpmDisplay1, text = (rpm1Counts[-1]))
    my_canvas.itemconfig(rpmDisplay2, text = (rpm2Counts[-1]))
    my_canvas.itemconfig(rpmDisplay3, text = (rpm3Counts[-1]))
    my_canvas.itemconfig(rpmDisplay4, text = (rpm4Counts[-1]))
    batteryDisplay.configure(text = (tempBatteryValues[-1] + '°C\n' + currentBattery[-1] +'A\n' + voltageBattery[-1] +'V'))
    #my_canvas.itemconfig(tempDisplay1, text = (temp1Values[-1] + '°C'))
    tempDisplay1.configure(text = ("Temperatura otoczenia: " + temp1Values[-1] + '°C'))
    #my_canvas.itemconfig(batteryDisplay, text=(tempBatteryValues[-1] + '°C\n') + (currentBattery[-1] +'A\n') + (voltageBattery[-1] +'V'))
    
def updateTimeCounter(timeStart):
    timeNow = datetime.now()
    timePassed = timeNow - timeStart
    formTime = str(timePassed).split(".")[0]
    label_time.configure(text='Długość pomiaru: ' + formTime)
    app_tk.after(1000, updateTimeCounter, timeStart)

rpmDisplay1=my_canvas.create_text(265, 230, text = '0.00', font=("Avenir", 16), fill='white')
rpmDisplay1r=my_canvas.create_text(265, 250, text = 'obr/min', font=("Avenir", 12), fill='white')

rpmDisplay2=my_canvas.create_text(760, 230, text = '0.00', font=("Avenir", 16), fill='white')
rpmDisplay2r=my_canvas.create_text(760, 250, text = 'obr/min', font=("Avenir", 12), fill='white')

rpmDisplay3=my_canvas.create_text(220, 455, text = '0.00', font=("Avenir", 16), fill='white')
rpmDisplay3r=my_canvas.create_text(220, 475, text = 'obr/min', font=("Avenir", 12), fill='white')

rpmDisplay4=my_canvas.create_text(805, 455, text = '0.00', font=("Avenir", 16), fill='white')
rpmDisplay4r=my_canvas.create_text(805, 475, text = 'obr/min', font=("Avenir", 12), fill='white')

batteryDisplay = customtkinter.CTkLabel(master = app_tk, text = ('SOC: 0%\n' + 'Temp.: 0°C\n'+'Prąd: 0A\n' + 'Napięcie: 0V'), font=("Avenir", 20), fg_color="#363636")
batteryDisplay.place(relx=0.55, rely=0.3, anchor = CENTER)

tempDisplay1=customtkinter.CTkLabel(master = app_tk, text = 'Temperatura otoczenia: 0°C', font=("Avenir", 20), fg_color="#363636")
tempDisplay1.place(relx=0.5, rely=0.47, anchor = CENTER)

label_time = customtkinter.CTkLabel(master = app_tk, text = "Długość pomiaru: 00:00:00", font=("Avenir", 20), fg_color="#363636")
label_time.place(relx=0.5, rely=0.8, anchor = CENTER)

# WSKAZANIE PRĘDKOŚCIOMIERZY
def update_arrows():
    global arrow1, arrow2, arrow3, arrow4
    new_angle1 = angle_transform(rpm1Counts[-1])
    new_angle2 = angle_transformreversed(rpm2Counts[-1])
    new_angle3 = angle_transformreversed(rpm3Counts[-1])
    new_angle4 = angle_transform(rpm4Counts[-1])
    arrow1 = change_angle(my_canvas, arrow1, 244, 172, 80, new_angle1)
    arrow2 = change_angle(my_canvas, arrow2, 782, 172, 80, new_angle2)
    arrow3 = change_angle(my_canvas, arrow3, 244, 395, 80, new_angle3)
    arrow4 = change_angle(my_canvas, arrow4, 782, 395, 80, new_angle4)

def change_angle(canvas, arrow, base_x, base_y, length, new_angle):
    my_canvas.delete(arrow)
    end_x = base_x + length * math.cos(math.radians(new_angle))
    end_y = base_y - length * math.sin(math.radians(new_angle))
    base1_x = base_x + 5 * math.cos(math.radians(new_angle + 90))
    base1_y = base_y - 5 * math.sin(math.radians(new_angle + 90))
    base2_x = base_x + 5 * math.cos(math.radians(new_angle - 90))
    base2_y = base_y - 5 * math.sin(math.radians(new_angle - 90))
    new_arrow_head = [(base1_x, base1_y), (base2_x, base2_y), (end_x, end_y)]
    new_arrow = canvas.create_polygon(new_arrow_head, fill='red')
    return new_arrow

def angle_transform(count):
    input_start = 0
    input_end = 20000
    output_start = 210
    output_end = -30
    output = output_start + ((output_end - output_start) / (input_end - input_start)) * (float(count) - input_start)
    if output > 210:
        output = 210
    if output < -30:
        output = -30
    return output

def angle_transformreversed(count):
    input_start = 0
    input_end = 20000
    output_start = -30
    output_end = 210
    output = output_start + ((output_end - output_start) / (input_end - input_start)) * (float(count) - input_start)
    if output > 210:
        output = 210
    if output < -30:
        output = -30
    return output

base_x, base_y = 397, 437
length = 60
angle = 210
end_x = base_x + length * math.cos(math.radians(angle))
end_y = base_y - length * math.sin(math.radians(angle))
base1_x = base_x + 5 * math.cos(math.radians(angle + 90))
base1_y = base_y - 5 * math.sin(math.radians(angle + 90))
base2_x = base_x + 5 * math.cos(math.radians(angle - 90))
base2_y = base_y - 5 * math.sin(math.radians(angle - 90))
arrow_head = [(base1_x, base1_y), (base2_x, base2_y), (end_x, end_y)]

arrow1 = my_canvas.create_polygon(arrow_head, fill='red')
arrow1 = change_angle(my_canvas, arrow1, 244, 172, 80, 210)

arrow2 = my_canvas.create_polygon(arrow_head, fill='red')
arrow2 = change_angle(my_canvas, arrow2, 782, 172, 80, -30)

arrow3 = my_canvas.create_polygon(arrow_head, fill='red')
arrow3 = change_angle(my_canvas, arrow3, 244, 395, 80, -30)

arrow4 = my_canvas.create_polygon(arrow_head, fill='red')
arrow4 = change_angle(my_canvas, arrow4, 782, 395, 80, 210)

# TWORZENIE POLA LOG
text_area = customtkinter.CTkTextbox(app_tk, wrap=tkinter.WORD, fg_color='black', text_color='white', width=240, height=140, font=("Avenir", 8))
text_area.pack(expand=True, fill=tkinter.BOTH)
text_area.place(relx=0.5, rely=0.64, anchor=tkinter.CENTER)
scrollbar = customtkinter.CTkScrollbar(app_tk, command=text_area.yview)
text_area.configure(yscrollcommand=scrollbar.set)

# THEME COLORS
dark_theme_bg = "#1E1E1E"  # Kolor tła
dark_theme_fg = "#FFFFFF"  # Kolor tekstu


app_tk.configure(bg=dark_theme_bg)
def on_closing():
    if rpm1Counts:
        if messagebox.askokcancel("Wyjście", "Czy chcesz wyjść? Stracisz niezapisane postępy."):
            app_tk.destroy()
            remoteControl_window.destroy()
    else:
        app_tk.destroy()
        remoteControl_window.destroy()
app_tk.protocol("WM_DELETE_WINDOW", on_closing)
app_tk.mainloop() 
