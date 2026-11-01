"""Upper limit of the Fed's federal funds target range (daily), from FRED.
Writes data/raw/fed_target_upper.csv."""
from common import RAW, download

download("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFEDTARU", RAW / "fed_target_upper.csv", force=True)
