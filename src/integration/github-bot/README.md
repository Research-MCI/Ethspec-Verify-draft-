# autoreum

> A GitHub App built with [Probot](https://github.com/probot/probot) that LLM code reviewer assistant for Ethereum development

## Setup

```sh
# Install dependencies
npm install

# Run the bot
npm start
```

## Docker

```sh
# 1. Build container
docker build -t autoreum .

# 2. Start container
docker run -e APP_ID=<app-id> -e PRIVATE_KEY=<pem-value> autoreum
```

## Contributing

If you have suggestions for how autoreum could be improved, or want to report a bug, open an issue! We'd love all and any contributions.

For more, check out the [Contributing Guide](CONTRIBUTING.md).

## License

[ISC](LICENSE) © 2026 rausyan
