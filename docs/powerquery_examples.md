# PowerQuery（M）例
## signals.csv
```
let
  Source = Csv.Document(Web.Contents("https://YOUR_DOMAIN/out/signals.csv"),[Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),
  Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
  Typed = Table.TransformColumnTypes(Promoted,{{"asof", type date}, {"symbol", type text}, {"action", type text}, {"score", type number}, {"theme", type text}, {"reason", type text}, {"side", type text}, {"qty_jpy", Int64.Type}})
in
  Typed
```

## orders.csv
```
let
  Source = Csv.Document(Web.Contents("https://YOUR_DOMAIN/out/orders.csv"),[Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),
  Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
  Typed = Table.TransformColumnTypes(Promoted,{{"asof", type date}, {"symbol", type text}, {"market", type text}, {"side", type text}, {"order_type", type text}, {"limit_price", type number}, {"qty", type number}, {"note", type text}})
in
  Typed
```
