from aiogram.fsm.state import State, StatesGroup

class Appointment(StatesGroup):
    waiting_for_confirmation = State()

class CouponStates(StatesGroup):
    waiting_for_choice = State()
    waiting_for_sessions = State()
    waiting_for_recipient = State()
    waiting_for_contact_method = State()
    waiting_for_telegram_contact = State()
    waiting_for_phone_contact = State()
    waiting_for_contact_info = State()
    waiting_for_sender = State()

class AdminStates(StatesGroup):
    waiting_for_coupon_id = State()
    waiting_for_date = State()
    waiting_for_schedule_action = State()
    waiting_for_coupon_to_mark = State()
    waiting_for_date_to_block = State()      
    waiting_for_date_to_unblock = State()