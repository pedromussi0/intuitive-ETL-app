from pydantic import BaseModel, Field
from typing import Optional, List

class OperatorSearchResult(BaseModel):
    # Use Field alias if Python variable name differs from DB column or desired JSON key
    registro_ans: int = Field(..., alias='Registro_ANS')
    cnpj: Optional[str] = Field(None, alias='CNPJ')
    razao_social: str = Field(..., alias='Razao_Social')
    nome_fantasia: Optional[str] = Field(None, alias='Nome_Fantasia')
    modalidade: Optional[str] = Field(None, alias='Modalidade')
    cidade: Optional[str] = Field(None, alias='Cidade')
    uf: Optional[str] = Field(None, alias='UF')
    rank: Optional[float] = Field(None) # Relevance score from FTS

    class Config:
        from_attributes = True
        
        populate_by_name = True 

class OperatorSearchResponse(BaseModel):
    total_count: int
    results: List[OperatorSearchResult]