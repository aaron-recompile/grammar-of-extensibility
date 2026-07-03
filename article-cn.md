# 比特币的扩展性语法学
## 升级插槽的字节级解剖

### 比特币不是靠"改字节"加功能的。它**预留插槽**——而区块浏览器,至今还用每个插槽"激活前的旧名"显示它。

---

这里有五枚比特币。在区块浏览器上,五个地址长得一模一样:`tb1p…`、`tb1p…`、`tb1p…`。同样的前缀、同样的长度、什么都一样。

然后你去花它们,witness 打开了。一枚只露出一个签名。一枚用 `OP_CAT` 把字节拼起来。一枚验证一条"任意消息"的签名。一枚强制这枚币下一步只能去哪。一枚做出的签名,居然不再绑定它花的是哪枚 UTXO。

同样的 `tb1p`,里面藏着天差地别的机器。**一个地址形状,怎么藏得下五种不同的升级机制——而比特币又是怎么不停加新机制、却从不弄坏旧的?**

通常研究这个的方式是问"CTV 能干什么?CAT 能干什么?"——这是**功能**问题,已经被写烂了。这篇问的是下一层的问题:**在协议的真实字节里,比特币到底把升级的余地预留在了哪些位置,每个预留的插槽能装下什么形状的升级?**

这个问题的答案,能从线格式上一个字节一个字节读出来。下面每个例子都是 signet 上的真实交易。有一个[交互式浏览器](./explorer.html)可以让你在它们之间切换、看每个插进哪个槽;这篇文章是那张地图。

我们从外往里,把洋葱一层层剥开。

## 第 1 层 —— 地址里只带了一个版本号

一个 Taproot 输出的脚本是 `51 20 <32字节>`。也就是 `OP_1`(witness **版本 1**)接 `OP_PUSHBYTES_32` 再接输出钥。`bc1p`/`tb1p` 里那个 `1`,**就是** witness version。

这是**唯一一个住在地址里**的升级层。接下来要见的所有东西都藏在 witness 里,不花就永远看不见。所以地址什么都告诉不了你:一枚纯 key-path 的币(`386dbb6a…`,witness = 一个 64 字节签名、根本没有脚本),和下面那些 covenant 币穿的是同一件 `tb1p`。

而且注意这一层本身就是一架梯子:`v0` 是 SegWit(`bc1q`),`v1` 是 Taproot(`bc1p`,我们五枚币都在这),而 **`v2` 到 `v16` 已定义、全空着**——十五级没碰过的横档。比特币哪天要加一套抗量子签名方案,最自然的挂法就是往上开一个新的 witness version。

## 第 2 层 —— 控制块首字节(基本上)是个谎

走 script-path 花费,witness 最后一项是*控制块*。人们爱往它首字节里读含义。我们例子里 APO 那笔是 `c0`、CSFS 那笔是 `c1`,很容易以为这个差别*意味着*升级机制上的什么。

不是——而且精确原因值得钉死。那个首字节把**两个字段塞进了一个字节**:高 7 位(`& 0xfe`)是 **leaf version**,最低 1 位(`& 0x01`)是一个 **parity 位**——taproot **输出钥 Q** 的 Y 坐标奇偶(Q 在 scriptPubKey 里只存 x-only,验证者要靠这一位才能重算 taproot commitment)。所以 `c0` 和 `c1` 是**同一个** leaf version——`0xc0`,标准 tapscript——只是 parity 相反;要看到真·不同的 leaf version,得是 `0xc2`。leaf version 才是那个可能承载升级的部分,而我们看的每片叶子它都是 `0xc0`。*下一个* leaf version `0xc2` 其实已经**定义**了——就是"tapscript v2"方言(Great Script Restoration 那条线,BIP-440/441)——但这里还没有它的链上样本:工具造好了,门还没开,是个预留的空槽。再上面的偶数值也都预留、空着。

所以第 2 层是个真插槽,但我们的升级不住这。两枚币可以一个显示 `c0`、一个 `c1`,却跑着*同一个* leaf version。这篇你要是只记住一条辟谣:**`c0` vs `c1` 是奇偶,不是机制。**

## 第 3 层 —— opcode 插槽,和它名字里的化石

现在到核心了。叶子内部,那个 opcode。而这里比特币有**两个不同的预留插槽**——这是整幅图里最重要、也最没人讲清楚的一个区分。

把两片叶子并排看:

```
CTV  (9ccbce8a…):   20 <32B 模板hash>  b3
                                       ▲ OP_NOP4
CSFS (51fceec6…):   20 ff1f9fa3…9986b8  cc  69  cc
                                        ▲ OP_CHECKSIGFROMSTACK
```

在区块浏览器上,那个 `b3` 显示成 **`OP_NOP4`**,那个 `cc` 显示成 **`OP_RETURN_204`**。这不是 bug,也不是随便标的。**显示名,是这个字节"激活前的身份证"——一块化石。** 而两块化石不同,恰恰因为 CTV 和 CSFS 占的是两个不同的预留插槽:

- **NOP 插槽。** `OP_NOP1…OP_NOP10` 当初被造出来就是*什么都不做*的——空操作。软分叉可以把其中一个重定义成"某条件不满足就中止"。它能做的仅此而已:一个只读检查。它**不能碰栈**,因为旧节点仍把这个字节当空操作,两边必须得出同一个结论。**CTV 住这**——它只是 peek 一眼模板 hash,问"这笔交易匹配吗?",从不 pop、从不 push。所以它能住进朴素的 NOP 槽(`OP_NOP4`),而且——因为 NOP 升级是跨上下文的——它连 Taproot 之外都能用。

- **OP_SUCCESS 插槽。** Tapscript(BIP-342)引入了一组约 80 个 `OP_SUCCESSx` 字节,带一个野性的性质:激活前,遇到它就让**整片叶子无条件成功**。这是*最宽松*的行为。而正是这一点让它能被重定义成*任何东西*——因为任何新规则,无论多严,只会让一个"原本必过"的脚本*更容易失败*,绝不会让它放行本不该放行的东西。所以一个 OP_SUCCESS opcode 可以自由地**读写栈**。`OP_CAT`(pop 两个、push 拼接)、`OP_CHECKSIGFROMSTACK`(pop 签名/消息/公钥、push 布尔)、`OP_INTERNALKEY`(push 内部钥)——全都要动栈,所以全都**必须**用 OP_SUCCESS 槽,没有一个塞得进 NOP。

这就是规则,而且不是品味问题——是被 opcode 的行为逼出来的:

```
新 opcode 要动栈吗?
  ├─ 不动,只判通过/失败  → NOP 槽        → CTV          (浏览器:OP_NOP4)
  └─ 要读/写栈           → OP_SUCCESS 槽  → CAT/CSFS/IK  (浏览器:OP_SUCCESS/RETURN_x)
```

这件事最戏剧性的版本,在浏览器"激活前"那一栏。昨天,一片 tapscript 里的 `0x7e` 是"这片叶子无条件通过、别问"。今天,同一个字节 pop 出两个栈元素、把它们拼起来。**软分叉没加一个字节——它悄悄换掉了一个本已存在的字节的含义。** 这种偷换,在几个预留字节上反复上演,就是比特币成长的大半方式。

## 第 4/5 层 —— 那枚根本不是 opcode 的币

现在是最特别的一个。`SIGHASH_ANYPREVOUT`(APO)是 covenant 邻域的超能力——Eltoo、Lightning Symmetry——你会以为它也是个 opcode。它不是。

把它的叶子(`096e31cc…`)和 CSFS 的叶子并排,盯着那把**同一个公钥**:

```
CSFS: 20   ff1f9fa3…9986b8      cc   ← 32字节 push,裸 x-only 公钥
APO:  21 01 ff1f9fa3…9986b8     ac   ← 33字节 push,一顶 0x01 帽子,普通 OP_CHECKSIG
```

同一段公钥材料 `ff1f9fa3…9986b8`。在 CSFS 叶里被 push 成 **32 字节**。在 APO 叶里是 **33**——戴了顶 `0x01` 帽子——而它后面的 opcode 只是个普通的 `OP_CHECKSIG`(`ac`)。**APO 根本没加任何新 opcode。** 它的全部机制就是那顶一字节帽子 + 一组新的 sighash flag:`0x01` 前缀把 `OP_CHECKSIG` 切进*anyprevout 模式*,让签名不再绑定它花的是哪枚 UTXO。

所以一把被 push 的公钥"是 32 还是 33 字节",是这个升级*住在哪一层*的指纹。32 字节:公钥被直接用(CSFS、CTV 的 hash、IK)。33 字节带 `0x01`:公钥是个模式开关,真正的机器在更深一层、在签名里。(这个"深一层"最漂亮的证明:APO 的两笔花费 `03c0577c…` 和 `46091190…`,在两枚不同的 UTXO 上带着**逐字节相同的 witness**——一个真的不在乎自己花的是哪枚币的签名。)

## 第 6 层 —— 那个空口袋

还有最后一个预留插槽,而且几乎全无文档:**annex**,一个必须以 `0x50` 开头的 witness 字段。它被预留、被签名覆盖,而截至今天——**什么用都没有。** 一个缝在每笔 Taproot 花费里的空口袋,等着未来某个升级给它含义。

这一处是地图上真正的空白。任何语言里关于 annex 的、面向开发者的文字都极少——这正好是插旗的地方:构造一笔真带非空 annex 的花费,在链上展示签名怎么覆盖它、脚本怎么看不见它。(这个实验,是这个系列还欠的唯一 artifact——而它值得做,恰恰因为没人做过。)

## 旋钮只是预设,网格才是整个空间

再回到 APO 一下,因为它撬开了一样东西。APO 蒙掉"我花的是哪枚币"时,不是一整块蒙掉的——它有**两个深浅**:`ANYPREVOUT` 蒙掉这枚币的**身份**(prevout),但仍然认它的**脚本**和**金额**;`ANYPREVOUTANYSCRIPT` 连脚本和金额也蒙掉。所以,一个签名对一个输入"承诺了什么",从来就不是一个开关——它是一**捆子字段**(身份、脚本、金额、sequence),而 APO 让你一片一片把它们剥下来。

现在用这个镜头回看输出侧。`SIGHASH_NONE` 蒙掉的是**整个输出**——收款人(脚本、"地址")和金额,一起、粗暴地一刀切掉。可输出也是同一种"捆":一个地址 + 一个金额。原则上,你**完全可以**只认**金额、不认收款人**,或者只认**收款人、不认金额**。只是标准 sighash 不给你这个旋钮——`ALL / SINGLE / NONE` 是三个粗档预设,压在一张细得多的网格上。

所以这东西真正的形状,是那 6 种 flag 只透露了一角的:

> 一个签名,承诺的是交易**子字段的一个子集**——这个输入的身份、那个输入的金额、这个输出的脚本、那个输出的金额、锁定时间……sighash flag 只是这张网格上的**几个粗档预设**。APO 在输入侧多给了几个细档。但网格本身很大,flag 只踩到它几个角。

回想 sighash 小册子《[签名能看见什么](https://sighash.bitcoincoding.dev/)》里那对 **看(SEE)/ 蒙(BLIND)** 旋钮:一个 flag 只能整块翻。底下这张网格更细——

```
   粗档旋钮(一个 sighash flag)              底下那张细网格
   输出:  ALL / SINGLE / NONE              每个输入  = [ 身份 | 脚本 | 金额 ]
   输入:  都认 / 只我(ACP) / 都不认(APO)     每个输出  = [ 地址 | 金额 ]

                    身份     脚本    金额
          输入 0     ● 看     ● 看    ● 看
          输入 1     ○ 蒙     ● 看    ● 看     ← APO 只蒙掉输入1的身份
          输出 0      —       ● 看    ○ 蒙     ← 认地址、蒙金额
          输出 1      —       ○ 蒙    ● 看     ← 蒙地址、认金额
                     ● = 看(SEE)      ○ = 蒙(BLIND)

   粗档 flag 只能整行翻 —— 网格上几个角。
   CAT + CSFS 能翻任意一格:想认哪几格就粘哪几格,再验。
```

而**这里**,它才从冷知识变成了要紧事。因为有一种办法能踩到网格上**任意**一点——不是预设,而是任你挑的、任意可承诺子字段的子集:你用 `OP_CAT` **亲手一段一段把要签的 message 拼出来**,再用 `OP_CHECKSIGFROMSTACK` 对着这张亲手拼的 message 验签。想只认输出 2 的**金额**、别的都不认?把那一格粘出来、签、验。只认 prevouts、不认金额?同一招。**粗档 flag 从来只是一段连续体上的采样点;CAT+CSFS 把整段连续体变成可寻址的。**

这就是为什么"证明 CAT+CSFS 能复现这些承诺"不是脚注。它说的是:**整张网格——`SIGHASH_ALL`、`ANYONECANPAY`、`SINGLE`、`ANYPREVOUT` 各自只踩到一个粗档角落的那张网格——今天,用已经激活的操作码,就能手搓着够到每一点。** flag 是预设,CAT+CSFS 是整台键盘。

## 数一数空着的插槽

退一步,整幅图就是一摞预留插槽,大部分还封着:

- Witness 版本 **v2–v16**:十五个,空。
- `0xc0` 以上的 leaf version:一整段,空。
- NOP opcode:用掉几个(CLTV、CSV),CTV 提案再占一个,其余开着。
- OP_SUCCESS opcode:约 80 个;CAT、CSFS、INTERNALKEY 占了,还剩约七十七个开着。
- annex:一个空口袋。

那是**上百个预留但空着的升级插槽**这个量级。每一个未来的软分叉,都得把自己折进这些形状之一——一个只读的 NOP 检查、一个动栈的 OP_SUCCESS opcode、一个 sighash-flag + 公钥前缀的把戏、一个新的 witness version、或者那个 annex——否则就得论证"再加一个新插槽"。**这套约束集——比特币愿意接受一个改动的那些形状——就是它扩展性的语法。** 它不写在任何一个 BIP 里。它写在字节里。

关于比特币脚本的写作,大多问一个 opcode *做什么*。这篇问的是它底下那个问题:*一个 opcode 是怎么被允许存在的*——而答案,竟然可以一个字节一个字节读出来,就在一个不打开就什么都不给你的 `tb1p` 地址上。

---

*本文引用的每一笔交易都在 signet 上。在[交互式浏览器](./explorer.html)里切换它们。各 opcode 的逐字节文章——[OP_CAT](https://medium.com/@aaron.recompile/op-cat-on-signet-concatenation-commitment-and-bitcoin-inquisition-ed34a07866d6)、[OP_CHECKSIGFROMSTACK](https://medium.com/@aaron.recompile/op-checksigfromstack-on-signet-sign-anything-verify-on-stack-9cf70ab07583)、[OP_CHECKTEMPLATEVERIFY](https://medium.com/@aaron.recompile/op-checktemplateverify-on-signet-locking-outputs-at-utxo-creation-time-1d623fbe3899)、[SIGHASH_ANYPREVOUT](https://medium.com/@aaron.recompile/sighash-anyprevout-on-signet-when-signatures-stop-binding-to-utxos-eed4fc475668)——在配套的 [signet 系列](https://medium.com/@aaron.recompile)。规范:[BIP-341/342](https://github.com/bitcoin/bips/blob/master/bip-0342.mediawiki)、[BIP-119](https://github.com/bitcoin/bips/blob/master/bip-0119.mediawiki)、[BIP-118](https://github.com/bitcoin/bips/blob/master/bip-0118.mediawiki)。*
