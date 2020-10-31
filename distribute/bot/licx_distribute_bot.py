from telegram import TelegramError
from telegram.ext import Updater, PicklePersistence, CommandHandler, run_async
from service.icon_network_service import *
import copy
from constants import *

SCORE_CREATED_HEIGHT = getCreatedSCOREHeight(getCreateTX())


def error(update, context):
    logger.warning('Update "%s" caused error: %s', update, context.error)


def setup_existing_user(dispatcher):
    """
    Tasks to ensure smooth user experience for existing users upon Bot restart
    """

    # Send a notification to existing users that the Bot got restarted
    restart_message = '여보세요!\n' \
                      'Me, *Harry*, just got restarted on the server! 🤖\n' \
                      'To make sure you have the latest features, please start ' \
                      'a fresh chat with me by typing /start.'
    context = {"dispatcher": dispatcher}
    try_message_to_all_users(dispatcher=dispatcher, text=restart_message)


@run_async
def start(update, context):
    """
    Send start message and start distribute job
    """

    if not is_admin(update):
        return

    update.message.reply_text(f"여보세요!\n"
                              f"I'm *Harry*, your *Liquid ICX distribution officer*! 🤖\n\n"
                              f"Once per *ICON Term* I call the *distribute* function "
                              f"of the LICX SCORE and notify you.\n"
                              f"To *manually* invoke distribute send me the /distribute command.\n\n"
                              f"ICON Term = 43120 blocks\n"
                              f"SCORE Address = {SCORE_ADDRESS}\n\n"
                              f"See you later!", parse_mode='markdown')


@run_async
def distribute_handler(update, context):
    """
    Distribute ready check called by hand
    """

    if not is_admin(update):
        return

    try:
        term_bounds = getCurrentTermBounds()
        last_distribute_height = getLastDistributeEventHeight()
        distribute(context, term_bounds, last_distribute_height)
    except Exception as e:
        logger.error(f"Distribute call failed:\n{e}")
        text = f"‼️ *LICX* Distribute called *failed* " \
               f"for term {term_bounds['start']} - {term_bounds['end']} ‼\n\n" \
               f"Error message:\n" \
               f"{e.message}"
        try_message_to_all_users(dispatcher=context.dispatcher, text=text)


def distribution_ready_check(context):
    """
    This job executes distribute at the right time
    """

    logger.info("checking if distribution is ready")
    try:
        term_bounds = getCurrentTermBounds()
        last_distribute_height = getLastDistributeEventHeight()
        if SCORE_CREATED_HEIGHT + (43120 * 2) < term_bounds["start"] and term_bounds["start"] > last_distribute_height:
            distribute(context, term_bounds, last_distribute_height)
    except Exception as e:
        logger.error(f"Is distribute ready check failed:\n{e}")
        text = f"‼️ *LICX* Is-distribute-ready check *failed* " \
               f"for term {term_bounds['start']} - {term_bounds['end']} ‼\n\n" \
               f"Error message:\n" \
               f"{e.message}"
        try_message_to_all_users(dispatcher=context.dispatcher, text=text)


def distribute(context, term_bounds, initial_distribute_height):
    """
    Send distribute TX until new Distribute Event is emitted
    """

    logger.info("distribution starts")
    text = f"*LICX* Joining, Reward Distribution, and Leaving is *starting* for " \
           f"term {term_bounds['start']} - {term_bounds['end']}!"
    try_message_to_all_users(dispatcher=context.dispatcher, text=text)

    while True:
        logger.info("distribution iteration")
        send_distribute_tx()
        sleep(3)
        if initial_distribute_height != getLastDistributeEventHeight():
            logger.info("distribution ended")
            text = f"*LICX* Joining, Reward Distribution, and Leaving *successfully " \
                   f"finished* for term {term_bounds['start']} - {term_bounds['end']}!"
            try_message_to_all_users(dispatcher=context.dispatcher, text=text)
            break


def try_message_to_all_users(dispatcher, text):
    chat_ids = copy.deepcopy(list(dispatcher.chat_data.keys()))
    for chat_id in chat_ids:
        try_message(dispatcher=dispatcher, chat_id=chat_id, text=text)


def try_message(dispatcher, chat_id, text, reply_markup=None):
    """
    Send a message to a user.
    """

    try:
        dispatcher.bot.send_message(chat_id, text, parse_mode='markdown', reply_markup=reply_markup)
    except TelegramError as e:
        if 'bot was blocked by the user' in e.message or "Chat not found" in e.message:
            print("Telegram user " + str(chat_id) + " blocked me or does not exist; removing him from the user list")
            delete_user(dispatcher, chat_id)
        else:
            print("Got Error\n" + str(e) + "\nwith telegram user " + str(chat_id))


def delete_user(dispatcher, chat_id):
    del dispatcher.chat_data[chat_id]
    del dispatcher.persistence.chat_data[chat_id]

    if chat_id in dispatcher.user_data:
        del dispatcher.user_data[chat_id]
    if chat_id in dispatcher.persistence.user_data:
        del dispatcher.persistence.user_data[chat_id]

    # Somehow session.data does not get updated if all users block the bot.
    # That makes problems on bot restart. That's why we delete the file ourselves.
    if len(dispatcher.persistence.chat_data) == 0:
        if os.path.exists(session_data_path):
            os.remove(session_data_path)


def is_admin(update):
    if update.effective_user.id not in ADMIN_USER_IDS:
        update.message.reply_text(f"❌ You are not an Admin! ❌\n"
                                  f"I'm *Harry*, I'm a loyal bot.",
                                  parse_mode='markdown')
        return False
    return True


def main():
    """
    Init telegram bot, attach handlers and wait for incoming requests.
    """

    # Init telegram bot
    bot = Updater(TELEGRAM_BOT_TOKEN, persistence=PicklePersistence(filename=session_data_path),
                  use_context=True)
    dispatcher = bot.dispatcher

    dispatcher.job_queue.run_repeating(distribution_ready_check, interval=JOB_INTERVAL_IN_SECONDS)
    setup_existing_user(dispatcher)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('distribute', distribute_handler))

    # Add error handler
    dispatcher.add_error_handler(error)

    # Start the bot
    bot.start_polling()
    logger.info('LICX Distribute Bot is running...')

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    bot.idle()


if __name__ == '__main__':
    main()
