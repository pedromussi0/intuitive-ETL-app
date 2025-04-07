## Visão Geral do Projeto

O projeto consiste em um conjunto de serviços e scripts que realizam as seguintes s principais:

1.  **Coleta de Dados:** Busca e baixa arquivos públicos da Agência Nacional de Saúde Suplementar (ANS).

2.  **Transformação:** Extrai e limpa dados de arquivos PDF específicos (Rol de Procedimentos).

3.  **Armazenamento:** Estrutura e importa dados cadastrais e financeiros da ANS em um banco de dados PostgreSQL.

4.  **Consulta via API:** Disponibiliza uma API RESTful para realizar buscas textuais nas operadoras cadastradas.

5.  **Interface Web:** Oferece uma interface simples (frontend) para interagir com a API de busca.

Todo o ambiente é configurado para rodar de forma containerizada utilizando Docker e Docker Compose.

## Índice

*   [Detalhes dos Módulos](#detalhes-dos-módulos)
    *   [1. Web Scraping](#1-web-scraping)
    *   [Transformação de Dados](#2-transformação-de-dados)
    *   [Banco de Dados](#3-banco-de-dados)
    *   [API (Backend)](#4-api-backend)
    *   [Frontend (Interface Web)](#5-frontend-interface-web)

## Detalhes dos Módulos

### 1. Web Scraping

*   **Diretório:** [`services/scraper/`](services/scraper/)
*   **Objetivo:** Acessar a página de atualização do Rol de Procedimentos da ANS, encontrar e baixar os PDFs "Anexo I - Rol de Procedimentos..." e "Anexo II - Diretrizes...", e compactá-los em um único arquivo ZIP.
*   **Implementação:**
    *   `scraper_utils.py`: Contém funções auxiliares para:
        *   Criar diretórios (`create_directories`).
        *   Buscar conteúdo HTML de uma UR.
        *   Encontrar links específicos de PDF no HTML.
        *   Baixar um arquivo de uma URL com retentativas.
        *   Criar um arquivo ZIP a partir de uma lista de arquivos.
    *   `main.py`: Orquestra o processo chamando as funções do `scraper_utils` na sequência correta (criar dirs -> buscar página -> achar links -> baixar arquivos -> zipar).
*   **Resultado:** Arquivo `data/processed/Anexos_Rol.zip` contendo os PDFs `anexo_i.pdf` e `anexo_ii.pdf` baixados.


### 2. Transformação de Dados

*   **Diretório:** [`services/transformer/`](services/transformer/)
*   **Objetivo:** Extrair a tabela "Rol de Procedimentos e Eventos em Saúde" do PDF `Anexo I` (obtido na  1), limpar os dados, substituir abreviações ("OD", "AMB") por seus significados completos, e salvar o resultado em um arquivo CSV estruturado, compactado como `Teste_pedro_mussi.zip`.
*   **Implementação:**
    *   `pdf_parser.py`: Utiliza `pdfplumber` para abrir o `anexo_i.pdf` (localizado em `data/raw/`) e extrair todas as tabelas a partir da página 3, limpando o texto das células.
    *   `data_cleaner.py`: Recebe as tabelas extraídas, identifica a linha de cabeçalho (procurando por colunas comuns), consolida as linhas de dados válidas (com mesmo número de colunas do cabeçalho) e aplica a substituição dos textos "OD" e "AMB" pelas descrições completas nas colunas correspondentes.
    *   `main.py`: Coordena o processo: chama o parser, o cleaner/transformer, salva o resultado em `data/processed/rol_procedimentos.csv` (delimitador `;`), e compacta este CSV no arquivo `data/processed/Teste_pedro_mussi.zip`.
*   **Resultado:** Arquivo `data/processed/Teste_pedro_mussi.zip`.

    
![Transformer Output CSV](https://github.com/user-attachments/assets/29379bd4-961f-405f-b64a-668691ec7860)
    

### 3. Banco de Dados

*   **Diretório:** [`services/database/`](services/database/)
*   **Objetivo:** Baixar dados públicos adicionais da ANS (Demonstrações Contábeis, Cadastro de Operadoras), estruturar um banco de dados PostgreSQL, importar esses dados e realizar consultas analíticas.
*   **Implementação:**
    *   `downloader.py`: Baixa os arquivos CSV/ZIP das Demonstrações Contábeis dos últimos 2 anos e o CSV do Cadastro de Operadoras (`Relatorio_cadop.csv`) do FTP da ANS para `data/raw/db_source/`.
    *   `sql/01_schema.sql`: Script SQL (`CREATE TABLE IF NOT EXISTS`) para definir as tabelas `operadoras` e `demonstracoes_contabeis`.
    *   `importer.py`: Script Python (`psycopg2`) que lê os CSVs baixados , realiza `TRUNCATE` e os importa para as tabelas do PostgreSQL, **validando a existência do `Registro_ANS`** na tabela `operadoras` antes de inserir em `demonstracoes_contabeis` para garantir integridade referencial (linhas órfãs são ignoradas). Usa inserção em lote.
    *   `sql/05_fts_setup.sql`: Script SQL para configurar o Full-Text Search (FTS) na tabela `operadoras` (coluna `fts_document`, trigger `tsvectorupdate`, índice GIN).
    *   `sql/03_analysis_quarter.sql` e `sql/04_analysis_year.sql`: Queries SQL que calculam as 10 operadoras com maiores despesas em "EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS..." no último trimestre e no último ano completo, respectivamente.
*   **Resultado:** Banco de dados PostgreSQL populado e pronto para consulta; resultados das queries analíticas.

    
       ![image](https://github.com/user-attachments/assets/794fdc47-9b7e-4a38-8632-1f8a74ef64d2)

    
       ![image](https://github.com/user-attachments/assets/03f43351-2a5d-49e1-b577-9aee6abab1db)

    
### 4. API (Backend)

*   **Diretório:** [`services/api/`](services/api/)
*   **Objetivo:** Criar um servidor web com uma rota (`GET /api/v1/operators/search`) para busca textual na lista de operadoras cadastradas (3.2), retornando os registros mais relevantes.
*   **Tecnologias:** FastAPI, Uvicorn, Asyncpg, Pydantic.
*   **Implementação:**
    *   Servidor FastAPI assíncrono com gestão de ciclo de vida para pool de conexões DB (`main.py`, `database.py`).
    *   Endpoint de busca que utiliza parâmetros `q`, `limit`, `offset` (`routers/operators.py`).
    *   Lógica de serviço (`services/search_service.py`) que consulta o PostgreSQL usando **Full-Text Search (FTS)** configurado na  3 (via `plainto_tsquery`, `ts_rank_cd`) e retorna resultados paginados e ordenados por relevância. Trata a conversão `BIGINT` -> `String` para o CNPJ.
    *   Modelos Pydantic para respostas (`models/operator.py`).
    *   Configuração CORS para acesso do frontend.

*   **Resultado:** API RESTful rodando e respondendo a buscas textuais.
    
    ![image](https://github.com/user-attachments/assets/ddde35cf-4e2d-4ad1-b542-9f2baa2912de)

    ![image](https://github.com/user-attachments/assets/75fd2b76-575d-43a3-bb55-90dd09bc7e73)

    ![image](https://github.com/user-attachments/assets/02d30197-8ed0-49c0-95fd-b70d345e09f6)


### 5. Frontend (Interface Web)

*   **Diretório:** [`frontend/`](frontend/)
*   **Objetivo:** Desenvolver uma interface web usando Vue.js para interagir com a API de busca de operadoras criada.
*   **Tecnologias:** Vue 3, Vite, Tailwind CSS, Nginx.
*   **Implementação:**
    *   Componente Vue (`OperatorSearch.vue`) com input de busca e exibição de resultados.
    *   Consome o endpoint `GET /api/v1/operators/search` do backend.
    *   Exibe a lista de operadoras encontradas com informações relevantes.
    *   Interface estilizada com Tailwind CSS.
    *   Configuração de build via Vite e serviço de arquivos estáticos via Nginx (Docker).

*   **Resultado:** Aplicação web funcional acessível pelo navegador para buscar operadoras.

    ![image](https://github.com/user-attachments/assets/91dbe38e-bf9e-4c59-a136-5cbf636149c4)
