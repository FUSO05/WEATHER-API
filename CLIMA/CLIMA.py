import openmeteo_requests
import tkinter as tk
import requests_cache
import pandas as pd
from retry_requests import retry
import datetime
from geopy.geocoders import Nominatim
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Funcao ler pass de um ficheiro
def get_password_from_file(file):
    try:
        with open('api-pass.txt', 'r') as file:
            password = file.read().strip()
            return password
    except Exception as e:
        print(f"Erro ao ler o ficheiro: {str(e)}")
        return None


# Funcao para salvar dados de API
def salvar_dados(dados, ficheiro):
    if isinstance(dados, pd.DataFrame):
        dados_str = dados.to_csv(index=False)
    elif isinstance(dados, str):
        dados_str = dados
    else:
        dados_str = str(dados)

    with open(ficheiro, "w") as file:
        file.write(dados_str)


# Enviar email
def send_email():
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'trabalho.lab.clima@gmail.com'
    to_address = 'trabalho.lab.clima@gmail.com'
    sender_password = get_password_from_file('api-pass.txt')
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_address
    msg['Subject'] = 'Alerta'
    html_message = 'Tenha cuidado'
    msg.attach(MIMEText(html_message, 'html'))
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_address, msg.as_string())
        print('Email enviado com sucesso!')
        return True
    except Exception as e:
        print('Erro ao enviar email:', str(e))
        return False
    finally:
        server.quit()


# Inserir cidade e transformar em coordenadas
def city_to_coordinates(city_name):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(city_name)
    if location:
        return location.latitude, location.longitude
    else:
        print(f"Coordenadas para '{city_name}' nao encontradas.")
        return None, None


# Fazer o display das informacoes
def display_info_clima(frame, title, data):
    frame.config(bg="#4B0082")
    frame.pack(padx=10, pady=10, fill="both", expand=True)
    tk.Label(frame, text=title, font=("Helvetica", 16), fg="white", bg="#4B0082").pack()
    tk.Label(frame, text=data, font=("Helvetica", 12), justify="left", fg="white", bg="#4B0082").pack()


# Analisar variaçao de temperatura
def identificar_variacoes_temperatura(dados):
   
     # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Identificar variações abruptas na temperatura
    max_diff = 0
    max_diff_date = None
    for indice, linha in dados.iterrows():
        temperatura_atual = linha['Temperatura (C)']
        temperatura_anterior = dados.iloc[indice - 1]['Temperatura (C)'] if indice > 0 else None
        if temperatura_anterior is not None:
            diff = abs(temperatura_atual - temperatura_anterior)
            if diff > max_diff:
                max_diff = diff
                max_diff_date = linha['Data']
                print(f"Nova diferenca maxima encontrada: {max_diff} , de {temperatura_atual} para {temperatura_anterior}| data: {max_diff_date}")
    return max_diff, max_diff_date


# Analisar variaçao de humidade
def identificar_mudancas_humidade(dados):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Identificar variações abruptas na humidade
    max_diff = 0
    max_diff_date = None
    for indice, linha in dados.iterrows():
        humidade_atual = linha['Humidade Relativa (%)']
        humidade_anterior = dados.iloc[indice - 1]['Humidade Relativa (%)'] if indice > 0 else None
        if humidade_anterior is not None:
            diff = abs(humidade_atual - humidade_anterior)
            if diff > max_diff and diff > 10:  # Ajuste o valor do limiar conforme necessário
                max_diff = diff
                max_diff_date = linha['Data']
                print(f"Variacao abrupta na humidade em {linha['Data']}: {humidade_anterior} -> {humidade_atual}")
    return max_diff, max_diff_date


# Analisar variaçao de chuva
def identificar_aumento_chuva(dados):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Identificar variações abruptas na chuva
    max_diff = 0
    max_diff_date = None
    for indice, linha in dados.iterrows():
        chuva_atual = linha['Chuva (mm)']
        chuva_anterior = dados.iloc[indice - 1]['Chuva (mm)'] if indice > 0 else None
        if chuva_anterior is not None:
            diff = abs(chuva_atual - chuva_anterior)
            if diff > max_diff and diff > 5:  # Ajuste o valor do limiar conforme necessário
                max_diff = diff
                max_diff_date = linha['Data']
                print(f"Variacao abrupta na chuva em {linha['Data']}: {chuva_anterior} -> {chuva_atual}")
    return max_diff, max_diff_date


# Analisar variaçao de velocidade de vento
def identificar_aumento_velocidade_vento(dados):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Identificar variações abruptas na velocidade do vento
    max_diff = 0
    max_diff_date = None
    for indice, linha in dados.iterrows():
        vento_atual = linha['Velocidade do Vento (km/h)']
        vento_anterior = dados.iloc[indice - 1]['Velocidade do Vento (km/h)'] if indice > 0 else None
        if vento_anterior is not None:
            diff = abs(vento_atual - vento_anterior)
            if diff > max_diff and diff > 10:  # Ajuste o valor do limiar conforme necessário
                max_diff = diff
                max_diff_date = linha['Data']
                print(f"Variacao abrupta na velocidade do vento em {linha['Data']}: {vento_anterior} -> {vento_atual}")
    return max_diff, max_diff_date


# Funcao para buscar os dados meteorologicos historicos
def buscar_dados_historicos(city_nameh, start_dateh, end_dateh):
    latitude_userh, longitude_userh = city_to_coordinates(city_nameh)
    if latitude_userh is None or longitude_userh is None:
        return  # Sair da funcao se as coordenadas nao forem encontradas

    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude_userh,
        "longitude": longitude_userh,
        "start_date": start_dateh,
        "end_date": end_dateh,
        "hourly": ["temperature_2m", "relative_humidity_2m"]
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "temperature_2m": hourly_temperature_2m,
        "relative_humidity_2m": hourly_relative_humidity_2m
    }

    window = tk.Tk()
    window.title("Meteorologia")
    window.configure(bg="#4B0082")
    current_frame = tk.Frame(window)
    display_info_clima(current_frame, "Informacao Historica", hourly_data)
    salvar_dados(hourly_data, "informacao_historica.txt")
    window.mainloop()


# Funcao para buscar dados meteorologicos
def buscar_dados_clima(city_name, start_hour, end_hour):
    latitude_user, longitude_user = city_to_coordinates(city_name)
    if latitude_user is None or longitude_user is None:
        return None  # Sair da funcao se as coordenadas nao forem encontradas

    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    start_time = datetime.datetime.now().replace(hour=start_hour, minute=0, second=0, microsecond=0).isoformat()
    end_time = datetime.datetime.now().replace(hour=end_hour, minute=0, second=0, microsecond=0).isoformat()

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude_user,
        "longitude": longitude_user,
        "current": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m"],
        "daily": ["temperature_2m_max", "temperature_2m_min"],
        "start_hour": start_time,
        "end_hour": end_time
    }
    responses = openmeteo.weather_api(url, params=params)
    return responses[0]


#Função para recolher dados de 30 dias
def get_30days(response, output_file):
    
   # Obtendo as coordenadas da cidade fornecida pelo usuário
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(response)
    if location is None:
        print(f"Coordenadas para '{response}' nao encontradas.")
        return

    latitude, longitude = location.latitude, location.longitude

    # Definindo as datas para 30 dias atrás e hoje
    data_atual = datetime.date.today()
    data_30_dias_atras = data_atual - datetime.timedelta(days=30)

    # Configurando a sessão para cache e tentativas de retransmissão
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Criando uma lista para armazenar os dados
    dados_30_dias = []

    # Obtendo os dados meteorológicos para os últimos 30 dias
    for i in range(30):
        data_inicio = (data_30_dias_atras + datetime.timedelta(days=i)).isoformat()
        data_fim = (data_30_dias_atras + datetime.timedelta(days=i+1)).isoformat()

        # Fazendo a chamada à API para os dados do dia
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m"],
            "start_hour": data_inicio,
            "end_hour": data_fim
        }
        response = openmeteo.weather_api(url, params=params)
        if not response:
            continue

        # Extraindo os valores relevantes dos dados de resposta
        current_data = response[0].Current()
        temperature = current_data.Variables(0).Value()
        humidity = current_data.Variables(1).Value()
        rain = current_data.Variables(2).Value()
        wind_speed = current_data.Variables(3).Value()

        # Salvando os valores em um dicionário
        dados_dia = {
            "Data": data_inicio,
            "Temperatura (C)": temperature,
            "Humidade Relativa (%)": humidity,
            "Chuva (mm)": rain,
            "Velocidade do Vento (km/h)": wind_speed
        }
        dados_30_dias.append(dados_dia)

    # Convertendo os dados para DataFrame do Pandas
    df = pd.DataFrame(dados_30_dias)

    # Salvando os dados em um arquivo CSV
    df.to_csv(output_file, index=False)
    

# Funcao para exibir informacoes atuais
def informacao_atual(response, window):
    
    temperatura_atual = response.Current().Variables(0).Value()
    humidade_atual = response.Current().Variables(1).Value()
    chuva_atual = response.Current().Variables(2).Value()
    vento_atual = response.Current().Variables(3).Value()


    current_data = (
        f"Temperatura: {response.Current().Variables(0).Value()} C\n"
        f"Humidade: {response.Current().Variables(1).Value()} %\n"
        f"Chuva: {response.Current().Variables(2).Value()} mm\n"
        f"Velocidade Vento: {response.Current().Variables(3).Value()} km/h"
    )
    current_frame = tk.Frame(window)
    
    display_info_clima(current_frame, "Informacao Atual", current_data)
    salvar_dados(current_data, "informacao_atual.txt")
    
    return temperatura_atual, humidade_atual, chuva_atual, vento_atual
    

# Funcao para exibir informacoes horarias
def informacao_horaria(response, window):
    hourly_data = pd.DataFrame(data={
        "Temperatura": response.Hourly().Variables(0).ValuesAsNumpy(),
        "Humidade Relativa": response.Hourly().Variables(1).ValuesAsNumpy(),
        "Chuva": response.Hourly().Variables(2).ValuesAsNumpy(),
        "Velocidade Vento": response.Hourly().Variables(3).ValuesAsNumpy()
    })
    hourly_frame = tk.Frame(window)
    display_info_clima(hourly_frame, "Informacao Horaria", hourly_data)
    salvar_dados(hourly_data, "informacao_horaria.txt")


# Funcao para exibir informacoes diarias
def informacao_diaria(response, window):
    daily_data = pd.DataFrame(data={
        "Max Temperatura": response.Daily().Variables(0).ValuesAsNumpy(),
        "Min Temperatura": response.Daily().Variables(1).ValuesAsNumpy()
    })
    daily_frame = tk.Frame(window)
    display_info_clima(daily_frame, "Informacao Diaria", daily_data)
    salvar_dados(daily_data, "informacao_diaria.txt")


# Funcao para inicializar a interface
def iniciar_interface():
    root = tk.Tk()
    root.title("METEOROLOGIA")
    root.configure(bg="#4B0082")

 
    def buscar_clima():
        city_name = cidade_entry.get()
        hora_inicial = int(hora_inicial_entry.get())
        hora_final = int(hora_final_entry.get())
       
        response = buscar_dados_clima(city_name, hora_inicial, hora_final)
        if response:
            window = tk.Tk()
            window.title("Meteorologia - Dados")
            window.configure(bg="#4B0082")

            frame_botoes = tk.Frame(window, bg="#4B0082")
            frame_botoes.pack(pady=20)

            botao1 = tk.Button(frame_botoes, text="Informacao Atual", command=lambda: informacao_atual(response, window))
            botao1.pack(side=tk.LEFT, padx=10)

            botao2 = tk.Button(frame_botoes, text="Informacao Horaria", command=lambda: informacao_horaria(response, window))
            botao2.pack(side=tk.LEFT, padx=10)

            botao3 = tk.Button(frame_botoes, text="Informacao Diaria", command=lambda: informacao_diaria(response, window))
            botao3.pack(side=tk.LEFT, padx=10)

            window.mainloop() 
        get_30days(city_name, "Informacao_30dias.txt")
        identificar_variacoes_temperatura("Informacao_30dias.txt")
        identificar_mudancas_humidade("Informacao_30dias.txt")
        identificar_aumento_chuva("Informacao_30dias.txt")
        identificar_aumento_velocidade_vento("Informacao_30dias.txt")

    def buscar_historicos():
        city_nameh = cidadeh_entry.get()
        start_dateh = start_dateh_entry.get()
        end_dateh = end_dateh_entry.get()

        buscar_dados_historicos(city_nameh, start_dateh, end_dateh)

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

    buscar_button_clima = tk.Button(root, text="Buscar Dados Meteorologicos", command=buscar_clima)
    buscar_button_clima.pack(pady=10)

    cidadeh_label = tk.Label(root, text="Cidade Historica:", bg="#4B0082", fg="white")
    cidadeh_label.pack(pady=10)
    cidadeh_entry = tk.Entry(root)
    cidadeh_entry.pack(pady=5)

    horah_inicial_label = tk.Label(root, text="Data Inicial Historica (yyyy-mm-dd):", bg="#4B0082", fg="white")
    horah_inicial_label.pack(pady=10)
    start_dateh_entry = tk.Entry(root)
    start_dateh_entry.pack(pady=5)

    horah_final_label = tk.Label(root, text="Data Final Historica (yyyy-mm-dd):", bg="#4B0082", fg="white")
    horah_final_label.pack(pady=10)
    end_dateh_entry = tk.Entry(root)
    end_dateh_entry.pack(pady=5)

    buscar_button_hist = tk.Button(root, text="Buscar Dados Meteorologicos Historicos", command=buscar_historicos)
    buscar_button_hist.pack(pady=20)

    root.mainloop()

    send_email()


iniciar_interface()
