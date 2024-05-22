import openmeteo_requests
import tkinter as tk
from tkinter import ttk
import requests_cache
import pandas as pd
from retry_requests import retry
import datetime
from geopy.geocoders import Nominatim
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import matplotlib.pyplot as plt

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
def send_email(mensagem):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'trabalho.lab.clima@gmail.com'
    to_address = 'trabalho.lab.clima@gmail.com'
    sender_password = get_password_from_file('api-pass.txt')
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_address
    msg['Subject'] = 'Alerta Condicoes Climaticas'
    html_message = mensagem
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
    max_diff_aumento = 0
    max_diff_queda = 0
    max_diff_date_aumento = None
    max_diff_date_queda = None
    for indice, linha in dados.iterrows():
        temperatura_atual = linha['Temperatura (C)']
        temperatura_anterior = dados.iloc[indice - 1]['Temperatura (C)'] if indice > 0 else None
        if temperatura_anterior is not None:
            diff = abs(temperatura_atual - temperatura_anterior)
            if temperatura_atual > temperatura_anterior:
                if diff > max_diff_aumento and diff > 4:  # Ajuste o valor do limiar conforme necessário
                    max_diff_aumento = diff
                    max_diff_date_aumento = linha['Data']
                    print(f"Aumento abrupto na temperatura em {linha['Data']} | {linha['Hora']}: {temperatura_anterior} -> {temperatura_atual}")
            elif temperatura_atual < temperatura_anterior:
                if diff > max_diff_queda and diff > 4:  # Ajuste o valor do limiar conforme necessário
                    max_diff_queda = diff
                    max_diff_date_queda = linha['Data']
                    print(f"Queda abrupta na temperatura em {linha['Data']} | {linha['Hora']}: {temperatura_anterior} -> {temperatura_atual}")

    return (max_diff_aumento, max_diff_date_aumento), (max_diff_queda, max_diff_date_queda)


# Analisar variaçao de humidade
def identificar_mudancas_humidade(dados):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Identificar variações abruptas na humidade
    max_diff_aumento = 0
    max_diff_queda = 0
    max_diff_date_aumento = None
    max_diff_date_queda = None
    for indice, linha in dados.iterrows():
        humidade_atual = linha['Humidade Relativa (%)']
        humidade_anterior = dados.iloc[indice - 1]['Humidade Relativa (%)'] if indice > 0 else None
        if humidade_anterior is not None:
            diff = abs(humidade_atual - humidade_anterior)
            if humidade_atual > humidade_anterior:
                if diff > max_diff_aumento and diff > 20:  # Ajuste o valor do limiar conforme necessário
                    max_diff_aumento = diff
                    max_diff_date_aumento = linha['Data']
                    print(f"Aumento abrupto na humidade em {linha['Data']} | {linha['Hora']}: {humidade_anterior} -> {humidade_atual}")
            elif humidade_atual < humidade_anterior:
                if diff > max_diff_queda and diff > 20:  # Ajuste o valor do limiar conforme necessário
                    max_diff_queda = diff
                    max_diff_date_queda = linha['Data']
                    print(f"Queda abrupta na humidade em {linha['Data']} | {linha['Hora']}: {humidade_anterior} -> {humidade_atual}")

    return (max_diff_aumento, max_diff_date_aumento), (max_diff_queda, max_diff_date_queda)


# Analisar variaçao de chuva
def identificar_aumento_chuva(dados):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Identificar variações abruptas na chuva
    max_diff_aumento = 0
    max_diff_queda = 0
    max_diff_date_aumento = None
    max_diff_date_queda = None
    for indice, linha in dados.iterrows():
        chuva_atual = linha['Chuva (mm)']
        chuva_anterior = dados.iloc[indice - 1]['Chuva (mm)'] if indice > 0 else None
        if chuva_anterior is not None:
            diff = abs(chuva_atual - chuva_anterior)
            if chuva_atual > chuva_anterior:
                if diff > max_diff_aumento and diff > 5:  # Ajuste o valor do limiar conforme necessário
                    max_diff_aumento = diff
                    max_diff_date_aumento = linha['Data']
                    print(f"Aumento abrupto na quantidade de chuva em {linha['Data']} | {linha['Hora']}: {chuva_anterior} -> {chuva_atual}")
            elif chuva_atual < chuva_anterior:
                if diff > max_diff_queda and diff > 5:  # Ajuste o valor do limiar conforme necessário
                    max_diff_queda = diff
                    max_diff_date_queda = linha['Data']
                    print(f"Queda abrupta na quantidade de chuva em {linha['Data']} | {linha['Hora']}: {chuva_anterior} -> {chuva_atual}")

    return (max_diff_aumento, max_diff_date_aumento), (max_diff_queda, max_diff_date_queda)


# Analisar variaçao de velocidade de vento
def identificar_aumento_velocidade_vento(dados):
    # Carregar os dados do arquivo CSV em um DataFrame
    dados = pd.read_csv(dados)

    # Verificar se o DataFrame está vazio
    if dados.empty:
        print("O DataFrame esta vazio. Nao ha dados para analisar.")
        return None

    # Identificar variações abruptas na velocidade do vento
    max_diff_aumento = 0
    max_diff_queda = 0
    max_diff_date_aumento = None
    max_diff_date_queda = None
    for indice, linha in dados.iterrows():
        vento_atual = linha['Velocidade do Vento (km/h)']
        vento_anterior = dados.iloc[indice - 1]['Velocidade do Vento (km/h)'] if indice > 0 else None
        if vento_anterior is not None:
            diff = abs(vento_atual - vento_anterior)
            if vento_atual > vento_anterior:
                if diff > max_diff_aumento and diff > 10:  # Ajuste o valor do limiar conforme necessário
                    max_diff_aumento = diff
                    max_diff_date_aumento = linha['Data']
                    print(f"Aumento abrupto na velocidade do vento em {linha['Data']} | {linha['Hora']}: {vento_anterior} -> {vento_atual}")
            elif vento_atual < vento_anterior:
                if diff > max_diff_queda and diff > 10:  # Ajuste o valor do limiar conforme necessário
                    max_diff_queda = diff
                    max_diff_date_queda = linha['Data']
                    print(f"Queda abrupta na velocidade do vento em {linha['Data']} | {linha['Hora']}: {vento_anterior} -> {vento_atual}")

    return (max_diff_aumento, max_diff_date_aumento), (max_diff_queda, max_diff_date_queda)


# Função para identificar condições propícias para furacões ou tornados
def identificar_condicoes_furacoes_tornados(dados):
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
            print(f"Condicoes propicias para furacoes ou tornados encontradas em {linha['Data']} {linha['Hora']}: Velocidade do Vento {vento_atual} km/h")
            send_email('Alerta-se todos os habitantes que se mantenham em casa. Alto risco de Furacao/Tornado.')
    return furacoes_tornados


# Função para identificar condições propícias para inundações
def identificar_condicoes_inundacoes(dados):
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
            print(f"Condicoes propicias para inundacoes encontradas em {linha['Data']}: Quantidade de Chuva {chuva_atual} mm")
            send_email('Alerta-se todos os habitantes que se mantenham fora de zonas litorais, e ficar em casa. Alto risco de Inundacao.')
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
    window = tk.Tk()
    window.title("Dados Historicos")
    window.configure(bg="#4B0082")

    tree = ttk.Treeview(window)
    tree["columns"] = list(df.columns)
    tree["show"] = "headings"

    for column in df.columns:
        tree.heading(column, text=column)
        tree.column(column, anchor='center')

    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))

    tree.pack(expand=True, fill='both')
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
def get_16days_futuro(response, output_file):
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

    # Definindo a data atual e a data para 16 dias no futuro
    data_atual = datetime.date.today()

    dados_16_dias = []

    # Fazendo a chamada à API para os dados de previsão
    url = "https://api.open-meteo.com/v1/forecast"
    for i in range(16):
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
            dados_16_dias.append(dado_hora)

    # Convertendo os dados para DataFrame do Pandas
    df = pd.DataFrame(dados_16_dias)

    # Salvando os dados em um arquivo CSV
    df.to_csv(output_file, index=False)    

# Funcao para exibir informacoes atuais
def informacao_atual(response):
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

    # Exibir os dados na interface gráfica
    window = tk.Tk()
    window.title("Informacao Atual")
    window.configure(bg="#4B0082")

    tree = ttk.Treeview(window)
    tree["columns"] = list(current_data.columns)
    tree["show"] = "headings"

    for column in current_data.columns:
        tree.heading(column, text=column)
        tree.column(column, anchor='center')

    for _, row in current_data.iterrows():
        tree.insert("", "end", values=list(row))

    tree.pack(expand=True, fill='both')
    window.mainloop()

    return temperatura_atual, humidade_atual, chuva_atual, vento_atual
    

# Funcao para exibir informacoes horarias
def informacao_horaria(response):
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

    # Salvar os dados em um arquivo CSV
    hourly_data.to_csv("informacao_horaria.txt", index=False)


    # Exibir os dados na interface gráfica
    window = tk.Tk()
    window.title("Informacao Horaria")
    window.configure(bg="#4B0082")

    tree = ttk.Treeview(window)
    tree["columns"] = list(hourly_data.columns)
    tree["show"] = "headings"

    for column in hourly_data.columns:
        tree.heading(column, text=column)
        tree.column(column, anchor='center')

    for _, row in hourly_data.iterrows():
        tree.insert("", "end", values=list(row))

    tree.pack(expand=True, fill='both')
    window.mainloop()


# Funcao para exibir informacoes diarias
def informacao_diaria(response):
    daily_times = pd.date_range(
        start=pd.to_datetime(response.Daily().Time(), unit="s", utc=True),
        periods=len(response.Daily().Variables(0).ValuesAsNumpy()),
        freq='D'
    )

    daily_data = pd.DataFrame({
        "Data": daily_times.date,
        "Max Temperatura (C)": response.Daily().Variables(0).ValuesAsNumpy(),
        "Min Temperatura (C)": response.Daily().Variables(1).ValuesAsNumpy()
    })

    # Salvar os dados em um arquivo CSV
    daily_data.to_csv("informacao_diaria.txt", index=False)

    # Exibir os dados na interface gráfica
    window = tk.Tk()
    window.title("Informacao Diaria")
    window.configure(bg="#4B0082")

    tree = ttk.Treeview(window)
    tree["columns"] = list(daily_data.columns)
    tree["show"] = "headings"

    for column in daily_data.columns:
        tree.heading(column, text=column)
        tree.column(column, anchor='center')

    for _, row in daily_data.iterrows():
        tree.insert("", "end", values=list(row))  # Corrigido aqui

    tree.pack(expand=True, fill='both')
    window.mainloop()


# Grafico da temperatura em funcao do tempo
def grafico_temperatura(csv_file):
    # Lendo os dados do arquivo CSV
    df = pd.read_csv(csv_file)

    # Convertendo as colunas 'Data' e 'Hora' para um único índice datetime
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    
    # Configurando o índice do DataFrame para a nova coluna datetime
    df.set_index('Datetime', inplace=True)

    # Criando o gráfico
    plt.figure(figsize=(15, 7))
    plt.plot(df.index, df['Temperatura (C)'], label='Temperatura (C)', color='blue')

    # Adicionando título e rótulos aos eixos
    plt.title('Temperatura em Funcao do Tempo')
    plt.xlabel('Tempo')
    plt.ylabel('Temperatura (C)')
    
    # Adicionando uma grade
    plt.grid(True)

    # Adicionando uma legenda
    plt.legend()

    # Mostrando o gráfico
    plt.show()
    

# Grafico da humidade em funcao do tempo
def grafico_humidade_relativa(csv_file):
    # Lendo os dados do arquivo CSV
    df = pd.read_csv(csv_file)

    # Convertendo as colunas 'Data' e 'Hora' para um único índice datetime
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    
    # Configurando o índice do DataFrame para a nova coluna datetime
    df.set_index('Datetime', inplace=True)

    # Criando o gráfico
    plt.figure(figsize=(15, 7))
    plt.plot(df.index, df['Humidade Relativa (%)'], label='Umidade Relativa (%)', color='blue')

    # Adicionando título e rótulos aos eixos
    plt.title('Humidade Relativa em Funcao do Tempo')
    plt.xlabel('Tempo')
    plt.ylabel('Humidade Relativa (%)')
    
    # Adicionando uma grade
    plt.grid(True)

    # Adicionando uma legenda
    plt.legend()

    # Mostrando o gráfico
    plt.show()
    

# Grafico da chuva em funcao do tempo
def grafico_chuva(csv_file):
    # Lendo os dados do arquivo CSV
    df = pd.read_csv(csv_file)

    # Convertendo as colunas 'Data' e 'Hora' para um único índice datetime
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    
    # Configurando o índice do DataFrame para a nova coluna datetime
    df.set_index('Datetime', inplace=True)

    # Criando o gráfico
    plt.figure(figsize=(15, 7))
    plt.plot(df.index, df['Chuva (mm)'], label='Chuva (mm)', color='green')

    # Adicionando título e rótulos aos eixos
    plt.title('Chuva em Funcao do Tempo')
    plt.xlabel('Tempo')
    plt.ylabel('Chuva (mm)')
    
    # Adicionando uma grade
    plt.grid(True)

    # Adicionando uma legenda
    plt.legend()

    # Mostrando o gráfico
    plt.show()
    

# Grafico do vento em funcao do tempo
def grafico_velocidade_vento(csv_file):
    # Lendo os dados do arquivo CSV
    df = pd.read_csv(csv_file)

    # Convertendo as colunas 'Data' e 'Hora' para um único índice datetime
    df['Datetime'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'])
    
    # Configurando o índice do DataFrame para a nova coluna datetime
    df.set_index('Datetime', inplace=True)

    # Criando o gráfico
    plt.figure(figsize=(15, 7))
    plt.plot(df.index, df['Velocidade do Vento (km/h)'], label='Velocidade do Vento (km/h)', color='orange')

    # Adicionando título e rótulos aos eixos
    plt.title('Velocidade do Vento em Funcao do Tempo')
    plt.xlabel('Tempo')
    plt.ylabel('Velocidade do Vento (km/h)')
    
    # Adicionando uma grade
    plt.grid(True)

    # Adicionando uma legenda
    plt.legend()

    # Mostrando o gráfico
    plt.show()
    

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

            botao1 = tk.Button(frame_botoes, text="Informacao Atual", command=lambda: informacao_atual(response))
            botao1.pack(side=tk.LEFT, padx=10)

            botao2 = tk.Button(frame_botoes, text="Informacao Horaria", command=lambda: informacao_horaria(response))
            botao2.pack(side=tk.LEFT, padx=10)

            botao3 = tk.Button(frame_botoes, text="Informacao Diaria", command=lambda: informacao_diaria(response))
            botao3.pack(side=tk.LEFT, padx=10)

            window.mainloop() 
        get_30days(city_name, "Informacao_30dias.txt")
        get_16days_futuro(city_name, "Informacao_16dias_futuro.txt")
        identificar_variacoes_temperatura("Informacao_30dias.txt")
        identificar_mudancas_humidade("Informacao_30dias.txt")
        identificar_aumento_chuva("Informacao_30dias.txt")
        identificar_aumento_velocidade_vento("Informacao_30dias.txt")
        identificar_condicoes_furacoes_tornados("Informacao_16dias_futuro.txt")
        identificar_condicoes_inundacoes("Informacao_16dias_futuro.txt")
        grafico_temperatura("Informacao_16dias_futuro.txt")
        grafico_chuva("Informacao_16dias_futuro.txt")
        grafico_chuva("Informacao_16dias_futuro.txt")
        grafico_velocidade_vento("Informacao_16dias_futuro.txt")


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
    

iniciar_interface()
