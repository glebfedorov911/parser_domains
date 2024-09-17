from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from .forms import FileForm


class ParserView(TemplateView):
    template_name = "parser/index.html"
    form_class = FileForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Парсер доменов"
        return context

    async def get(self, request, *args, **kwargs):
        return render(request, self.template_name, context={"title": "Парсер доменов", "form": self.form_class})

    async def post(self, request, *args, **kwargs):
        print(self.request.FILES)
        return redirect(reverse("parser"))