# oss-pocket

Signature: Mourad.Soltani

Local CSV tracker for the EU-wide €10,000 cross-border B2C distance-selling threshold used by the One Stop Shop (OSS) regime. Built for solo EU sellers who outgrow a spreadsheet before they outgrow a spreadsheet tool.

This is not tax advice and it does not file a return. It only scores the rows you mark as in-scope.

## Why this exists

Union OSS registration is generally required once cross-border B2C distance sales of goods and TBE services to other EU countries exceed €10,000 in the current and previous calendar year. Solo sellers usually track that number in a sheet and miss domestic-vs-export exclusions. oss-pocket makes the exclusion rules explicit and testable.

No public GitHub repository named oss-pocket, and no repository described as a CSV distance-selling threshold tracker, was found when this package was created.

## CSV columns

| column | values |
| --- | --- |
| date | YYYY-MM-DD |
| seller_country | ISO-2 EU member state |
| buyer_country | ISO-2 |
| net_eur | decimal euros, net of VAT |
| buyer_type | b2c or b2b |
| supply | goods, tbe, or service |
| note | optional |

Rows that count: same calendar year, seller matches `--seller`, buyer is a different EU country, buyer is B2C, supply is `goods` or `tbe`, amount is positive.

Rows that do not count: domestic sales, B2B, non-EU buyers, general services, other years.

## Run

```bash
python3 -m oss_pocket.cli health
python3 -m oss_pocket.cli report samples/sales.csv --seller FR --year 2026
```

Exit codes: `0` under threshold, `2` at or over threshold, `1` on bad input.

## Tests

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

## License

MIT. Copyright Mourad.Soltani.
