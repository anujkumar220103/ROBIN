# Pydantic schemas for health check API responses.

from pydantic import BaseModel


class RootResponse(BaseModel):
    name: str
    version: str
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class DatabaseHealthResponse(BaseModel):
    status: str
    database: str
