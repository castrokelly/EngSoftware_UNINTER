import json
import boto3
import os
import pandas as pd
import numpy as np
import joblib
import awswrangler as wr # Pode ser útil para alguma manipulação, mas não essencial aqui

# Nome do bucket S3 onde o modelo treinado e o scaler estão armazenados
MODEL_ARTIFACTS_BUCKET = os.environ.get("MODEL_ARTIFACTS_BUCKET_NAME", "tcc-kelly-model-artifacts-bucket")
MODEL_KEY = os.environ.get("MODEL_S3_KEY", "notebooks/best_failure_prediction_model.joblib") # Chave do modelo no S3
SCALER_KEY = os.environ.get("SCALER_S3_KEY", "notebooks/feature_scaler.joblib") # Chave do scaler no S3
COLUMNS_KEY = os.environ.get("COLUMNS_S3_KEY", "notebooks/model_columns.json") # Chave do JSON com as colunas

s3_client = boto3.client("s3")

# Variáveis globais para carregar o modelo e o scaler apenas uma vez (otimização para Lambda)
model = None
scaler = None
model_columns = None

def load_model_artifacts():
    """Carrega o modelo, scaler e colunas do S3 se ainda não estiverem carregados."""
    global model, scaler, model_columns
    
    if model is None:
        try:
            model_path = "/tmp/model.joblib"
            s3_client.download_file(MODEL_ARTIFACTS_BUCKET, MODEL_KEY, model_path)
            model = joblib.load(model_path)
            print(f"Modelo carregado de s3://{MODEL_ARTIFACTS_BUCKET}/{MODEL_KEY}")
        except Exception as e:
            print(f"Erro ao carregar o modelo do S3: {e}")
            raise e
            
    if scaler is None:
        try:
            scaler_path = "/tmp/scaler.joblib"
            s3_client.download_file(MODEL_ARTIFACTS_BUCKET, SCALER_KEY, scaler_path)
            scaler = joblib.load(scaler_path)
            print(f"Scaler carregado de s3://{MODEL_ARTIFACTS_BUCKET}/{SCALER_KEY}")
        except Exception as e:
            print(f"Erro ao carregar o scaler do S3: {e}")
            raise e

    if model_columns is None:
        try:
            columns_path = "/tmp/model_columns.json"
            s3_client.download_file(MODEL_ARTIFACTS_BUCKET, COLUMNS_KEY, columns_path)
            with open(columns_path, "r") as f:
                model_columns = json.load(f)
            print(f"Colunas do modelo carregadas de s3://{MODEL_ARTIFACTS_BUCKET}/{COLUMNS_KEY}")
        except Exception as e:
            print(f"Erro ao carregar as colunas do modelo do S3: {e}")
            raise e

def lambda_handler(event, context):
    """
    Função Lambda para realizar predições de falha.
    Espera receber os dados de features de uma janela como entrada no corpo da requisição HTTP (via API Gateway).
    """
    print(f"Evento recebido: {event}")
    
    try:
        load_model_artifacts() # Garante que modelo, scaler e colunas estão carregados
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Erro ao carregar artefatos do modelo: {str(e)}"})
        }

    if model is None or scaler is None or model_columns is None:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Modelo, scaler ou colunas não puderam ser carregados."})
        }

    try:
        # O corpo da requisição do API Gateway estará em event["body"] como uma string JSON
        if isinstance(event.get("body"), str):
            input_data = json.loads(event["body"])
        else:
            input_data = event.get("body") # Se já for um dict (ex: teste direto da Lambda)
            
        if not input_data:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Corpo da requisição vazio ou inválido."})
            }
        
        # Espera-se que input_data seja um dicionário representando uma única janela de features
        # ou uma lista de dicionários para predição em batch (vamos tratar um único por simplicidade aqui)
        # Exemplo de input_data: 
        # {
        #   "wind_speed_m_s_mean": 7.1, "wind_speed_m_s_std": 1.9, ...,
        #   "vibration_y_g_median": 0.1
        # }
        
        # Converter para DataFrame do Pandas para aplicar o scaler e predição
        # Garantir que a ordem das colunas e as colunas presentes são as mesmas do treinamento
        df_input = pd.DataFrame([input_data])
        
        # Reordenar e selecionar colunas conforme o treinamento
        # Adicionar colunas faltantes com NaN (ou valor padrão, mas o scaler deve ter sido treinado com isso em mente)
        for col in model_columns:
            if col not in df_input.columns:
                df_input[col] = np.nan # Ou 0, ou média - depende da estratégia de preenchimento no treino
        
        df_input = df_input[model_columns] # Garante a ordem e seleção correta das colunas
        
        # Lidar com NaNs (ex: preencher com média se foi feito no treino, ou o scaler pode falhar)
        # O ideal é que o pipeline de features já garanta que não há NaNs ou que são tratados consistentemente.
        # Se o scaler foi treinado com dados que tinham NaNs preenchidos, a mesma estratégia deve ser usada aqui.
        # Por simplicidade, vamos assumir que o scaler lida com isso ou que os dados de entrada são limpos.
        # Se o scaler foi treinado após preenchimento de NaNs com média, por exemplo:
        # df_input.fillna(df_input.mean(), inplace=True) # CUIDADO: a média aqui é do input, não do treino.
        # O correto seria usar médias do conjunto de treino salvas, ou garantir que não há NaNs.
        # Para este exemplo, vamos assumir que as features de entrada são completas.
        if df_input.isnull().values.any():
             print("Alerta: Dados de entrada contêm NaNs. Preenchendo com 0 para evitar erro no scaler/modelo.")
             df_input.fillna(0, inplace=True) # Estratégia simples, pode não ser a ideal.

        # Aplicar o scaler
        input_scaled = scaler.transform(df_input)
        
        # Realizar a predição
        prediction = model.predict(input_scaled)
        prediction_proba = model.predict_proba(input_scaled) if hasattr(model, "predict_proba") else None
        
        result = {
            "predicted_label": int(prediction[0]), # Convertendo para int nativo para JSON
            "prediction_probabilities": prediction_proba[0].tolist() if prediction_proba is not None else "N/A"
        }
        
        # Mapear label numérico para significado (opcional, mas útil)
        label_map = {0: "Normal", 1: "Falha Caixa de Engrenagens (Superaquecimento)", 2: "Falha de Vibração"}
        result["predicted_status"] = label_map.get(int(prediction[0]), "Desconhecido")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result)
        }

    except Exception as e:
        print(f"Erro durante a predição: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Erro interno do servidor durante a predição: {str(e)}"})
        }

# Exemplo de como testar localmente (não faz parte do código da Lambda em si)
# if __name__ == "__main__":
#     # Simular um evento de entrada do API Gateway (corpo como string JSON)
#     # Certifique-se de que os artefatos (modelo, scaler, colunas) estão no bucket S3 configurado
#     # e que as variáveis de ambiente MODEL_ARTIFACTS_BUCKET, MODEL_KEY, etc., estão setadas
#     # ou que os arquivos estão localmente e a função load_model_artifacts é adaptada para teste local.
    
#     # Para um teste real, você precisaria de credenciais AWS e dos artefatos no S3.
#     # Este é um exemplo de payload, as features devem corresponder às usadas no treinamento.
#     mock_api_gateway_event = {
#         "body": json.dumps({
#             "gearbox_temperature_c_mean": 75.0, 
#             "gearbox_temperature_c_std": 2.5,
#             "gearbox_temperature_c_min": 72.0,
#             "gearbox_temperature_c_max": 78.0,
#             "gearbox_temperature_c_median": 75.0,
#             "generator_power_kw_mean": 1600.0, 
#             "generator_power_kw_std": 250.0,
#             # ... (todas as outras features esperadas pelo modelo e presentes em model_columns.json)
#             "rotation_speed_rpm_mean": 15.0,
#             "rotation_speed_rpm_std": 3.0,
#             "rotation_speed_rpm_min": 10.0,
#             "rotation_speed_rpm_max": 20.0,
#             "rotation_speed_rpm_median": 15.0,
#             "vibration_x_g_mean": 0.15,
#             "vibration_x_g_std": 0.03,
#             "vibration_x_g_min": 0.1,
#             "vibration_x_g_max": 0.2,
#             "vibration_x_g_median": 0.15,
#             "vibration_y_g_mean": 0.16,
#             "vibration_y_g_std": 0.04,
#             "vibration_y_g_min": 0.11,
#             "vibration_y_g_max": 0.22,
#             "vibration_y_g_median": 0.16,
#             "wind_speed_m_s_mean": 8.0,
#             "wind_speed_m_s_std": 2.0,
#             "wind_speed_m_s_min": 5.0,
#             "wind_speed_m_s_max": 12.0,
#             "wind_speed_m_s_median": 8.0
#             # Certifique-se de que todas as colunas de model_columns.json estão aqui
#         })
#     }
#     # print(lambda_handler(mock_api_gateway_event, None))
#     print("Para testar localmente, descomente, configure o payload e o ambiente AWS.")

