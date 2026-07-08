SELECT 
    substr(DtCriacao,1,10) AS DtDia,
    count(DISTINCT idCliente) AS DAU

FROM transacoes
GROUP BY DtDia
ORDER BY DtDia