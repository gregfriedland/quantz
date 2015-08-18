from pyalgotrade import strategy
from pyalgotrade import plotter
from pyalgotrade.tools import yahoofinance
from pyalgotrade.technical import bollinger
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade import broker

USE_STOPS = False

class BBands(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, bBandsPeriod, numStdevs):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = instrument
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__bbands = bollinger.BollingerBands(feed[instrument].getAdjCloseDataSeries(), bBandsPeriod, numStdevs)

    def getBollingerBands(self):
        return self.__bbands

    # called when trade is entered to use stop order
    def onEnterOk(self, position):
        if USE_STOPS:
            execInfo = position.getEntryOrder().getExecutionInfo()

            lower = self.__bbands.getLowerBand()[-1]
            middle = self.__bbands.getMiddleBand()[-1]
            upper = self.__bbands.getUpperBand()[-1]
            stopPrice = execInfo.getPrice() - 2*(upper - lower)
            self.info("BUY at $%.2f (stop=%.2f)" % (execInfo.getPrice(), stopPrice))

            self.__position.exitStop(stopPrice, True)

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        if position.getExitOrder().getType() == broker.Order.Type.STOP:
            order_type = "stop"
        else:
            order_type = "market"
        self.info("SELL at $%.2f with a %s order" % (execInfo.getPrice(), order_type))
        self.__position = None


    def onExitCanceled(self, position):
        if not USE_STOPS:
            # If the exit was canceled, re-submit it.
            self.__position.exitMarket()

    def onBars(self, bars):
        lower = self.__bbands.getLowerBand()[-1]
        middle = self.__bbands.getMiddleBand()[-1]
        upper = self.__bbands.getUpperBand()[-1]
        if lower is None:
            return

        shares = self.getBroker().getShares(self.__instrument)
        bar = bars[self.__instrument]
        if shares == 0 and bar.getAdjClose() < lower:
            sharesToBuy = int(0.9 * self.getBroker().getCash(False) / bar.getClose())
            self.__position = self.enterLong(self.__instrument, sharesToBuy)
        elif shares > 0 and bar.getAdjClose() > upper:
            if USE_STOPS:
                self.__position.cancelExit()
            self.__position.exitMarket()

def main(plot):
    instrument = "googl"
    bBandsPeriod = 40
    numStdevs = 1

    # Download the bars.
    feed = yahoofinance.build_feed([instrument], 2014, 2015, "data")

    strat = BBands(feed, instrument, bBandsPeriod, numStdevs)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, True, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("upper", strat.getBollingerBands().getUpperBand())
        plt.getInstrumentSubplot(instrument).addDataSeries("middle", strat.getBollingerBands().getMiddleBand())
        plt.getInstrumentSubplot(instrument).addDataSeries("lower", strat.getBollingerBands().getLowerBand())

    strat.run()
    print "Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05)

    if plot:
        plt.plot()


if __name__ == "__main__":
    main(True)