from django.db.models import Count, Max, Min
from django.db.models.functions import TruncDay
from django.shortcuts import render_to_response

from blockchain.models import Block, Output
from chartit import DataPool, Chart


def block_chart(_):
    blockpivotdata = DataPool(
        series=[{
            'options': {
                'source': Block.objects.raw("select 1 as hash, "
                                            "max(total_difficulty) as total_difficulty, "
                                            "date(DATE_TRUNC('day', timestamp)) as date, count(hash) as blocks "
                                            "from blockchain_block "
                                            "group by DATE_TRUNC('day', timestamp) order by date")
            },
            'terms': [
                'date',
                'blocks',
                'total_difficulty',
            ]
        }]
    )

    blockpivcht = Chart(
        datasource=blockpivotdata,
        series_options=[{
            'options': {
                'type': 'line',
                'xAxis': 0,
                'yAxis': 0,
                'zIndex': 1,
                'legendIndex': 1,
            },
            'terms': {
                'date': ['blocks']
            }}, {
            'options': {
                'type': 'line',
                'xAxis': 1,
                'yAxis': 1,
                'legendIndex': 0,
            },
            'terms': {
                'date': ['total_difficulty']
            }
        }],
        chart_options={
            'title': {
                'text': 'Blocks and Total Difficulty'
            },
            'xAxis': [
                {
                    'title': {
                        'text': 'Date',
                    },
                    'labels': {
                        'enabled': True
                    }
                },
                {
                    'title': {
                        'text': 'Date',
                        'style': {
                            'display': 'none'
                        }
                    },
                    'labels': {
                        'enabled': False
                    },
                    'lineColor': 'transparent',
                    'tickLength': 0,
                }
            ],
            'yAxis': [
                {
                    'title': {
                        'text': 'Blocks',
                        'style': {
                            'color': '#70b3ef'
                        }
                    },
                    'labels': {
                        'enabled': True
                    },
                },
                {
                    'title': {
                        'text': 'Total Difficulty'
                    },
                    'labels': {
                        'enabled': True
                    }
                }
            ],
            'legend': {
                'enabled': True
            },
        }
    )
    return render_to_response('explorer/block_chart.html', {'blockchart': blockpivcht})


def fee_chart(_):
    feepivotdata = DataPool(
        series=[{
            'options': {
                'source': Block.objects.raw("select 1 as hash, "
                                            "date(DATE_TRUNC('day', timestamp)) as date, sum(fee)/1000000 as fee "
                                            "from blockchain_block t1 join blockchain_kernel t2 "
                                            "on t2.block_id=t1.hash "
                                            "group by DATE_TRUNC('day', timestamp) order by date")
            },
            'terms': [
                'date',
                'fee'
            ]
        }]
    )

    feepivcht = Chart(
        datasource=feepivotdata,
        series_options=[{
            'options': {
                'type': 'line',
                'stacking': False
            },
            'terms': {
                'date': [
                    'fee',
                ]
            }
        }],
        chart_options={
            'title': {
                'text': 'Transaction Fee Chart'},
            'xAxis': {
                'title': {
                    'text': 'Date'}},
            'yAxis': {
                'title': {
                    'text': 'Tx Fee'}},
            'legend': {
                'enabled': False},
            'credits': {
                'enabled': False}},
    )
    return render_to_response('explorer/fee_chart.html', {'feechart': feepivcht})
