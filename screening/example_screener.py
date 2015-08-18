#!python

import urllib2
import re
import datetime
import os
import pandas
import time

sp500short = ['a', 'aa', 'aapl', 'abbv', 'abc', 'abt', 'ace', 'aci', 'acn', 'adbe', 'adi', 'adm', 'adp']
sp500 = open("sp500.txt").read().strip().split()
wilshire5000 = open("wilshire5000.txt").read().strip().split()

data_texts = ["Trailing P/E", "Market Cap", "Forward P/E", "PEG Ratio", "Price/Sales", "Price/Book",
    "Enterprise Value/EBITDA", "Profit Margin", "Operating Margin", "Return on Assets", "Return on Equity",
    "Revenue", "Revenue Per Share", "Qtrly Revenue Growth", "Gross Profit", "EBITDA", "Diluted EPS",
    "Qtrly Earnings Growth", "Total Cash", "Total Cash Per Share", "Total Debt", "Total Debt/Equity",
    "Current Ratio", "Book Value Per Share", "Operating Cash Flow", "Levered Free Cash Flow", "Beta",
    "52-Week Change", "52-Week High", "52-Week Low", "50-Day Moving Average", "200-Day Moving Average",
    "Avg Vol \(3 month\)", "Avg Vol \(10 day\)", "Shares Outstanding", "\% Held by Insiders", 
    "% Held by Institutions", "Shares Short", "Short Ratio", "Forward Annual Dividend Yield", 
    "Trailing Annual Dividend Yield"]

regexs = {text: re.compile("<td((?!<td).)*>%s.*?</td>(?P<data><td.*?</td>)" % text) for text in data_texts}
# regexs = {
#     # <td class="yfnc_tablehead1" width="74%">Market Cap (intraday)<font size="-1"><sup>5</sup></font>:</td><td class="yfnc_tabledata1"><span id="yfs_j10_a">13.32B</span></td>
#     "market_cap": re.compile("<td((?!<td).)*>Market Cap \(intraday\).*?:</td>(?P<data><td.*?</td>)")
#     #"market_cap": re.compile("Market Cap \(intraday\).*?:</td>")
#     }

TAG_RE = re.compile(r'<[^>]+>')
def remove_tags(html):
    return TAG_RE.sub("", html)

def load_ticker_html(root_dir, ticker):
    #date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(root_dir, "info_%s.html" % (ticker))

    if not os.path.exists(file_path):
        print "    Downloading data for: " + ticker
        html = urllib2.urlopen('http://finance.yahoo.com/q/ks?s='+ticker).read()
        open(file_path, 'w').write(html)
        time.sleep(0.1)
    else:
        print "    Loading data from disk for: " + ticker

    return open(file_path).read()

def create_dataframe(tickers, regexs):
    df = pandas.DataFrame(columns=data_texts, index=tickers)

    for ticker in tickers:
        html = load_ticker_html("data", ticker)

        for name, regex in regexs.iteritems():
            match = regex.search(html)
            if match:
                match = remove_tags(match.group("data"))
                df[name][ticker] = match

            # print "(%4s) %s: %s" % (ticker, name, match)
    return df

if __name__ == "__main__":
    screener_df = create_dataframe(wilshire5000, regexs)
    screener_df.to_csv("wilshire5000_fundamentals.csv")


