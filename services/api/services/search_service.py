import asyncpg
from typing import List, Tuple
from logging import getLogger
from ..models.operator import OperatorSearchResult  # Use relative import

logger = getLogger(__name__)


async def search_operators_db(
    pool: asyncpg.Pool, search_term: str, limit: int, offset: int
) -> Tuple[int, List[OperatorSearchResult]]:
    """
    Performs a full-text search on the operadoras table.
    Returns total count and a list of results.
    """

    search_query = """
        SELECT
            "registro_ans", "cnpj"::text AS "cnpj", "razao_social", "nome_fantasia",
            "modalidade", "cidade", "uf",
            COALESCE(ts_rank_cd(fts_document, query), 0) AS rank
        FROM operadoras, plainto_tsquery('portuguese', $1) query
        WHERE query @@ fts_document OR "registro_ans"::text = $1 -- Allow searching by exact ANS ID too
        ORDER BY rank DESC, "razao_social" ASC -- Primary sort by rank, secondary by name
        LIMIT $2 OFFSET $3;
    """

    # Query to get the total count matching the search term
    count_query = """
        SELECT COUNT(*)
        FROM operadoras, plainto_tsquery('portuguese', $1) query
        WHERE query @@ fts_document OR "registro_ans"::text = $1;
    """

    try:
        async with pool.acquire() as connection:
            # Execute count query first
            total_count_record = await connection.fetchrow(count_query, search_term)
            total_count = total_count_record["count"] if total_count_record else 0

            if total_count == 0:
                return 0, []

            # Execute search query
            records = await connection.fetch(search_query, search_term, limit, offset)

            # Convert asyncpg Records to Pydantic models
            results = []
            for record in records:
                record_dict = dict(record)

                if record_dict.get("CNPJ") is not None:
                    record_dict["CNPJ"] = str(record_dict["CNPJ"])
                results.append(OperatorSearchResult.model_validate(record_dict))

            return total_count, results

    except Exception as e:
        logger.exception(
            f"Database error during operator search for term '{search_term}': {e}"
        )
        raise RuntimeError(f"Database error during search: {e}")
