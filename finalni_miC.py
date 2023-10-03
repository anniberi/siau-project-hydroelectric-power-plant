import paho.mqtt.client as mqtt
import time

# Definiranje MQTT broker adrese i porta:
broker_address = "broker.hivemq.com"
port = 1883

# Kreiranje MQTT klijenta:
client = mqtt.Client("Mikrokontroler")

# Globalne varijable:
kapacitet = 6370000
dotok_vode = [250, -110, -3000] # Promjena vode po sekundi u stanju 0, 1, 2
skladisteno = 6367000 # U stanju 0 voda ce se napuniti do kraja za 12 sekundi
stanje = 0 # Na pocetku se puno voda

# Definiranje funkcije za primanje poruka:
def on_message(client, userdata, message):
	global stanje
	stanje = int(message.payload.decode())
	#print(f"Primljena poruka: {message.payload.decode()}")
	#print(f"Stanje je {stanje}")

# Postavljanje message handler funkcije:
client.on_message = on_message

# Konektovanje na MQTT broker:
client.connect(broker_address, port)

# Definiranje topic-a i poruke za publish-anje:
topic_za_slanje = "siau_seminarski_berina_topic1"
topic_za_primanje = "siau_seminarski_berina_topic2"

# Ovaj klijent se subscribe-a na topic za primanje poruka:
client.subscribe(topic_za_primanje)

# Zapocni loop-anje:
client.loop_start()

# Sad radimo glavni dio:
while True:
	# Koliko vode je sada skladisteno je jednako
	# prethodnom stanju skladistene vode plus
	# trenutni dodtok vode:
	skladisteno = skladisteno + dotok_vode[stanje]
	
	# Ako smo skladistili vise od ukupnog kapaciteta
	# bazena, onda postavljamo da je na maksimalnoj vrijednosti
	# skladistene vrijendosti, a stanje prebacujemo na stanje
	# brzog praznjenja - emergency praznjenje (sto je u kodu stanje 2):
	if skladisteno >= kapacitet:
		skladisteno = kapacitet
		stanje = 2
	# Ako smo u stanju 0 (stanje akumulacije vode) ili
	# u stanju 2 onda je snaga 0, a ako je u stanju 1 (stanje 
	# generisanja struje), onda je snaga proporcionalna
	# visini skladistene vode:
	if stanje == 0 or stanje == 2:
		snaga = 0
	else:
		snaga = 72 * skladisteno / kapacitet
	
	# Porukom je onda trenutno stanje, kolicina skladistene vode
	# i trenutna snaga:
	opis = ["Akumulacija vode", "Generisanje struje", "Brzo praznjenje"]
	message = f"Trenutno stanje je: {opis[stanje]}\nKolicina skladistene vode je: {skladisteno} m^{3}\nTrenutna snaga iznosi: {snaga:.2f} MW"
	
	# Objavi poruku:
	client.publish(topic_za_slanje, message)
		
	# Ponovi svake sekunde:
	time.sleep(1)

# Zaustavi loop:
client.loop_stop()
