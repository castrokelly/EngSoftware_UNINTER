import json
import boto3
import os
import pandas as pd
from io import StringIO, BytesIO
import awswrangler as wr # Usar awswrangler para facilitar leitura/escrita no S3 com pandas

# Nome do bucket S3 onde os dados processados/features serão armazenados
PROCESSED_DATA_BUCKET = os.environ.get("PROCESSED_DATA_BUCKET_NAME", "tcc-kelly-processed-turbine-data-bucket")

s3_client = boto3.client("s3")

def calculate_features(df_window):
    """Calcula features estatísticas para uma janela de dados."""
    features = {}
    for col in df_window.columns:
        if pd.api.types.is_numeric_dtype(df_window[col]):
            features[f"{col}_mean"] = df_window[col].mean()
            features[f"{col}_std"] = df_window[col].std()
            features[f"{col}_min"] = df_window[col].min()
            features[f"{col}_max"] = df_window[col].max()
            features[f"{col}_median"] = df_window[col].median()
            # Adicionar mais features se necessário (ex: skew, kurtosis, FFT para vibração)
    
    # A label da janela é o último label conhecido na janela (ou o mais frequente, etc.)
    # Para simplificar, se qualquer ponto na janela for anômalo, a janela é anômala.
    if "label" in df_window.columns:
        features["label"] = 1 if df_window["label"].any() else 0 
        # Poderia ser mais sofisticado, ex: tipo de falha predominante
    else:
        features["label"] = 0 # Default para normal se não houver label
        
    if "timestamp" in df_window.columns:
         # Usar o último timestamp da janela como referência
        features["window_end_timestamp"] = df_window["timestamp"].iloc[-1]
        
    return features

def lambda_handler(event, context):
    """
    Função Lambda para processar dados brutos do S3 (entregues pelo Firehose),
    extrair features e salvar os dados processados em outro bucket S3.
    Esta função seria tipicamente acionada por um evento S3 (PutObject) no bucket de dados brutos.
    """
    print(f"Evento recebido: {event}")

    # Obter informações do bucket e do objeto do evento S3
    source_bucket = event["Records"][0]["s3"]["bucket"]["name"]
    source_key = event["Records"][0]["s3"]["object"]["key"]

    print(f"Processando arquivo: s3://{source_bucket}/{source_key}")

    try:
        # Ler o arquivo JSON do S3 (awswrangler lida bem com partições do Firehose)
        # O Firehose pode entregar múltiplos JSONs em um único arquivo S3, ou arquivos gzippados.
        # awswrangler.s3.read_json geralmente lida com isso.
        # Se os dados estiverem em formato JSON Lines (um JSON por linha), o awswrangler também suporta.
        df_raw = wr.s3.read_json(path=f"s3://{source_bucket}/{source_key}", lines=True, orient="records")
        print(f"Lidos {len(df_raw)} registros do arquivo {source_key}")
        
        if df_raw.empty:
            print("Arquivo vazio, nada a processar.")
            return {"statusCode": 200, "body": json.dumps("Arquivo vazio.")}

        # Converter colunas para tipos corretos se necessário (ex: timestamp)
        if "timestamp" in df_raw.columns:
            df_raw["timestamp"] = pd.to_datetime(df_raw["timestamp"])
        
        # Lógica de janelamento e extração de features
        # Para este exemplo, vamos usar janelas deslizantes simples.
        # O tamanho da janela e o passo devem ser definidos com base no caso de uso.
        WINDOW_SIZE_MINUTES = 10 # Exemplo: janela de 10 minutos
        STEP_MINUTES = 5       # Exemplo: passo de 5 minutos
        
        # Assumindo que os dados estão ordenados por timestamp e chegam a cada minuto
        window_size_points = WINDOW_SIZE_MINUTES 
        step_points = STEP_MINUTES

        processed_features_list = []
        
        if not df_raw.empty and "timestamp" in df_raw.columns:
            df_raw = df_raw.sort_values(by="timestamp")
            for i in range(0, len(df_raw) - window_size_points + 1, step_points):
                df_window = df_raw.iloc[i : i + window_size_points]
                if not df_window.empty:
                    features = calculate_features(df_window)
                    # Adicionar identificador da turbina se disponível no nome do arquivo/path
                    # Ex: extrair de source_key
                    turbine_id_str = "unknown_turbine"
                    try:
                        # Tentativa de extrair turbine_id do nome do arquivo (ex: turbine_1_...)
                        parts = source_key.split("/")[-1].split("_")
                        if parts[0] == "turbine" and len(parts) > 1:
                            turbine_id_str = f"turbine_{parts[1]}"
                    except Exception as e:
                        print(f"Não foi possível extrair turbine_id do nome do arquivo {source_key}: {e}")
                    features["turbine_id"] = turbine_id_str
                    processed_features_list.append(features)
        else:
            print("DataFrame vazio ou sem coluna 'timestamp' após leitura. Não é possível janelar.")

        if not processed_features_list:
            print("Nenhuma feature foi extraída.")
            return {"statusCode": 200, "body": json.dumps("Nenhuma feature extraída.")}

        df_processed = pd.DataFrame(processed_features_list)
        
        # Salvar as features processadas em formato Parquet no bucket de destino
        # O Parquet é eficiente para armazenamento e consultas analíticas.
        # O nome do arquivo de saída pode incluir informações do arquivo de origem ou timestamp.
        output_filename = source_key.replace(".json", "").replace(".gz", "") + "_features.parquet"
        output_path = f"s3://{PROCESSED_DATA_BUCKET}/features/{output_filename}"
        
        wr.s3.to_parquet(df=df_processed, path=output_path)
        print(f"Features processadas salvas em: {output_path}")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Arquivo {source_key} processado. {len(df_processed)} janelas de features salvas em {output_path}"})
        }

    except Exception as e:
        print(f"Erro ao processar o arquivo {source_key}: {e}")
        # Adicionar notificação de erro (ex: SNS) ou dead-letter queue (DLQ) para a Lambda
        raise e # Levantar a exceção para que a Lambda possa tentar novamente ou ir para DLQ

# Exemplo de evento S3 (simplificado) para teste local:
# if __name__ == "__main__":
#     mock_s3_event = {
#         "Records": [
#             {
#                 "s3": {
#                     "bucket": {"name": "tcc-kelly-raw-turbine-data-bucket-test"}, # Use um bucket de teste
#                     "object": {"key": "raw_data/year=2025/month=05/day=13/hour=10/some_firehose_delivery.json.gz"} # Exemplo de chave
#                 }
#             }
#         ]
#     }
#     # Para testar localmente, você precisaria:
#     # 1. Ter o awswrangler e pandas instalados.
#     # 2. Configurar credenciais AWS.
#     # 3. Criar os buckets S3 de origem e destino.
#     # 4. Colocar um arquivo JSON (ou JSON Lines, gzippado) no bucket de origem no caminho esperado.
#     #    O conteúdo do JSON deve ser uma lista de dicionários como os gerados por simulate_turbine_data.py
#     # print(lambda_handler(mock_s3_event, None))
#     print("Para testar localmente, descomente e configure o mock_s3_event e o ambiente AWS.")

