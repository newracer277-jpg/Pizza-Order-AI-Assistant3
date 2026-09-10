import pytest
from modules.tools.user import (
    get_user_address,
    get_status_last_order,
    get_user_last_orders,
    save_user_address
)
from modules.tools.user import get_user_address


class FakeUser:
    def __init__(self, address=None):
        self.address = address


class FakeService:
    def __init__(self, user):
        self.user = user

    def get_user_data(self, user_id):
        return self.user


class FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def test_get_user_address_returns_address(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        "modules.tools.user.SessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        "modules.tools.user.UserService",
        lambda session: FakeService(
            FakeUser("Победа 22")
        ),
    )

    result = get_user_address.invoke({})

    assert result == "Адрес пользователя: Победа 22"


def test_get_user_address_returns_message_when_address_missing(
    monkeypatch,
):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        "modules.tools.user.SessionLocal",
        lambda: FakeSession(),
    )

    monkeypatch.setattr(
        "modules.tools.user.UserService",
        lambda session: FakeService(
            FakeUser(None)
        ),
    )

    result = get_user_address.invoke({})

    assert result == (
        "У вас нет сохранённого адреса. "
        "Пожалуйста, укажите адрес для доставки."
    )


def test_get_user_address_returns_message_when_user_id_missing(
    monkeypatch,
):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: None,
    )

    result = get_user_address.invoke({})

    assert result == (
        "Не удалось определить пользователя."
    )

def test_get_status_last_order_returns_status(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        "modules.tools.user.SessionLocal",
        lambda: FakeSession(),
    )

    class FakeServiceWithStatus:
        def get_user_data(self, user_id):
            return FakeUserWithOrder(123)

        def get_status(self, order_id):
            assert order_id == 123
            return "доставляется"

    class FakeUserWithOrder:
        def __init__(self, order_id):
            self.last_order_id = order_id

    monkeypatch.setattr(
        "modules.tools.user.UserService",
        lambda session: FakeServiceWithStatus(),
    )

    result = get_status_last_order.invoke({})

    assert result == (
        "Статус последнего заказа: доставляется"
    )


def test_get_status_last_order_user_not_found(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        "modules.tools.user.SessionLocal",
        lambda: FakeSession(),
    )

    class FakeService:
        def get_user_data(self, user_id):
            return None

    monkeypatch.setattr(
        "modules.tools.user.UserService",
        lambda session: FakeService(),
    )

    result = get_status_last_order.invoke({})

    assert result == "Пользователь не найден."


def test_get_status_last_order_without_orders(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        "modules.tools.user.SessionLocal",
        lambda: FakeSession(),
    )

    class FakeService:
        def get_user_data(self, user_id):
            user = FakeUser()
            user.last_order_id = None
            return user

    monkeypatch.setattr(
        "modules.tools.user.UserService",
        lambda session: FakeService(),
    )

    result = get_status_last_order.invoke({})

    assert result == "У пользователя нет заказов."


def test_get_status_last_order_without_user_id(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: None,
    )

    result = get_status_last_order.invoke({})

    assert result == (
        "Не удалось определить пользователя."
    )    


def test_get_user_last_orders_returns_orders(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        "modules.tools.user.SessionLocal",
        lambda: FakeSession(),
    )

    class FakeOrder:
        def __str__(self):
            return "Маргарита - 2 шт. - 678 руб."

    class FakeService:
        def get_user_orders(self, user_id, limit):
            assert user_id == 1
            assert limit == 10

            return [
                FakeOrder(),
            ]

    monkeypatch.setattr(
        "modules.tools.user.UserService",
        lambda session: FakeService(),
    )

    result = get_user_last_orders.invoke({})

    assert "Последние заказы:" in result
    assert "Маргарита - 2 шт. - 678 руб." in result

def test_get_user_last_orders_returns_empty_message(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        "modules.tools.user.SessionLocal",
        lambda: FakeSession(),
    )

    class FakeService:
        def get_user_orders(self, user_id, limit):
            assert user_id == 1
            assert limit == 10
            return []

    monkeypatch.setattr(
        "modules.tools.user.UserService",
        lambda session: FakeService(),
    )

    result = get_user_last_orders.invoke({})

    assert result == "У вас нет истории заказов."    


def test_get_user_last_orders_without_user_id(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: None,
    )

    result = get_user_last_orders.invoke({})

    assert result == "Не удалось определить пользователя."


def test_get_user_last_orders_handles_error(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        "modules.tools.user.SessionLocal",
        lambda: FakeSession(),
    )

    class FakeService:
        def get_user_orders(self, user_id, limit):
            raise RuntimeError("Ошибка базы данных")

    monkeypatch.setattr(
        "modules.tools.user.UserService",
        lambda session: FakeService(),
    )

    result = get_user_last_orders.invoke({})

    assert result == (
        "Ошибка при получении истории заказов: "
        "Ошибка базы данных"
    )

def test_save_user_address(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        "modules.tools.user.SessionLocal",
        lambda: FakeSession(),
    )

    class FakeService:
        def update_address(self, user_id, address):
            assert user_id == 1
            assert address == "Победа 22"

            return address

    monkeypatch.setattr(
        "modules.tools.user.UserService",
        lambda session: FakeService(),
    )

    result = save_user_address.invoke({
        "address": "Победа 22",
    })

    assert result == "Адрес сохранён: Победа 22"     


def test_save_user_address_without_user_id(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: None,
    )

    result = save_user_address.invoke({
        "address": "Победа 22",
    })

    assert result == "Не удалось определить пользователя."

def test_save_user_address_handles_error(monkeypatch):

    monkeypatch.setattr(
        "modules.tools.user.get_user_id",
        lambda: 1,
    )

    monkeypatch.setattr(
        "modules.tools.user.SessionLocal",
        lambda: FakeSession(),
    )

    class FakeService:
        def update_address(self, user_id, address):
            raise RuntimeError("Ошибка базы данных")

    monkeypatch.setattr(
        "modules.tools.user.UserService",
        lambda session: FakeService(),
    )

    result = save_user_address.invoke({
        "address": "Победа 22",
    })

    assert result == (
        "Ошибка сохранения адреса: "
        "Ошибка базы данных"
    )    