import pandas as pd
import numpy as np
import time
import json
from datetime import datetime, timedelta

# Parâmetros da simulação
NUM_TURBINES = 3
DATA_POINTS_PER_HOUR = 60 # 1 ponto por minuto
SIMULATION_HOURS = 24 * 30 # Simular por 30 dias
OUTPUT_DIR = "/home/ubuntu/tcc_kelly_castro/data_simulation/"

# Características normais de operação (exemplo)
NORMAL_WIND_SPEED_AVG = 7.0  # m/s
NORMAL_WIND_SPEED_STD = 2.0
NORMAL_ROTATION_SPEED_AVG = 15.0 # RPM
NORMAL_ROTATION_SPEED_STD = 3.0
NORMAL_GEARBOX_TEMP_AVG = 60.0 # °C
NORMAL_GEARBOX_TEMP_STD = 5.0
NORMAL_GENERATOR_POWER_AVG = 1500 # kW
NORMAL_GENERATOR_POWER_STD = 300
NORMAL_VIBRATION_X_AVG = 0.1 # g
NORMAL_VIBRATION_X_STD = 0.02
NORMAL_VIBRATION_Y_AVG = 0.1 # g
NORMAL_VIBRATION_Y_STD = 0.02

# Padrões de anomalia (simplificado)
# Anomalia 1: Superaquecimento da caixa de engrenagens (aumento gradual da temperatura)
ANOMALY_GEARBOX_TEMP_INCREASE_RATE = 0.1 # °C por ponto de dado

# Anomalia 2: Aumento de vibração (aumento súbito)
ANOMALY_VIBRATION_INCREASE_FACTOR = 5.0

def generate_normal_data(num_points):
    data = pd.DataFrame()
    data["timestamp"] = [datetime.now() - timedelta(minutes=i) for i in range(num_points)][::-1]
    data["wind_speed_m_s"] = np.random.normal(NORMAL_WIND_SPEED_AVG, NORMAL_WIND_SPEED_STD, num_points)
    data["rotation_speed_rpm"] = np.random.normal(NORMAL_ROTATION_SPEED_AVG, NORMAL_ROTATION_SPEED_STD, num_points)
    data["gearbox_temperature_c"] = np.random.normal(NORMAL_GEARBOX_TEMP_AVG, NORMAL_GEARBOX_TEMP_STD, num_points)
    data["generator_power_kw"] = np.random.normal(NORMAL_GENERATOR_POWER_AVG, NORMAL_GENERATOR_POWER_STD, num_points)
    data["vibration_x_g"] = np.random.normal(NORMAL_VIBRATION_X_AVG, NORMAL_VIBRATION_X_STD, num_points)
    data["vibration_y_g"] = np.random.normal(NORMAL_VIBRATION_Y_AVG, NORMAL_VIBRATION_Y_STD, num_points)
    data["label"] = 0 # 0 para normal
    return data

def introduce_gearbox_overheating_anomaly(df, start_index, duration_points):
    df_anomaly = df.copy()
    for i in range(duration_points):
        if start_index + i < len(df_anomaly):
            df_anomaly.loc[start_index + i, "gearbox_temperature_c"] += ANOMALY_GEARBOX_TEMP_INCREASE_RATE * (i + 1)
            df_anomaly.loc[start_index + i, "label"] = 1 # 1 para falha na caixa de engrenagens
    return df_anomaly

def introduce_vibration_anomaly(df, start_index, duration_points):
    df_anomaly = df.copy()
    for i in range(duration_points):
        if start_index + i < len(df_anomaly):
            df_anomaly.loc[start_index + i, "vibration_x_g"] *= ANOMALY_VIBRATION_INCREASE_FACTOR
            df_anomaly.loc[start_index + i, "vibration_y_g"] *= ANOMALY_VIBRATION_INCREASE_FACTOR
            df_anomaly.loc[start_index + i, "label"] = 2 # 2 para falha de vibração
    return df_anomaly

if __name__ == "__main__":
    total_data_points = SIMULATION_HOURS * DATA_POINTS_PER_HOUR

    for turbine_id in range(1, NUM_TURBINES + 1):
        print(f"Gerando dados para a turbina {turbine_id}...")
        df_turbine = generate_normal_data(total_data_points)

        # Introduzir anomalias em momentos aleatórios
        if turbine_id == 1: # Turbina 1 com superaquecimento
            anomaly_start = np.random.randint(total_data_points // 2, total_data_points - (DATA_POINTS_PER_HOUR * 5)) # Pelo menos 5h antes do fim
            anomaly_duration = DATA_POINTS_PER_HOUR * 3 # Anomalia dura 3 horas
            df_turbine = introduce_gearbox_overheating_anomaly(df_turbine, anomaly_start, anomaly_duration)
            print(f"Anomalia de superaquecimento introduzida na turbina {turbine_id} a partir do ponto {anomaly_start}")

        elif turbine_id == 2: # Turbina 2 com problema de vibração
            anomaly_start = np.random.randint(total_data_points // 3, total_data_points - (DATA_POINTS_PER_HOUR * 6))
            anomaly_duration = DATA_POINTS_PER_HOUR * 2 # Anomalia dura 2 horas
            df_turbine = introduce_vibration_anomaly(df_turbine, anomaly_start, anomaly_duration)
            print(f"Anomalia de vibração introduzida na turbina {turbine_id} a partir do ponto {anomaly_start}")
        
        # Turbina 3 permanece normal para ter dados de referência

        # Arredondar valores para um número razoável de casas decimais
        for col in df_turbine.columns:
            if df_turbine[col].dtype == float:
                df_turbine[col] = df_turbine[col].round(4)

        # Salvar dados em formato JSON (simulando o que seria enviado para S3/Kinesis)
        # Em um cenário real, cada ponto de dado ou pequenos batches seriam enviados.
        # Aqui, salvamos um arquivo por turbina para simplificar.
        output_filename = f"{OUTPUT_DIR}turbine_{turbine_id}_data.json"
        
        # Converter timestamps para string ISO format para serialização JSON
        df_turbine["timestamp"] = df_turbine["timestamp"].astype(str)
        
        data_to_save = df_turbine.to_dict(orient="records")
        
        with open(output_filename, "w") as f:
            json.dump(data_to_save, f, indent=4)
        
        print(f"Dados da turbina {turbine_id} salvos em {output_filename}")

    print("Simulação de dados concluída.")

