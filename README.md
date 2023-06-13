# Decodify

Decodify is a Chrome extension that enhances Etherscan and other EaaS (Explorers as a Service) platforms by leveraging rotki's powerful decoding capabilities for EVM chains.

> **Note**: Decodify currently supports only EVM chains that are compatible with rotki.

## Running Your Own Decoding Server

You can set up your own server to perform the decoding. Before you begin, obtain the required API keys:

- [Optimism Etherscan API key](https://optimistic.etherscan.io/apis)
- [Etherscan API key](https://docs.etherscan.io/getting-started/viewing-api-usage-statistics)

### Using Docker Image (Recommended)

1. Run the following command, replacing `<preferred_port>`, `<api-key>` (Etherscan), and `<api-key>` (Optimism Etherscan) with your values:

   ```
   docker run -d -p <preferred_port>:2000 -e ETHEREUM_API_KEY=<api-key> -e OPTIMISM_API_KEY=<api-key> prettyirrelevant/decodify
   ```

2. Ping `localhost:<selected_port>` to verify that the server is up and running.

### Local Setup

1. Set up a Python virtual environment and clone the repository.
2. Change the directory to `/api` and install the dependencies using `pip install -r requirements.txt`.
3. Set the environment variables `ETHEREUM_API_KEY` and `OPTIMISM_API_KEY` with your API keys.
4. Run the server with `PYTHONOPTIMIZE=1 flask run`.

## Acknowledgments

- [rotki](https://github.com/rotki/rotki) for providing the decoding feature.
- Icons8 for the extension's logo.
