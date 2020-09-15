import logging
import os

from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.wallet.wallet import KeyWallet

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ICX_SERVICE = IconService(HTTPProvider(os.getenv("ICON_SERVICE_PROVIDER")))
SCORE_ADDRESS = os.getenv("SCORE_ADDRESS")
TRACKER_ENDPOINT = os.getenv("TRACKER_API_URL") + "contract/eventLogList"
WALLET = KeyWallet.load(bytes.fromhex(os.getenv("PRIVATE_KEY")))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
storage_path = os.sep.join([os.path.dirname(os.path.realpath(__file__)), os.path.pardir, 'storage'])
session_data_path = os.sep.join([storage_path, 'session.data'])
