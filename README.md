# cerche

This is an experimental search engine for conversational AI such as parl.ai, large language models such as OpenAI GPT3, and humans (maybe).


## Usage

Start Docker.

```bash
make docker/run/hub
# in another terminal
curl -X POST localhost:8082 -d "q=turing&n=1"
```

## Development

### Installation

```bash
make bare/install
```

### Configuration 

You might require a `.env` file:

`.env`
```bash
GOOGLE_SEARCH_CX=
GOOGLE_SEARCH_KEY=
PROD_PROJECT_ID=
PROD_REGISTRY=
DATASET_URL=
```
