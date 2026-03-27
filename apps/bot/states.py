from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_email = State()
    waiting_photo = State()
