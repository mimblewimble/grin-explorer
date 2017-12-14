from django.db.models import Count, Max, Min
from django.views.generic import ListView, DetailView, TemplateView
from django.shortcuts import redirect

from blockchain.models import Block, Output


class BlockList(ListView):
    template_name = "explorer/block_list.html"
    context_object_name = "block_list"

    queryset = Block.objects.order_by("-timestamp")
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["highest_block"] = Block.objects.order_by("height").last()
        context["latest_block"] = Block.objects.order_by("timestamp").last()
        context["total_emission"] = Output.objects.filter(output_type="Coinbase").count() * 50

        context["competing_chains"] = Block.objects \
                                           .filter(height__gte=context["highest_block"].height - 100) \
                                           .values("height") \
                                           .annotate(cnt=Count("height")) \
                                           .aggregate(Max("cnt"))["cnt__max"]
        context["forked_at"] = Block.objects \
                                    .filter(height__gte=context["highest_block"].height - 1000) \
                                    .values("height") \
                                    .annotate(cnt=Count("height")) \
                                    .filter(cnt__gt=1) \
                                    .aggregate(Min("height"))["height__min"]

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
