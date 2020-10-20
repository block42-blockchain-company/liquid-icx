import logging
import os

from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.wallet.wallet import KeyWallet

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
NETWORK = os.getenv("NETWORK", "TESTNET")
SCORE_ADDRESS = os.getenv("SCORE_ADDRESS")
WALLET = KeyWallet.load(bytes.fromhex(os.getenv("PRIVATE_KEY")))
ADMIN_USER_IDS = [int(admin_id) for admin_id in
                  os.environ['ADMIN_USER_IDS'].split(",")] if 'ADMIN_USER_IDS' in os.environ else []

if NETWORK == "MAINNET":
    TRACKER_API = "https://tracker.icon.foundation/v3"
    ICON_SERVICE_PROVIDER = "https://ctz.solidwallet.io/api/v3"
    NETWORK_ID = 1
elif NETWORK == "TESTNET":
    TRACKER_API = "https://bicon.tracker.solidwallet.io/v3"
    ICON_SERVICE_PROVIDER = "https://bicon.net.solidwallet.io/api/v3"
    NETWORK_ID = 3
else:
    logging.error("No valid network is specified!")
    exit(69)

ICX_SERVICE = IconService(HTTPProvider(ICON_SERVICE_PROVIDER))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
storage_path = os.sep.join([os.path.dirname(os.path.realpath(__file__)), os.path.pardir, 'storage'])
session_data_path = os.sep.join([storage_path, 'session.data'])

JOB_INTERVAL_IN_SECONDS = 10
