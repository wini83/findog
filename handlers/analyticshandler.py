import datetime
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
    plt.plot(data.index, data[column], color='#087E8B', lw=1, zorder=5)
    plt.title(column, fontsize=17)
    plt.xlabel('Period', fontsize=13)
    plt.xticks(fontsize=9)
    plt.ylabel('Amount', fontsize=13)
    plt.yticks(fontsize=9)
    plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()
    return


def plot_all_columns(data_frame):
    try:
        shutil.rmtree(PLOT_DIR)
        os.mkdir(PLOT_DIR)
    except FileNotFoundError:
        os.mkdir(PLOT_DIR)
    counter = 1
    for column in data_frame.columns:
        plot(data_frame, column, filename=f'{PLOT_DIR}/{counter}.png')
        counter += 1

def generate__current_index():
    today = datetime.date.today()
    year = today.year
    month = today.month
    return datetime.date(year=year, month=month, day=1)

class AnalyticsHandler(AbstractHandler):
    run_dry: bool = False

    def handle(self, context: HandlerContext) -> HandlerContext:
        logger.info("Analytics started")
        try:
            if not self.run_dry:
                dict_data = anaytics.generate_dataframe(context.payment_book)
                data_frame = pd.DataFrame.from_dict(dict_data, orient='index')
                # data_frame['Total'] = data_frame.sum(axis=1)
                # dupa.to_html("output.html")
                # plot_all_columns(data_frame)
                row = data_frame.filter(items=[generate__current_index()], axis=0)
                # row = row.transpose()
                # row.to_html("output.html")
                # plt.figure(figsize=(12, 4))
                # vector = row.iloc[0]
                colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
                vector = row.transpose()
                vector.to_html("output.html")
                ax = vector.plot(kind="bar",
                                 y = generate__current_index(),
                                 # autopct='%1.1f%%',
                                 #shadow=True,
                                 # colors=colors,
                                 #ylabel = "",
                                 #labeldistance=None,
                                 legend=True)
                ax.legend(bbox_to_anchor=(1, 1.02), loc='upper left')
                plt.savefig("output.png", dpi=300, bbox_inches='tight', pad_inches=0)
                logger.info("Analytics completed")
        except Exception as e:
            logger.exception("Problem with Analytics", exc_info=e)
            context.pushover.error("Problem with Analytics")
        return super().handle(context)

    def __str__(self):
        return "Analytics"
