import datetime
import os
import sys
import textwrap
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
import urllib
import webbrowser

import mysql.connector as connector
import pygame
import pyscreenshot
import pyttsx3
import speech_recognition
import wikipedia
import wolframalpha
from PIL import Image, ImageTk

''' 
 The following class holds all the attributes and variables for our application
 it initiates the top level tkinter widget passed, contains various listeners
 for user input events and also creates a connection to the database
 
 All the important actions are performed within this class.
'''
class PersonalAssistant:
    
    '''
      This function uses the system time to select an appropriate greeting message
      for the user on the startup of this application.
    '''
    def wishMe(self):

        hour = datetime.datetime.now().hour

        if hour >= 0 and hour < 12:

            self.showInCommandText("Hello, Good Morning.")
            self.speak("Hello, Good Morning.")

        elif hour >= 12 and hour < 17:

            self.showInCommandText("Hello, Good Afternoon.")
            self.speak("Hello, Good Afternoon.")

        else:

            self.showInCommandText("Hello, Good Evening.")
            self.speak("Hello, Good Evening.")
            
            
    '''
      This function takes the input passed by the user in the text mode.
      It makes the necessary changes in the state of the widgets and the
      application and then starts a new thread to interpret the input.
    '''
    def takeTextCommand(self):

        command = self.commandEntry.get()

        if len(command) > 0:

            self.commandEntry.delete(0, "end")

            try:

                while self.textThread.is_alive():

                    self.mixer.music.stop()

                    self.mixer.music.unload()

            except:
                pass
            
            # starts a dedicated thread for the function statementReceived

            self.textThread = threading.Thread(
                target=self.statementReceived, args=(command,)
            )

            self.textThread.start()
            
    
    '''
      This function takes the input passed my the user in the audio mode.
      It uses the microphone as the source and then lets the voice recognizer
      listen to it in the background.
    '''
    def takeMicCommand(self):

        self.mixer.music.stop()

        self.mixer.music.unload()
        
        # makes necessary changes to the UI

        self.micButton["state"] = tk.DISABLED

        self.enterButton["state"] = tk.DISABLED

        self.commandEntry.delete(0, "end")

        self.commandEntry["state"] = tk.DISABLED

        self.showInCommandText("Listening...")

        with self.microphone as source:

            if self.setupAudioInput:
                
                # listens to the user's environment for <duration> seconds and adjusts
                # to the noise levels
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)

                self.setupAudioInput = False

            self.changeRobotIcon("content-border6.png")

            print("Listening...")

        self.stop = self.recognizer.listen_in_background(source, self.callback)
        
    
    '''
      This function is the callback for when the audio has been recognized
      by the recognizer.
    '''
    def callback(self, recognizer, audio):

        try:
            # uses the google audio recogniser
            statement = self.recognizer.recognize_google(
                audio, language="en-in")

            print(f"You said: {statement}\n")

        except Exception:
            # if audio decryption fails, following actions are performed
            statement = "none"

            self.changeRobotIcon("expressionless-border6.png")

            self.speak("Pardon me, please say that again\n")

        self.stop(wait_for_stop=False)

        self.micButton["state"] = tk.NORMAL

        self.enterButton["state"] = tk.NORMAL

        self.commandEntry["state"] = tk.NORMAL

        self.statementReceived(statement)
        
    
    '''
      This function uses the deciphered input from the user obtained by either
      the text or the audio mode and then proceeds with the appropriate options.
    '''
    def statementReceived(self, statement):

        statement = statement.replace("Try saying : ", "")

        self.showInCommandText(statement)

        statement = statement.lower()

        if statement == "none":
            return

        statement = statement.replace("please", "")

        if statement.startswith("can you"):

            statement = statement.replace("can you", "")

        if "bye" in statement:

            self.topInstance.quit()

        elif "wikipedia" in statement:

            self.wiki(statement)

        elif "open" in statement:
            self.open(statement)

        elif any(s in statement for s in ["weather", "temperature"]):

            self.changeRobotIcon("happy-border6.png")

            self.speak("Displaying the Weather Report...")

            webbrowser.open_new_tab("https://www.google.com/search?q=weather")

        elif "news" in statement:

            self.changeRobotIcon("happy-border6.png")

            self.speak("Displaying the latest News Headlines...")

            webbrowser.open_new_tab("https://timesofindia.indiatimes.com/")

        elif "search" in statement:

            self.search(statement)

        elif "screenshot" in statement:

            self.changeRobotIcon("screenshot-border6.png")

            self.speak("Capturing a screenshot...")

            self.takeScreenshot()

        elif "your name" in statement:

            self.changeRobotIcon("greeting-border6.png")

            self.speak(
                "My name is Micro! I'm your personal assistant. I will be happy to help you with your daily tasks."
            )

        elif any(s in statement for s in ("add", "create", "make", "insert")) and any(
            s in statement for s in ["event", "task", "to do"]
        ):

            self.add_to_do()

        elif any(s in statement for s in ("update", "modify", "change")) and any(
            s in statement for s in ["event", "task", "to do"]
        ):

            self.update_to_do()

        elif any(s in statement for s in ("delete", "remove", "change")) and any(
            s in statement for s in ["event", "task", "to do"]
        ):

            self.delete_to_do()

        elif any(s in statement for s in ["event", "task", "to do"]):

            self.changeRobotIcon("happy-border6.png")
            self.commandEntry.insert(0, 'Try saying : "Add event"')
            self.show_to_do()

        else:

            self.output.delete(*self.output.get_children())

            self.changeRobotIcon("thinking-border6.png")

            self.output.insert(parent="", index=0,
                               values=("Working on it...",))

            self.answer(statement)
            
    
    '''
      Displays the text/voice input by the user in a specific UI widget
      of the application for simplicity.
    '''
    def showInCommandText(self, statement):
        
        # formats text appropriate before displaying

        if statement == "none":
            self.canvas.itemconfig(self.commandText, text="? ? ?")
        elif len(statement) <= 40:

            self.canvas.itemconfig(
                self.commandText, text=statement.capitalize())

        else:

            self.canvas.itemconfig(
                self.commandText,
                text=statement[:8].capitalize()
                + "....."
                + statement[-27:-1]
                + statement[-1],
            )
            
    
    '''
      This function user the processed output of the application and then
      provides it back to the user in the audio mode, using the text to speech
      module of python.
    '''
    def speak(self, sentence, fillInTV=True):
        
        
        # waits for the ongoing speech to finish
        while self.mixer.music.get_busy():
            time.sleep(0.1)

        # fills in the output UI by default
        if fillInTV:

            self.output.delete(*self.output.get_children())

            self.output.column("#1", width=480, stretch=tk.YES)

            for i in range(2, 5):

                self.output.column("#2", width=0, stretch=tk.NO)

            self.output.heading("#1", text="")
            self.output.configure(selectmode="none")

            self.output.insert(
                parent="", index=0, values=("\n".join(textwrap.wrap(sentence, 88)),)
            )

        self.mixer.music.stop()

        self.mixer.music.unload()

        outfile = "temp.wav"
        
        # removes a temporary audio file if it already exists, proceeds further otherwise

        try:

            os.remove(outfile)

        except Exception as e:
            pass

        # saves the speech to the temp file
        self.engine.save_to_file(sentence, outfile)

        self.engine.runAndWait()
        
        # loads the speech from the file and plays it using pygame mixers

        pygame.mixer.music.load(outfile)

        pygame.mixer.music.play()
        
    
    '''
      This function is called whenever a question is asked which is not
      present in the application's domain. It uses the Wolfram Alpha API
      to provide the user with a meaningful reply.
    '''
    def answer(self, question):


        client = wolframalpha.Client("JWJJTA-28PAL9AULQ")

        res = client.query(question)

        try:
            
            # extracts answer from the result

            answer = next(res.results).text

            self.changeRobotIcon("happy-border6.png")

            self.speak(answer)

        except:
            
            # if no appropriate answer is found
            self.changeRobotIcon("buzzed-border6.png")

            self.speak("Sorry, I didn't understand")
            
            
    '''
      This function uses the wikipedia library to look for the given input.
    '''
    def wiki(self, statement):

        self.changeRobotIcon("thinking-border6.png")

        self.speak("Searching Wikipedia...")

        statement = statement[statement.index("wikipedia") + 9::].strip()

        try:

            # uses the wikipedia module to get data
            results = wikipedia.summary(statement, sentences=3)

            self.changeRobotIcon("happy-border6.png")

            self.speak("According to Wikipedia,")

            self.speak(results)

        except wikipedia.exceptions.WikipediaException:
            
            # if wikipedia has no data about the query

            self.changeRobotIcon("upset-border6.png")

            self.speak(
                "Sorry, but Wikipedia has no information about that topic yet.")
            
            
    '''
      This function opens up the given website/webpage's address using the
      user's default internet browser.
    '''
    def open(self, statement):

        statement = statement[statement.index("open") + 4::]
        statement = statement.strip()

        while " " in statement:

            statement = statement.replace(" ", "")

        self.changeRobotIcon("happy-border6.png")

        self.speak("Opening " + statement)

        statement = "https://www." + statement

        if not statement.endswith(".com"):

            statement = statement + ".com/"

        webbrowser.open_new_tab(statement)

        
    '''
      This function opens up the google search output webpage for the given
      query using the user's default internet browser.
    '''
    def search(self, statement):

        statement = statement.replace("search", "")
        statement = statement.strip()

        self.changeRobotIcon("happy-border6.png")

        self.speak("Searching on Google.com...")

        webbrowser.open_new_tab("https://www.google.com/search?q=" + statement)

        
    '''
      This function uses the python screenshotting library to take a screenshot
      of the user's computer screen and save it locally in the application directory.
    '''
    def takeScreenshot(self):
        # minimises window
        self.topInstance.iconify()
        
        image = pyscreenshot.grab()
        image.save("CAPTURE.png")
        
        # restores window to original size
        self.topInstance.deiconify()
        
        
    '''
      Obtains the records from the to do list table of the user's local database,
      and displays it in the tkinter treeview.
    '''
    def show_to_do(self):

        # fetches records and stores them in a tuple
        self.cursor.execute(
            "SELECT * FROM TO_DO_LIST ORDER BY EVENT_DATETIME ASC")

        results = self.cursor.fetchall()
        
        # informs the user about the number of records in the list

        if len(results) > 0:

            self.speak("Your to do list has " + str(len(results)) + " events.")

        else:

            self.speak(
                'Your to do list is currently empty. Try saying, "Add an event" to expand it.'
            )

        if results == None:
            return

        # appropriately formats the obtained data and stores them in a new list.
        todoListData = []

        for row in results:

            todoListData += [
                (
                    row[0],
                    datetime.datetime.strftime(row[1], "%A %d %B %Y %I:%M %p"),
                    row[2],
                    "Completed/Past Due" if row[3] else "Due",
                )
            ]
            
        # makes necessary changes to the output UI

        self.output.delete(*self.output.get_children())

        self.output.configure(selectmode="extended")

        for i in range(1, 5):

            self.output.column(f"#{i}", width=120, stretch=tk.NO)

        self.output.heading("#1", text="Event Number")

        self.output.heading("#2", text="Event Date Time")

        self.output.heading("#3", text="Event Name")

        self.output.heading("#4", text="Completion Status")

        for col in self.output["columns"]:

            self.output.column(col, width=120)

        for i in todoListData:

            self.output.insert(parent="", index=0, values=(i))

            
    '''
      Implements the delete record functionality for a table via python interfacing.
      Deletes the records selected by the user from the treeview containing the
      "Show to do" output.
    '''
    def delete_to_do(self):

        # if the user hasn't selected any record then the following actios are performed
        if len(self.output.selection()) == 0:

            self.changeRobotIcon("buzzed-border6.png")

            self.speak(
                "No events were selected. Please try again after selecting the events from the table below",
                fillInTV=False,
            )

            self.commandEntry.delete(0, "end")

            self.commandEntry.insert(
                0, "No event(s) selected. Please try again...")

            self.show_to_do()
            return

        # gets the "event number" of the records selected
        eno = tuple()

        for selection in self.output.selection():

            eno += (self.output.item(selection)["values"][0],) + (0,)
            
        # executes SQL Query

        self.cursor.execute(
            f"DELETE FROM TO_DO_LIST WHERE EVENT_NUMBER IN {eno}")
        self.connection.commit()

        self.changeRobotIcon("happy-border6.png")

        # intimates user
        self.speak(
            f"Events with number {eno[:len(eno)-1]} were successfully deleted.", fillInTV=False
        )

        self.show_to_do()
        
    '''
      Implements the update record functionality on a table via python interfacing.
      Opens a new pop up window to change the properties of the existing record that
      was selected by the user from the output of "show to do"
    '''
    def update_to_do(self):

        # checks if the user has selected a record or not
        if len(self.output.selection()) == 0:

            self.changeRobotIcon("buzzed-border6.png")

            self.speak(
                "No events were selected. Please try again after selecting the events from the table below",
                fillInTV=True,
            )

            self.commandEntry.delete(0, "end")

            self.commandEntry.insert(
                0, "No event(s) selected. Please try again...")

            self.show_to_do()
            return
        
        # in case the user selects more than one record, these actions are performed
        elif len(self.output.selection()) > 1:

            self.changeRobotIcon("expressionless-border6.png")

            self.speak(
                "Only one event can be updated at a time, please try again",
                fillInTV=False,
            )

            self.commandEntry.delete(0, "end")

            self.commandEntry.insert(
                0, "Only one event can be updated at a time...")

            self.output.selection_clear()

            self.show_to_do()
            return
        
        # obtains the old values in the record
        
        self.oldUpdateValues = self.output.item(
            self.output.selection())["values"]
        self.oldUpdateValues[1] = datetime.datetime.strptime(
            self.oldUpdateValues[1], "%A %d %B %Y %I:%M %p"
        )

        # passes the above values to a new child window whilst creating UI

        self.win = tk.Toplevel(self.topInstance)

        self.win.grab_set()

        self.win.title("Update Selected Event")

        _bgcolor = "#abd9e5"

        _fgcolor = "#12153b"

        _font = ("Segoe UI", "14")

        # window properties

        self.win.minsize(450, 300)

        self.win.resizable(1, 1)

        self.win.configure(bg="#abd9e5")

        tk.Label(
            self.win,
            text=f"Event Number - {self.oldUpdateValues[0]}",
            bg=_bgcolor,
            font=_font,
            fg=_fgcolor,
        ).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10, columnspan=3)

        tk.Label(
            self.win, text="Event Name -", bg=_bgcolor, font=_font, fg=_fgcolor
        ).grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)

        self.eventName = ttk.Entry(self.win, width=32, font=_font)
        self.eventName.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
        self.eventName.insert(0, self.oldUpdateValues[2])

        tk.Label(
            self.win, text="Event Datetime -", bg=_bgcolor, font=_font, fg=_fgcolor
        ).grid(row=2, column=0, sticky=tk.W, padx=10, pady=10, columnspan=2)
        self.eventDatetime = ttk.Entry(self.win, width=32, font=_font)
        self.eventDatetime.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
        self.eventDatetime.insert(0, self.oldUpdateValues[1])

        tk.Label(
            self.win,
            text="Please enter datetime in [yyyy-mm-dd hh:mm] format",
            bg=_bgcolor,
            font=("Segoe UI", 10),
            fg=_fgcolor,
        ).grid(row=3, column=0, sticky=tk.W, padx=10, columnspan=2)

        tk.Label(
            self.win, text="Completion Status -", bg=_bgcolor, font=_font, fg=_fgcolor
        ).grid(row=4, column=0, sticky=tk.W, padx=10, pady=10)

        self.completionState = ttk.Combobox(
            self.win, values=["Due", "Completed/Past Due"], font=_font, state="readonly"
        )
        self.completionState.set(self.oldUpdateValues[3])
        self.completionState.grid(
            row=4, column=1, sticky=tk.W, padx=10, pady=10)

        self.style.configure("my.TButton", font=_font)
        self.updateButton = ttk.Button(
            self.win, text="SUBMIT", style="my.TButton", command=self.update
        )
        self.updateButton.grid(row=5, column=1, sticky=tk.E, padx=10, pady=40)

        
    '''
      This function executes the SQL query and performs the necessary actions to
      inform the user about the updation/failure.
    '''
    def update(self):
        
        # executes SQL Query
        try:
            self.cursor.execute(
                f'UPDATE TO_DO_LIST SET EVENT_NAME = \'{self.eventName.get()}\', EVENT_DATETIME = \'{self.eventDatetime.get()}\', event_completed = {0 if self.completionState.get() == "Due" else 1} WHERE  EVENT_NUMBER = {int(self.oldUpdateValues[0])};'
            )
        except:

            # If the app fails to update, it performs the following steps.
            self.changeRobotIcon("upset-border6.png")

            self.speak(
                "I encountered an error whilst updating, please check your input and try again.",
                fillInTV=False,
            )
            self.initiateShowTODOThread()
            self.win.grab_release()
            self.win.destroy()
            return
        
        # If the updation is successful then the following steps are performed.

        self.win.grab_release()
        self.win.destroy()

        self.connection.commit()

        self.changeRobotIcon("happy-border6.png")

        self.speak(
            f"Event number {self.oldUpdateValues[0]} was successfully updated.",
            fillInTV=False,
        )

        self.initiateShowTODOThread()

        
    '''
      Implements the insert record functionality on a table via python interfacing.
      Opens a new pop up window to add the properties of the new record.
    '''
    def add_to_do(self):
        
        # creates UI

        self.winAdd = tk.Toplevel(self.topInstance)

        self.winAdd.grab_set()

        self.winAdd.title("Insert Event")

        _bgcolor = "#abd9e5"

        _fgcolor = "#12153b"

        _font = ("Segoe UI", "14")

        self.winAdd.minsize(450, 300)

        self.winAdd.resizable(1, 1)

        self.winAdd.configure(bg="#abd9e5")

        tk.Label(
            self.winAdd, text="Event Name -", bg=_bgcolor, font=_font, fg=_fgcolor
        ).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)

        self.eventNameAdd = ttk.Entry(self.winAdd, width=32, font=_font)
        self.eventNameAdd.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)

        tk.Label(
            self.winAdd, text="Event Datetime -", bg=_bgcolor, font=_font, fg=_fgcolor
        ).grid(row=1, column=0, sticky=tk.W, padx=10, pady=10, columnspan=2)
        self.eventDatetimeAdd = ttk.Entry(self.winAdd, width=32, font=_font)
        self.eventDatetimeAdd.grid(
            row=1, column=1, sticky=tk.W, padx=10, pady=10)

        tk.Label(
            self.winAdd,
            text="Please enter datetime in [yyyy-mm-dd hh:mm] format",
            bg=_bgcolor,
            font=("Segoe UI", 10),
            fg=_fgcolor,
        ).grid(row=2, column=0, sticky=tk.W, padx=10, columnspan=2)

        tk.Label(
            self.winAdd,
            text="Completion Status -",
            bg=_bgcolor,
            font=_font,
            fg=_fgcolor,
        ).grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)

        self.completionStateAdd = ttk.Combobox(
            self.winAdd,
            values=["Due", "Completed/Past Due"],
            font=_font,
            state="readonly",
        )
        self.completionStateAdd.set("Due")
        self.completionStateAdd.grid(
            row=3, column=1, sticky=tk.W, padx=10, pady=10)

        self.insertButton = ttk.Button(
            self.winAdd, text="SUBMIT", style="my.TButton", command=self.insert
        )
        self.insertButton.grid(row=4, column=1, sticky=tk.E, padx=10, pady=40)
        
    
    '''
      This function executes the SQL query and performs the necessary actions to
      inform the user about the insertion/failure.
    '''
    def insert(self):
        
        # executes SQL Query

        try:
            self.cursor.execute(
                f'INSERT INTO TO_DO_LIST(EVENT_NAME, EVENT_DATETIME, EVENT_COMPLETED) VALUES(\'{self.eventNameAdd.get()}\', \'{self.eventDatetimeAdd.get()}\', {0 if self.completionStateAdd.get() == "Due" else 1});'
            )
        except Exception as e:
            
            # If the app runs into an error, following steps are performed
            
            print(e)
            self.changeRobotIcon("upset-border6.png")

            self.winAdd.grab_release()
            self.winAdd.destroy()

            self.speak(
                "I couldn't add the event, please check your input and try again.",
                fillInTV=False,
            )

            self.initiateShowTODOThread()

            return

        # If the insertion was successful, then the following steps are performed.
        self.winAdd.grab_release()
        self.winAdd.destroy()

        self.connection.commit()

        self.changeRobotIcon("happy-border6.png")

        self.commandEntry.insert(0, 'Try saying : "Update event"')

        self.speak(
            f"Added one event to your to-do list.",
            fillInTV=False,
        )

        self.initiateShowTODOThread()
        
    
    '''
      Changes the Robot face icon in the Applicatoin UI by using a local image.
    '''
    def changeRobotIcon(self, location="greeting-border6.png"):
        self.img = Image.open(location)
        self.img = self.img.resize((200, 220), Image.ANTIALIAS)
        self.img = ImageTk.PhotoImage(self.img)
        self.topInstance.img = self.img
        
        # adds images object to the UI
        self.img = self.canvas.create_image(
            325, 130, anchor=tk.CENTER, image=self.img)

        
    '''
      Creates a thread for the "Show to do" function and starts it.
    '''
    def initiateShowTODOThread(self):
        self.TODOThread = threading.Thread(target=self.show_to_do)
        self.TODOThread.start()
        
    
    '''
      This function is called whenever an object of the class is initialized.
      It creates a connection to the database, initializes important variables,
      creates the UI and greets the user.
    '''
    def __init__(self, top=None):

        # makes necessary connections to the database

        try:
            self.connection = connector.connect(
                host="localhost", user="root", passwd="admin", database="micro_pa"
            )

            if not self.connection.is_connected():

                print(("Unable to connect to database."))

                top.quit()

            self.cursor = self.connection.cursor()

        except:

            print(("Unable to connect to database."))

            top.quit()

        # initialises variables defined earlier

        self.topInstance = top

        self.engine = pyttsx3.init("sapi5")

        self.mixer = pygame.mixer

        self.mixer.init()

        self.voices = self.engine.getProperty("voices")

        self.vol = self.engine.getProperty("volume")

        self.engine.setProperty("voice", self.voices[1].id)

        self.setupAudioInput = True

        self.recognizer = speech_recognition.Recognizer()

        self.recognizer.pause_threshold = 0.4

        self.recognizer.non_speaking_duration = 0.4

        self.recognizer.energy_threshold = 4000

        self.microphone = speech_recognition.Microphone()

        # defines standard colors

        _bgcolor = "#d9d9d9"

        _fgcolor = "#000000"

        # sets up the themed tkinter style

        self.style = ttk.Style()

        if sys.platform == "win32":

            self.style.theme_use("vista")

        self.style.configure(".", background=_bgcolor)

        self.style.configure(".", foreground=_fgcolor)

        self.style.configure(".", font="TkDefaultFont")

        # sets up window properties

        top.minsize(650, 750)

        top.maxsize(650, 750)

        top.resizable(1, 1)

        top.title("Personal Assistant")

        root.wm_attributes("-transparentcolor", "grey")
        
        
        # creates the UI

        self.canvas = tk.Canvas(
            top, width=650, height=750, bd=0, highlightthickness=0, relief=tk.FLAT
        )

        self.canvas.pack()

        """WHENEVER YOU NEED TO ADD AN IMAGE, DO FOLLOW THE FOLLOWING 5 LINES OF CODE, VERY MUCH NECESSARY"""

        self.bgimg = Image.open("background.png")

        """RESIZE THE IMAGE AS NEEDED HERE (WIDTH, HEIGHT)"""

        self.bgimg = self.bgimg.resize((650, 750), Image.ANTIALIAS)

        self.bgimg = ImageTk.PhotoImage(self.bgimg)

        """THIS LINE ESPECIALLY IS A DEAL BREAKER, NEVER FORGET THIS OR ELSE, IMAGE WONT SHOW UP {TOP.IMAGE_VARIABLE_NAME}"""

        top.bgimg = self.bgimg

        self.bgimg = self.canvas.create_image(
            0, 0, anchor=tk.NW, image=self.bgimg)

        self.changeRobotIcon()

        self.commandText = self.canvas.create_text(
            325, 250, anchor="center", font=("Century Gothic", "18", "bold")
        )

        """ self.canvas.itemconfig(self.commandText, text="text has changed!")  -> TO CHANGE THE TEXT DURING RUNTIME, NOT MORE THAN 40 CHAR, ON THE SAME LINE"""

        self.commandEntry = ttk.Entry(
            self.canvas, width=32, font=("Arial", "16"), foreground="grey"
        )

        self.commandEntry.insert(0, 'Try saying : "Show me my to do list"')

        self.canvas.create_window(
            270, 340, anchor=tk.CENTER, window=self.commandEntry)

        self.sendImg = Image.open("sendIcon.png")

        self.sendImg = self.sendImg.resize((30, 30), Image.ANTIALIAS)

        self.sendImg = ImageTk.PhotoImage(self.sendImg)

        top.sendImg = self.sendImg

        self.enterButton = tk.Button(
            self.canvas,
            height=30,
            width=30,
            image=self.sendImg,
            bg="white",
            relief="flat",
            font=("Helvetica", 14),
            command=self.takeTextCommand,
        )

        self.canvas.create_window(
            500, 340, anchor=tk.CENTER, window=self.enterButton)

        self.micImg = Image.open("micIcon.png")

        self.micImg = self.micImg.resize((30, 30), Image.ANTIALIAS)

        self.micImg = ImageTk.PhotoImage(self.micImg)

        top.micImage = self.micImg

        self.micButton = tk.Button(
            self.canvas,
            height=30,
            width=30,
            image=self.micImg,
            bg="white",
            relief="flat",
            font=("Helvetica", 14),
            command=self.takeMicCommand,
        )

        self.canvas.create_window(
            550, 340, anchor=tk.CENTER, window=self.micButton)

        self.frame = tk.Frame(self.canvas)

        self.frame.pack(side=tk.TOP, expand=1, fill=tk.BOTH)

        self.canvas.create_window(
            325, 550, window=self.frame, anchor=tk.CENTER)

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.output = ttk.Treeview(self.frame, selectmode="none")

        self.output.column("#0", width=0, stretch=tk.NO)

        self.output.configure(columns=("#1", "#2", "#3", "#4"))

        self.output.column("#1", width=480, stretch=tk.YES)

        for i in range(2, 5):

            self.output.column(f"#{i}", width=0, stretch=tk.NO)

        self.output.pack(side="left")

        self.outputScrollbar = ttk.Scrollbar(
            self.frame, orient=tk.VERTICAL, command=self.output.yview
        )

        self.output.configure(yscrollcommand=self.outputScrollbar.set)

        self.outputScrollbar.pack(side="right", fill="y")

        
        # greets the user
        self.wishMe()

        
'''
  Main function of this python program, it creates an object of the
  PersonalAssistant class and then proceeds to initiate the top level
  Tkinter window.
'''
if __name__ == "__main__":

    root = tk.Tk()

    PersonalAssistant(root)
    root.mainloop()
