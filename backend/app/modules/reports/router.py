from typing import Annotated

from fastapi import APIRouter, Query

from app.modules.auth.dependencies import DbSession, ManagerUser
from app.modules.reports import service
from app.modules.reports.schemas import ReportQuery, SalesReport

router = APIRouter(prefix="/reports", tags=["Relatórios"])


@router.get("/sales", response_model=SalesReport, summary="Relatório de vendas por período")
def sales_report(
    _: ManagerUser, db: DbSession, query: Annotated[ReportQuery, Query()]
) -> SalesReport:
    return service.sales_report(db, query)
