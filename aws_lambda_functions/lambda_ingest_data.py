import json
import boto3
import os
import datetime

# Nome do bucket S3 para onde os dados brutos serão enviados pelo Kinesis Firehose
# Este bucket deve ser configurado como destino no Kinesis Data Firehose
RAW_DATA_BUCKET = os.environ.get("RAW_DATA_BUCKET_NAME", "tcc-kelly-raw-turbine-data-bucket")

# Cliente S3
s3_client = boto3.client("s3")

def lambda_handler(event, context):
    """
    Função Lambda para simular a ingestão de dados de sensores de turbinas eólicas.
    Em um cenário real, esta função poderia ser acionada por um evento do IoT Core
    ou receber dados diretamente de sensores.
    Para este protótipo, ela lê os arquivos JSON simulados e os envia para 
    um stream do Kinesis Data Firehose (que por sua vez os salvará no S3).
    
    Alternativamente, se o Kinesis Firehose não for usado diretamente na ingestão inicial,
    esta Lambda poderia processar os dados e colocá-los diretamente no S3 
    no formato esperado pelo restante do pipeline.
    
    Para simplificar e focar no fluxo serverless, vamos simular que esta Lambda
    recebe um batch de dados (por exemplo, de um arquivo JSON) e o envia para o Firehose.
    Neste exemplo, vamos assumir que o evento de entrada contém o nome do arquivo 
    JSON simulado a ser processado.
    """
    print(f"Evento recebido: {event}")

    # Para este exemplo, vamos assumir que o evento contém o nome de um arquivo
    # no diretório de simulação. Em um cenário real, os dados viriam de outra fonte.
    # Exemplo de evento esperado: {"simulation_file": "turbine_1_data.json"}
    
    simulation_file_name = event.get("simulation_file")
    if not simulation_file_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Nome do arquivo de simulação não fornecido no evento."})
        }

    # Caminho para os dados simulados (ajustar conforme necessário se a Lambda tiver acesso ao EFS ou S3)
    # Para este protótipo, vamos assumir que a Lambda tem acesso a um diretório local
    # onde os dados simulados foram colocados (o que não é típico para Lambdas reais sem EFS).
    # Uma abordagem mais realista seria a Lambda ler de um bucket S3 onde os arquivos simulados foram carregados.
    
    # Simulando a leitura do arquivo (em um cenário real, isso seria diferente)
    # Vamos assumir que o arquivo está em um bucket S3 acessível pela Lambda.
    # Para este exemplo, vamos apenas simular o conteúdo.
    # Este código precisaria ser adaptado para ler o arquivo de onde ele realmente está (ex: S3)
    # ou para receber os dados diretamente no payload do evento.

    # ---- INÍCIO DA SIMULAÇÃO DE LEITURA DE ARQUIVO ----
    # Esta parte é uma simplificação. Em um deploy real, a Lambda não leria de /home/ubuntu.
    # Ela leria de S3 ou receberia os dados no evento.
    try:
        # Simulação: Ler o arquivo JSON do diretório local (NÃO FAZER ISSO EM PRODUÇÃO REAL SEM EFS)
        # Em um cenário real, o arquivo estaria em S3 e seria lido com s3_client.get_object
        # ou os dados viriam diretamente no evento.
        # Para fins de prototipagem local, vamos manter assim, mas com ressalvas.
        file_path = f"/home/ubuntu/tcc_kelly_castro/data_simulation/{simulation_file_name}"
        with open(file_path, "r") as f:
            records = json.load(f)
        print(f"Lidos {len(records)} registros do arquivo {simulation_file_name}")
    except Exception as e:
        print(f"Erro ao ler o arquivo de simulação {simulation_file_name}: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Erro ao processar arquivo de simulação: {str(e)}"})
        }
    # ---- FIM DA SIMULAÇÃO DE LEITURA DE ARQUIVO ----

    # Nome do stream do Kinesis Data Firehose (deve ser criado previamente no AWS)
    firehose_stream_name = os.environ.get("FIREHOSE_STREAM_NAME", "tcc-kelly-turbine-data-firehose-stream")
    firehose_client = boto3.client("firehose")

    # Enviar registros para o Kinesis Data Firehose
    # O Firehose espera uma lista de dicionários com uma chave "Data"
    # O conteúdo de "Data" deve ser bytes, então serializamos para JSON e codificamos para UTF-8.
    # O Firehose adiciona uma nova linha automaticamente entre os registros se configurado.
    
    # Dividir em batches para não exceder limites do Firehose (PutRecordBatch)
    # Limite: 500 registros ou 4MB por batch
    batch_size = 450 # Um pouco abaixo do limite para segurança
    records_sent_count = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        firehose_records = []
        for record in batch:
            # Adicionar um timestamp de ingestão para rastreabilidade
            record["ingestion_timestamp_utc"] = datetime.datetime.utcnow().isoformat()
            firehose_records.append({"Data": json.dumps(record).encode("utf-8")})
        
        if not firehose_records:
            continue
            
        try:
            response = firehose_client.put_record_batch(
                DeliveryStreamName=firehose_stream_name,
                Records=firehose_records
            )
            print(f"Batch enviado para o Firehose. Resposta: {response}")
            if response.get("FailedPutCount", 0) > 0:
                print(f"Falha ao enviar alguns registros: {response.get('RequestResponses')}")
                # Adicionar lógica de tratamento de falhas/reprocessamento aqui
            else:
                records_sent_count += len(firehose_records)

        except Exception as e:
            print(f"Erro ao enviar batch para o Kinesis Data Firehose: {e}")
            # Adicionar lógica de tratamento de falhas aqui
            # Pode ser necessário reenviar ou registrar a falha
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Erro ao enviar dados para o Firehose: {str(e)}"})
            }

    print(f"Total de {records_sent_count} registros enviados para o Kinesis Data Firehose.")
    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"{records_sent_count} registros processados e enviados para o Firehose.", "source_file": simulation_file_name})
    }

# Exemplo de como testar localmente (não faz parte do código da Lambda em si)
if __name__ == "__main__":
    # Simular um evento de entrada
    # Certifique-se de que o arquivo simulate_turbine_data.py foi executado antes
    # e que os arquivos JSON existem no diretório especificado.
    
    # Para testar, você precisaria configurar credenciais AWS e ter o Firehose stream criado.
    # Este teste local é mais para a lógica da função, não para a interação real com AWS sem mocks.
    
    # Crie um arquivo de teste, por exemplo, turbine_1_data.json usando o simulate_turbine_data.py
    # e coloque-o em /home/ubuntu/tcc_kelly_castro/data_simulation/
    # (ou ajuste o caminho no código da Lambda - lembrando que isso é para teste local)
    
    # mock_event = {"simulation_file": "turbine_1_data.json"}
    # print(lambda_handler(mock_event, None))
    print("Para testar localmente, descomente as linhas acima e garanta que o ambiente AWS está configurado.")
    print("Lembre-se que o acesso a arquivos locais pela Lambda não é o padrão em produção.")

