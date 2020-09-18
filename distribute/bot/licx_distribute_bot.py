from telegram import TelegramError
from telegram.ext import Updater, PicklePersistence, CommandHandler, run_async
from constants import *
from service.icon_network_service import *

SCORE_CREATED_HEIGHT = getCreatedSCOREHeight(getCreateTX())


def error(update, context):
    logger.warning('Update "%s" caused error: %s', update, context.error)


def setup_existing_user(dispatcher):
    """
    Tasks to ensure smooth user experience for existing users upon Bot restart
    """

    # Iterate over all existing users
    chat_ids = dispatcher.user_data.keys()
    delete_chat_ids = []
    for chat_id in filter(lambda x: x in ADMIN_USER_IDS, chat_ids):
        # Send a notification to existing users that the Bot got restarted
        restart_message = '여보세요!\n' \
                          'Me, *Harry*, just got restarted on the server! 🤖\n' \
                          'To make sure you have the latest features, please start ' \
                          'a fresh chat with me by typing /start.'
        try:
            dispatcher.bot.send_message(chat_id, restart_message, parse_mode='markdown')
        except TelegramError as e:
            if 'bot was blocked by the user' in e.message:
                delete_chat_ids.append(chat_id)
                continue
            else:
                print("Got Error\n" + str(e) + "\nwith telegram user " + str(chat_id))

        # Start monitoring jobs for all existing users
        if 'job_started' not in dispatcher.user_data[chat_id]:
            dispatcher.user_data[chat_id]['job_started'] = True
        dispatcher.job_queue.run_repeating(distribution_ready_check, interval=JOB_INTERVAL_IN_SECONDS, context={
            'chat_id': chat_id,
            'user_data': dispatcher.user_data[chat_id]
        })

    for chat_id in delete_chat_ids:
        logger.warning("Telegram user " + str(chat_id) + " blocked me; removing him from the user list")
        delete_user(dispatcher, chat_id)


def delete_user(dispatcher, chat_id):
    del dispatcher.user_data[chat_id]
    del dispatcher.chat_data[chat_id]
    del dispatcher.persistence.user_data[chat_id]
    del dispatcher.persistence.chat_data[chat_id]

    # Somehow session.data does not get updated if all users block the bot.
    # That's why we delete the file ourselves.
    if len(dispatcher.persistence.user_data) == 0:
        if os.path.exists(session_data_path):
            os.remove(session_data_path)


@run_async
def start(update, context):
    """
    Send start message and start distribute job
    """

    if not is_admin(update):
        return

    # Start job for user
    if 'job_started' not in context.user_data:
        context.job_queue.run_repeating(distribution_ready_check, interval=JOB_INTERVAL_IN_SECONDS, context={
            'chat_id': update.message.chat.id,
            'user_data': context.user_data
        })
        context.user_data['job_started'] = True
        context.user_data['nodes'] = {}

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

    term_bounds = getCurrentTermBounds()
    last_distribute_height = getLastDistributeEventHeight()
    chat_id = update.message.chat.id
    try:
        distribute(context, chat_id, term_bounds, last_distribute_height)
    except Exception as e:
        logger.error(f"Distribute call failed:\n{e}")
        context.bot.send_message(chat_id,
                                 f"‼️ *LICX* Distribute called *failed* "
                                 f"for term {term_bounds['start']} - {term_bounds['end']} ‼\n\n"
                                 f"Error message:\n"
                                 f"{e.message}",
                                 parse_mode='markdown')


def distribution_ready_check(context):
    """
    This job executes distribute at the right time
    """

    logger.info("checking if distribution is ready")
    try:
        term_bounds = getCurrentTermBounds()
        last_distribute_height = getLastDistributeEventHeight()
        if SCORE_CREATED_HEIGHT + (43120 * 2) < term_bounds["start"] and term_bounds["start"] > last_distribute_height:
            distribute(context, context.job.context['chat_id'], term_bounds, last_distribute_height)
    except Exception as e:
        logger.error(e)


def distribute(context, chat_id, term_bounds, initial_distribute_height):
    """
    Send distribute TX until new Distribute Event is emitted
    """

    logger.info("distribution starts")
    context.bot.send_message(chat_id,
                             f"*LICX* Joining, Reward Distribution, and Leaving is *starting* for "
                             f"term {term_bounds['start']} - {term_bounds['end']}!",
                             parse_mode='markdown')

    while True:
        logger.info("distribution iteration")
        send_distribute_tx()
        sleep(3)
        if initial_distribute_height != getLastDistributeEventHeight():
            logger.info("distribution ended")
            context.bot.send_message(chat_id,
                                    f"*LICX* Joining, Reward Distribution, and Leaving *successfully "
                                    f"finished* for term {term_bounds['start']} - {term_bounds['end']}!",
                                    parse_mode='markdown')
            break


def is_admin(update):
    if update.effective_user.id not in ADMIN_USER_IDS:
        update.message.reply_text(f"❌ You are not an Admin! ❌\n"
                                  f"I'm *Harry*, I'm a loyal bot.",
                                  parse_mode='markdown')
        return 0
    return 1


def main():
    """
    Init telegram bot, attach handlers and wait for incoming requests.
    """

    # Init telegram bot
    bot = Updater(TELEGRAM_BOT_TOKEN, persistence=PicklePersistence(filename=session_data_path),
                  use_context=True)
    dispatcher = bot.dispatcher

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
