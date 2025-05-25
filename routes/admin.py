from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, FSInputFile
from states import ItemForm, DeleteItemForm
from markups import confirmation, menu, gender_choice, category_choice, product_choice
from api.crud import create_product, del_product
from api.database import session
from api.models import Product

router = Router()

@router.callback_query(default_state)
async def choose_action(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    action = callback_query.data

    if action in ["add_item", "delete_item"]:
        await callback_query.answer()
        await state.set_data({
            "action": action,
            "message_id": callback_query.message.message_id
        })

        await bot.edit_message_caption(
            caption="🧍 Choose gender:",
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=await gender_choice()
        )
        await state.set_state(ItemForm.gender)

@router.callback_query(ItemForm.gender)
async def get_gender(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    gender = callback_query.data
    await state.update_data({"gender": gender})
    data = await state.get_data()

    if data["action"] == "add_item":
        await bot.edit_message_caption(
            caption="📂 Select or enter a category:",
            chat_id=callback_query.from_user.id,
            message_id=data["message_id"],
            reply_markup=await category_choice()
        )
        await state.set_state(ItemForm.category)

    elif data["action"] == "delete_item":
        await bot.edit_message_caption(
            caption="📦 Select product to delete:",
            chat_id=callback_query.from_user.id,
            message_id=data["message_id"],
            reply_markup=await product_choice(gender=gender)
        )
        await state.set_state(DeleteItemForm.product_id)

    await callback_query.answer()

@router.callback_query(DeleteItemForm.product_id)
async def delete_product(callback_query: CallbackQuery, state: FSMContext):
    async with session() as async_session:
        await del_product(async_session, int(callback_query.data))
    await callback_query.answer("🗑️ Item deleted!")
    await callback_query.message.edit_caption(
        caption=(
            "✨ <b>Welcome to our store!</b>\n\n"
            "Here you will find your favorite brands at prices 4–5 times lower than on official websites."
        ),
        reply_markup=await menu(callback_query.from_user.id)
    )
    await state.clear()

@router.callback_query(ItemForm.category)
async def get_category_callback(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data({"category": callback_query.data})

    if data["action"] == "add_item":
        await callback_query.message.edit_caption(caption="📝 Enter item title:")
        await state.set_state(ItemForm.title)

    await callback_query.answer()

@router.message(ItemForm.category)
async def get_category_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data({"category": message.text})

    if data["action"] == "add_item":
        await bot.edit_message_caption(
            caption="📝 Enter item title:",
            chat_id=message.from_user.id,
            message_id=data["message_id"]
        )
        await state.set_state(ItemForm.title)

    await message.delete()

@router.message(ItemForm.title)
async def get_title(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.update_data({"title": message.text})

    if data["action"] == "add_item":
        await bot.edit_message_caption(
            caption="📸 Send a product photo:",
            chat_id=message.from_user.id,
            message_id=data["message_id"]
        )
        await state.set_state(ItemForm.photo)

    await message.delete()

@router.message(ItemForm.photo)
async def get_photo(message: Message, state: FSMContext, bot: Bot):
    if message.photo:
        data = await state.get_data()
        await state.update_data({"photo": message.photo[-1].file_id})
        await bot.edit_message_caption(
            caption="💶 Enter item price in EUR:",
            chat_id=message.from_user.id,
            message_id=data["message_id"]
        )
        await state.set_state(ItemForm.price_in_eur)
    await message.delete()

@router.message(ItemForm.price_in_eur)
async def get_price(message: Message, state: FSMContext, bot: Bot):
    await state.update_data({"price": message.text})
    data = await state.get_data()

    await bot.edit_message_media(
        media=InputMediaPhoto(
            media=data["photo"],
            caption=(
                f"📦 <b>Item Preview:</b>\n\n"
                f"📁 Category: <b>{data.get('category')}</b>\n"
                f"📝 Title: <b>{data.get('title')}</b>\n"
                f"💶 Price: <b>{data.get('price')} EUR</b>\n"
                f"🧍 Gender: <b>{data.get('gender').capitalize()}</b>\n\n"
                "✅ Confirm to proceed or ❌ cancel."
            ),
            parse_mode="HTML"
        ),
        chat_id=message.from_user.id,
        message_id=data["message_id"],
        reply_markup=await confirmation(data["action"])
    )
    await state.set_state(ItemForm.price_in_eur)
    await message.delete()

@router.callback_query(ItemForm.price_in_eur)
async def confirm_item(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    if callback_query.data == "allow" and data["action"] == "add_item":
        async with session() as async_session:
            await create_product(session, {
                "name": data["title"],
                "category": data["category"],
                "price": int(data["price"]),
                "photo": data["photo"],
                "gender": data["gender"]
            })

    await callback_query.answer("✅ Item added!" if callback_query.data == "allow" else "❌ Cancelled!")

    await bot.edit_message_media(
        media=InputMediaPhoto(
            media=FSInputFile("logo.jpg"),
            caption=(
                "✨ <b>Welcome to our store!</b>\n\n"
                "Here you will find your favorite brands at prices 4–5 times lower than on official websites."
            ),
            parse_mode="HTML"
        ),
        chat_id=callback_query.from_user.id,
        message_id=data["message_id"],
        reply_markup=await menu(callback_query.from_user.id)
    )
    await state.clear()