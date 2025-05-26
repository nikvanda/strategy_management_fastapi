from fastapi import APIRouter

router = APIRouter(prefix='/strategies')


@router.post('/')
async def create_strategy():
    pass


@router.get('/')
async def get_all_strategies():
    pass


@router.get('/{strategy_id}')
async def get_strategy():
    pass


@router.patch('/{strategy_id}')
async def update_strategy():
    pass


@router.delete('/{strategy_id}')
async def delete_strategy():
    pass


@router.post('/{strategy_id}/simulate')
async def get_strategy():
    pass
