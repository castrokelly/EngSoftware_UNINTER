### Configuração do Amazon API Gateway para Expor a API de Predição

O Amazon API Gateway é um serviço totalmente gerenciado que facilita a criação, publicação, manutenção, monitoramento e proteção de APIs em qualquer escala. No contexto deste TCC, o API Gateway será utilizado para criar um endpoint HTTP RESTful que exporá a funcionalidade de predição de falhas, servindo como a interface entre o dashboard de visualização (ou outros clientes) e a função Lambda de inferência (`lambda_predict_failure.py`).

**Principais Etapas de Configuração do API Gateway (a serem detalhadas no TCC):**

1.  **Criação da API:**
    *   **Tipo de API:** API REST (HTTP API também é uma opção mais leve, mas API REST oferece mais funcionalidades como validação de requests, transformation templates, etc. Para este protótipo, uma API REST é adequada).
    *   **Nome e Descrição da API:** Definir um nome significativo (ex: `FailurePredictionAPI`) e uma descrição.

2.  **Criação de Recursos e Métodos:**
    *   **Recurso:** Criar um recurso para representar o endpoint de predição (ex: `/predict` ou `/turbine/predict`).
    *   **Método HTTP:** Para o recurso `/predict`, criar um método `POST`, pois os dados da janela de features para predição serão enviados no corpo da requisição.

3.  **Integração com a Função Lambda de Inferência:**
    *   **Tipo de Integração:** `Lambda Function`.
    *   **Usar Integração de Proxy Lambda (Lambda Proxy Integration):** Esta é a forma recomendada e mais simples. Com a integração de proxy, o API Gateway passa todo o evento da requisição HTTP (incluindo headers, corpo, parâmetros de query string, etc.) diretamente para a função Lambda. A Lambda, por sua vez, deve retornar uma resposta em um formato específico que o API Gateway entende para construir a resposta HTTP.
    *   **Função Lambda:** Especificar o ARN da função `lambda_predict_failure.py`.
    *   **Permissões:** Conceder permissão para o API Gateway invocar a função Lambda. Isso geralmente é feito automaticamente ao configurar a integração pelo console, ou pode ser adicionado via AWS CLI/SDK/IaC (ex: `aws lambda add-permission`).

4.  **Modelos de Dados e Validação de Requisição (Opcional, mas Recomendado para APIs robustas):**
    *   **Modelos (Models):** Definir um modelo JSON Schema para o corpo da requisição `POST /predict`, especificando as features esperadas e seus tipos de dados. Isso permite que o API Gateway valide o payload da requisição antes de invocar a Lambda, retornando um erro 400 (Bad Request) se o payload for inválido.
    *   **Validação de Requisição:** Habilitar a validação do corpo da requisição usando o modelo definido.

5.  **Configuração de Resposta do Método (Method Response) e Resposta de Integração (Integration Response):**
    *   Com a integração de proxy Lambda, a Lambda é responsável por formatar a resposta HTTP completa (statusCode, headers, body). O API Gateway simplesmente passa essa resposta de volta ao cliente.
    *   É bom definir os códigos de status HTTP esperados (ex: 200 OK, 400 Bad Request, 500 Internal Server Error) na configuração do Método de Resposta para documentação da API.

6.  **Autorização (Opcional para este protótipo, mas crucial para APIs de produção):**
    *   Para proteger a API, podem ser configurados autorizadores, como:
        *   **IAM:** Para autenticação baseada em credenciais AWS.
        *   **Amazon Cognito User Pools:** Para autenticação de usuários.
        *   **Lambda Authorizers (Custom Authorizers):** Para lógicas de autorização personalizadas.
    *   Para o protótipo do TCC, a API pode ser inicialmente implantada sem autorização complexa para simplificar, mas a importância da segurança deve ser mencionada.

7.  **CORS (Cross-Origin Resource Sharing):**
    *   Se o dashboard de visualização for hospedado em um domínio diferente da API, será necessário habilitar o CORS no API Gateway. Isso envolve configurar os cabeçalhos `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers` nas respostas do método (especialmente para o método `OPTIONS` que o navegador envia como preflight request).

8.  **Implantação da API (Deployment):**
    *   Após configurar a API, ela deve ser implantada em um estágio (Stage), como `dev`, `test` ou `prod` (ex: `v1`).
    *   A implantação gera um URL de invocação público para a API (ex: `https://{api-id}.execute-api.{region}.amazonaws.com/{stageName}/predict`).

9.  **Monitoramento e Logging:**
    *   O API Gateway se integra com o Amazon CloudWatch para logging de acessos, erros e métricas de desempenho (como latência, contagem de requisições, erros 4XX/5XX).
    *   Habilitar o logging de execução e o logging de acesso no CloudWatch para o estágio da API.

Ao utilizar o API Gateway, cria-se um ponto de entrada gerenciado, seguro e escalável para a lógica de predição implementada na função Lambda. A descrição detalhada desta configuração, incluindo exemplos de como a função Lambda `lambda_predict_failure.py` deve formatar sua resposta para a integração de proxy, será incluída no capítulo de Desenvolvimento do Software do TCC.
