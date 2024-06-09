import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from models import MoneyTransaction, TransactionType, User
from pydantic_models.transaction import WithdrawCreate
from services.transaction_service import TransactionService
from services.redis_service import RedisService


@pytest.fixture
def mock_db_session(mocker):
    return mocker.MagicMock()


@pytest.fixture
def mock_redis_service(mocker):
    service = mocker.MagicMock(RedisService)
    service.get = AsyncMock(return_value=None)
    service.set = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_user_service(mocker):
    return mocker.patch('services.user_service.UserService')


@pytest.fixture
def sender_user():
    return User(id=1, balance=Decimal('1000.00'))


@pytest.fixture
def receiver_user():
    return User(id=2, balance=Decimal('500.00'))


def test_transfer_money(mock_db_session, sender_user, receiver_user):
    transaction = TransactionService.transfer_money(
        mock_db_session, sender_user, receiver_user, Decimal('100.00'), TransactionType.TRANSFER
    )

    assert sender_user.balance == Decimal('900.00')
    assert receiver_user.balance == Decimal('600.00')
    assert transaction.sender_id == sender_user.id
    assert transaction.receiver_id == receiver_user.id
    assert transaction.amount == Decimal('100.00')
    assert transaction.type == TransactionType.TRANSFER
    mock_db_session.add.assert_called_once_with(transaction)


def test_withdraw_money_success(mock_db_session, sender_user):
    with patch('services.user_service.UserService.fetch', return_value=sender_user):
        transaction = WithdrawCreate(sender_id=1, amount=Decimal('200.00'))

        db_transaction = TransactionService.withdraw_money(mock_db_session, transaction)

        assert sender_user.balance == Decimal('800.00')
        assert db_transaction.sender_id == sender_user.id
        assert db_transaction.amount == Decimal('200.00')
        assert db_transaction.type == TransactionType.WITHDRAWAL
        mock_db_session.add.assert_called_once_with(db_transaction)


def test_withdraw_money_insufficient_balance(mock_db_session, sender_user):
    with patch('services.user_service.UserService.fetch', return_value=sender_user):
        transaction = WithdrawCreate(sender_id=1, amount=Decimal('2000.00'))

        with pytest.raises(Exception, match="Insufficient balance"):
            TransactionService.withdraw_money(mock_db_session, transaction)

        assert sender_user.balance == Decimal('1000.00')
        mock_db_session.add.assert_not_called()


def test_withdraw_money_user_not_found(mock_db_session):
    with patch('services.user_service.UserService.fetch', return_value=None):
        transaction = WithdrawCreate(sender_id=1, amount=Decimal('200.00'))

        with pytest.raises(Exception, match="User not found"):
            TransactionService.withdraw_money(mock_db_session, transaction)

        mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_get_all_transactions(mock_db_session, mock_redis_service):
    mock_db_session.query(MoneyTransaction).all.return_value = [
        MoneyTransaction(id=1, sender_id=1, receiver_id=2, amount=Decimal('100.00'), type=TransactionType.TRANSFER)
    ]

    transactions = await TransactionService.get_all_transactions(mock_db_session, mock_redis_service)

    assert len(transactions) == 1
    assert transactions[0]['id'] == 1
    assert transactions[0]['sender_id'] == 1
    assert transactions[0]['receiver_id'] == 2
    assert transactions[0]['amount'] == '100.00'
    assert transactions[0]['type'] == TransactionType.TRANSFER


@pytest.mark.asyncio
async def test_get_user_transactions(mock_db_session, mock_redis_service, sender_user):
    mock_db_session.query(MoneyTransaction).all.return_value = [
        MoneyTransaction(id=1, sender_id=1, receiver_id=2, amount=Decimal('100.00'), type=TransactionType.TRANSFER),
        MoneyTransaction(id=2, sender_id=2, receiver_id=1, amount=Decimal('50.00'), type=TransactionType.TRANSFER)
    ]
    mock_redis_service.get.return_value = None

    transactions = await TransactionService.get_user_transactions(mock_db_session, mock_redis_service, user_id=1)

    assert len(transactions) == 2
    assert transactions[0]['sender_id'] == 1 or transactions[0]['receiver_id'] == 1


@pytest.mark.asyncio
async def test_get_transactions_between_users(mock_db_session, mock_redis_service, sender_user, receiver_user):
    mock_db_session.query(MoneyTransaction).all.return_value = [
        MoneyTransaction(id=1, sender_id=1, receiver_id=2, amount=Decimal('100.00'), type=TransactionType.TRANSFER),
        MoneyTransaction(id=2, sender_id=2, receiver_id=1, amount=Decimal('50.00'), type=TransactionType.TRANSFER),
        MoneyTransaction(id=3, sender_id=1, receiver_id=3, amount=Decimal('30.00'), type=TransactionType.TRANSFER)
    ]
    mock_redis_service.get.return_value = None

    transactions = await TransactionService.get_transactions_between_users(mock_db_session, mock_redis_service, user1_id=1, user2_id=2)

    assert len(transactions) == 2
    assert all((t['sender_id'] in [1, 2] and t['receiver_id'] in [1, 2]) for t in transactions)
