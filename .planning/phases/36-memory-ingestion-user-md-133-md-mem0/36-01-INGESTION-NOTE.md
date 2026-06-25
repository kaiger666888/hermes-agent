# Phase 36 — Memory Ingestion Operator-Action Note

**Authored:** 2026-06-25 (Plan 36-02)
**Audience:** Kai (operator), Phase 37 verification
**Purpose:** Single document the operator reads to complete the live mem0 ingestion that Plans 36-01 + 36-02 prepared.

---

## Status

- **Plan 36-01 (tooling built):** COMPLETE — `batch_ingest.py` + `spot_check.py` exist at `plugins/memory/mem0/scripts/` (commits `d7aa2eb7c`, `50ee1b8b2`).
- **Plan 36-02 (USER.md migrated + dry-run validated + this note):** COMPLETE — `~/.hermes/memories/USER.md` carries openclaw-origin frontmatter; dry-run enumerates 124 files successfully; this note is committed.
- **Live ingestion (MEM-02 / MEM-03 / MEM-04 end-to-end verification):** **BLOCKED** on operator configuring `MEM0_API_KEY`. Until then the runtime mem0 backend has zero entries and Phase 37 SC#2-4 cannot be exercised. The commands below unblock it in <5 minutes.

---

## File Count Correction

`ROADMAP.md`, `STATE.md`, and `REQUIREMENTS.md` MEM-02 all state **"133 .md files / 1.3MB"**. The verified actual count, gathered 2026-06-25 per `36-CONTEXT.md`, is:

- **File count:** 124 `.md` files (not 133)
- **Total content size:** **837,136 bytes (817 KB)**, not 1.3 MB (~37% smaller than estimated)

Independently reproducible:

```
$ find ~/.openclaw/workspace/memory -name '*.md' | wc -l
124
$ find ~/.openclaw/workspace/memory -name '*.md' -exec wc -c {} + | tail -1
837136 总计
```

Phase 37 verification and any future doc-consistency patch should treat **124 files / 817 KB** as the source of truth. The "133 / 1.3 MB" figure was a planning estimate that preceded direct filesystem inspection. A doc-consistency patch (ROADMAP.md + STATE.md + REQUIREMENTS.md MEM-02) is **flagged but out of Phase 36 scope** — Phase 36 ships against the verified 124 number.

---

## Inventory (dry-run output)

Output of `python3 plugins/memory/mem0/scripts/batch_ingest.py --dry-run` captured 2026-06-25. 124 file lines, format `{path}\t{sha256-hex}`. Hashes are computed over UTF-8 file bodies.

```
/home/kai/.openclaw/workspace/memory/2025-06-03.md	9ff336b2447a57514feb29564bcef61489eeca8c3403cd6ec5b17001ffc18012
/home/kai/.openclaw/workspace/memory/2025-06-13.md	f8d3b4d200973b372b33cc6db77f8f657a1a2d073af3e250ddd5b92103c1396d
/home/kai/.openclaw/workspace/memory/2025-06-14.md	047daa449c1296faf498712ffd7733361976cf2c5e7dfcc5a8a3a5b382181a9d
/home/kai/.openclaw/workspace/memory/2026-02-12.md	fb029295af287312ba2287b902b55dc66f1cc04d5aceac0a7c438e13e6bc4c54
/home/kai/.openclaw/workspace/memory/2026-02-13.md	ffb116c92bfaa482b4d256e638ccbb3983f65094642243312bc8aca2f3467f95
/home/kai/.openclaw/workspace/memory/2026-02-15.md	5c7b4cd21fbb1e54126bc045a1f677a9cfd975526201596fe33031708683ae57
/home/kai/.openclaw/workspace/memory/2026-02-16.md	59ada0be0d9665f9c968cd271c4fee4483f89f6fac11435c537b9fce54d4877
/home/kai/.openclaw/workspace/memory/2026-02-17.md	98d23200091fd7d6215ac8e9dfff2813a07c94405224eda44c5d6ca6be35a310
/home/kai/.openclaw/workspace/memory/2026-02-18.md	403fd0559f9ec132a798d41820dc570b7830e4f169b6fab78debd1416ac51aa9
/home/kai/.openclaw/workspace/memory/2026-02-19.md	c5f7f0909933ea2c4a7864937787787100a93a7a0ccbea4677c2a25668b6f81f
/home/kai/.openclaw/workspace/memory/2026-02-20.md	97cd0537fed08b27d8f4c87e255d1595dcae40e559c71899b5f3c66dd5a4d56e
/home/kai/.openclaw/workspace/memory/2026-02-21.md	8e6cf9aa685932c9901be301d3ac29893bf03aaa1a70537cf55884bb83103c69
/home/kai/.openclaw/workspace/memory/2026-02-22.md	dd657dd1357e056178580f852799c44b57dcfee9959204f0e376b222226a3aaa
/home/kai/.openclaw/workspace/memory/2026-02-24.md	e03f69fbd5a03703be6a860eb726dc2e76e417e9cf7cadfebc21758584742448
/home/kai/.openclaw/workspace/memory/2026-02-25.md	22289c6b8fc77113f70fc9e1bb30d111f0f62a62e75db7cdc9f629aea0e9b3b4
/home/kai/.openclaw/workspace/memory/2026-02-28.md	8da183be80e97c0419685d04f553a3334129a1b19fa3a520a0ad439e164d7520
/home/kai/.openclaw/workspace/memory/2026-03-01.md	0acab35522615c0d31e35ffa709626f72a163ddbd15ebd63caafda6f3b7663b4
/home/kai/.openclaw/workspace/memory/2026-03-02.md	c3723c5397450002b7059e01e84a2eaa20a0cb1769c108bd13718eda278fa12c
/home/kai/.openclaw/workspace/memory/2026-03-03.md	77fbf3e67d09a96f6b7f7b3abdd839e9fb75ac7328301ca9c40acc12cbe4f191
/home/kai/.openclaw/workspace/memory/2026-03-04.md	763c6398fae6f6921c605ebf957d6b08a60069e6e9c6855ce82982423d5715b5
/home/kai/.openclaw/workspace/memory/2026-03-05.md	a60a37af32fbf31bf4500a406386d5e963ba3c87721bcad7f1200ffda7dc5a02
/home/kai/.openclaw/workspace/memory/2026-03-06.md	78bab57ff7a11741f42101321dbc5d6bf120df0332af9473296c6416792b81fb
/home/kai/.openclaw/workspace/memory/2026-03-07.md	65932cfcd403c54ff4f24bede33bdc75930b18c3bb44f144b672ab1165b400da
/home/kai/.openclaw/workspace/memory/2026-03-08.md	924bef8339891a812874c088f51fbdc66f5a7716540092d43f3eec6840c8ac02
/home/kai/.openclaw/workspace/memory/2026-03-09.md	151d4ccb9fe352a26bc4c81e6457eda88be29d376187fd1ab4ac0667be027b0c
/home/kai/.openclaw/workspace/memory/2026-03-10.md	e84c3871826ff760baf612ae456e775ae5c1cf05a4b5f8032c52f007df15d59b
/home/kai/.openclaw/workspace/memory/2026-03-12.md	76784638c4410d6597c9b16d29d2e906e726a1b858f35bd52d0b3c0a55cf1fd5
/home/kai/.openclaw/workspace/memory/2026-03-13.md	3515cef6b9e42d31455aab939d49d69a712e3415e6d6683a6d80664fb15acb32
/home/kai/.openclaw/workspace/memory/2026-03-14.md	205df8f1f34048d3360609cd7690b12933711ee42776e3439b4863795751a0c0
/home/kai/.openclaw/workspace/memory/2026-03-15.md	5dd428390c4a46430aae652cab2c642734fee58f9351fcebc403597f37a23d80
/home/kai/.openclaw/workspace/memory/2026-03-16.md	4801a49ed76f5c5caf42e4a4f09614a020494b1a6f45b4283baf21b9145b8a97
/home/kai/.openclaw/workspace/memory/2026-03-17.md	67888b392041a9ed6fc8ec7d3bb675e85e2199831f335fe368ce21a4a774b36c
/home/kai/.openclaw/workspace/memory/2026-03-18.md	5f6a6142fc8d03eaff155bf29e1d1a7c45ce8de7664eafab9a48833cab6cf871
/home/kai/.openclaw/workspace/memory/2026-03-19.md	eb7d75e8e136235909bbd16edb382790f57eff7b71bebb68414ae6d041d9ff68
/home/kai/.openclaw/workspace/memory/2026-03-20.md	86bf1abee929a264efe8389bae16433b2fd42149286d3aa259300f3672b9df8a
/home/kai/.openclaw/workspace/memory/2026-03-21.md	b6afe87a284316a00d67be575cf805b7af442cba1c940205ede49abbdcf490a7
/home/kai/.openclaw/workspace/memory/2026-03-22.md	7e9d18566806e92855c3709b44b5b457e9b5668bdadfeb685cf674adfc817ab4
/home/kai/.openclaw/workspace/memory/2026-03-23.md	b82d737dd3027c941201556e46cc45e6e1b9398f5171a02e45271962e19c53b6
/home/kai/.openclaw/workspace/memory/2026-03-24.md	2dddd18bbe9ec5005697f2cb1f0d51d85dca96b47d2a92421c86d8448afc5d3d
/home/kai/.openclaw/workspace/memory/2026-03-25.md	a90177ca7bf2cfc81e55cf76c54ea2c3f1de762bd283ba94e415c940eb481813
/home/kai/.openclaw/workspace/memory/2026-03-26.md	4ff89702998dfa4c88d1f02c587857bc52a0ec2a306c10ed3090cb1ecfc4c437
/home/kai/.openclaw/workspace/memory/2026-03-27.md	490deb74be5fbb48d4cb414c45daefe9687e7cf43e3c5aaa9627808acacb8dc6
/home/kai/.openclaw/workspace/memory/2026-03-28.md	1eca4882a502d0ced0ccb74c546c525e3c7da72f9191553d3b3609bbf53f0a76
/home/kai/.openclaw/workspace/memory/2026-03-30.md	f1b522427e8e6a68658b48af3b8d226a96ec63e168e5d2ae0fb17e6298608271
/home/kai/.openclaw/workspace/memory/2026-03-31.md	fb037dcd97d2637e8a7d960d33124beacc32d9000109be889601ffbf81ab82fc
/home/kai/.openclaw/workspace/memory/2026-04-13.md	2f9d44e3a0c204af72a3ec8be356955b02feba29f4625b4ea3acb0d1c30651a5
/home/kai/.openclaw/workspace/memory/2026-04-14.md	1eb6b1c99adbc81341507153017e26d6f79e86b4ee4134e26b8a5025f6704573
/home/kai/.openclaw/workspace/memory/2026-04-15.md	3ca4ec3a7f43839a7a7a6ce4a58d88291d334d937d99973389a1d188ea32fd88
/home/kai/.openclaw/workspace/memory/2026-04-16.md	76e6c2edd40d1a1fb23a879493b8c59196e382f2eaaaf21dfbb00d91cb0b1970
/home/kai/.openclaw/workspace/memory/2026-04-18.md	d88aa54c0c42bf4502d3673fbd39bdc1e7d7ebbfefd04c73dd70c5d61c3316fa
/home/kai/.openclaw/workspace/memory/2026-04-19.md	14a96c2c7e4f8ae2cc6704567a9fba82185df540d01e935b812a2ecb530f0b09
/home/kai/.openclaw/workspace/memory/2026-04-20.md	6a2ba113fc9cf2a2aeac0433d204cf51fdc63e4310015029bfc558238c27e0e3
/home/kai/.openclaw/workspace/memory/2026-04-22.md	b319b5e064f9a0a2d2c4c0abb43d0e6f86d1560a623787027a34fa9deaecf0a8
/home/kai/.openclaw/workspace/memory/2026-04-23.md	968c1b3c614de159b2d310bb2f6b54a50543370f5380ccee803ec2e976d762f1
/home/kai/.openclaw/workspace/memory/2026-04-24.md	b10ac88898895c8427744a3daf4a082b045dbb80a30ec7b67ffe9b005e980640
/home/kai/.openclaw/workspace/memory/2026-04-26.md	ef211c9ad418f8c0255144e888ca51fff87dc21b5b8dfcff2106221cd03ca115
/home/kai/.openclaw/workspace/memory/2026-04-30.md	887701b81ba51b12dadd490d52adfa20ae733a5539e8beca46b8c90dd8cddbfa
/home/kai/.openclaw/workspace/memory/2026-05-02.md	35de56a76edf1fec17727d2625eb433ebabcb28447d9a4cf92af48c7b0896b86
/home/kai/.openclaw/workspace/memory/2026-05-09.md	69da514f50ee09b77f9a8e68db5c1c37fd327759c3af66575242b97fa8598e01
/home/kai/.openclaw/workspace/memory/2026-05-10.md	fd312bbb1cc0f88f53ffb09a98d33fece3d27b4eb2b468015c3c6c8542f19053
/home/kai/.openclaw/workspace/memory/2026-05-11.md	6e7696aea2bd9d5baea9ffe1dba7c74a15ef4dd208155ea785c4f23c7d7a4edf
/home/kai/.openclaw/workspace/memory/2026-05-13.md	30b5a7c57f6456415d4a8430726ca872c7601933e6676421a8c8031f3d632be0
/home/kai/.openclaw/workspace/memory/2026-05-14.md	ed3f671d16b18be80d6bb2474973c3bfab13b14d5bebd259541f2c2a212307cf
/home/kai/.openclaw/workspace/memory/2026-05-16.md	48f511a3ea2ba4d041dd3be2fafb0db6b2e54f0496867a9f3d23a5d9def683ba
/home/kai/.openclaw/workspace/memory/2026-05-17.md	1501b4a6e149ba1130ee09cc95ea326b44820fd100f7407e7551c0d8dd5f044f
/home/kai/.openclaw/workspace/memory/2026-05-21.md	edc102a404b73597ccb2441a084a15260ebb3d55aa5cdd9e39a621bdc56e6d57
/home/kai/.openclaw/workspace/memory/2026-05-23.md	100148f96303066bb4c146ab5ebae1818dae456266a87da20468fe9656d672d9
/home/kai/.openclaw/workspace/memory/2026-05-25.md	b6b92017b0fd4ee815738b5d2bdcec48d587369418927ee0b1d4b519005943cb
/home/kai/.openclaw/workspace/memory/2026-05-26.md	65aeaaf3cd73ff558f43d58acedfa5e546653f5493205acd8752ccf2569e6434
/home/kai/.openclaw/workspace/memory/2026-05-27.md	911e19d58668024e5440eb1310df15bbc79ea7520cb4f6a408de5860ed3dd1f8
/home/kai/.openclaw/workspace/memory/2026-05-28.md	f4b856969b3d022d7d9bf0bcc9556ccdb74949e1ef177dacb0392fb6546079c0
/home/kai/.openclaw/workspace/memory/2026-05-29.md	c18cf728bd25759b6223265949efeea7f3a40173f5faefcfcc64b6775664cd71
/home/kai/.openclaw/workspace/memory/2026-05-30.md	80f61a38894dd2c10c629dd0c43453384f58234b6f74665327043c40d82e29a6
/home/kai/.openclaw/workspace/memory/2026-05-31.md	f3ea727f3a079abd169e7e8bd4c48ac153436f4e6675827ecd74baeaa25035c3
/home/kai/.openclaw/workspace/memory/2026-06-01.md	dcc928fb5fe7728234fd75b41e1e0b1b9d4d97c18c740138b4354279977b2437
/home/kai/.openclaw/workspace/memory/2026-06-02.md	31a181699fcbf11a35b3d4483d97a7fc70271806cf30a560d5f545e559cfb982
/home/kai/.openclaw/workspace/memory/2026-06-03-comfyui-trellis2-deployment.md	4fe0cc4d35a9fb7e6090655b285f83dcc629f4fd531fe47167b6e631a7d5d7c5
/home/kai/.openclaw/workspace/memory/2026-06-03.md	5efa91462482d4ab86ae1adb9079a1a6bc7666b144ef3f3f5490d10e4abf1244
/home/kai/.openclaw/workspace/memory/2026-06-04.md	9e75070a36116b41e0e9b626e8572cb3adcf47bcc542ad240c2a227f294acd81
/home/kai/.openclaw/workspace/memory/2026-06-05.md	21eafeec9be1cf95ce4ed730abaecab9d3c27f1e7ddc067a17e6e0a9dc3b5c47
/home/kai/.openclaw/workspace/memory/2026-06-06.md	6a730c8f5ead9ced813ba0ecb1dfd8b6b8b426f4b02660e277f5f1e7caf318aa
/home/kai/.openclaw/workspace/memory/2026-06-07.md	54710e384b7239766e86ba85fc3c39f10c04a700a1dbb0bd8b6a4b570b163ba1
/home/kai/.openclaw/workspace/memory/2026-06-08.md	b1ebad7d737b74076080f3c997303b3bee19889248216cd52d7265c58d8cf801
/home/kai/.openclaw/workspace/memory/2026-06-09.md	7bbfd42a682e5c7964ce8eeeda577986a1df3ee9f67bf916313adf08990fbce2
/home/kai/.openclaw/workspace/memory/2026-06-10.md	db62cba0e4f63b758c2cb962cf4015c98236f4bc47d30422e58832bf701bffec
/home/kai/.openclaw/workspace/memory/2026-06-11.md	c6b1e1fda9a7bc60da276bd62db04fcab4a0fccb5941b08466594cfc43800a69
/home/kai/.openclaw/workspace/memory/2026-06-13.md	cecc5ab535431c3c6a1e8dedf44ae25925d628b0358827aa2ba75ea0ae673411
/home/kai/.openclaw/workspace/memory/2026-06-14.md	ee49d75eb18779f3c2e77c031c385c948a51815497f092aef4ab31e1b8693dce
/home/kai/.openclaw/workspace/memory/2026-06-16.md	ffba5063e68f5b6c84d490a693efe843ce06ea3c73375d144ef64f3fedf21522
/home/kai/.openclaw/workspace/memory/2026-06-18.md	e532d1224b11f1b812963b8f2d48cdf47989288e7ac438c08f5160185101efbf
/home/kai/.openclaw/workspace/memory/2026-06-19.md	49a88594a07b3bd40c3e5560c2e145d395bae89d2ace2010c1f7796e28726ea8
/home/kai/.openclaw/workspace/memory/2026-06-22.md	ab65e416a75b162a8cea02c418eba232c6c4cd1b76f27d10334a4e0aaa1c67c9
/home/kai/.openclaw/workspace/memory/2026-06-25.md	3ecf70d7704afe7b30ab33b6b2fa61a8f1d71b589a67662bea0c36a976e88fec
/home/kai/.openclaw/workspace/memory/blender-video-integration-research.md	0845688d6cf2cf515205f4b17f8c49e45ff31e25caa40a15dae2989c239e4303
/home/kai/.openclaw/workspace/memory/brave-api-fix.md	72ef3baf3a968dc1dfeddee549519e867b8dd6156f02a5f8072ecdec2823710f
/home/kai/.openclaw/workspace/memory/canvas-research-report-2025-06-29.md	bc7a732fba630a5535272f40a31d2eb4bd294763cd89e398164f3c8c01f5fef5
/home/kai/.openclaw/workspace/memory/creative-methodology-research-2026-06-17.md	30c0aec84592cf7d1c71483af7bcf4dcb92c7c47f130ed120e2b07751de06205
/home/kai/.openclaw/workspace/memory/daily-task-execution-summary-2026-04-27.md	afc47a7e0fb0b45288d2aa0629d5c63d13c30961877888c8bcae78952e36e43d
/home/kai/.openclaw/workspace/memory/daily-task-execution-summary-2026-04-29.md	9855bf1620bd5263697ce29993a0fcb960885e08a21c3dfc98ead1bd24338743
/home/kai/.openclaw/workspace/memory/daily-tasks-2026-04-24-final-report.md	40f7724135f6eaeafc10d9863b98de72e5cf06c400da30c3c1aba827893741de
/home/kai/.openclaw/workspace/memory/github-review-2026-03-26.md	0c6e36485783cd1ade9919618387018ff62cf197382c6ed51d58f3af3a42ef08
/home/kai/.openclaw/workspace/memory/github-review-2026年02月24日.md	169f4e9faf5233fb2d8dbd334043f60ca01610f3f2e4bc87ac4bdef152514320
/home/kai/.openclaw/workspace/memory/github-review-2026年03月02日.md	93d8f41541f81f960b2d4b84305d861efbc1d1cd47e95a7ecd9d97088779dde0
/home/kai/.openclaw/workspace/memory/github-review-2026年03月04日.md	c77ebfea3f252850cafa0fb8e5976d86b803ae5f18905c6e555b0a19d1d3e871
/home/kai/.openclaw/workspace/memory/knowledge-visualization-research-2026-03-19.md	27ff1f2502d9ef95b5e1ff54387e531c082fc8d10154c345fb5c3aa6db5b2b61
/home/kai/.openclaw/workspace/memory/mental-models-history.md	2e9e68fa906d956a62ab477e67de0c12503090f43c7ebf625d700d60200bae3b
/home/kai/.openclaw/workspace/memory/model-revert-2026-02-12.md	7d68ecf7ff2851dbf39c25cb306a35145b68d1d87a02b553052b6a207942cca1
/home/kai/.openclaw/workspace/memory/model-update-2026-02-12.md	8aace12a558f594eab09af3acdd109f2ed79ad6ab30850b5c9c64ab34b6683c9
/home/kai/.openclaw/workspace/memory/nightly-review-guide.md	08386204897222de4239d05a187a9ab990d8dd4d8fb8fb7a49791ff75f034e12
/home/kai/.openclaw/workspace/memory/nightly-review-summary-2026-02-25.md	0ce50b2208f74a635f0d32bb2362e76ca0ddbc77f049fcdd1884a0bfdb9c22dd
/home/kai/.openclaw/workspace/memory/nightly-review-summary-2026-04-26.md	2cfd0bd6d80bde16e9669706a23767dfc29f4719cadb3c40e789b879116caa26
/home/kai/.openclaw/workspace/memory/nightly-review-summary-2026-05-05.md	bd8a3422ad561903df24a5a0f4aca2540e39654014380f781b4b906a3865946d
/home/kai/.openclaw/workspace/memory/nightly-review-summary-2026-06-21.md	ab066d0a29f591b467d5a18852fcce43f7b3f79dfa2056d6f442391f73a6e89a
/home/kai/.openclaw/workspace/memory/open-source-music-generation-research.md	2c130e8a34c96cafda00435d2ba1127e3bf1310c602ea7af6ab1fff364e8b1f1
/home/kai/.openclaw/workspace/memory/proxy-emergency-fix.md	de37b8d44ed743db7ca1484b70713361f1e0e1c5f9ba41c70744a64944df188b
/home/kai/.openclaw/workspace/memory/proxy-solution.md	c14483b9dcbd5a4f90f9c93309988209ea6a4c1fe84c3a01d2c3e9c646753f0c
/home/kai/.openclaw/workspace/memory/research-comfyui-gguf-fp8-2026-05-31.md	4b8fc84756c01faf2fb796b52e97fa35f878b3845241d1e37cb2d2d6249a39af
/home/kai/.openclaw/workspace/memory/research-comfyui-node-editor-2026-05-30.md	0b1ac2177bff0927dd7eabd585fc815c8151e59c9078df9339e5a622458e8ccd
/home/kai/.openclaw/workspace/memory/research-openclaw-claude-code.md	18ced56cccd8f29414533b8054e2a480e0ab28a1d45b929fc46581616eed39df
/home/kai/.openclaw/workspace/memory/search-fallback-implementation.md	90eb850b04220a52c3c3756a09fbab871b0a163d1f19676627b3376fad3eae65
/home/kai/.openclaw/workspace/memory/uml-tech-radar-summary-2026-04-18.md	1f91073cc26d2d93c39e03b2a4195f9e070849281491eb969b580c19ab66248c
/home/kai/.openclaw/workspace/memory/umlvision-tech-radar-2026-W24.md	99da90fd5b5b851c91caa04455a87c16f82009b34a38c7f6103339b933c481cd
/home/kai/.openclaw/workspace/memory/vibecoding-2026-02-28.md	337bd45a864743d84586bc6336c12159f4b4751c310eaac6238a57f506928657
/home/kai/.openclaw/workspace/memory/vibecoding-content.md	46463f8a32fb1b477f2a4b6f705e225035ada7d92df997179732707947f2567f
```

**Summary line (stderr):** `DRY-RUN: would ingest 124 files (backend presence unknown without API access)`

---

## Tooling Built (Plan 36-01)

Two standalone CLIs at `plugins/memory/mem0/scripts/`:

- **`batch_ingest.py`** — Idempotent batch ingestion keyed on SHA-256 `content_hash` stored in mem0 metadata. Re-runs produce zero new entries when files are unchanged.
  - Flags: `--dry-run` (no API), `--limit N`, `--quiet`, `--source-dir PATH`
  - `--help` one-liner: *"Idempotent batch ingestion of openclaw memory notes into mem0 backend. Re-runs produce zero new entries when files are unchanged (keyed on SHA-256 content_hash stored in mem0 metadata)."*
- **`spot_check.py`** — 5-query verification CLI (mixed CN/EN) covering AIGC deployment / ComfyUI / Trellis / ACE-Step / CosyVoice. Per-query try/except keeps one failure from aborting the run.
  - Flags: `--list-queries` (offline), `--top-k N`, `--no-rerank`, `--quiet`
  - `--help` one-liner: *"5-query spot check of the mem0 backend across AIGC/ComfyUI/Trellis/ACE-Step/CosyVoice topics."*

Both reuse `plugins.memory.mem0._load_config` (env vars + `~/.hermes/mem0.json` precedence) — zero duplicated config logic.

---

## Operator Action Required — Live Ingestion

> **BLOCKER for MEM-02 / MEM-03 / MEM-04 end-to-end verification.**
> `MEM0_API_KEY` is NOT set in `~/.hermes/.env` and `~/.hermes/mem0.json` does not exist. The mem0 cloud backend cannot be reached until the operator completes the steps below.

### Prerequisites

1. **Install mem0 SDK** (if not already installed):
   ```
   python3 -c "import mem0" || pip install mem0ai
   ```
2. **Obtain an API key** from https://app.mem0.ai → API Keys.
3. **Configure the key** in one of two ways:
   - **Option A (env var):** Append `MEM0_API_KEY=<key>` to `~/.hermes/.env`
   - **Option B (config file):** Create `~/.hermes/mem0.json` with:
     ```json
     {"api_key": "<key>", "user_id": "hermes-user", "agent_id": "hermes"}
     ```

### Commands to run (in order, from repo root)

1. **Live ingest** — pulls all 124 files into the backend:
   ```
   python3 plugins/memory/mem0/scripts/batch_ingest.py
   ```
   Expected output: `Ingestion complete: total=124 ingested=124 skipped=0 failed=0`

2. **Spot-check (5 queries)** — verifies semantic search returns relevant results:
   ```
   python3 plugins/memory/mem0/scripts/spot_check.py
   ```
   Expected: 5 query blocks, each with ≥1 result.

3. **Idempotency re-test** — re-run the ingest to confirm zero duplicates:
   ```
   python3 plugins/memory/mem0/scripts/batch_ingest.py
   ```
   Expected: `Ingestion complete: total=124 ingested=0 skipped=124 failed=0`

---

## Expected Outcomes for Phase 37 Verification

The Phase 37 success criteria translate to the following assertion commands. The operator can pre-run them after live ingestion to confirm readiness.

**SC#1 — USER.md migration provenance:**
```
head -6 ~/.hermes/memories/USER.md
# Expected: frontmatter with 'openclaw-origin: true', 'migrated-at: 2026-06-25',
#           'source-path: ~/.openclaw/workspace/USER.md'
```

**SC#2 — 124 entries in mem0 backend:**
```
python3 -c "from mem0 import MemoryClient; import json; cfg=json.load(open('$HOME/.hermes/mem0.json')); c=MemoryClient(api_key=cfg['api_key']); print(len(c.get_all(filters={'user_id':'hermes-user'})))"
# Expected: >= 124
```

**SC#3 — Spot-check returns non-empty results:**
```
python3 plugins/memory/mem0/scripts/spot_check.py
# Expected: each of the 5 query blocks shows >=1 result (non-empty)
```

**SC#4 — Idempotency (re-run produces zero new entries):**
```
python3 plugins/memory/mem0/scripts/batch_ingest.py
# Expected: total=124 ingested=0 skipped=124 failed=0
```

---

## Partial-Ingest Decision

**No partial-ingest decision has been made.** Default scope = all 124 files.

If the operator chooses to ingest only a subset (e.g., most recent N files, or exclude files matching a pattern), document the rationale here **before** running and update SC#2's expectation accordingly.

- Example partial-ingest command: `python3 plugins/memory/mem0/scripts/batch_ingest.py --limit 50` (processes the alphabetically-first 50 — likely the oldest dates).
- Note: `--limit` operates on sorted-by-name order, which interleaves date files with named-research files. It is NOT a "most recent" filter. If recency matters, the operator must move older files out of `~/.openclaw/workspace/memory/` temporarily.

---

## What Phase 36 Ships Without MEM0_API_KEY

Phase 36 ships the following operator-ready artifacts even though live ingestion is deferred:

- **Tooling (Plan 36-01):** `batch_ingest.py` + `spot_check.py` committed at `plugins/memory/mem0/scripts/`. Functional and dry-run-validated.
- **USER.md migration (Plan 36-02):** `~/.hermes/memories/USER.md` exists with `openclaw-origin` frontmatter and byte-identical body to the openclaw source (operator-state, not git-tracked).
- **Dry-run-validated inventory (Plan 36-02):** This document. The 124-file inventory above is reproducible via `python3 plugins/memory/mem0/scripts/batch_ingest.py --dry-run` — exit code 0, no API key required.

Live MEM-02 / MEM-03 / MEM-04 verification is deferred to the operator (commands above) and confirmed by Phase 37 SC#2-4 checks once the backend is populated.
