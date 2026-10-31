from typing import Any

from fastapi import APIRouter, Depends

from app.services import auth, costs

router = APIRouter(prefix="/api/ops", tags=["ops"], dependencies=[Depends(auth.owner_only)])


@router.get("/runs")
def runs() -> dict[str, Any]:
    """Runs with duration, status per stage and cost per step (units estimated from the price table)."""
    return {"prices": costs.PRICES, "budget_usd": costs.PLAN_BUDGET_USD, "runs": costs.list_runs()}
