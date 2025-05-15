from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from states import ItemForm
from markups import confirmation, menu

router = Router()

@router.callback_query(ItemForm.price_in_eur)
async def add_item(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    if callback_query.data == "allow":
        await callback_query.answer("Added!")
    if callback_query.data == "deny":
        await callback_query.answer("Denied!")
    await bot.edit_message_caption(
        caption=(
            "✨ <b>Welcome to our store!</b>\n\n"
            "Here you will find your favorite brands at a price 4-5 times lower than on official websites.\n\n"
            "🔂We work directly with original factories - no intermediaries and markups.\n\n"
            "🔂We will deliver the goods to anywhere in the world for free.\n\n"
            "🔂If you want, we will help you choose a model personally for you!\n\n"
        ),
        reply_markup=await menu(callback_query.from_user.id),
        message_id=data["message_id"],
        chat_id=callback_query.from_user.id
    )
    await state.clear()

@router.callback_query()
async def set_action(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    actions = ["add_item", "delete_item"]
    if callback_query.data in actions:
        current = await bot.edit_message_caption(
            caption="Select or enter category:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id
        )
        await state.set_data({
            "action": callback_query.data,
            "message_id": current.message_id
        })
        await state.set_state(ItemForm.category)

@router.message(ItemForm.category)
async def set_category(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    if data.get("action") == "add_item":
        await bot.edit_message_caption(
            caption="Enter item title:",
            chat_id=message.from_user.id,
            message_id=data["message_id"]
        )
        await state.update_data({"category": message.text})
        await state.set_state(ItemForm.title)
    await message.delete()

@router.message(ItemForm.title)
async def set_title(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await bot.edit_message_caption(
        caption="Enter item price per EUR:",
        chat_id=message.from_user.id,
        message_id=data["message_id"]
    )
    await state.update_data({"title": message.text})
    await state.set_state(ItemForm.price_in_eur)
    await message.delete()

@router.message(ItemForm.price_in_eur)
async def set_price(message: Message, state: FSMContext, bot: Bot):
    await state.update_data({"price": message.text})
    data = await state.get_data()
    await bot.edit_message_caption(
        caption=(
            f"Category: {data.get('category')}\n"
            f"Title: {data.get('title')}\n"
            f"Price: {data.get('price')} EUR"
        ),
        chat_id=message.from_user.id,
        message_id=data["message_id"],
        reply_markup=await confirmation(data["action"])
    )
    await message.delete()