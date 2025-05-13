### Configuração do Amazon Kinesis Data Firehose

Dentro da arquitetura serverless proposta para o sistema de manutenção preditiva, o Amazon Kinesis Data Firehose desempenha um papel crucial no pipeline de ingestão de dados. Ele atua como um serviço totalmente gerenciado para carregar dados de streaming de forma confiável em data lakes, data stores e ferramentas de análise.

No contexto deste TCC, o Kinesis Data Firehose será configurado para receber os dados de sensores das turbinas eólicas (enviados pela função Lambda `lambda_ingest_data.py`) e entregá-los de forma organizada e eficiente a um bucket do Amazon S3, que funcionará como o repositório central de dados brutos (data lake).

**Principais Etapas de Configuração (a serem detalhadas no TCC):**

1.  **Criação do Delivery Stream:**
    *   **Origem (Source):** Direct PUT (já que os dados serão enviados diretamente por uma função Lambda usando o AWS SDK).
    *   **Destino (Destination):** Amazon S3.
2.  **Transformação de Dados (Opcional, mas Recomendado):**
    *   O Firehose permite invocar uma função Lambda para transformar os dados em trânsito antes de entregá-los ao S3. Isso pode ser útil para converter formatos (ex: JSON para Parquet), enriquecer dados ou realizar validações adicionais. Para este protótipo, pode-se iniciar sem transformações complexas no Firehose, delegando-as para a etapa de processamento posterior, ou implementar uma transformação simples se necessário.
3.  **Configurações do Destino S3:**
    *   **Bucket S3:** Especificar o bucket S3 de destino (ex: `tcc-kelly-raw-turbine-data-bucket`).
    *   **Prefixação Dinâmica:** Configurar prefixos no S3 para organizar os dados de forma eficiente, facilitando consultas e processamentos futuros. Uma estrutura comum é baseada em data e hora da chegada dos dados, por exemplo: `year=YYYY/month=MM/day=DD/hour=HH/`.
    *   **Buffer Hints:** Configurar o tamanho do buffer (ex: 128 MiB) e o intervalo de buffer (ex: 900 segundos). O Firehose agrupa os dados recebidos e os entrega ao S3 quando o buffer atinge o tamanho ou o intervalo configurado, o que ocorrer primeiro. Isso ajuda a otimizar os custos de armazenamento e o número de objetos no S3.
    *   **Compressão de Dados:** Habilitar a compressão de dados (ex: GZIP ou SNAPPY) para reduzir os custos de armazenamento no S3 e melhorar o desempenho de consultas.
    *   **Criptografia de Dados:** Configurar a criptografia dos dados em repouso no S3 (ex: usando SSE-S3 ou SSE-KMS).
4.  **Permissões (IAM Role):**
    *   O Kinesis Data Firehose precisará de uma IAM Role com permissões para escrever no bucket S3 de destino e, se aplicável, para invocar a função Lambda de transformação e escrever logs no CloudWatch.
5.  **Monitoramento e Logging:**
    *   Habilitar o logging de erros para o CloudWatch Logs, permitindo o monitoramento da operação do delivery stream e a identificação de possíveis problemas na entrega dos dados.

Ao utilizar o Kinesis Data Firehose, simplifica-se a arquitetura de ingestão, pois ele lida automaticamente com o escalonamento, a entrega confiável e o agrupamento de dados, permitindo que as funções Lambda foquem na lógica de negócio da ingestão e do processamento inicial. A descrição detalhada desta configuração será incluída no capítulo de Desenvolvimento do Software do TCC, ilustrando como este serviço se integra ao pipeline serverless proposto.
