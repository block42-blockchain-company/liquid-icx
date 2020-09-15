from telegram.ext import Updater, PicklePersistence, CommandHandler, run_async
from constants import *
from service.icon_network_service import *

SCORE_CREATED_HEIGHT = getCreatedSCOREHeight(getCreateTX())

def error(update, context):
    logger.warning('Update "%s" caused error: %s', update, context.error)

@run_async
def start(update, context):
    """
    Send start message and start distribute job
    """

    # Start job for user
    if 'job_started' not in context.user_data:
        context.job_queue.run_repeating(distribution_ready_check, interval=10, context={
            'chat_id': update.message.chat.id,
            'user_data': context.user_data
        })
        context.user_data['job_started'] = True
        context.user_data['nodes'] = {}

@run_async
def distribute_handler(update, context):
    """
    Distribute ready check called by hand
    """

    distribution_ready_check(update.message.chat.id)


def distribute_job(context):
    """
    This job executes calls distribution_ready_check repeatedly
    """

    distribution_ready_check(context.job.context['chat_id'])


def distribution_ready_check(chat_id):
    """
    This job executes distribute at the right time
    """

    chat_id = context.job.context['chat_id']

    try:
        term_bounds = getCurrentTermBounds()
        last_distribute_height = getLastDistributeEventHeight()
        if SCORE_CREATED_HEIGHT + (43120 * 2) < term_bounds["start"] and \
                (last_distribute_height is None or term_bounds["start"] > last_distribute_height):
            context.bot.send_message(chat_id,
                                     f"*LICX* Joining, Reward Distribution, and Leaving is *starting* for "
                                     f"term {term_bounds['start']} - {term_bounds['end']}!",
                                     parse_mode='markdown')
            while last_distribute_height != getLastDistributeEventHeight():
                distribute()
                sleep(3)

            context.bot.send_message(chat_id,
                                     f"*LICX* Joining, Reward Distribution, and Leaving *successfully "
                                     f"finished* for term {term_bounds['start']} - {term_bounds['end']}!",
                                     parse_mode='markdown')
    except Exception as e:
        logger.error(e)


def main():
    """
    Init telegram bot, attach handlers and wait for incoming requests.
    """

    # Init telegram bot
    bot = Updater(TELEGRAM_BOT_TOKEN, persistence=PicklePersistence(filename=session_data_path),
                  use_context=True)
    dispatcher = bot.dispatcher

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
