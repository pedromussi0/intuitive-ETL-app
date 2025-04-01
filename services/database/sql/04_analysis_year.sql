-- Top 10 operadoras com maiores despesas em "EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS ..." no último ano completo disponível.

WITH LatestDataYear AS (
    -- Find the year of the latest data entry
    SELECT EXTRACT(YEAR FROM MAX(DATA)) as max_year
    FROM demonstracoes_contabeis
),
TargetYear AS (
    -- Define the target year as the year before the latest data entry's year
    SELECT max_year - 1 as analysis_year
    FROM LatestDataYear
),
-- Calculate total expenses per operator for the target account in the target year
YearlyExpenses AS (
    SELECT
        dc.REGISTRO_ANS,
        SUM(dc.VL_SALDO_FINAL) AS total_despesa_ano
    FROM demonstracoes_contabeis dc
    JOIN TargetYear ty ON EXTRACT(YEAR FROM dc.DATA) = ty.analysis_year
    WHERE
        dc.DESCRICAO = 'EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS  DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR '
    GROUP BY
        dc.REGISTRO_ANS
)
-- Select operator details and order by the calculated expense
SELECT
    op.Registro_ANS,
    op.Razao_Social,
    ye.total_despesa_ano
FROM YearlyExpenses ye
JOIN operadoras op ON ye.REGISTRO_ANS = op.Registro_ANS
ORDER BY
    ye.total_despesa_ano DESC
LIMIT 10;