from pydantic import BaseModel, Field
from typing import Optional, List


class OperatorSearchResult(BaseModel):
    # Use Field alias if Python variable name differs from DB column or desired JSON key
    registro_ans: int = Field(..., alias="registro_ans")
    cnpj: Optional[str] = Field(None, alias="cnpj")
    razao_social: str = Field(..., alias="razao_social")
    nome_fantasia: Optional[str] = Field(None, alias="nome_fantasia")
    modalidade: Optional[str] = Field(None, alias="modalidade")
    cidade: Optional[str] = Field(None, alias="cidade")
    uf: Optional[str] = Field(None, alias="uf")
    rank: Optional[float] = Field(None)  # Relevance score from FTS

    class Config:
        from_attributes = True

        populate_by_name = True


class OperatorSearchResponse(BaseModel):
    total_count: int
    results: List[OperatorSearchResult]
