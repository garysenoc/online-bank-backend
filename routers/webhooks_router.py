from typing import Annotated

from fastapi import APIRouter, Header, Request

router = APIRouter(
    prefix = "/webhooks"
)

@router.post('/payment', status_code = 200)
async def payments(signature: Annotated[str, Header()], req: Request):
  print(req.body)
  print(signature)