import os
import shutil

from loguru import logger

import anaytics
from handlers.context import HandlerContext
from handlers.handler import AbstractHandler
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['axes.spines.top'] = False
rcParams['axes.spines.right'] = False
PLOT_DIR = 'plots'


def plot(data: pd.DataFrame, column, filename: str) -> None:
    plt.figure(figsize=(12, 4))
    plt.grid(color='#F2F2F2', alpha=1, zorder=0)
    plt.plot(data.index, data[column], color='#087E8B', lw=3, zorder=5)
    plt.title(column, fontsize=17)
    plt.xlabel('Period', fontsize=13)
    plt.xticks(fontsize=9)
    plt.ylabel('Amount', fontsize=13)
    plt.yticks(fontsize=9)
    plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()
    return


class AnalyticsHandler(AbstractHandler):
    run_dry: bool = False

    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Analytics started")
        try:
            if not self.run_dry:
                try:
                    shutil.rmtree(PLOT_DIR)
                    os.mkdir(PLOT_DIR)
                except FileNotFoundError:
                    os.mkdir(PLOT_DIR)
                dict_data = anaytics.generate_dataframe(context.payment_book)
                data_frame = pd.DataFrame.from_dict(dict_data, orient='index')
                data_frame['Total'] = data_frame.sum(axis=1)
                # dupa.to_html("output.html")
                counter = 1
                for column in data_frame.columns:
                    plot(data_frame, column, filename=f'{PLOT_DIR}/{counter}.png')
                    counter += 1
                logger.info("Analytics completed")
        except Exception as e:
            logger.exception("Problem with Analytics", exc_info=e)
            context.pushover.error("Problem with Analytics")
        return super().handle(context)

    def __str__(self):
        return "Analytics"
