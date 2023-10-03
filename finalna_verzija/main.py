# Ukljucivanje potrebnih biblioteka:
import sys
import paho.mqtt.client as mqtt
import random

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QWidget
from PyQt6.QtWidgets import QProgressBar, QGridLayout, QDateTimeEdit, QToolBar, QLabel, QVBoxLayout
from PyQt6.QtWidgets import QWidget, QStatusBar, QDialog, QDialogButtonBox, QMessageBox

from PyQt6.QtCore import QCoreApplication, QEvent, QObject, QTimer, Qt
from PyQt6.QtCore import QFile, QTextStream, QDateTime

from PyQt6.QtGui import QPainter, QColor, QAction, QPalette, QImageWriter

# Konfiguracija MQTT brokera:
broker_adress = "broker.hivemq.com"
# 2 topic-a za slanje i primanje poruka:
topic1 = "siau_seminarski_berina_topic1"
topic2 = "siau_seminarski_berina_topic2"

# Sljedeca klasa sluzi za azuziranje teksta koji se treba ispisvati u prozoru,
# tj. update-a primljenu poruku:
class AzurirajTekst(QEvent):
    def __init__(self, message):
        super().__init__(QEvent.Type(QEvent.registerEventType()))
        self.message = message

# Klasa za prozor:
class MojProzor(QMainWindow):
    # Inicijalizacija:
    def __init__(self):
        super().__init__()
        self.progress_bar = QProgressBar(self)#.orientation(QtCore.Qt.Vertical)
        self.progress_bar.setOrientation(Qt.Orientation.Vertical)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setTextDirection(QProgressBar.Direction.TopToBottom)
        self.progress_bar.setStyleSheet("QProgressBar { text-align: center; }")
        self.progress_bar.setFixedSize(100, 400)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { text-align: center; }")
        self.initUI()
        self.setup_mqtt()
        self.last_received_message = ""
        self.skladistena_voda = 6367000

    def update_progress_bar(self, skladistena_voda):
        if 0 <= skladistena_voda <= 6370000:
            pomocna = int(skladistena_voda / 6370000 * 100)
            self.progress_bar.setValue(pomocna)

    # Funkcija za UI:
    def initUI(self):
        # Kreiram widget za prikazivanje poruka u prozoru:
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        # Toolbar na vrhu:
        toolbar = QToolBar("Glavni toolbar")
        self.addToolBar(toolbar)

        # Dodavanje button-a za toolbar:
        file_button1 = QAction("Spasi trenutno stanje kao sliku", self)
        file_button1.setStatusTip("Spasava trenutno stanje kao sliku")
        file_button1.triggered.connect(self.spasi_stanje)

        edit_button1 = QAction("Promijeni boju teksta u random boju", self)
        edit_button1.setStatusTip("Mijenja boju teksta u neku random boju")
        edit_button1.triggered.connect(self.promijeni_boju)

        # Dodavanje meni item-a u toolbar:
        menu = self.menuBar()

        file_menu = menu.addMenu("File")
        file_menu.addAction(file_button1)

        edit_menu = menu.addMenu("Edit")
        edit_menu.addAction(edit_button1)

        # Dodavanje vremena i datuma u app:
        self.time_label = QLabel(self)

        timer = QTimer(self)
        timer.timeout.connect(self.azuriraj_trenutno_vrijeme)
        timer.start(1000)

        self.time_label.setVisible(True)

        # Tri button-a za tri stanja:
        self.button1 = QPushButton("Promijeni na stanje 0 (akumulacija vode)", self)
        self.button2 = QPushButton("Promijeni na stanje 1 (generisanje struje)", self)
        self.button3 = QPushButton("Promijeni na stanje 2 (brzo praznjenje)", self)

        # Sta rade ti button-i:
        self.button1.clicked.connect(self.posalji_poruku1)
        self.button2.clicked.connect(self.posalji_poruku2)
        self.button3.clicked.connect(self.posalji_poruku3)

        # Inicijalno postavljanje progress bar-a:
        self.update_progress_bar(6367000)

        # Kako ce sve biti poredano na ekranu:
        layout = QGridLayout()

        layout.addWidget(self.text_edit, 0, 0, 1, 3)
        layout.addWidget(self.button1, 3, 0, 1, 1)
        layout.addWidget(self.button2, 3, 1, 1, 1)
        layout.addWidget(self.button3, 3, 2, 1, 1)
        layout.addWidget(self.progress_bar, 0, 3, 3, 3)
        layout.addWidget(self.time_label, 4, 0, 1, 3)

        # Kreiranje centralnog widget-a:
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Naslov prozora:
        self.setWindowTitle("Kontrolna soba hidroelektrane")

        # Velicina prozora:
        self.setGeometry(100, 100, 800, 700)


    def setup_mqtt(self):
        # Kreiranje MQTT klijenta:
        self.mqtt_client = mqtt.Client("Kontrolna soba")
        self.mqtt_client.on_message = self.on_mqtt_message

        # Konktovanje na broker:
        self.mqtt_client.connect(broker_adress)
        # Subscribe na topic:
        self.mqtt_client.subscribe(topic1)
        # Startanje MQTT loop-a:
        self.mqtt_client.loop_start()

    def on_mqtt_message(self, client, userdata, message):
        # Primljena poruka:
        recieved_message = message.payload.decode()

        # Zadnje primljena poruka:
        self.last_received_message = recieved_message

        # Printanje primljene poruke na konzolu:
        print(recieved_message)

        # Treba se nova poruka prikazivati u prozoru:
        QCoreApplication.postEvent(self, AzurirajTekst(recieved_message))

        # Ekstraktujemo iz poruku kolicinu vode u bazenu, radi progress bar-a:
        keyword = "Kolicina skladistene vode je:"
        indeks = recieved_message.find(keyword)

        if indeks != -1: # Ne bi ovo nikad trebalo biti
            startni = indeks + len(keyword)
            zavrsni = recieved_message.find("m^3", startni)
            if zavrsni != -1:
                podstring = recieved_message[startni : zavrsni].strip()
                skladistena_voda = float(podstring)
                self.update_progress_bar(int(skladistena_voda))
            else:
                print("Nesto nije ok!")
        else:
            print("Nesto nije ok!")

    def posalji_poruku1(self):
        self.publish_message("0", topic2)

    def posalji_poruku2(self):
        self.publish_message("1", topic2)

    def posalji_poruku3(self):
        self.publish_message("2", topic2)

    def publish_message(self, message, topic):
        self.mqtt_client.publish(topic, message)

    def customEvent(self, event):
        if isinstance(event, AzurirajTekst):
            self.text_edit.setPlainText(f"{event.message}")

    def spasi_stanje(self):
        stanje = self.grab()
        file_name = "spaseno_stanje.jpg" # Dodaj prompt za imenovanje slike
        stanje.save(file_name)

    def promijeni_boju(self):
        palette = QPalette()
        boja = QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        palette.setColor(QPalette.ColorRole.WindowText, boja)
        self.text_edit.setPalette(palette)
        self.text_edit.setStyleSheet(f"color: {boja.name()};")

    def azuriraj_trenutno_vrijeme(self):
        current_datetime = QDateTime.currentDateTime()
        self.time_label.setText(current_datetime.toString("yyyy-MM-dd hh:mm:ss"))

# main funkcija:
def main():
    # Pokretanje aplikacije:
    app = QApplication(sys.argv)

    # Dodavanje i CSS file-a:
    css_file = QFile("style.css")
    css_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
    stream = QTextStream(css_file)
    stylesheet = stream.readAll()
    app.setStyleSheet(stylesheet)

    # Kreiranje i prikazivanje prozora:
    window = MojProzor()
    window.show()

    # Kraj programa:
    sys.exit(app.exec())

# Pozivanje main-a:
if __name__ == "__main__":
    main()

