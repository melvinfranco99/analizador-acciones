"""
Universo de acciones a analizar: constituyentes aproximados del S&P 500
y del Nasdaq 100 (grandes empresas de EE. UU., la inmensa mayoria
disponibles en brokers como Trade Republic).

La lista es una instantanea razonablemente actual pero no oficial: los
indices cambian su composicion con el tiempo. Si un ticker esta obsoleto
o deslistado, el motor de analisis simplemente lo salta sin romper la
ejecucion (ver engine/data.py).
"""

SP500 = [
    # Tecnologia
    "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "ADBE", "AMD", "ACN", "CSCO",
    "IBM", "TXN", "QCOM", "INTU", "NOW", "AMAT", "ADI", "LRCX", "MU", "KLAC",
    "SNPS", "CDNS", "PANW", "FTNT", "ANSS", "ROP", "MSI", "HPQ", "DELL", "NXPI",
    "MCHP", "ON", "GLW", "TEL", "APH", "KEYS", "TDY", "TER", "ZBRA", "JBL",
    "STX", "WDC", "GEN", "AKAM", "JNPR", "NTAP", "SWKS", "QRVO", "ENPH", "FSLR",
    "EPAM", "PTC", "CTSH", "IT", "GDDY", "HPE", "VRSN",
    # Comunicacion
    "GOOGL", "GOOG", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "CHTR",
    "EA", "TTWO", "WBD", "OMC", "IPG", "MTCH", "LYV", "NWSA", "NWS", "FOXA", "FOX", "PARA",
    # Consumo discrecional
    "AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "BKNG", "TJX", "SBUX", "ABNB",
    "MAR", "GM", "F", "ORLY", "AZO", "YUM", "ROST", "CMG", "HLT", "DHI",
    "LEN", "NVR", "PHM", "GRMN", "ULTA", "EBAY", "ETSY", "BBY", "DPZ", "POOL",
    "LVS", "MGM", "WYNN", "RCL", "CCL", "NCLH", "APTV", "TSCO", "KMX", "GPC",
    # Consumo basico
    "PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "MDLZ", "CL", "KMB",
    "GIS", "STZ", "SYY", "KHC", "HSY", "MKC", "KDP", "KR", "ADM", "TSN",
    "CHD", "CLX", "TAP", "CAG", "CPB", "SJM", "HRL", "BF-B", "LW", "EL", "MNST",
    # Salud
    "UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "BMY",
    "AMGN", "MDT", "ELV", "CVS", "CI", "ISRG", "GILD", "VRTX", "REGN", "ZTS",
    "SYK", "BSX", "BDX", "HCA", "MCK", "HUM", "IDXX", "IQV", "A", "RMD",
    "EW", "DXCM", "BIIB", "MTD", "WAT", "CAH", "COO", "ALGN", "MRNA", "ZBH",
    "STE", "VTRS", "INCY", "CRL", "HOLX", "TECH", "PODD", "RVTY",
    # Financieras
    "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPGI", "BLK",
    "AXP", "C", "SCHW", "CB", "PGR", "MMC", "ICE", "CME", "USB", "PNC",
    "AON", "TFC", "AIG", "MET", "TRV", "AFL", "ALL", "PRU", "MSCI", "AJG",
    "BK", "STT", "FITB", "HBAN", "RF", "CFG", "KEY", "NTRS", "SYF", "DFS",
    "MTB", "CBOE", "FDS", "WTW", "GL", "L", "RJF", "IVZ", "BEN", "PFG", "ACGL", "CINF", "HIG", "AMP",
    # Industriales
    "CAT", "HON", "UNP", "RTX", "BA", "GE", "DE", "LMT", "UPS", "ADP",
    "ETN", "NOC", "GD", "ITW", "EMR", "CSX", "NSC", "WM", "PH", "TDG",
    "CTAS", "FDX", "PCAR", "JCI", "CARR", "GWW", "CMI", "RSG", "ODFL", "XYL",
    "HWM", "IR", "OTIS", "AME", "ROK", "PAYX", "VRSK", "FAST", "LHX", "DOV",
    "EFX", "BR", "EXPD", "J", "PWR", "TT", "URI", "LDOS", "HII", "TXT",
    "ALLE", "MAS", "NDSN", "SNA", "PNR", "SWK", "CHRW", "AOS", "GNRC",
    # Energia
    "XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "OXY", "WMB",
    "KMI", "OKE", "HES", "HAL", "DVN", "BKR", "TRGP", "FANG", "CTRA", "EQT",
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "ED", "PEG",
    "WEC", "ES", "AWK", "DTE", "PPL", "FE", "AEE", "CMS", "CNP", "ATO", "NI", "LNT", "EVRG", "PNW",
    # Materiales
    "LIN", "SHW", "APD", "ECL", "FCX", "NEM", "NUE", "DOW", "DD", "PPG",
    "VMC", "MLM", "ALB", "IFF", "CTVA", "LYB", "CE", "AVY", "MOS", "EMN", "PKG", "IP", "BALL", "AMCR", "STLD",
    # Inmobiliario
    "PLD", "AMT", "EQIX", "CCI", "PSA", "O", "SPG", "WELL", "DLR", "AVB",
    "EQR", "VTR", "SBAC", "ARE", "MAA", "INVH", "ESS", "KIM", "UDR", "HST", "REG", "CPT", "BXP", "VICI", "EXR", "IRM",
]

NASDAQ100_EXTRA = [
    # Empresas del Nasdaq 100 que no suelen coincidir con la lista anterior
    "MRVL", "DDOG", "CRWD", "TEAM", "WDAY", "ZS", "MDB", "ILMN", "ASML",
    "MELI", "TTD", "ZM", "DLTR", "SIRI", "GFS", "ARM", "SMCI", "APP",
    "PYPL", "LULU", "ADSK", "CSGP", "CDW", "PDD", "AZN", "PCTY", "CCEP",
    "GEHC", "ONON", "DASH",
]

UNIVERSE = list(dict.fromkeys(SP500 + NASDAQ100_EXTRA))
