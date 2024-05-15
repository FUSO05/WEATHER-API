import openmeteo_requests
import tkinter as tk
import requests_cache
import pandas as pd
from retry_requests import retry
import datetime
from geopy.geocoders import Nominatim

#Função para salvar dados de API
def salvar_dados(dados, ficheiro):
    
    if isinstance(dados, pd.DataFrame):
        dados_str = dados.to_csv(index = False)
       
    elif isinstance(dados, str):
         dados_str = dados
         
    else:
        dados_str = str(dados) 

    with open(ficheiro, "w") as file:
        file.write(dados_str)


def city_to_coordinates(city_name):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(city_name)
    if location:
        return location.latitude, location.longitude
    else:
        print(f"Coordinates for '{city_name}' not found.")
        return None, None


def display_info_clima(frame, title, data):
        frame.config(bg="#4B0082")    
        frame.pack(padx=10, pady=10, fill="both", expand=True)
        tk.Label(frame, text=title, font=("Helvetica", 16), fg="white", bg="#4B0082").pack()  # Letra branca
        tk.Label(frame, text=data, font=("Helvetica", 12), justify="left", fg="white", bg="#4B0082").pack()  # Letra branca

# Função para ir buscar os dados meteorológicos   
def buscar_dados_historicos(city_nameh, start_dateh, end_dateh):
    
    latitude_userh, longitude_userh = city_to_coordinates(city_nameh)
    if latitude_userh is None or longitude_userh is None:
        return  # Exit function if coordinates not found

    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
	"latitude": latitude_userh,
	"longitude": longitude_userh,
	"start_date": start_dateh,
	"end_date": end_dateh,
	"hourly": ["temperature_2m", "relative_humidity_2m"]
}   
    responses = openmeteo.weather_api(url, params=params)

    global response
    response = responses[0]
   
    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
	    start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
	    end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
	    freq = pd.Timedelta(seconds = hourly.Interval()),
	    inclusive = "left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m

    # Criação da janela tkinter
    window = tk.Tk()
    window.title("Meteorologia")
    window.configure(bg="#4B0082")
    current_frame = tk.Frame(window)
    display_info_clima(current_frame, "Informacao Atual", hourly_data)
    salvar_dados(hourly_data, "Informacao_historica")
        
def buscar_dados_clima(city_name, start_hour, end_hour):
    
    latitude_user, longitude_user = city_to_coordinates(city_name)
    if latitude_user is None or longitude_user is None:
        return  # Exit function if coordinates not found

    # Configuração do cliente da API Open-Meteo com cache e tentativas de retransmissão em caso de erro
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    
    start_time = datetime.datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0).isoformat()
    end_time = datetime.datetime.now().replace(hour=end_hour, minute=0, second=0, microsecond=0).isoformat()


    # A ordem das variáveis em horário ou diário é importante para atribuí-las corretamente abaixo
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude_user,
        "longitude":  longitude_user,
        "current": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m"],
        "daily": ["temperature_2m_max", "temperature_2m_min"],
        "start_hour": start_time,
        "end_hour": end_time
    }
    responses = openmeteo.weather_api(url, params=params)

    # Processamento da primeira localização.               Importante----Adicionar um loop for para múltiplas localizações
    global response
    response = responses[0]
    
   
    

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
        city_name = cidade_entry.get()
        hora_inicial = int(hora_inicial_entry.get())
        hora_final = int(hora_final_entry.get())

        buscar_dados_clima(city_name, hora_inicial, hora_final)

    def buscar_historicos():
        city_nameh = cidadeh_entry.get()
        start_dateh = start_dateh_entry.get()
        end_dateh = end_dateh_entry.get()

        buscar_dados_historicos(city_nameh, start_dateh, end_dateh)
        
    
    # Widgets para entrada de dados
    cidade_label = tk.Label(root, text="Cidade:", bg="#4B0082", fg="white")
    cidade_label.pack(pady=10)
    cidade_entry = tk.Entry(root)
    cidade_entry.pack(pady=5)

    hora_inicial_label = tk.Label(root, text="Hora Inicial (0-23):", bg="#4B0082", fg="white")
    hora_inicial_label.pack(pady=10)
    hora_inicial_entry = tk.Entry(root)
    hora_inicial_entry.pack(pady=5)

    hora_final_label = tk.Label(root, text="Hora Final (0-23):", bg="#4B0082", fg="white")
    hora_final_label.pack(pady=10)
    hora_final_entry = tk.Entry(root)
    hora_final_entry.pack(pady=5)

    # Botões para acionar as buscas
    buscar_button_clima = tk.Button(root, text="Buscar Dados Meteorologicos", command=buscar_clima)
    buscar_button_clima.pack(pady=10)

    # Widgets para entrada de dados históricos
    cidadeh_label = tk.Label(root, text="Cidade historica:", bg="#4B0082", fg="white")
    cidadeh_label.pack(pady=10)
    cidadeh_entry = tk.Entry(root)
    cidadeh_entry.pack(pady=5)

    horah_inicial_label = tk.Label(root, text="Data Inicial historica (yy-mm-dd):", bg="#4B0082", fg="white")
    horah_inicial_label.pack(pady=10)
    start_dateh_entry = tk.Entry(root)
    start_dateh_entry.pack(pady=5)

    horah_final_label = tk.Label(root, text="Data Final historica (yy-mm-dd):", bg="#4B0082", fg="white")
    horah_final_label.pack(pady=10)
    end_dateh_entry = tk.Entry(root)
    end_dateh_entry.pack(pady=5)

    buscar_button_hist = tk.Button(root, text="Buscar Dados Meteorologicos Historicos", command=buscar_historicos)
    buscar_button_hist.pack(pady=20)


    root.mainloop()

    
# Iniciar a interface para inserir latitude e longitude
iniciar_interface()
