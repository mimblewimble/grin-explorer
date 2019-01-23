from django.db.models import Count, Sum, Max, Min
from django.db.models.functions import TruncDay
from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import redirect

from blockchain.models import Block, Output
from chartit import DataPool, Chart


class BlockList(ListView):
    template_name = "explorer/block_list.html"
    context_object_name = "block_list"

    queryset = Block.objects.order_by("-timestamp")
    paginate_by = 20

    def get_block_chart(self):
        blockpivotdata = DataPool(
            series=[{
                'options': {
                    'source': Block.objects.raw("select 1 as hash, to_char(timestamp,'MM-dd') as niceday, "
                                                "max(total_difficulty) as total_difficulty, "
                                                "date(DATE_TRUNC('day', timestamp)) as date, count(hash) as num "
                                                "from blockchain_block "
                                                "group by DATE_TRUNC('day', timestamp),niceday order by date")
                },
                'terms': [
                    'niceday',
                    'num',
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
                    'niceday': ['num']
                }}, {
                'options': {
                    'type': 'line',
                    'xAxis': 1,
                    'yAxis': 1,
                    'legendIndex': 0,
                },
                'terms': {
                    'niceday': ['total_difficulty']
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
                            'style': {
                                'display': 'none'
                            }
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
                            'enabled': False
                        },
                    },
                    {
                        'title': {
                            'text': 'Total Diff'
                        },
                        'labels': {
                            'enabled': False
                        }
                    }
                ],
                'legend': {
                    'enabled': False
                },
            }
        )
        return blockpivcht

    def get_fee_chart(self):
        feepivotdata = DataPool(
            series=[{
                'options': {
                    'source': Block.objects.raw("select 1 as hash, to_char(timestamp,'MM-dd') as niceday, "
                                                "date(DATE_TRUNC('day', timestamp)) as date, sum(fee)/1000000 as fee "
                                                "from blockchain_block t1 join blockchain_kernel t2 "
                                                "on t2.block_id=t1.hash "
                                                "group by DATE_TRUNC('day', timestamp),niceday order by date")
                },
                'terms': [
                    'niceday',
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
                    'niceday': [
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
        return feepivcht

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if Block.objects.exists():
            context["highest_block"] = Block.objects.order_by("height").last()
            context["latest_block"] = Block.objects.order_by("timestamp").last()
            context["total_emission"] = Block.objects.order_by("total_difficulty").last().height * 60

            context["competing_chains"] = Block.objects \
                                               .filter(height__gte=context["highest_block"].height - 60) \
                                               .values("height") \
                                               .annotate(cnt=Count("height")) \
                                               .aggregate(Max("cnt"))["cnt__max"]
            context["forked_at"] = Block.objects \
                                        .filter(height__gte=context["highest_block"].height - 60) \
                                        .values("height") \
                                        .annotate(cnt=Count("height")) \
                                        .filter(cnt__gt=1) \
                                        .aggregate(Min("height"))["height__min"]

            context['thumb_chart_list'] = [self.get_block_chart(), self.get_fee_chart()]

        return context


class BlockDetail(DetailView):
    model = Block

    template_name = "explorer/block_detail.html"
    context_object_name = "blk"


class BlocksByHeight(TemplateView):
    template_name = "explorer/blocks_by_height.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["blocks"] = self.blocks
        context["height"] = self.height

        return context

    def get(self, request, height):
        self.blocks = Block.objects.filter(height=height).order_by("-total_difficulty")
        self.height = height

        if len(self.blocks) == 1:
            return redirect("block-detail", pk=self.blocks[0].hash, permanent=False)
        else:
            return super().get(request)


class Search(TemplateView):
    template_name = "explorer/search_results.html"
    results = None
    q_isdigit = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["q"] = self.q
        context["q_isdigit"] = self.q_isdigit
        context["results"] = self.results

        return context

    def get(self, request):
        self.q = request.GET.get("q", "").strip()

        # search query is valid block height
        if self.q.isdigit():
            self.q_isdigit = True

            if Block.objects.filter(height=self.q).count():
                return redirect("blocks-by-height", height=self.q, permanent=False)

        # require at least 8 characters
        if len(self.q) >= 6:
            self.results = Block.objects.filter(hash__startswith=self.q)

            # if only one result, redirect to found block
            if self.results.count() == 1:
                return redirect("block-detail", pk=self.results[0].hash, permanent=False)

        return super().get(request)
