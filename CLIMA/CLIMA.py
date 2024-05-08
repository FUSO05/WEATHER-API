import openmeteo_requests
import tkinter as tk
import requests_cache
import pandas as pd
from retry_requests import retry
"""import yagmail

#Função para enviar email a user
def enviar_email():
     
    # Configurar yagmail com sua conta do Gmail
    remetente = 'trabalho.lab.clima@gmail.com'
    senha = 'VamosTirar20.'
    destinatario = 'lnluisnunes2005@gmail.com'
    assunto = 'Assunto do E-mail'
    corpo = 'Corpo do E-mail'

    # Criar um objeto yagmail
    yag = yagmail.SMTP(remetente, senha)

    #Enviar o e-mail
    yag.send(to=destinatario, subject=assunto, contents=corpo)
    
    #Fechar a conexão
    yag.close() """

#Função para slavar dados de API
def salvar_dados(dados, ficheiro):
    
    if isinstance(dados, pd.DataFrame):
        dados_str = dados.to_csv(index = False)
       
    elif isinstance(dados, str):
         dados_str = dados
         
    else:
        dados_str = str(dados) 

    with open(ficheiro, "w") as file:
        file.write(dados_str)

# Função para ir buscar os dados meteorológicos   
def buscar_dados_clima(latitude_user, longitude_user):
    
    # Configuração do cliente da API Open-Meteo com cache e tentativas de retransmissão em caso de erro
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    
    # A ordem das variáveis em horário ou diário é importante para atribuí-las corretamente abaixo
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude_user,
        "longitude":  longitude_user,
        "current": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m"],
        "daily": ["temperature_2m_max", "temperature_2m_min"]
    }
    responses = openmeteo.weather_api(url, params=params)

    # Processamento da primeira localização.               Importante----Adicionar um loop for para múltiplas localizações
    global response
    response = responses[0]
    
   
    # Função para exibir informações meteorológicas em uma janela
    def display_info_clima(frame, title, data):
            frame.config(bg="#4B0082")    
            frame.pack(padx=10, pady=10, fill="both", expand=True)
            tk.Label(frame, text=title, font=("Helvetica", 16), fg="white", bg="#4B0082").pack()  # Letra branca
            tk.Label(frame, text=data, font=("Helvetica", 12), justify="left", fg="white", bg="#4B0082").pack()  # Letra branca

    # Exibição das informações meteorológicas atuais         
    def informacao_atual():
            current_data = (
                f"Temperatura: {response.Current().Variables(0).Value()} C\n"
                f"Humidade: {response.Current().Variables(1).Value()} %\n"
                f"Chuva: {response.Current().Variables(2).Value()} mm\n"
                f"Velocidade Vento: {response.Current().Variables(3).Value()} km/h"
            )
            current_frame = tk.Frame(window)
            display_info_clima(current_frame, "Informacao Atual", current_data)
            salvar_dados(current_data, "informacao_atual")
            
                    
    # Exibição das informações meteorológicas horárias 
    def informacao_horaria():
        hourly_data = pd.DataFrame(data={
            "Temperatura": response.Hourly().Variables(0).ValuesAsNumpy(),
            "Humidade Relativa": response.Hourly().Variables(1).ValuesAsNumpy(),
            "Chuva": response.Hourly().Variables(2).ValuesAsNumpy(),
            "Velocidade Vento": response.Hourly().Variables(3).ValuesAsNumpy()
        })
        hourly_frame = tk.Frame(window)
        display_info_clima(hourly_frame, "Informacao Horaria", hourly_data)
        salvar_dados(hourly_data, "informacao_horaria")

    # Exibição das informações meteorológicas diárias       
    def informacao_diaria():
        daily_data = pd.DataFrame(data={
            "Max Temperatura": response.Daily().Variables(0).ValuesAsNumpy(),
            "Min Temperatura": response.Daily().Variables(1).ValuesAsNumpy()
        })
        daily_frame = tk.Frame(window)
        display_info_clima(daily_frame, "Informacao Diaria", daily_data)
        salvar_dados(daily_data, "informacao_diaria")
        


    # Criação da janela tkinter
    window = tk.Tk()
    window.title("Meteorologia")
    window.configure(bg="#4B0082")

    frame_botoes = tk.Frame(window, bg="#4B0082")
    frame_botoes.pack(pady=20)

    # Botões e posicionamento na janela
    botao1 = tk.Button(frame_botoes, text="Informacao atual", command=informacao_atual)
    botao1.pack(side=tk.LEFT, padx=10)

    botao2 = tk.Button(frame_botoes, text="Informacao horaria", command=informacao_horaria)
    botao2.pack(side=tk.LEFT, padx=10)

    botao3 = tk.Button(frame_botoes, text="Informacao diaria", command=informacao_diaria)
    botao3.pack(side=tk.LEFT, padx=10)
    
    
    window.mainloop()

def iniciar_interface():
    root = tk.Tk()
    root.title("METEOROLOGIA")
    root.configure(bg="#4B0082")

    def buscar_clima():
        latitude = latitude_entry.get()
        longitude = longitude_entry.get()
        buscar_dados_clima(latitude, longitude)
        root.destroy()  # Fecha a janela de entrada após buscar os dados

    latitude_label = tk.Label(root, text="Latitude:", bg="#4B0082", fg="white")
    latitude_label.pack(pady=10)
    latitude_entry = tk.Entry(root)
    latitude_entry.pack(pady=5)

    longitude_label = tk.Label(root, text="Longitude:", bg="#4B0082", fg="white")
    longitude_label.pack(pady=10)
    longitude_entry = tk.Entry(root)
    longitude_entry.pack(pady=5)

    buscar_button = tk.Button(root, text="Buscar Dados Meteorologicos", command=buscar_clima)
    buscar_button.pack(pady=20)

  

    root.mainloop()
    
# Iniciar a interface para inserir latitude e longitude
iniciar_interface()
