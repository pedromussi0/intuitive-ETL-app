-- Top 10 operadoras com maiores despesas em "EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS ..." no último trimestre disponível.

-- Find the latest date (end of quarter) available in the data
WITH LatestQuarter AS (
    SELECT MAX(DATA) as latest_data
    FROM demonstracoes_contabeis
),
-- Calculate total expenses per operator for the target account in the latest quarter
QuarterlyExpenses AS (
    SELECT
        dc.REGISTRO_ANS,
        SUM(dc.VL_SALDO_FINAL) AS total_despesa_trimestre
    FROM demonstracoes_contabeis dc
    JOIN LatestQuarter lq ON dc.DATA = lq.latest_data
    WHERE
        dc.DESCRICAO = 'EVENTOS/ SINISTROS CONHECIDOS OU AVISADOS  DE ASSISTÊNCIA A SAÚDE MEDICO HOSPITALAR '
    GROUP BY
        dc.REGISTRO_ANS
)
-- Select operator details and order by the calculated expense
SELECT
    op.Registro_ANS,
    op.Razao_Social,
    qe.total_despesa_trimestre
FROM QuarterlyExpenses qe
JOIN operadoras op ON qe.REGISTRO_ANS = op.Registro_ANS
ORDER BY
    qe.total_despesa_trimestre DESC
LIMIT 10;