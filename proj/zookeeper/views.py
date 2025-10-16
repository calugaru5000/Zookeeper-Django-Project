# proj/zookeeper/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import AnimalForm

from .models import Animal, Species


# 1️⃣ List View — show only the logged-in user's animals, with filters
class AnimalListView(LoginRequiredMixin, ListView):
    model = Animal
    template_name = 'Zoo/animals_list.html'
    context_object_name = 'animals'

    def get_queryset(self):
        qs = Animal.objects.filter(owner=self.request.user)
        species = self.request.GET.get('species')
        enclosure = self.request.GET.get('enclosure')
        q = self.request.GET.get('q')

        if species:
            qs = qs.filter(species__id=species)
        if enclosure:
            qs = qs.filter(enclosure__icontains=enclosure)
        if q:
            qs = qs.filter(name__icontains=q)

        return qs.select_related('species')
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context['species_list'] = Species.objects.all()
        return context

# 2️⃣ Detail View — also restricted to current user
class AnimalDetailView(LoginRequiredMixin, DetailView):
    model = Animal
    template_name = 'Zoo/animal_detail.html'
    context_object_name = 'animal'

    def get_queryset(self):
        return Animal.objects.filter(owner=self.request.user)


# 3️⃣ Create / Update / Delete Views — generic CBVs
class AnimalCreateView(LoginRequiredMixin, CreateView):
    model = Animal
    form_class=AnimalForm
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('animals_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class AnimalUpdateView(LoginRequiredMixin, UpdateView):
    model = Animal
    fields = ['name', 'species', 'enclosure']
    template_name = 'Zoo/animal_form.html'
    success_url = reverse_lazy('animals_list')

    def get_queryset(self):
        return Animal.objects.filter(owner=self.request.user)


class AnimalDeleteView(LoginRequiredMixin, DeleteView):
    model = Animal
    template_name = 'Zoo/confirm_delete.html'
    success_url = reverse_lazy('animals_list')

    def get_queryset(self):
        return Animal.objects.filter(owner=self.request.user)


# 4️⃣ Feed View — POST only
@require_POST
@login_required
def feed_view(request, pk):
    animal = get_object_or_404(Animal, pk=pk, owner=request.user)
    animal.last_fed_at = timezone.now()
    animal.save()
    return redirect('animal_detail', pk=pk)
