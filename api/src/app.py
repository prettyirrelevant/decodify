from gevent import monkey  # isort: skip
monkey.patch_all()  # isort: skip

from os import environ
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify
from flask_caching import Cache
from flask_cors import CORS
from marshmallow import validate
from rotkehlchen.api.v1.fields import (
    EvmAddressField,
    EvmChainNameField,
    EVMTransactionHashField,
)
from rotkehlchen.chain.accounts import BlockchainAccountData
from rotkehlchen.errors.misc import InputError
from rotkehlchen.types import ChainID, EvmAddress, EVMTxHash
from webargs.fields import DelimitedList
from webargs.flaskparser import use_kwargs
from werkzeug.exceptions import HTTPException

from .utils import RotkiLite

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env', verbose=True)

app = Flask(__name__)
if not environ.get('REDIS_URL', None):
    app.config['CACHE_TYPE'] = 'FileSystemCache'

    cache_dir = BASE_DIR / '.cache'
    cache_dir.mkdir(exist_ok=True)

    app.config['CACHE_DIR'] = cache_dir
    app.config['CACHE_OPTIONS'] = {'mode': 511}
else:
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_URL'] = environ.get('REDIS_URL')

cache = Cache(app)
cors = CORS(app)
rotki = RotkiLite(
    data_directory=BASE_DIR / 'data',
    password='deeznut',
    ethereum_api_key=environ.get('ETHEREUM_API_KEY'),
    optimism_api_key=environ.get('OPTIMISM_API_KEY'),
)


@app.errorhandler(Exception)
def generic_errorhandler(e):
    return jsonify(errors=[str(e)]), 500


@app.errorhandler(HTTPException)
def http_errorhandler(e: HTTPException):
    resp = e.get_response()
    if resp.status_code in {400, 422}:
        messages = e.data.get('messages', ['Invalid request.'])
    else:
        messages = [e.description]

    return jsonify(errors=messages), resp.status_code


@app.get('/')
def index() -> Response:
    """This endpoint serves as a PING endpoint."""
    return jsonify(message='welcome to decodify api'), 200


@app.get('/transactions/<tx_hash>/<chain>/addresses')
@cache.cached()
@use_kwargs({'tx_hash': EVMTransactionHashField(required=True), 'chain': EvmChainNameField(required=True, limit_to=[ChainID.ETHEREUM, ChainID.OPTIMISM])}, location='view_args')  # noqa: E501
def fetch_transaction_addresses(tx_hash: EVMTxHash, chain: ChainID):
    addresses = rotki.fetch_transaction_addresses(
        chain=chain,
        tx_hash=tx_hash,
    )
    return jsonify(data=addresses), 200


@app.get('/transactions/<tx_hash>/<chain>/decode')
@cache.cached()
@use_kwargs({'tx_hash': EVMTransactionHashField(required=True), 'chain': EvmChainNameField(required=True, limit_to=[ChainID.ETHEREUM, ChainID.OPTIMISM])}, location='view_args')  # noqa: E501
@use_kwargs({'related_addresses': DelimitedList(EvmAddressField(), required=True, validate=validate.Length(max=2))}, location='query')  # noqa: E501
def decode_transaction(
    tx_hash: EVMTxHash,
    chain: ChainID,
    related_addresses: list[EvmAddress],
) -> Response:
    """This endpoint decodes a transaction."""
    # step 1: add the address to the datbase.
    try:
        with rotki.database.user_write() as write_cursor:
            rotki.database.add_blockchain_accounts(
                write_cursor=write_cursor,
                account_data=[
                    BlockchainAccountData(
                        chain=chain.to_blockchain(),
                        address=addy,
                    )
                    for addy in related_addresses
                ],
            )
    except InputError:
        pass

    # step 2: decode the transaction.
    events = rotki.decode_transaction(chain=chain, tx_hash=tx_hash)

    # step 3: cleanup
    try:
        with rotki.database.user_write() as write_cursor:
            rotki.database.remove_single_blockchain_accounts(
                write_cursor=write_cursor,
                blockchain=chain.to_blockchain(),
                accounts=related_addresses,
            )
    except InputError:
        pass

    # step 4: return the decoded transaction as JSON.
    return jsonify(
        data=[
            event.serialize_for_api(
                customized_event_ids=[],
                ignored_ids_mapping={},
                hidden_event_ids=[],
            )
            for event in events
        ],
    ), 200
