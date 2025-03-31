-- services/database/sql/01_schema.sql
-- Schema definition for ANS data

-- Disable foreign key checks temporarily for table creation/dropping if needed


DROP TABLE IF EXISTS demonstracoes_contabeis;
DROP TABLE IF EXISTS operadoras;

-- Tabela para os dados cadastrais das operadoras ativas
CREATE TABLE operadoras (
    Registro_ANS INT PRIMARY KEY,             -- Registro ANS as primary key
    CNPJ BIGINT UNIQUE,                       -- CNPJ 
    Razao_Social VARCHAR(255) NOT NULL,       -- Company's official name
    Nome_Fantasia VARCHAR(255),               -- Trading name
    Modalidade VARCHAR(100),                  -- Modality (e.g., Medicina de Grupo)
    Logradouro VARCHAR(255),                  -- Street address
    Numero VARCHAR(50),                       -- Street number
    Complemento VARCHAR(100),                 -- Address complement
    Bairro VARCHAR(100),                      -- Neighborhood
    Cidade VARCHAR(100),                      -- City
    UF CHAR(2),                               -- State abbreviation
    CEP VARCHAR(9),                           -- Postal Code (e.g., 00000-000)
    DDD VARCHAR(3),                           -- Area code
    Telefone VARCHAR(50),                     -- Phone number(s)
    Fax VARCHAR(50),                          -- Fax number(s)
    Endereco_eletronico VARCHAR(255),         -- Email address
    Representante VARCHAR(255),               -- Representative's name
    Cargo_Representante VARCHAR(100),         -- Representative's title
    Regiao_Comercializacao VARCHAR(100),      -- Region of operation (might be TEXT if long)
    Data_Registro_ANS DATE                    -- Date of registration with ANS
    -- Add other columns from the header if needed
);

-- Tabela para as demonstrações contábeis trimestrais
CREATE TABLE demonstracoes_contabeis (
    ID BIGSERIAL PRIMARY KEY,                 -- Auto-incrementing ID (PostgreSQL specific, use AUTO_INCREMENT for MySQL)
    DATA DATE NOT NULL,                       -- Date of the accounting report (end of quarter)
    REGISTRO_ANS INT NOT NULL,                -- Foreign key linking to operadoras table
    CONTA_CONTABIL VARCHAR(50) NOT NULL,      -- Accounting account code
    DESCRICAO VARCHAR(255) NOT NULL,          -- Description of the accounting account
    VL_SALDO_FINAL NUMERIC(18, 2),            -- Final balance value (adjust precision as needed)
    VL_SALDO_INICIAL NUMERIC(18, 2),          -- initial balance 

    
    CONSTRAINT fk_operadora
        FOREIGN KEY(REGISTRO_ANS)
        REFERENCES operadoras(Registro_ANS)
        ON DELETE CASCADE 
);

CREATE INDEX idx_demonstracoes_data ON demonstracoes_contabeis (DATA);
CREATE INDEX idx_demonstracoes_reg_ans ON demonstracoes_contabeis (REGISTRO_ANS);
CREATE INDEX idx_demonstracoes_conta ON demonstracoes_contabeis (CONTA_CONTABIL);
CREATE INDEX idx_demonstracoes_desc ON demonstracoes_contabeis (DESCRICAO); 

COMMIT; 