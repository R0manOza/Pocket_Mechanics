"""Lab 8 — Pydantic schemas for MCP tool inputs."""

from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError


class PocketMechanicsTipInput(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    vehicle_hint: str = Field(default="", max_length=200)
    auth_token: str = Field(default="", alias="_auth_token")

    model_config = {"populate_by_name": True, "extra": "ignore"}


def validate_tool_input(tool_name: str, arguments: dict) -> PocketMechanicsTipInput:
    if tool_name != "ask_pocket_mechanics_tip":
        raise ValueError("unknown_tool")
    return PocketMechanicsTipInput(**(arguments or {}))
