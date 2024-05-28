import openmeteo_requests
import seaborn as sns
import numpy as np
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import requests_cache
import pandas as pd
from retry_requests import retry
import datetime
from geopy.geocoders import Nominatim
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import folium
from folium.plugins import MarkerCluster

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
def send_email(email_user, mensagem):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'trabalho.lab.clima@gmail.com'
    to_address = email_user
    sender_password = get_password_from_file('api-pass.txt')
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email_user
    msg['Subject'] = 'Alerta Condicoes Climaticas'
    html_message = mensagem
    msg.attach(MIMEText(html_message, 'html'))
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email_user, msg.as_string())
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
        messagebox.showinfo("Aviso", "Por favor, insira o nome da cidade.")

# Adicionar mensagem
def add_message(popup_window, message):
    if popup_window is None:
        popup_window = ctk.CTkToplevel(root)
    ctk.CTkLabel(popup_window, text=message).pack()
    
popup_window = None

# Criar janela de pop-up
def create_popup_window(master):
    popup = ctk.CTkToplevel(master)
    popup.title("Eventos")
    
    scrollbar = ctk.CTkScrollbar(popup)
    scrollbar.pack(side="right", fill="y")

    text = ctk.CTkText(popup, wrap="word", yscrollcommand=scrollbar.set)
    text.pack(expand=True, fill="both")

    scrollbar.config(command=text.yview)

    return popup, text

def exibir_graficos_horarios(frame):
    df = pd.read_csv("informacao_horaria.txt")
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    df.set_index('Datetime', inplace=True)

    # Gráfico de Temperatura
    fig_temperatura, ax_temp = plt.subplots(figsize=(8, 4))
    ax_temp.plot(df.index, df['Temperatura (C)'], label='Temperatura (C)', color='red')
    ax_temp.set_title('Temperatura em Funcao do Tempo')
    ax_temp.set_xlabel('Tempo')
    ax_temp.set_ylabel('Temperatura (C)')
    ax_temp.grid(True)
    ax_temp.legend()
    ax_temp.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.setp(ax_temp.get_xticklabels(), rotation=20, ha='right', fontsize=10)

    canvas_temp = FigureCanvasTkAgg(fig_temperatura, master=frame)
    canvas_temp.draw()
    canvas_temp.get_tk_widget().grid(row=1, column=0, padx=10, pady=5, sticky='nsew')

    # Gráfico de Humidade
    fig_humidade, ax_hum = plt.subplots(figsize=(8, 4))
    ax_hum.plot(df.index, df['Humidade Relativa (%)'], label='Humidade Relativa (%)', color='blue')
    ax_hum.set_title('Humidade Relativa em Funcao do Tempo')
    ax_hum.set_xlabel('Tempo')
    ax_hum.set_ylabel('Humidade Relativa (%)')
    ax_hum.grid(True)
    ax_hum.legend()
    ax_hum.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.setp(ax_hum.get_xticklabels(), rotation=20, ha='right', fontsize=10)

    canvas_hum = FigureCanvasTkAgg(fig_humidade, master=frame)
    canvas_hum.draw()
    canvas_hum.get_tk_widget().grid(row=1, column=1, padx=10, pady=5, sticky='nsew')

    frame.grid_rowconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    
    

def identificar_variacoes_temperatura(dados, popup_window):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Calcular a derivada da temperatura em relação ao tempo
    tempo = np.arange(len(dados))  # Usar índices como tempo
    temperatura = dados['Temperatura (C)'].to_numpy()
    derivada_temperatura = np.gradient(temperatura, tempo)

    # Identificar mudanças abruptas na derivada da temperatura
    max_diff_aumento = 0
    max_diff_queda = 0
    max_diff_date_aumento = None
    max_diff_date_queda = None
    for indice, derivada in enumerate(derivada_temperatura):
        if derivada > 3:  # Threshold para aumento abrupto
            max_diff_aumento = derivada
            max_diff_date_aumento = dados.iloc[indice]['Data']
            message = f"Aumento abrupto na derivada da temperatura em {dados.iloc[indice]['Data']} | {dados.iloc[indice]['Hora']}: {max_diff_aumento}"
            add_message(popup_window, message)
        elif derivada < -3:  # Threshold para queda abrupta
            max_diff_queda = derivada
            max_diff_date_queda = dados.iloc[indice]['Data']
            message = f"Queda abrupta na derivada da temperatura em {dados.iloc[indice]['Data']} | {dados.iloc[indice]['Hora']}: {max_diff_queda}"
            add_message(popup_window, message)

    return (max_diff_aumento, max_diff_date_aumento), (max_diff_queda, max_diff_date_queda)


# Função para identificar variações abruptas na humidade
def identificar_mudancas_humidade(dados, popup_window):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Calcular a derivada da umidade em relação ao tempo
    tempo = np.arange(len(dados))  # Usar índices como tempo
    humidade = dados['Humidade Relativa (%)'].to_numpy()
    derivada_umidade = np.gradient(humidade, tempo)

    # Identificar mudanças abruptas na derivada da umidade
    max_diff_aumento = 0
    max_diff_queda = 0
    max_diff_date_aumento = None
    max_diff_date_queda = None
    for indice, derivada in enumerate(derivada_umidade):
        if derivada > 15:  # Threshold para aumento abrupto
            max_diff_aumento = derivada
            max_diff_date_aumento = dados.iloc[indice]['Data']
            message = f"Aumento abrupto na derivada da humidade em {dados.iloc[indice]['Data']} | {dados.iloc[indice]['Hora']}: {max_diff_aumento}"
            add_message(popup_window, message)
        elif derivada < -15:  # Threshold para queda abrupta
            max_diff_queda = derivada
            max_diff_date_queda = dados.iloc[indice]['Data']
            message = f"Queda abrupta na derivada da humidade em {dados.iloc[indice]['Data']} | {dados.iloc[indice]['Hora']}: {max_diff_queda}"
            add_message(popup_window, message)

    return (max_diff_aumento, max_diff_date_aumento), (max_diff_queda, max_diff_date_queda)



# Função para identificar variações abruptas na quantidade de chuva
def identificar_aumento_chuva(dados, popup_window):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Calcular a derivada da quantidade de chuva em relação ao tempo
    tempo = np.arange(len(dados))  # Usar índices como tempo
    chuva = dados['Chuva (mm)'].to_numpy()
    derivada_chuva = np.gradient(chuva, tempo)

    # Identificar mudanças abruptas na derivada da quantidade de chuva
    max_diff_aumento = 0
    max_diff_queda = 0
    max_diff_date_aumento = None
    max_diff_date_queda = None
    for indice, derivada in enumerate(derivada_chuva):
        if derivada > 1.5:  # Threshold para aumento abrupto
            max_diff_aumento = derivada
            max_diff_date_aumento = dados.iloc[indice]['Data']
            message = f"Aumento abrupto na derivada da quantidade de chuva em {dados.iloc[indice]['Data']} | {dados.iloc[indice]['Hora']}: {max_diff_aumento}"
            add_message(popup_window, message)
        elif derivada < -1.5:  # Threshold para queda abrupta
            max_diff_queda = derivada
            max_diff_date_queda = dados.iloc[indice]['Data']
            message = f"Queda abrupta na derivada da quantidade de chuva em {dados.iloc[indice]['Data']} | {dados.iloc[indice]['Hora']}: {max_diff_queda}"
            add_message(popup_window, message)

    return (max_diff_aumento, max_diff_date_aumento), (max_diff_queda, max_diff_date_queda)



# Função para identificar variações abruptas na velocidade do vento
def identificar_aumento_velocidade_vento(dados, popup_window):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Calcular a derivada da velocidade do vento em relação ao tempo
    tempo = np.arange(len(dados))  # Usar índices como tempo
    velocidade_vento = dados['Velocidade do Vento (km/h)'].to_numpy()
    derivada_velocidade_vento = np.gradient(velocidade_vento, tempo)

    # Identificar mudanças abruptas na derivada da velocidade do vento
    max_diff_aumento = 0
    max_diff_queda = 0
    max_diff_date_aumento = None
    max_diff_date_queda = None
    for indice, derivada in enumerate(derivada_velocidade_vento):
        if derivada > 10:  # Threshold para aumento abrupto
            max_diff_aumento = derivada
            max_diff_date_aumento = dados.iloc[indice]['Data']
            message = f"Aumento abrupto na derivada da velocidade do vento em {dados.iloc[indice]['Data']} | {dados.iloc[indice]['Hora']}: {max_diff_aumento}"
            add_message(popup_window, message)
        elif derivada < -10:  # Threshold para queda abrupta
            max_diff_queda = derivada
            max_diff_date_queda = dados.iloc[indice]['Data']
            message = f"Queda abrupta na derivada da velocidade do vento em {dados.iloc[indice]['Data']} | {dados.iloc[indice]['Hora']}: {max_diff_queda}"
            add_message(popup_window, message)

    return (max_diff_aumento, max_diff_date_aumento), (max_diff_queda, max_diff_date_queda)




# Função para identificar condições propícias para furacões ou tornados
def identificar_condicoes_furacoes_tornados(dados, popup_window):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Identificar condições propícias para furacões ou tornados
    furacoes_tornados = []
    for _, linha in dados.iterrows():
        vento_atual = linha['Velocidade do Vento (km/h)']
        if vento_atual > 100:  # Limiar para identificar condições propícias para furacões ou tornados
            furacoes_tornados.append((linha['Data'], linha['Hora'], vento_atual))
            message = f"Condicoes propicias para furacoes ou tornados encontradas em {linha['Data']} {linha['Hora']}: Velocidade do Vento {vento_atual} km/h"
            add_message(popup_window, message)
            send_email(email_user, 'Alerta-se todos os habitantes que se mantenham em casa. Alto risco de Furacao/Tornado.')
    return furacoes_tornados


# Função para identificar condições propícias para inundações
def identificar_condicoes_inundacoes(dados, popup_window):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Identificar condições propícias para inundações
    inundacoes = []
    for _, linha in dados.iterrows():
        chuva_atual = linha['Chuva (mm)']
        if chuva_atual > 5:  # Limiar para identificar condições propícias para inundações
            inundacoes.append((linha['Data'], linha['Hora'], chuva_atual))
            message = f"Condicoes propicias para inundacoes encontradas em {linha['Data']}: Quantidade de Chuva {chuva_atual} mm"
            add_message(popup_window, message)
            send_email(email_user, 'Alerta-se todos os habitantes que se mantenham fora de zonas litorais, e ficar em casa. Alto risco de Inundacao.')
    return inundacoes


# Funcao para buscar os dados meteorologicos historicos
def buscar_dados_historicos(city_nameh, start_dateh, end_dateh):
    latitude_userh, longitude_userh = city_to_coordinates(city_nameh)
    if latitude_userh is None or longitude_userh is None:
        print(f"Coordenadas para '{city_nameh}' nao encontradas.")
        return  # Sair da função se as coordenadas não forem encontradas

    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude_userh,
        "longitude": longitude_userh,
        "start_date": start_dateh,
        "end_date": end_dateh,
        "hourly": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m"]
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_rain = hourly.Variables(2).ValuesAsNumpy()
    hourly_wind_speed = hourly.Variables(3).ValuesAsNumpy()

    # Criar uma faixa de datas e horas
    hourly_times = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        periods=len(hourly_temperature_2m),
        freq=pd.Timedelta(seconds=hourly.Interval())
    )

    # Estruturar os dados em um DataFrame do Pandas
    df = pd.DataFrame({
        "Data": hourly_times.date,
        "Hora": hourly_times.time,
        "Temperatura (C)": hourly_temperature_2m,
        "Humidade Relativa (%)": hourly_relative_humidity_2m,
        "Chuva (mm)": hourly_rain,
        "Velocidade do Vento (km/h)": hourly_wind_speed
    })

    # Salvar os dados em um arquivo CSV
    df.to_csv("informacao_historica.txt", index=False)

    # Exibir os dados na interface gráfica
    window = tk.Toplevel(root)
    window.title("Dados Historicos")

    frame = ttk.Frame(window)
    frame.pack(expand=True, fill='both')

    # Adicionar Treeview para mostrar os dados
    tree = ttk.Treeview(frame, columns=list(df.columns), show="headings")
    for column in df.columns:
        tree.heading(column, text=column, anchor='center')
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))
    tree.pack(expand=True, fill='both')

    # Adicionar Canvas para os gráficos
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))
    fig.suptitle('Dados Meteorologicos Historicos')

    ax_temp = axs[0, 0]
    ax_temp.plot(hourly_times, hourly_temperature_2m, label='Temperatura (C)', color='red')
    ax_temp.set_title('Temperatura em Funcao do Tempo')
    ax_temp.set_ylabel('Temperatura (C)')
    ax_temp.grid(True)
    ax_temp.legend()
    ax_temp.tick_params(axis='both', which='both', labelsize=8)

    ax_hum = axs[0, 1]
    ax_hum.plot(hourly_times, hourly_relative_humidity_2m, label='Humidade Relativa (%)', color='blue')
    ax_hum.set_title('Humidade Relativa em Funcao do Tempo')
    ax_hum.set_ylabel('Humidade Relativa (%)')
    ax_hum.grid(True)
    ax_hum.legend()
    ax_hum.tick_params(axis='both', which='both', labelsize=8)

    ax_rain = axs[1, 0]
    ax_rain.plot(hourly_times, hourly_rain, label='Chuva (mm)', color='green')
    ax_rain.set_title('Chuva em Funcao do Tempo')
    ax_rain.set_ylabel('Chuva (mm)')
    ax_rain.grid(True)
    ax_rain.legend()
    ax_rain.tick_params(axis='both', which='both', labelsize=8)

    ax_wind = axs[1, 1]
    ax_wind.plot(hourly_times, hourly_wind_speed, label='Velocidade do Vento (km/h)', color='orange')
    ax_wind.set_title('Velocidade do Vento em Funcao do Tempo')
    ax_wind.set_xlabel('Tempo')
    ax_wind.set_ylabel('Velocidade do Vento (km/h)')
    ax_wind.grid(True)
    ax_wind.legend()

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(expand=True, fill='both')

    # Adicionar botão "Sair" diretamente à janela principal
    btn_voltar = ttk.Button(window, text="Sair", command=lambda: [window.destroy(), root.deiconify()])
    btn_voltar.pack(pady=10)

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

    # Configurando a sessão para cache e tentativas de retransmissão
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Definindo as datas para 30 dias atrás e hoje
    data_atual = datetime.date.today()
    data_30_dias_atras = data_atual - datetime.timedelta(days=30)

    dados_30_dias = []

    # Fazendo a chamada à API para os dados do dia
    url = "https://api.open-meteo.com/v1/forecast"
    for i in range(30):
        data_consulta = data_30_dias_atras + datetime.timedelta(days=i)
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m"],
            "start_date": data_consulta,
            "end_date": data_consulta
        }
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]   
        
        # Extraindo os valores relevantes dos dados de resposta
        Temperatura = response.Hourly().Variables(0).ValuesAsNumpy()
        Humidade_Relativa = response.Hourly().Variables(1).ValuesAsNumpy()
        Chuva = response.Hourly().Variables(2).ValuesAsNumpy()
        Velocidade_Vento = response.Hourly().Variables(3).ValuesAsNumpy()

        # Iterando sobre os valores de cada hora do dia
        for j in range(len(Temperatura)):
            # Organizando os dados da hora no formato desejado
            dado_hora = {
                "Data": data_consulta.isoformat(),
                "Hora": f"{j:02d}:00",  # Formato HH:00
                "Temperatura (C)": Temperatura[j],
                "Humidade Relativa (%)": Humidade_Relativa[j],
                "Chuva (mm)": Chuva[j],
                "Velocidade do Vento (km/h)": Velocidade_Vento[j]
            }
            dados_30_dias.append(dado_hora)

    # Convertendo os dados para DataFrame do Pandas
    df = pd.DataFrame(dados_30_dias)

    # Salvando os dados em um arquivo CSV
    df.to_csv(output_file, index=False)
    

# Funçao para recolher dados de 16 dias futuros
def get_15days_futuro(response, output_file):
    # Obtendo as coordenadas da cidade fornecida pelo usuário
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(response)
    if location is None:
        print(f"Coordenadas para '{response}' nao encontradas.")
        return

    latitude, longitude = location.latitude, location.longitude

    # Configurando a sessão para cache e tentativas de retransmissão
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Definindo a data atual e a data para 15 dias no futuro
    data_atual = datetime.date.today()

    dados_15_dias = []

    # Fazendo a chamada à API para os dados de previsão
    url = "https://api.open-meteo.com/v1/forecast"
    for i in range(15):
        data_consulta = data_atual + datetime.timedelta(days=i)
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ["temperature_2m", "relative_humidity_2m", "rain", "wind_speed_10m"],
            "start_date": data_consulta,
            "end_date": data_consulta
        }
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        # Extraindo os valores relevantes dos dados de resposta
        Temperatura = response.Hourly().Variables(0).ValuesAsNumpy()
        Humidade_Relativa = response.Hourly().Variables(1).ValuesAsNumpy()
        Chuva = response.Hourly().Variables(2).ValuesAsNumpy()
        Velocidade_Vento = response.Hourly().Variables(3).ValuesAsNumpy()

        # Iterando sobre os valores de cada hora do dia
        for j in range(len(Temperatura)):
            # Organizando os dados da hora no formato desejado
            dado_hora = {
                "Data": data_consulta.isoformat(),
                "Hora": f"{j:02d}:00",  # Formato HH:00
                "Temperatura (C)": Temperatura[j],
                "Humidade Relativa (%)": Humidade_Relativa[j],
                "Chuva (mm)": Chuva[j],
                "Velocidade do Vento (km/h)": Velocidade_Vento[j]
            }
            dados_15_dias.append(dado_hora)
    
    # Convertendo os dados para DataFrame do Pandas
    df = pd.DataFrame(dados_15_dias)

    # Salvando os dados em um arquivo CSV
    df.to_csv(output_file, index=False)    

# Funcao para exibir informacoes atuais
def informacao_atual(response, frame):
    temperatura_atual = response.Current().Variables(0).Value()
    humidade_atual = response.Current().Variables(1).Value()
    chuva_atual = response.Current().Variables(2).Value()
    vento_atual = response.Current().Variables(3).Value()

    current_data = pd.DataFrame({
        "Informacao Atual": ["Temperatura", "Humidade", "Chuva", "Velocidade do Vento"],
        "Valor": [temperatura_atual, humidade_atual, chuva_atual, vento_atual]
    })

    # Salvar os dados em um arquivo de texto
    with open("informacao_atual.txt", "w") as file:
        file.write(current_data.to_string(index=False))

    for widget in frame.winfo_children():
        widget.destroy()


    tree = ttk.Treeview(frame, columns=list(current_data.columns), show="headings")
    for column in current_data.columns:
        tree.heading(column, text=column)
    for _, row in current_data.iterrows():
        tree.insert("", "end", values=list(row))
    tree.pack(expand=True, fill='both')

    return temperatura_atual, humidade_atual, chuva_atual, vento_atual

    
# Função para exibir informações horárias e gráficos
def informacao_horaria(response, frame):
    hourly_times = pd.date_range(
        start=pd.to_datetime(response.Hourly().Time(), unit="s", utc=True),
        periods=len(response.Hourly().Variables(0).ValuesAsNumpy()),
        freq=pd.Timedelta(seconds=response.Hourly().Interval())
    )

    hourly_data = pd.DataFrame({
        "Data": hourly_times.date,
        "Hora": hourly_times.time,
        "Temperatura (C)": response.Hourly().Variables(0).ValuesAsNumpy(),
        "Humidade Relativa (%)": response.Hourly().Variables(1).ValuesAsNumpy(),
        "Chuva (mm)": response.Hourly().Variables(2).ValuesAsNumpy(),
        "Velocidade do Vento (km/h)": response.Hourly().Variables(3).ValuesAsNumpy()
    })

    hourly_data.to_csv("informacao_horaria.txt", index=False)

    for widget in frame.winfo_children():
        widget.destroy()

    container = ttk.Frame(frame)
    container.pack(expand=True, fill='both')

    tree = ttk.Treeview(container, columns=list(hourly_data.columns), show="headings")
    for column in hourly_data.columns:
        tree.heading(column, text=column)
    for _, row in hourly_data.iterrows():
        tree.insert("", "end", values=list(row))
    tree.grid(row=0, column=0, columnspan=2, sticky='nsew')

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    exibir_graficos_horarios(container)

def informacao_diaria(response, frame):
    daily_times = pd.date_range(
        start=pd.to_datetime(response.Daily().Time(), unit="s", utc=True),
        periods=len(response.Daily().Variables(0).ValuesAsNumpy()),
        freq=pd.Timedelta(seconds=response.Daily().Interval())
    )

    daily_data = pd.DataFrame({
        "Data": daily_times.date,
        "Max Temperatura (C)": response.Daily().Variables(0).ValuesAsNumpy(),
        "Min Temperatura (C)": response.Daily().Variables(1).ValuesAsNumpy()
    })

    daily_data.to_csv("informacao_diaria.txt", index=False)

    for widget in frame.winfo_children():
        widget.destroy()


    tree = ttk.Treeview(frame, columns=list(daily_data.columns), show="headings")
    for column in daily_data.columns:
        tree.heading(column, text=column)
    for _, row in daily_data.iterrows():
        tree.insert("", "end", values=list(row))
    tree.pack(expand=True, fill='both')


def grafico_temperatura(csv_file):
    df = pd.read_csv(csv_file)
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    df.set_index('Datetime', inplace=True)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(df.index, df['Temperatura (C)'], label='Temperatura (C)', color='red')
    ax.set_title('Temperatura em Funcao do Tempo')
    ax.set_xlabel('Tempo')
    ax.set_ylabel('Temperatura (C)')
    ax.grid(True)
    ax.legend()

    # Ajustes para a formatação das datas no eixo x
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=40, ha='right', fontsize=7)

    return fig

# Gráfico da humidade em função do tempo
def grafico_humidade_relativa(csv_file):
    df = pd.read_csv(csv_file)
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    df.set_index('Datetime', inplace=True)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(df.index, df['Humidade Relativa (%)'], label='HUmidade Relativa (%)', color='blue')
    ax.set_title('Humidade Relativa em Funcao do Tempo')
    ax.set_xlabel('Tempo')
    ax.set_ylabel('Humidade Relativa (%)')
    ax.grid(True)
    ax.legend()

    # Ajustes para a formatação das datas no eixo x
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=40, ha='right', fontsize=7)

    return fig

# Gráfico da chuva em função do tempo
def grafico_chuva(csv_file):
    df = pd.read_csv(csv_file)
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    df.set_index('Datetime', inplace=True)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(df.index, df['Chuva (mm)'], label='Chuva (mm)', color='green')
    ax.set_title('Chuva em Funcao do Tempo')
    ax.set_xlabel('Tempo')
    ax.set_ylabel('Chuva (mm)')
    ax.grid(True)
    ax.legend()

    # Ajustes para a formatação das datas no eixo x
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=40, ha='right', fontsize=7)

    return fig

# Gráfico do vento em função do tempo
def grafico_velocidade_vento(csv_file):
    df = pd.read_csv(csv_file)
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    df.set_index('Datetime', inplace=True)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(df.index, df['Velocidade do Vento (km/h)'], label='Velocidade do Vento (km/h)', color='orange')
    ax.set_title('Velocidade do Vento em Funcao do Tempo')
    ax.set_xlabel('Tempo')
    ax.set_ylabel('Velocidade do Vento (km/h)')
    ax.grid(True)
    ax.legend()

    # Ajustes para a formatação das datas no eixo x
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=40, ha='right', fontsize=7)

    return fig

def exibir_graficos(notebook):
    global frame_graficos
    
    # Limpa o frame_graficos antes de adicionar novos gráficos
    for widget in frame_graficos.winfo_children():
        widget.destroy()

    # Criar gráficos
    fig_temperatura = grafico_temperatura("Informacao_15dias_futuro.txt")
    fig_humidade = grafico_humidade_relativa("Informacao_15dias_futuro.txt")
    fig_chuva = grafico_chuva("Informacao_15dias_futuro.txt")
    fig_velocidade_vento = grafico_velocidade_vento("Informacao_15dias_futuro.txt")

    # Criar Canvas para exibir os gráficos
    canvas_temperatura = FigureCanvasTkAgg(fig_temperatura, master=frame_graficos)
    canvas_temperatura.draw()
    canvas_temperatura.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    canvas_humidade = FigureCanvasTkAgg(fig_humidade, master=frame_graficos)
    canvas_humidade.draw()
    canvas_humidade.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    canvas_chuva = FigureCanvasTkAgg(fig_chuva, master=frame_graficos)
    canvas_chuva.draw()
    canvas_chuva.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    canvas_velocidade_vento = FigureCanvasTkAgg(fig_velocidade_vento, master=frame_graficos)
    canvas_velocidade_vento.draw()
    canvas_velocidade_vento.get_tk_widget().grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

    # Configurar pesos das linhas e colunas para que se expandam dinamicamente
    frame_graficos.grid_rowconfigure(0, weight=1)
    frame_graficos.grid_rowconfigure(1, weight=1)
    frame_graficos.grid_columnconfigure(0, weight=1)
    frame_graficos.grid_columnconfigure(1, weight=1)
   
    # Atualizar o notebook
    frame_graficos.update()


def abrir_aba_informacoes(response):
    global aba_informacoes
    aba_informacoes = tk.Toplevel(root)
    aba_informacoes.title("Informacoes Meteorologicas")
    aba_informacoes.configure(bg="#1A1A1A")  # Definir a cor de fundo
    aba_informacoes.geometry("800x600")  # Define o tamanho da janela
   
    style = ttk.Style()
    style.configure("Background.TFrame", background="#1A1A1A", relief='sunken', fieldbackground="#1A1A1A")

    notebook = ttk.Notebook(aba_informacoes)
    notebook.pack(expand=True, fill="both")

    # Abas para diferentes informações
    global frame_atual, frame_horaria, frame_diaria, frame_graficos
    frame_atual = ttk.Frame(notebook, style="Background.TFrame")
    frame_horaria = ttk.Frame(notebook, style="Background.TFrame")
    frame_diaria = ttk.Frame(notebook, style="Background.TFrame")
    frame_graficos = ttk.Frame(notebook, style="Background.TFrame")

    notebook.add(frame_atual, text="Informacao Atual")
    notebook.add(frame_horaria, text="Informacao Horaria")
    notebook.add(frame_diaria, text="Informacao Diaria")
    notebook.add(frame_graficos, text="Graficos")

    # Adicionar botão "Voltar" diretamente ao notebook
    btn_voltar = tk.Button(notebook, text="Sair", command=voltar_janela_principal, width=10)
    notebook.add(btn_voltar, text="Menu Principal")
    notebook.pack(expand=True, fill="both")

    def selecionar_aba(event, response):
        aba_selecionada = event.widget.select()
        aba_index = event.widget.index(aba_selecionada)

        if aba_index == 0:
            informacao_atual(response, frame_atual)
        elif aba_index == 1:
            informacao_horaria(response, frame_horaria)
        elif aba_index == 2:
            informacao_diaria(response, frame_diaria)
        elif aba_index == 3:
            exibir_graficos(frame_graficos)
        elif aba_index == 4:
            voltar_janela_principal()
        
    # Bind para trocar de aba
    notebook.bind("<<NotebookTabChanged>>", lambda event: selecionar_aba(event, response))     


    # Inicializar com a aba de "Informacao Atual"
    informacao_atual(response, frame_atual)


def voltar_janela_principal():
    aba_informacoes.destroy()
    root.deiconify()  # Fazer a janela principal reaparecer   
        

def iniciar_interface():
    global root, cidade_entry, hora_inicial_entry, hora_final_entry, frame_clima, frame_clima_historico, popup_window
    root = ctk.CTk()
    root.title("METEOROLOGIA")
    root.configure(bg="#1A1A1A")
    root.geometry("800x600")  # Define o tamanho inicial da janela


    # Função para sair da aplicação
    def on_closing():
        if messagebox.askokcancel("Sair", "Tem a certeza que deseja sair?"):
            root.destroy()


    def buscar_clima():
        city_name = cidade_entry.get()
        hora_inicial_text = hora_inicial_entry.get()
        hora_final_text = hora_final_entry.get()

        # Verificar se os campos foram preenchidos corretamente
        if not city_name:
            messagebox.showinfo("Aviso", "Por favor, insira o nome da cidade.")
            return
        if not hora_inicial_text.isdigit() or not 0 <= int(hora_inicial_text) <= 23:
            messagebox.showinfo("Aviso", "Por favor, insira uma hora inicial valida (0-23).")
            return
        if not hora_final_text.isdigit() or not 0 <= int(hora_final_text) <= 23:
            messagebox.showinfo("Aviso", "Por favor, insira uma hora final valida (0-23).")
            return

        # Convertendo as horas para inteiros depois de passar nas verificações acima
        hora_inicial = int(hora_inicial_text)
        hora_final = int(hora_final_text)


        response = buscar_dados_clima(city_name, hora_inicial, hora_final)
        if response:
            abrir_aba_informacoes(response)
            root.withdraw()
            popup_window = ctk.CTkToplevel(root)  # Criar a janela de pop-up apenas se houver dados para mostrar
            popup_window.title("Eventos")  
            
            # Funções adicionais (substitua por suas funções reais)
            get_30days(city_name, "Informacao_30dias.txt")
            get_15days_futuro(city_name, "Informacao_15dias_futuro.txt")
            identificar_variacoes_temperatura("Informacao_30dias.txt", popup_window)
            identificar_mudancas_humidade("Informacao_30dias.txt", popup_window)
            identificar_aumento_chuva("Informacao_30dias.txt", popup_window)
            identificar_aumento_velocidade_vento("Informacao_30dias.txt", popup_window)
            identificar_condicoes_furacoes_tornados("Informacao_15dias_futuro.txt", popup_window)
            identificar_condicoes_inundacoes("Informacao_15dias_futuro.txt", popup_window)

    def buscar_historicos():
        city_nameh = cidadeh_entry.get()
        start_dateh = start_dateh_entry.get()
        end_dateh = end_dateh_entry.get()
   
        buscar_dados_historicos(city_nameh, start_dateh, end_dateh)
        root.withdraw()
        

    def alternar_busca(event=None):
        selected_option = combobox_busca.get()
        if selected_option == "Clima Atual":
            frame_clima.pack(expand=True, fill='both')
            frame_clima_historico.pack_forget()
        else:
            frame_clima.pack_forget()
            frame_clima_historico.pack(expand=True, fill='both')

    def confirmar_email():
        global email_user
        email_user = email_entry.get()
        if email_user:
            messagebox.showinfo("Sucesso", "Email guardado!")
        else:
            messagebox.showwarning("Erro", "Por favor, insira um email valido.")


    # Combobox para alternar entre Clima Atual e Clima Histórico
    combobox_busca = ctk.CTkComboBox(root, values=["Clima Atual", "Clima Historico"], command=alternar_busca)
    combobox_busca.set("Clima Atual")  # Valor padrão
    combobox_busca.pack(pady=10)

    # Frame para Clima Atual
    frame_clima = ctk.CTkFrame(root)
    frame_clima.pack(expand=True, fill='both')
    
    # Entry para email
    email_entry = ctk.CTkEntry(frame_clima)
    email_entry.pack(pady=10)

    # Botão para confirmar email
    btn_confirmar = ctk.CTkButton(frame_clima, text="Confirmar Email", command=confirmar_email)
    btn_confirmar.pack(pady=10)
    
    cidade_label = ctk.CTkLabel(frame_clima, text="Cidade:")
    cidade_label.pack(pady=10)
    cidade_entry = ctk.CTkEntry(frame_clima)
    cidade_entry.pack(pady=5)

    hora_inicial_label = ctk.CTkLabel(frame_clima, text="Hora Inicial (0-23):")
    hora_inicial_label.pack(pady=10)
    hora_inicial_entry = ctk.CTkEntry(frame_clima)
    hora_inicial_entry.pack(pady=5)

    hora_final_label = ctk.CTkLabel(frame_clima, text="Hora Final (0-23):")
    hora_final_label.pack(pady=10)
    hora_final_entry = ctk.CTkEntry(frame_clima)
    hora_final_entry.pack(pady=5)

    buscar_button_clima = ctk.CTkButton(frame_clima, text="Buscar Dados Meteorologicos", command=buscar_clima)
    buscar_button_clima.pack(pady=10)
    
    
    frame_clima_historico = ctk.CTkFrame(root)

    cidadeh_label = ctk.CTkLabel(frame_clima_historico, text="Cidade Historica:")
    cidadeh_label.pack(pady=10)
    cidadeh_entry = ctk.CTkEntry(frame_clima_historico)
    cidadeh_entry.pack(pady=5)

    horah_inicial_label = ctk.CTkLabel(frame_clima_historico, text="Data Inicial Historica (yyyy-mm-dd):")
    horah_inicial_label.pack(pady=10)
    start_dateh_entry = ctk.CTkEntry(frame_clima_historico)
    start_dateh_entry.pack(pady=5)

    horah_final_label = ctk.CTkLabel(frame_clima_historico, text="Data Final Historica (yyyy-mm-dd):")
    horah_final_label.pack(pady=10)
    end_dateh_entry = ctk.CTkEntry(frame_clima_historico)
    end_dateh_entry.pack(pady=5)

    buscar_button_hist = ctk.CTkButton(frame_clima_historico, text="Buscar Dados Meteorologicos Historicos", command=buscar_historicos)
    buscar_button_hist.pack(pady=20)

    alternar_busca()  # Inicializa a interface com a seleção padrão

     
    root.protocol("WM_DELETE_WINDOW", on_closing)
 

    root.mainloop()


iniciar_interface()

