from pathlib import Path
from typing import TYPE_CHECKING, Any

from rotkehlchen.chain.ethereum.constants import ETHEREUM_ETHERSCAN_NODE
from rotkehlchen.chain.ethereum.node_inquirer import EthereumInquirer
from rotkehlchen.chain.ethereum.transactions import EthereumTransactions
from rotkehlchen.chain.optimism.constants import OPTIMISM_ETHERSCAN_NODE
from rotkehlchen.chain.optimism.node_inquirer import OptimismInquirer
from rotkehlchen.chain.optimism.transactions import OptimismTransactions
from rotkehlchen.chain.polygon_pos.constants import POLYGON_POS_ETHERSCAN_NODE
from rotkehlchen.chain.polygon_pos.node_inquirer import PolygonPOSInquirer
from rotkehlchen.chain.polygon_pos.transactions import PolygonPOSTransactions
from rotkehlchen.constants import DEFAULT_SQL_VM_INSTRUCTIONS_CB
from rotkehlchen.db.dbhandler import DBHandler
from rotkehlchen.globaldb.handler import GlobalDBHandler
from rotkehlchen.greenlets.manager import GreenletManager
from rotkehlchen.types import (ChainID, EvmAddress, EVMTxHash, ExternalService,
                               ExternalServiceApiCredentials)
from rotkehlchen.user_messages import MessagesAggregator

from .exceptions import UnexpectedChainIDError

if TYPE_CHECKING:
    from rotkehlchen.accounting.structures.evm_event import EvmEvent
    from rotkehlchen.chain.evm.decoding.decoder import EVMTransactionDecoder
    from rotkehlchen.chain.evm.transactions import EvmTransactions
    from rotkehlchen.db.drivers.gevent import DBCursor


class RotkiLite:
    def __init__(
            self,
            data_directory: Path,
            password: str,
            polygon_api_key: str,
            ethereum_api_key: str,
            optimism_api_key: str,
    ) -> None:
        self.__msg_aggregator = MessagesAggregator()
        self.__greenlet_manager = GreenletManager(self.__msg_aggregator)
        self.__data_dir = data_directory
        self.__data_dir.mkdir(exist_ok=True)
        self.__user_data_dir = self.__data_dir / 'deezy'
        self.__user_data_dir.mkdir(exist_ok=True)

        GlobalDBHandler(
            data_dir=self.__data_dir,
            sql_vm_instructions_cb=DEFAULT_SQL_VM_INSTRUCTIONS_CB,
        )
        self.database = DBHandler(
            user_data_dir=self.__user_data_dir,
            password=password,
            msg_aggregator=self.__msg_aggregator,
            initial_settings=None,
            sql_vm_instructions_cb=DEFAULT_SQL_VM_INSTRUCTIONS_CB,
            resume_from_backup=False,
        )
        with self.database.user_write() as write_cursor:
            populate_db_with_rpc_nodes(write_cursor)
            self._add_api_keys_to_database(
                write_cursor=write_cursor,
                ethereum_etherscan_key=ethereum_api_key,
                optimism_etherscan_key=optimism_api_key,
                polygon_etherscan_key=polygon_api_key,
            )

        # Initialise all node inquirers
        ethereum_inquirer = EthereumInquirer(
            greenlet_manager=self.__greenlet_manager,
            database=self.database,
        )
        optimism_inquirer = OptimismInquirer(
            greenlet_manager=self.__greenlet_manager,
            database=self.database,
        )
        polygon_inquirer = PolygonPOSInquirer(
            greenlet_manager=self.__greenlet_manager,
            database=self.database,
        )

        # Initialise all transactions objects
        self.__ethereum_transactions = EthereumTransactions(
            ethereum_inquirer=ethereum_inquirer,
            database=self.database,
        )
        self.__optimism_transactions = OptimismTransactions(
            optimism_inquirer=optimism_inquirer,
            database=self.database,
        )
        self.__polygon_transactions = PolygonPOSTransactions(
            polygon_pos_inquirer=polygon_inquirer,
            database=self.database,
        )

        # To prevent circular imports.
        from rotkehlchen.chain.ethereum.decoding.decoder import \
            EthereumTransactionDecoder
        from rotkehlchen.chain.optimism.decoding.decoder import \
            OptimismTransactionDecoder
        from rotkehlchen.chain.polygon_pos.decoding.decoder import \
            PolygonPOSTransactionDecoder

        self.__ethereum_tx_decoder = EthereumTransactionDecoder(
            database=self.database,
            ethereum_inquirer=ethereum_inquirer,
            transactions=self.__ethereum_transactions,
        )
        self.__optimism_tx_decoder = OptimismTransactionDecoder(
            database=self.database,
            optimism_inquirer=optimism_inquirer,
            transactions=self.__optimism_transactions,
        )
        self.__polygon_tx_decoder = PolygonPOSTransactionDecoder(
            database=self.database,
            polygon_pos_inquirer=polygon_inquirer,
            transactions=self.__polygon_transactions,
        )

    def _add_api_keys_to_database(
        self,
        write_cursor: 'DBCursor',
        ethereum_etherscan_key: str,
        optimism_etherscan_key: str,
        polygon_etherscan_key: str,
    ) -> None:
        """Add API keys to the database for various Etherscan services.

        Parameters:
            write_cursor: A database cursor with write access.
            ethereum_etherscan_key: The API key for Ethereum Etherscan service.
            optimism_etherscan_key: The API key for Optimism Etherscan service.
            polygon_etherscan_key: The API key for Polygon Etherscan service.
        """
        self.database.add_external_service_credentials(
            write_cursor=write_cursor,
            credentials=[
                ExternalServiceApiCredentials(
                    service=ExternalService.ETHERSCAN,
                    api_key=ethereum_etherscan_key,
                ),
                ExternalServiceApiCredentials(
                    service=ExternalService.OPTIMISM_ETHERSCAN,
                    api_key=optimism_etherscan_key,
                ),
                ExternalServiceApiCredentials(
                    service=ExternalService.POLYGON_POS_ETHERSCAN,
                    api_key=polygon_etherscan_key,
                )
            ],
        )

    def _get_transactions(self, chain_id: ChainID) -> 'EvmTransactions':
        """Get the EvmTransactions instance for the specified ChainID.

        Parameters:
            chain_id: The ID of the blockchain chain.

        Raises:
            UnexpectedChainIDError: if the `chain_id` is not supported yet.

        Returns:
            EvmTransactions: An instance of EvmTransactions
            for the specified chain, or None if the chain is not supported.
        """
        if chain_id == ChainID.ETHEREUM:
            return self.__ethereum_transactions
        if chain_id == ChainID.OPTIMISM:
            return self.__optimism_transactions
        if chain_id == ChainID.POLYGON_POS:
            return self.__polygon_transactions

        raise UnexpectedChainIDError

    def _get_transactions_decoder(self, chain_id: ChainID) -> 'EVMTransactionDecoder':
        """Get the appropriate EVMTransactionDecoder based on the ChainID.

        Parameters:
            chain_id: The ID of the blockchain chain.

        Raises:
            UnexpectedChainIDError: if the `chain_id` is not supported yet.

        Returns:
            An instance of EVMTransactionDecoder for the specified chain.
        """
        if chain_id == ChainID.ETHEREUM:
            return self.__ethereum_tx_decoder
        if chain_id == ChainID.OPTIMISM:
            return self.__optimism_tx_decoder
        if chain_id == ChainID.POLYGON_POS:
            return self.__polygon_tx_decoder

        raise UnexpectedChainIDError

    def _query_transaction(self, chain: ChainID, tx_hash: EVMTxHash) -> dict[str, Any]:
        """Get transaction information by its hash.

        Parameters:
            chain: The ID of the Ethereum chain.
            tx_hash: The hash of the transaction to query.

        Returns:
            A dictionary containing transaction information.
        """
        transactions = self._get_transactions(chain)
        return transactions.evm_inquirer.etherscan.get_transaction_by_hash(tx_hash)

    def fetch_transaction_addresses(self, chain: ChainID, tx_hash: EVMTxHash) -> list[EvmAddress]:
        """Fetch the ``from`` and ``to``  in a transaction.

        Parameters:
            chain: The ID of the Ethereum chain.
            tx_hash: The hash of the transaction to query.

        Returns:
            A list of EvmAddress objects representing the addresses that are not contracts.
        """
        addresses = []
        transaction = self._query_transaction(chain, tx_hash)
        if not transaction:
            return addresses

        transactions = self._get_transactions(chain)
        for addy in (transaction['from'], transaction['to']):
            if transactions.evm_inquirer.etherscan.get_code(addy) == '0x':
                addresses.append(addy)

        return addresses

    def decode_transaction(self, chain: ChainID, tx_hash: EVMTxHash) -> list['EvmEvent']:
        """Decode an Ethereum transaction using its hash.

        Parameters:
            chain: The ID of the Ethereum chain.
            tx_hash: The hash of the transaction to decode.

        Returns:
            A list of EvmEvent objects representing the decoded events from the transaction.
        """
        transactions = self._get_transactions(chain)
        transactions.get_or_query_transaction_receipt(tx_hash)

        decoder = self._get_transactions_decoder(chain)
        return decoder.decode_transaction_hashes(ignore_cache=False, tx_hashes=[tx_hash])


def populate_db_with_rpc_nodes(write_cursor: 'DBCursor') -> None:
    """Populates the database with RPC nodes' information.

    Parameters:
        write_cursor: A database cursor with write access.
    """
    nodes = [
        ETHEREUM_ETHERSCAN_NODE.serialize_for_db(),
        OPTIMISM_ETHERSCAN_NODE.serialize_for_db(),
        POLYGON_POS_ETHERSCAN_NODE.serialize_for_db(),
    ]

    write_cursor.executemany(
        'INSERT OR IGNORE INTO rpc_nodes(name, endpoint, owned, active, weight, blockchain) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        nodes,
    )
