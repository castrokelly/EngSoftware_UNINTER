# TCC Engenharia de Software - UNINTER
## Desenvolvimento de um Sistema Preditivo de Falhas em Equipamentos da Indústria de Energia utilizando Aprendizado de Máquina e Arquitetura Serverless na Nuvem

**Autora:** Kelly Christine Alvarenga de Castro

Este repositório contém todos os artefatos de software desenvolvidos para o Trabalho de Conclusão de Curso em Engenharia de Software pela UNINTER.

## Estrutura do Projeto

O projeto está organizado da seguinte forma:

-   `aws_lambda_functions/`: Contém o código Python para as funções AWS Lambda.
    -   `lambda_ingest_data.py`: Função para ingestão de dados simulados.
    -   `lambda_process_data.py`: Função para processamento de dados e extração de features.
    -   `lambda_predict_failure.py`: Função para realizar predições usando o modelo treinado.
-   `dashboard_frontend/`: Contém o código-fonte do dashboard de visualização desenvolvido em React.
    -   `src/App.js`: Componente principal da aplicação React.
    -   (Outros arquivos e pastas gerados pelo `create-react-app`)
-   `data_simulation/`:
    -   `simulate_turbine_data.py`: Script Python para gerar dados simulados de sensores de turbinas eólicas.
-   `docs/`: Contém documentos descritivos da arquitetura e configuração de serviços AWS.
    -   `api_gateway_config_description.md`: Descrição da configuração do Amazon API Gateway.
    -   `kinesis_firehose_config_description.md`: Descrição da configuração do Amazon Kinesis Data Firehose.
    -   `step_functions_config_description.md`: Descrição conceitual da orquestração com AWS Step Functions.
-   `notebooks/`:
    -   `model_training.ipynb`: Notebook Jupyter para análise exploratória de dados, treinamento e avaliação dos modelos de machine learning.
-   `modelo_salvo/` (Este diretório seria onde os modelos treinados e scalers seriam salvos localmente pelo notebook, mas no fluxo serverless, eles são salvos no S3. O notebook detalha o processo de salvamento e carregamento do S3).

## Como Utilizar

1.  **Texto do TCC:** O documento principal do TCC (`TCC_Kelly_Castro_EngSoftware_UNINTER.md` ou `.pdf/.docx`) descreve toda a pesquisa, metodologia, desenvolvimento e resultados.
2.  **Simulação de Dados:** Execute o script `data_simulation/simulate_turbine_data.py` para gerar dados de exemplo.
   ```bash
   python data_simulation/simulate_turbine_data.py
   ```
3.  **Notebook de Treinamento:** Abra e execute o notebook `notebooks/model_training.ipynb` em um ambiente Jupyter com as bibliotecas Python necessárias instaladas (Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn, Joblib, Boto3, AWSWrangler). Este notebook detalha o processo de carregamento de dados (simulados ou do S3), treinamento e avaliação dos modelos.
4.  **Funções Lambda:** O código em `aws_lambda_functions/` é projetado para ser implantado na AWS Lambda. Cada função tem suas dependências e configurações específicas (como permissões IAM e variáveis de ambiente) que precisariam ser configuradas no console da AWS ou via IaC (Infrastructure as Code) como SAM ou CDK.
    *   A `lambda_ingest_data.py` enviaria dados para o Kinesis Firehose.
    *   A `lambda_process_data.py` seria acionada por novos dados no S3 (via Kinesis) para processá-los.
    *   A `lambda_predict_failure.py` carregaria o modelo do S3 e serviria predições via API Gateway.
5.  **Dashboard Frontend:**
    *   Navegue até o diretório `dashboard_frontend/`.
    *   Instale as dependências: `npm install` (ou `pnpm install` se configurado).
    *   Inicie o servidor de desenvolvimento: `npm start`.
    *   Abra o navegador em `http://localhost:3000`.
    *   **Importante:** O arquivo `dashboard_frontend/src/App.js` contém uma constante `API_ENDPOINT` que precisa ser atualizada com o URL real do seu endpoint do API Gateway após a implantação da `lambda_predict_failure`.

## Implantação na AWS (Conceitual)

A implantação completa dos componentes serverless na AWS envolveria:

1.  **Configuração de Buckets S3:** Para dados brutos, dados processados e artefatos de modelo.
2.  **Configuração do Kinesis Data Firehose:** Para streaming de dados brutos para o S3.
3.  **Criação de Funções Lambda:** Upload do código e configuração de gatilhos, permissões IAM e variáveis de ambiente.
4.  **Criação do API Gateway:** Para expor a `lambda_predict_failure` como um endpoint HTTP.
5.  **Treinamento e Salvamento do Modelo:** Executar o notebook `model_training.ipynb` para treinar e salvar o modelo e o scaler no S3.
6.  **Hospedagem do Dashboard:** Build do projeto React e upload dos arquivos estáticos para um bucket S3 configurado para hospedagem de site, opcionalmente com CloudFront para distribuição.

Consulte os arquivos em `docs/` para descrições conceituais da configuração de alguns desses serviços.

## Requisitos

*   Python 3.8+
*   Bibliotecas Python listadas no notebook e nos scripts (Pandas, NumPy, Scikit-learn, Boto3, AWSWrangler, etc.)
*   Node.js e npm para o dashboard React
*   Conta AWS para implantação dos componentes serverless (opcional, para teste completo do fluxo)

Este projeto visa demonstrar a aplicação de Engenharia de Software e Aprendizado de Máquina na criação de uma solução de manutenção preditiva.

