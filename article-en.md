# The Grammar of Bitcoin's Extensibility

### Bitcoin doesn't add features by changing bytes. It reserves *slots* — and the block explorer still shows each one under its pre-activation name.

---

Here are five Bitcoin coins. On a block explorer, all five addresses look identical: `tb1p…`, `tb1p…`, `tb1p…`. Same prefix, same length, same everything.

Then you spend them, and the witness opens up. One reveals nothing but a signature. One assembles bytes with `OP_CAT`. One checks a signature over an arbitrary message. One forces the coin's next destination. One makes a signature that no longer commits to the UTXO it spends.

Same `tb1p`. Wildly different machinery inside. **How does one address shape hide five different upgrade mechanisms — and how does Bitcoin keep adding more without ever breaking the old ones?**

The usual way to study this is to ask "what can CTV do? what can CAT do?" — a *feature* question, and it's been written to death. This is a different question, one layer down: **where, in the actual bytes of the protocol, did Bitcoin pre-reserve room for these upgrades, and what shape can each reserved slot hold?**

That question has an answer you can read off the wire, byte by byte. Every example below is a real transaction on signet. There's an [interactive explorer](./explorer.html) that lets you flip between them and watch each one plug into its slot; this essay is the map.

Let's peel the onion from the outside in.

## Layer 1 — the address only carries the version number

A Taproot output's script is `51 20 <32 bytes>`. That's `OP_1` (witness **version 1**) followed by `OP_PUSHBYTES_32` and the output key. The `1` in `bc1p`/`tb1p` *is* the witness version.

This is the one and only upgrade layer that lives **in the address**. Everything else we're about to meet is hidden in the witness and never shows up until you spend. Which is why the address can't tell you anything: a plain key-path coin (`386dbb6a…`, witness = one 64-byte signature, no script at all) wears the exact same `tb1p` as the covenant coins below.

And notice the ladder this layer already is: `v0` is SegWit (`bc1q`), `v1` is Taproot (`bc1p`, where all five of our coins live), and **`v2` through `v16` are defined and empty** — fifteen untouched rungs. When Bitcoin someday adds, say, a quantum-resistant signature scheme, the natural place to hang it is a new witness version up here.

## Layer 2 — the control block's first byte is (mostly) a lie

Spend by script-path and the witness ends with a *control block*. People love to read meaning into its first byte. In our examples it's `c0` for the APO leaf and `c1` for the CSFS leaf, and it's tempting to think that difference *means* something about the upgrade.

It doesn't — and the precise reason is worth pinning down. That first byte packs **two fields into one byte**: its top seven bits (`& 0xfe`) are the **leaf version**, and its lowest bit (`& 0x01`) is a **parity bit** — the Y-coordinate parity of the taproot *output* key `Q` (which lives x-only in the scriptPubKey, so a verifier needs the parity to recompute the taproot commitment). So `c0` and `c1` are the **same** leaf version — `0xc0`, standard tapscript — with opposite parity; you'd need `0xc2` to see a genuinely different leaf version. The leaf version is the part that could someday carry an upgrade, and for every leaf we'll see it is `0xc0`. The *next* leaf version, `0xc2`, is already **defined** — it's the "tapscript v2" dialect (the Great Script Restoration line, BIP-440/441) — but there's no on-chain example of it here yet: it's a reserved slot with the tooling built and the door not yet opened. Higher even values are reserved and empty too.

So Layer 2 is a real slot, but our upgrades don't live here. Two coins can show `c0` and `c1` and be running the *same* leaf version. If you only remember one debunking from this essay: **`c0` vs `c1` is parity, not mechanism.**

## Layer 3 — the opcode slot, and the fossil in its name

Now the heart of it. Inside the leaf, the opcode. And here Bitcoin has **two different reserved slots**, which is the single most important — and least explained — distinction in the whole picture.

Look at two leaves, side by side:

```
CTV  (9ccbce8a…):   20 <32B template hash>  b3
                                             ▲ OP_NOP4
CSFS (51fceec6…):   20 ff1f9fa3…9986b8  cc  69  cc
                                        ▲ OP_CHECKSIGFROMSTACK
```

On a block explorer, that `b3` shows up as **`OP_NOP4`**, and that `cc` shows up as **`OP_RETURN_204`**. Those aren't bugs, and they aren't arbitrary. **A display name is the byte's pre-activation identity — a fossil.** And the two fossils are different because CTV and CSFS occupy two different reserved slots:

- **The NOP slot.** `OP_NOP1…OP_NOP10` were built to do *nothing* — no-ops. A soft fork can redefine one to mean "if some condition fails, abort." That's all it can do: a read-only check. It **cannot touch the stack**, because old nodes still treat the byte as a no-op, and both must reach the same verdict. **CTV fits here** — it only peeks at a template hash and asks "does this transaction match?" It never pops, never pushes. So it can live in the humble NOP slot (`OP_NOP4`), and — because NOP upgrades are context-general — it even works outside Taproot.

- **The OP_SUCCESS slot.** Tapscript (BIP-342) introduced a set of ~80 `OP_SUCCESSx` bytes with a wild property: before activation, encountering one makes the **entire leaf succeed unconditionally**. That's the *most permissive* possible behavior. And that's exactly what makes it safe to redefine into *anything* — because any new rule, however strict, can only make a formerly-always-passing script *fail more*, never pass something it shouldn't. So an OP_SUCCESS opcode is free to **read and rewrite the stack**. `OP_CAT` (pop two, push their concatenation), `OP_CHECKSIGFROMSTACK` (pop sig/message/pubkey, push a boolean), `OP_INTERNALKEY` (push the internal key) — all of them move the stack, so all of them **must** use an OP_SUCCESS slot. None could fit a NOP.

That's the rule, and it isn't a taste — it's forced by the opcode's behavior:

```
Does the new opcode need to move the stack?
  ├─ No, just pass/fail        → NOP slot        → CTV          (explorer: OP_NOP4)
  └─ Yes, read/write the stack → OP_SUCCESS slot  → CAT/CSFS/IK  (explorer: OP_SUCCESS/RETURN_x)
```

The dramatic version of this lives in the "before" column of the explorer. Yesterday, `0x7e` in a tapscript was "this leaf passes, no questions asked." Today the same byte pops two stack items and concatenates them. **The soft fork didn't add a byte — it quietly swapped the meaning of one that was already there.** That swap, repeated across a handful of reserved bytes, is most of how Bitcoin grows.

## Layer 4/5 — the coin that isn't even an opcode

Now the odd one out. `SIGHASH_ANYPREVOUT` (APO) is a covenant-adjacent superpower — Eltoo, Lightning Symmetry — and you'd expect it to be an opcode too. It isn't.

Look at its leaf (`096e31cc…`) next to the CSFS leaf, and watch the **same key**:

```
CSFS: 20   ff1f9fa3…9986b8      cc   ← 32-byte push, bare x-only key
APO:  21 01 ff1f9fa3…9986b8     ac   ← 33-byte push, a 0x01 "hat", plain OP_CHECKSIG
```

Identical public key material, `ff1f9fa3…9986b8`. In the CSFS leaf it's pushed as **32 bytes**. In the APO leaf it's **33** — wearing a `0x01` prefix — and the opcode after it is just an ordinary `OP_CHECKSIG` (`ac`). **APO adds no new opcode at all.** Its entire mechanism is that one-byte hat plus a new set of sighash flags: the `0x01` prefix flips `OP_CHECKSIG` into *anyprevout mode*, where the signature stops committing to which UTXO it spends.

So the "is it 32 or 33 bytes?" of a pushed key is a fingerprint of *which layer* the upgrade lives in. 32 bytes: the key is used directly (CSFS, CTV's hash, IK). 33 bytes with a `0x01`: the key is a mode switch, and the real machinery is one layer deeper, down in the signature. (The prettiest proof of that depth: APO's two spends `03c0577c…` and `46091190…` carry the **byte-identical witness** on two different UTXOs — a signature that genuinely doesn't care which coin it's spending.)

## Layer 6 — the empty pocket

There's one more reserved slot, and it's almost entirely undocumented: the **annex**, a witness field that must start with `0x50`. It's reserved, signed-over, and — as of today — **used for nothing at all.** An empty pocket sewn into every Taproot spend, waiting for a future upgrade to give it meaning.

This one is a genuine blank on the map. There's very little developer-facing writing about the annex in any language, which makes it the natural place to plant a flag: construct a spend that actually carries a non-empty annex, and show, on-chain, exactly how the signature covers it and the script can't see it. (That experiment is the one artifact this series still owes — and the reason it's worth doing is precisely that nobody has.)

## The dial is a preset. The grid is the whole space.

Go back to APO for a moment, because it cracks something open. When APO drops "which coin am I spending," it doesn't drop it as one lump — it has two depths. `ANYPREVOUT` drops the coin's *identity* (the outpoint) but still commits to its *script* and its *amount*; `ANYPREVOUTANYSCRIPT` drops the script and the amount too. So the thing a signature commits to about an input was never one switch — it's a bundle of sub-fields (identity, script, amount, sequence), and APO lets you peel them off one at a time.

Now turn that lens on the output side. `SIGHASH_NONE` drops *the whole output* — both the recipient (the script, the "address") and the amount, together, in one coarse move. But an output is the same kind of bundle: an address and a value. There is no reason in principle you couldn't commit to *the amount but not the recipient*, or *the recipient but not the amount*. Standard sighash simply doesn't hand you that dial — `ALL / SINGLE / NONE` are three coarse presets over a much finer grid.

So here is the real shape of the thing, the one the six flags only hint at:

> A signature commits to a **subset of the transaction's sub-fields** — this input's identity, that input's amount, this output's script, that output's value, the locktime, and so on. The sighash flags are a handful of **coarse presets** over that grid. APO adds a few finer ones on the input side. But the grid itself is large, and the flags visit only a few of its corners.

Recall the **SEE (看) / BLIND (蒙)** dials from the sighash booklet, [*What a Signature Can See*](https://sighash.bitcoincoding.dev/): a flag flips fields only in big blocks. The grid underneath is finer —

```
   the coarse dial (a sighash flag)         the fine grid underneath
   OUTPUT:  ALL / SINGLE / NONE             each input  = [ identity | script | amount ]
   INPUT :  all / mine(ACP) / none(APO)     each output = [ address  | amount ]

                    identity   script   amount
          in 0        ● 看      ● 看     ● 看
          in 1        ○ 蒙      ● 看     ● 看     ← APO blinds just in-1's identity
          out 0        —        ● 看     ○ 蒙     ← SEE the address, BLIND the amount
          out 1        —        ○ 蒙     ● 看     ← BLIND the address, SEE the amount
                       ● = SEE (看)      ○ = BLIND (蒙)

   A flag can only flip whole rows — a few corners of this grid.
   CAT + CSFS flip ANY cell: glue exactly the fields you want, then verify.
```

And *this* is where it stops being trivia. Because there is a way to reach **any** point on that grid — not a preset, whatever subset of committable sub-fields you like. You assemble the signed message yourself, field by field, with `OP_CAT`, and check the signature over exactly that assembly with `OP_CHECKSIGFROMSTACK`. Want to commit to just the *amount* of output 2 and nothing else? Glue that one field, sign it, verify it. Just the prevouts and none of the amounts? Same move. The coarse flags were always samples of a continuum; CAT + CSFS make the whole continuum addressable.

That is why showing CAT + CSFS can reproduce these commitments is not a footnote. It is the statement that the entire grid — every committable sub-field subset that `SIGHASH_ALL`, `ANYONECANPAY`, `SINGLE`, and `ANYPREVOUT` each reach one coarse corner of — is reachable by hand, today, on already-activated opcodes. The flags are the presets. CAT + CSFS is the full keyboard.

## Count the empty slots

Step back and the whole picture is a stack of reserved slots, most of them still sealed:

- Witness versions **v2–v16**: fifteen, empty.
- Leaf versions above `0xc0`: a whole range, empty.
- NOP opcodes: a couple used (CLTV, CSV), CTV proposed for one more, the rest open.
- OP_SUCCESS opcodes: ~80 of them; CAT, CSFS, INTERNALKEY spoken for, roughly seventy-seven still open.
- The annex: one empty pocket.

That's on the order of **a hundred reserved-but-empty upgrade slots**. Every future soft fork has to fold itself into one of these shapes — a read-only NOP check, a stack-moving OP_SUCCESS opcode, a sighash-flag-and-pubkey-prefix trick, a new witness version, or the annex — or it has to argue for adding a brand-new slot. **That constraint set — the shapes Bitcoin will accept a change in — is the grammar of its extensibility.** It's not written in any one BIP. It's written in the bytes.

Most writing about Bitcoin script asks what an opcode *does*. This asks the question underneath: *how an opcode is allowed to exist at all* — and the answer turns out to be legible, one byte at a time, on a `tb1p` address that gives nothing away until you open it.

---

*Every transaction cited here is on signet. Flip between them in the [interactive explorer](./explorer.html). Byte-level write-ups of the individual opcodes — [OP_CAT](https://medium.com/@aaron.recompile/op-cat-on-signet-concatenation-commitment-and-bitcoin-inquisition-ed34a07866d6), [OP_CHECKSIGFROMSTACK](https://medium.com/@aaron.recompile/op-checksigfromstack-on-signet-sign-anything-verify-on-stack-9cf70ab07583), [OP_CHECKTEMPLATEVERIFY](https://medium.com/@aaron.recompile/op-checktemplateverify-on-signet-locking-outputs-at-utxo-creation-time-1d623fbe3899), [SIGHASH_ANYPREVOUT](https://medium.com/@aaron.recompile/sighash-anyprevout-on-signet-when-signatures-stop-binding-to-utxos-eed4fc475668) — are in the companion [signet series](https://medium.com/@aaron.recompile). Specs: [BIP-341/342](https://github.com/bitcoin/bips/blob/master/bip-0342.mediawiki) (tapscript & OP_SUCCESS), [BIP-119](https://github.com/bitcoin/bips/blob/master/bip-0119.mediawiki) (CTV), [BIP-118](https://github.com/bitcoin/bips/blob/master/bip-0118.mediawiki) (APO).*
