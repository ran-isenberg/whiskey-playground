STACK_NAME = 'WhiskeyAgentStack'
RUNTIME_NAME = 'whiskey_sommelier'

MODEL_ID = 'us.anthropic.claude-haiku-5-5'
FOUNDATION_MODEL = 'anthropic.claude-haiku-5-5'
FALLBACK_MODEL_ID = 'us.anthropic.claude-sonnet-5-5'
FALLBACK_FOUNDATION_MODEL = 'anthropic.claude-sonnet-5-5'
PROFILE_REGIONS = ['us-east-1', 'us-east-2', 'us-west-2']

EMBEDDING_MODEL = 'amazon.titan-embed-text-v2:0'
EMBEDDING_DIM = 1024

INVENTORY_KEY = 'inventory/inventory.json'

AGENT_ENV_DEFAULTS = {
    'MAX_MATCHES': '3',
    'SCORE_THRESHOLD': '50',
    'RETRIEVE_K': '12',
    'ORDERING_ENABLED': 'false',
    'LOG_LEVEL': 'INFO',
}

BUILD_AGENT_DIR = 'build/agent'
BUILD_CHAT_DIR = 'build/chat'
UI_DIST_DIR = 'ui/dist'
