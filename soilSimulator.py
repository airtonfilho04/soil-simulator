import time
import pika
import random
import threading
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import animation

credentials = pika.PlainCredentials('login', 'password')
parameters = pika.ConnectionParameters('192.168.1.71', 5672, '/', credentials)

class irrigation:
    def __init__(self):
        self.irrigacao = False

    def ligar(self):
        self.irrigacao = True

    def desligar(self):
        self.irrigacao = False

irrigation = irrigation()

class graphDraw:
    def __init__(self):
        self.x = []
        self.y = []

    def appendX(self, value):
        self.x.append(value)

    def appendY(self, value):
        self.y.append(value)

graph = graphDraw()

class soilSimulation(threading.Thread):
    def __init__(self, idt, nome):
        threading.Thread.__init__(self)
        self.idt = idt
        self.nome = nome

    def run(self):
        print('Iniciando a Simulacao')

        credentials = pika.PlainCredentials('login', 'password')
        connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.1.71', 5672, '/', credentials))
        channel = connection.channel()

        global ini
        count = 0
        pM = 40

        df = pd.DataFrame(columns=['col1', 'col2'])

        while(True):
            if(irrigation.irrigacao):
                pM = pM - random.randint(3,5)
            else:
                pM = pM + random.randint(2,3)

            channel.queue_declare(queue='data.source', durable=True)
            channel.basic_publish(exchange='', routing_key='data.source', body=str(pM))
            ini = time.time()
            time.sleep(1)

            df.loc[count] = [count, pM]
            print(count)
            count = count + 1 

            if(count == 100):
                df.to_excel("output.xlsx")


class irrigationControl(threading.Thread):
    def __init__(self, idt, nome):
        threading.Thread.__init__(self)
        self.idt = idt
        self.nome = nome

    def run(self):
        print('Iniciando Recebimento')

        credentials = pika.PlainCredentials('login', 'password')
        connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.1.71', 5672, '/', credentials))
        channel = connection.channel()

        channel.queue_declare(queue='data.sink', durable=True)

        tempos = []
        df_tempos = pd.DataFrame(columns=['tempos'])

        def callback(ch, method, properties, body):
            body = body.decode("utf-8")
            if(body == 'Ligar'):
                irrigation.ligar()
                fim = time.time()
                tempos.append(fim - ini)
            if(body == 'Desligar'):
                irrigation.desligar()
                fim = time.time()
                tempos.append(fim - ini)
            print(tempos)
            print(' [x] Received %r' % body)
            if(len(tempos) == 30):
                for i in range(len(tempos)):
                    df_tempos.loc[i] = tempos[i]
                df_tempos.to_excel("tempos")

        channel.basic_consume(queue='data.sink', on_message_callback=callback, auto_ack=True)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()


soilSimulation1 = soilSimulation(1, 'soilSimulation1')
irrigationControl1 = irrigationControl(1, 'irrigationControl1')

arrThread = []
arrThread.append(soilSimulation1)
arrThread.append(irrigationControl1)

soilSimulation1.start()
irrigationControl1.start()

for i in arrThread:
    i.join()

