# The Grammar of Bitcoin's Extensibility

### 🔗 Live: **[slots.bitcoincoding.dev](https://slots.bitcoincoding.dev)** — the interactive upgrade-slot explorer + the essay

Bitcoin doesn't add a feature by inventing a new byte. It **reserves slots** in advance, then fills them — and the block explorer still shows each filled slot under its **pre-activation name**. This is a byte-level field guide to those slots: which one CAT, CSFS, CTV, APO and INTERNALKEY each plug into, read off real on-chain (signet) bytes.

## What's here

| | |
|---|---|
| **`explorer.html`** | The interactive **Upgrade-Slot Explorer** — pick an opcode, see its real leaf bytes, watch which reserved slot it plugs into, and why the explorer still shows its pre-activation "fossil" name. |
| **`article-en.md`** | The essay: peel the onion from the address inward — witness version → leaf version → the opcode slot (NOP vs OP_SUCCESS) → the `0x01` hat → the empty annex → count the unopened slots. |

## Quick start

Open **`index.html`** (or the live site) and hit **Open the Upgrade-Slot Explorer**. Pick CAT / CSFS / CTV / APO and watch which reserved slot each one plugs into, on real bytes.

## Further reading

- Companion signet series (opcode by opcode): [medium.com/@aaron.recompile](https://medium.com/@aaron.recompile)
- Sibling piece: [What a Signature Can See](https://sighash.bitcoincoding.dev) — the sighash playground
- Specs: [BIP-341/342](https://github.com/bitcoin/bips/blob/master/bip-0342.mediawiki) (Taproot / tapscript / OP_SUCCESS) · [BIP-119](https://github.com/bitcoin/bips/blob/master/bip-0119.mediawiki) (CTV) · [BIP-118](https://github.com/bitcoin/bips/blob/master/bip-0118.mediawiki) (APO)

## License

Text and figures © the author. Code is MIT. Every byte is from real on-chain (signet) transactions.
